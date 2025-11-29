import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import locale
import numpy as np
import time
import threading
import logging
import json
import socket
from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server, REGISTRY
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# ========== Configuração de Tags Unificadas ==========
SERVICE_NAME = os.getenv("DD_SERVICE", "gerenciador-despesas")
ENV_NAME = os.getenv("DD_ENV", "production")
VERSION = os.getenv("DD_VERSION", "0.2")
HOSTNAME = os.getenv("HOSTNAME", socket.gethostname())
NAMESPACE = os.getenv("KUBE_NAMESPACE", "gerenciador-despesas")
POD_NAME = os.getenv("POD_NAME", HOSTNAME)

# ========== Configuração de Logging (JSON para Loki) ==========
# Emitir sempre uma única linha JSON para stdout (facilita scraping por promtail)
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()]
)
# Não deixar o LoggingInstrumentor alterar o formato do logging (evita KeyError)
# iremos enriquecer logs manualmente
LoggingInstrumentor().instrument(set_logging_format=False)

class StructuredLogger:
    """Logger que emite JSON com metadata + trace ids quando disponíveis."""
    def __init__(self, name):
        self.logger = logging.getLogger(name)

    def _current_trace_fields(self):
        try:
            span = trace.get_current_span()
            ctx = span.get_span_context()
            if ctx is None:
                return {}
            trace_id = getattr(ctx, "trace_id", 0)
            span_id = getattr(ctx, "span_id", 0)
            fields = {}
            if trace_id:
                fields["dd.trace_id"] = format(trace_id, "032x")
            if span_id:
                fields["dd.span_id"] = format(span_id, "016x")
            return fields
        except Exception:
            return {}

    def _log(self, level, message, **kwargs):
        # accept `extra` key to be compatible with previous calls
        extra = kwargs.pop("extra", {})
        if not isinstance(extra, dict):
            extra = {}

        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": SERVICE_NAME,
            "env": ENV_NAME,
            "version": VERSION,
            "pod": POD_NAME,
            "namespace": NAMESPACE,
            "level": level.upper(),
            "logger": self.logger.name,
            "message": message,
        }
        log_data.update(self._current_trace_fields())
        log_data.update(extra)
        log_data.update(kwargs)
        # Emitir JSON (uma linha)
        getattr(self.logger, level)(json.dumps(log_data, default=str))

    def info(self, message, **kwargs):
        self._log("info", message, **kwargs)

    def error(self, message, **kwargs):
        self._log("error", message, **kwargs)

    def warning(self, message, **kwargs):
        self._log("warning", message, **kwargs)

    def debug(self, message, **kwargs):
        self._log("debug", message, **kwargs)

logger = StructuredLogger(__name__)

# ========== OpenTelemetry (traces + optional metrics export via OTLP) ==========
def sanitize_otlp_endpoint(raw: str) -> str:
    if not raw:
        return ""
    # OTLP gRPC exporter expects host:port; strip scheme if present
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw.split("://", 1)[1]
    return raw

OTLP_ENDPOINT = sanitize_otlp_endpoint(
    os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", os.getenv("OTLP_GRPC_ENDPOINT", "tempo.monitoring.svc.cluster.local:4317"))
)

if 'otel_configured' not in st.session_state:
    try:
        resource = Resource.create({
            "service.name": SERVICE_NAME,
            "service.version": VERSION,
            "service.namespace": NAMESPACE,
            "deployment.environment": ENV_NAME,
            "service.instance.id": POD_NAME,
            "host.name": HOSTNAME,
            "k8s.namespace.name": NAMESPACE,
            "k8s.pod.name": POD_NAME,
            "k8s.cluster.name": os.getenv("K8S_CLUSTER_NAME", "gke-test-1"),
            "cloud.provider": "gcp",
            "cloud.platform": "gcp_kubernetes_engine",
        })

        # Tracing
        trace.set_tracer_provider(TracerProvider(resource=resource))
        if OTLP_ENDPOINT:
            try:
                otlp_trace_exporter = OTLPSpanExporter(endpoint=OTLP_ENDPOINT, insecure=True)
                span_processor = BatchSpanProcessor(otlp_trace_exporter)
                trace.get_tracer_provider().add_span_processor(span_processor)
                logger.info("OTLP trace exporter configurado", otlp_endpoint=OTLP_ENDPOINT)
            except Exception as e:
                logger.warning("Falha ao configurar OTLP trace exporter, continuando sem exporter", error=str(e))
        else:
            logger.warning("OTLP endpoint vazio — traces serão coletados localmente sem exportação")

        # Metrics (optional OTLP export); we still expose Prometheus via start_http_server
        if OTLP_ENDPOINT:
            try:
                otlp_metric_exporter = OTLPMetricExporter(endpoint=OTLP_ENDPOINT, insecure=True)
                metric_reader = PeriodicExportingMetricReader(otlp_metric_exporter)
                metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))
                logger.info("OTLP metric exporter configurado", otlp_endpoint=OTLP_ENDPOINT)
            except Exception as me:
                logger.warning("Não foi possível configurar OTLP metric exporter", error=str(me))

    except Exception as e:
        logger.error("Erro ao configurar OpenTelemetry", error=str(e))

    st.session_state.otel_configured = True

tracer = trace.get_tracer(__name__)

# ========== Métricas Prometheus (criação segura) ==========
def safe_get(name):
    try:
        return REGISTRY._names_to_collectors.get(name)
    except Exception:
        return None

def get_or_create_counter(name, description, labelnames=None):
    existing = safe_get(name)
    if existing:
        return existing
    return Counter(name, description, labelnames or [])

def get_or_create_histogram(name, description, labelnames=None):
    existing = safe_get(name)
    if existing:
        return existing
    return Histogram(name, description, labelnames or [])

def get_or_create_gauge(name, description, labelnames=None):
    existing = safe_get(name)
    if existing:
        return existing
    return Gauge(name, description, labelnames or [])

def get_or_create_info(name, description):
    existing = safe_get(name)
    if existing:
        return existing
    return Info(name, description)

despesas_adicionadas = get_or_create_counter('despesas_adicionadas_total', 'Total de despesas adicionadas', ['categoria', 'tipo'])
receitas_adicionadas = get_or_create_counter('receitas_adicionadas_total', 'Total de receitas adicionadas', ['categoria'])
tempo_processamento = get_or_create_histogram('operacao_duracao_segundos', 'Tempo de processamento de operações', ['operacao'])
tempo_carregamento_dados = get_or_create_histogram('carregamento_dados_segundos', 'Tempo de carregamento de dados do CSV')
saldo_atual = get_or_create_gauge('saldo_atual_reais', 'Saldo atual em reais')
total_despesas_gauge = get_or_create_gauge('total_despesas_reais', 'Total de despesas em reais')
total_receitas_gauge = get_or_create_gauge('total_receitas_reais', 'Total de receitas em reais')
registros_totais = get_or_create_gauge('registros_totais', 'Total de registros no sistema')
registros_por_categoria = get_or_create_gauge('registros_por_categoria', 'Registros por categoria', ['categoria'])
app_info = get_or_create_info('aplicacao', 'Informações da aplicação')

try:
    if hasattr(app_info, 'info'):
        app_info.info({
            'version': VERSION,
            'name': SERVICE_NAME,
            'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
            'framework': 'streamlit'
        })
except Exception:
    pass

app_health = get_or_create_gauge('app_health', 'Status de saúde da aplicação (1=saudável, 0=não saudável)')
app_health.set(1)

# ========== Iniciar Servidor de Métricas Prometheus ==========
def iniciar_metricas():
    try:
        port = int(os.getenv("METRICS_PORT", "8000"))
        start_http_server(port)
        logger.info("Servidor de métricas Prometheus iniciado", metrics_port=port)
    except Exception as e:
        logger.error("Erro ao iniciar servidor de métricas: " + str(e))
        try:
            app_health.set(0)
        except Exception:
            pass

if 'metricas_iniciadas' not in st.session_state:
    threading.Thread(target=iniciar_metricas, daemon=True).start()
    st.session_state.metricas_iniciadas = True

# ========== Configurações de locale, css e funções de negócio ==========
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')
except Exception:
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except Exception:
        logger.warning("Não foi possível configurar o locale para português")

def load_css(css_file):
    with tracer.start_as_current_span("load_css"):
        try:
            with open(css_file, 'r') as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
            logger.info(f"CSS carregado: {css_file}")
        except Exception as e:
            logger.error(f"Erro ao carregar CSS: {e}")

if os.path.exists('style.css'):
    load_css('style.css')
else:
    logger.warning("Arquivo style.css não encontrado")

def carregar_dados():
    with tracer.start_as_current_span("carregar_dados") as span:
        csv_file = "despesas_br.csv"
        start_time = time.time()
        try:
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file)
                span.set_attribute("registros_carregados", len(df))
                logger.info(f"Dados carregados: {len(df)} registros")
                tempo_carregamento_dados.observe(time.time() - start_time)
                return df
            else:
                span.set_attribute("novo_arquivo", True)
                logger.info("Arquivo CSV não encontrado, criando novo DataFrame")
                return pd.DataFrame(columns=["Data", "Descrição", "Categoria", "Valor", "Tipo"])
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {e}")
            try:
                span.record_exception(e)
            except Exception:
                pass
            app_health.set(0)
            return pd.DataFrame(columns=["Data", "Descrição", "Categoria", "Valor", "Tipo"])

def calcular_metricas(df):
    with tracer.start_as_current_span("calcular_metricas") as span:
        start_time = time.time()
        try:
            total_despesas = df[df['Tipo'] == 'Despesa']['Valor'].sum() if 'Tipo' in df.columns else 0.0
            total_receitas = df[df['Tipo'] == 'Receita']['Valor'].sum() if 'Tipo' in df.columns else 0.0
            saldo = float(total_receitas) - float(total_despesas)
            total_despesas_gauge.set(float(total_despesas))
            total_receitas_gauge.set(float(total_receitas))
            saldo_atual.set(float(saldo))
            registros_totais.set(len(df))
            if not df.empty and 'Categoria' in df.columns:
                categorias = df.groupby('Categoria').size()
                for categoria, count in categorias.items():
                    registros_por_categoria.labels(categoria=categoria).set(int(count))
            span.set_attribute("total_despesas", float(total_despesas))
            span.set_attribute("total_receitas", float(total_receitas))
            span.set_attribute("saldo", float(saldo))
            span.set_attribute("total_registros", len(df))
            duracao = time.time() - start_time
            tempo_processamento.labels(operacao='calcular_metricas').observe(duracao)
            logger.info(f"Métricas calculadas - Despesas: R$ {float(total_despesas):.2f}, Receitas: R$ {float(total_receitas):.2f}, Saldo: R$ {float(saldo):.2f}")
            return float(total_despesas), float(total_receitas), float(saldo)
        except Exception as e:
            logger.error(f"Erro ao calcular métricas: {e}")
            try:
                span.record_exception(e)
            except Exception:
                pass
            return 0.0, 0.0, 0.0

def exibir_metricas(total_despesas, total_receitas, saldo, container=None):
    """Exibir as métricas em cards"""
    with tracer.start_as_current_span("exibir_metricas"):
        destino = container if container else st
        
        col1, col2, col3 = destino.columns(3)
        
        with col1:
            destino.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>R$ {total_despesas:.2f}</div>
                <div class='metric-label'>TOTAL DESPESAS</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            destino.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>R$ {total_receitas:.2f}</div>
                <div class='metric-label'>TOTAL RECEITAS</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            cor_saldo = 'green' if saldo >= 0 else 'red'
            destino.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value' style='color: {cor_saldo};'>R$ {saldo:.2f}</div>
                <div class='metric-label'>SALDO</div>
            </div>
            """, unsafe_allow_html=True)

# ========== Streamlit UI (mantido) ==========
if 'data' not in st.session_state:
    st.session_state.data = carregar_dados()

if 'dados_atualizados' not in st.session_state:
    st.session_state.dados_atualizados = False

st.title("💸 Gerenciador Inteligente de Despesas")
metricas_container = st.container()
total_despesas, total_receitas, saldo = calcular_metricas(st.session_state.data)

with metricas_container:
    if not st.session_state.data.empty:
        exibir_metricas(total_despesas, total_receitas, saldo)

# ========== Abas principais ==========
tab1, tab2, tab3 = st.tabs(["📝 Nova Despesa", "📊 Análise", "📋 Registros"])

# === Aba de Nova Despesa ===
with tab1:
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    
    with st.form("expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Data", format="DD/MM/YYYY")
            description = st.text_input("Descrição")
        
        with col2:
            amount = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            tipo = st.selectbox("Tipo", options=["Despesa", "Receita"])
        
        # Categorias padrão
        categorias = ["Alimentação", "Transporte", "Entretenimento", "Serviços", "Compras", "Outros"]
        if 'Categoria' in st.session_state.data.columns and not st.session_state.data.empty:
            categorias = sorted(list(set(categorias + st.session_state.data['Categoria'].unique().tolist())))
        
        category = st.selectbox("Categoria", options=categorias)

        submitted = st.form_submit_button("Adicionar")

        if submitted and description and amount > 0:
            with tracer.start_as_current_span("adicionar_registro") as span:
                start_time = time.time()
                
                try:
                    # Formatar a data
                    formatted_date = date.strftime("%d/%m/%Y")
                    
                    new_entry = {
                        "Data": formatted_date, 
                        "Descrição": description, 
                        "Categoria": category, 
                        "Valor": amount, 
                        "Tipo": tipo
                    }
                    
                    # Adicionar ao DataFrame
                    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_entry])], ignore_index=True)
                    
                    # Salvar no CSV
                    st.session_state.data.to_csv("despesas_br.csv", index=False)
                    
                    # Atualizar métricas
                    if tipo == "Despesa":
                        despesas_adicionadas.labels(categoria=category, tipo=tipo).inc()
                    else:
                        receitas_adicionadas.labels(categoria=category).inc()
                    
                    # Adicionar atributos ao span
                    span.set_attribute("tipo", tipo)
                    span.set_attribute("categoria", category)
                    span.set_attribute("valor", float(amount))
                    span.set_attribute("descricao", description)
                    
                    # Log estruturado
                    logger.info(
                        "Registro adicionado",
                        tipo=tipo,
                        categoria=category,
                        valor=amount,
                        descricao=description
                    )
                    
                    st.session_state.dados_atualizados = True
                    
                    # Mensagem de sucesso
                    st.success(f"✅ {tipo} adicionada: {description} - R$ {amount:.2f} ({category})")
                    
                    # Recalcular métricas
                    novo_total_despesas, novo_total_receitas, novo_saldo = calcular_metricas(st.session_state.data)
                    
                    # Registrar tempo de processamento
                    duracao = time.time() - start_time
                    tempo_processamento.labels(operacao='adicionar_registro').observe(duracao)
                    
                    # Atualizar interface
                    with metricas_container:
                        exibir_metricas(novo_total_despesas, novo_total_receitas, novo_saldo)
                    
                    # Recarregar a página para limpar o formulário
                    st.rerun()
                        
                except Exception as e:
                    logger.error(f"Erro ao adicionar registro: {e}")
                    span.record_exception(e)
                    st.error(f"❌ Erro ao adicionar registro: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# === Aba de Análise ===
with tab2:
    if st.session_state.data.empty:
        st.info("📊 Adicione algumas despesas para visualizar a análise.")
    else:
        with tracer.start_as_current_span("gerar_analise"):
            start_time = time.time()
            
            st.subheader("📈 Análise de Despesas por Categoria")
            
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                periodo = st.selectbox("Período", ["Tudo", "Este Mês", "Últimos 3 Meses"])
            
            with col2:
                tipo_analise = st.selectbox("Tipo", ["Despesas", "Receitas", "Ambos"])
            
            # Filtrar dados
            filtered_data = st.session_state.data.copy()
            
            if periodo != "Tudo":
                filtered_data['Data'] = pd.to_datetime(filtered_data['Data'], format='%d/%m/%Y', errors='coerce')
                hoje = pd.Timestamp.now()
                
                if periodo == "Este Mês":
                    filtro_data = (filtered_data['Data'].dt.month == hoje.month) & (filtered_data['Data'].dt.year == hoje.year)
                    filtered_data = filtered_data[filtro_data]
                elif periodo == "Últimos 3 Meses":
                    tres_meses_atras = hoje - pd.DateOffset(months=3)
                    filtro_data = (filtered_data['Data'] >= tres_meses_atras) & (filtered_data['Data'] <= hoje)
                    filtered_data = filtered_data[filtro_data]
            
            if tipo_analise != "Ambos":
                filtered_data = filtered_data[filtered_data['Tipo'] == tipo_analise.rstrip('s')]
            
            if filtered_data.empty:
                st.info("Sem dados para o período e tipo selecionados.")
            else:
                category_totals = filtered_data.groupby('Categoria')['Valor'].sum().sort_values(ascending=False)
                cores = plt.cm.viridis(np.linspace(0, 1, len(category_totals)))
                
                # Gráfico de Barras
                fig, ax = plt.subplots(figsize=(10, 6))
                bars = category_totals.plot(kind="bar", ax=ax, color=cores)
                ax.set_ylabel("Valor (R$)")
                ax.set_title("Total por Categoria")
                
                for i, bar in enumerate(bars.patches):
                    valor = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., valor + 5, f'R$ {valor:.2f}', 
                           ha='center', va='bottom', fontweight='bold')
                
                plt.xticks(rotation=45)
                plt.tight_layout()
                st.pyplot(fig)

                # Gráfico de Pizza
                st.subheader("🥧 Distribuição por Categoria")
                fig2, ax2 = plt.subplots(figsize=(10, 6))
                
                wedges, texts, autotexts = ax2.pie(
                    category_totals, labels=None, autopct="%1.1f%%",
                    shadow=True, colors=cores, startangle=90,
                    wedgeprops={'linewidth': 1, 'edgecolor': 'white'}
                )
                
                for autotext in autotexts:
                    autotext.set_fontsize(10)
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                
                ax2.set_title("Proporção por Categoria")
                ax2.legend(wedges, category_totals.index, title="Categorias",
                          loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
                
                plt.tight_layout()
                st.pyplot(fig2)
                
                # Tabela de resumo
                st.subheader("📊 Resumo por Categoria")
                resumo = pd.DataFrame({
                    'Categoria': category_totals.index,
                    'Valor Total (R$)': category_totals.values,
                    'Porcentagem (%)': (category_totals.values / category_totals.values.sum() * 100).round(2)
                })
                st.dataframe(resumo, hide_index=True, use_container_width=True)
            
            # Registrar tempo
            duracao = time.time() - start_time
            tempo_processamento.labels(operacao='gerar_analise').observe(duracao)
            logger.info(f"Análise gerada em {duracao:.2f} segundos")

# === Aba de Registros ===
with tab3:
    with tracer.start_as_current_span("exibir_registros"):
        st.subheader("📋 Todos os Registros")
        
        if st.session_state.data.empty:
            st.info("📝 Nenhum registro encontrado. Adicione uma despesa ou receita!")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                categorias_unicas = sorted(st.session_state.data['Categoria'].unique().tolist())
                filtro_categoria = st.multiselect(
                    "Filtrar por Categoria", 
                    options=["Todas"] + categorias_unicas,
                    default=["Todas"]
                )
            
            with col2:
                ordenar_por = st.selectbox(
                    "Ordenar por", 
                    options=["Data (mais recente)", "Data (mais antiga)", "Valor (maior)", "Valor (menor)"]
                )
            
            filtered_data = st.session_state.data.copy()
            
            if "Todas" not in filtro_categoria and filtro_categoria:
                filtered_data = filtered_data[filtered_data['Categoria'].isin(filtro_categoria)]
            
            if ordenar_por == "Data (mais recente)":
                filtered_data['Data_temp'] = pd.to_datetime(filtered_data['Data'], format='%d/%m/%Y', errors='coerce')
                filtered_data = filtered_data.sort_values(by="Data_temp", ascending=False)
                filtered_data = filtered_data.drop(columns=['Data_temp'])
            elif ordenar_por == "Data (mais antiga)":
                filtered_data['Data_temp'] = pd.to_datetime(filtered_data['Data'], format='%d/%m/%Y', errors='coerce')
                filtered_data = filtered_data.sort_values(by="Data_temp", ascending=True)
                filtered_data = filtered_data.drop(columns=['Data_temp'])
            elif ordenar_por == "Valor (maior)":
                filtered_data = filtered_data.sort_values(by="Valor", ascending=False)
            elif ordenar_por == "Valor (menor)":
                filtered_data = filtered_data.sort_values(by="Valor", ascending=True)
            
            if not filtered_data.empty:
                # Exibir dataframe
                st.dataframe(
                    filtered_data,
                    height=400,
                    hide_index=True,
                    use_container_width=True
                )
                
                # Estatísticas
                st.subheader("📊 Estatísticas")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total de Registros", len(filtered_data))
                
                with col2:
                    total_filtrado = filtered_data['Valor'].sum()
                    st.metric("Valor Total", f"R$ {total_filtrado:.2f}")
                
                with col3:
                    media = filtered_data['Valor'].mean()
                    st.metric("Valor Médio", f"R$ {media:.2f}")
            else:
                st.info("Sem registros para mostrar com os filtros selecionados.")

# ========== Footer ==========
st.markdown("""
<div style="text-align: center; padding: 20px; margin-top: 50px; border-top: 1px solid #ddd;">
    💰 <b>Gerenciador Inteligente de Despesas</b> - Desenvolvido com Streamlit<br>
    📊 Métricas: <a href="http://localhost:8000/metrics" target="_blank">Prometheus</a> | 
    🔍 Traces: Tempo | 📝 Logs: Loki
</div>
""", unsafe_allow_html=True)