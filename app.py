import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import locale
import numpy as np
import time

# Configurar locale para português do Brasil
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except:
        st.warning("Não foi possível configurar o locale para português. Algumas formatações podem não aparecer corretamente.")

# ========== Carregar CSS de arquivo externo ==========
def load_css(css_file):
    with open(css_file, 'r') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Carregar CSS
if os.path.exists('style.css'):
    load_css('style.css')
else:
    st.warning("Arquivo style.css não encontrado. O estilo padrão será usado.")

# ========== Funções Auxiliares ==========
def carregar_dados():
    """Carregar dados do arquivo CSV."""
    csv_file = "despesas_br.csv"
    if os.path.exists(csv_file):
        return pd.read_csv(csv_file)
    else:
        return pd.DataFrame(columns=["Data", "Descrição", "Categoria", "Valor", "Tipo"])

def calcular_metricas(df):
    """Calcular as métricas financeiras."""
    total_despesas = df[df['Tipo'] == 'Despesa']['Valor'].sum()
    total_receitas = df[df['Tipo'] == 'Receita']['Valor'].sum() if 'Receita' in df['Tipo'].values else 0
    saldo = total_receitas - total_despesas
    return total_despesas, total_receitas, saldo

def exibir_metricas(total_despesas, total_receitas, saldo, container=None):
    """Exibir as métricas em cards."""
    destino = container if container else st
    
    col1, col2, col3 = destino.columns(3)
    
    with col1:
        destino.markdown("""
        <div class="metric-card">
            <div class="metric-value">R$ {:.2f}</div>
            <div class="metric-label">TOTAL DESPESAS</div>
        </div>
        """.format(total_despesas), unsafe_allow_html=True)
    
    with col2:
        destino.markdown("""
        <div class="metric-card">
            <div class="metric-value">R$ {:.2f}</div>
            <div class="metric-label">TOTAL RECEITAS</div>
        </div>
        """.format(total_receitas), unsafe_allow_html=True)
    
    with col3:
        destino.markdown("""
        <div class="metric-card">
            <div class="metric-value" style="color: {};">R$ {:.2f}</div>
            <div class="metric-label">SALDO</div>
        </div>
        """.format('green' if saldo >= 0 else 'red', saldo), unsafe_allow_html=True)

# ========== Estado da Aplicação ==========
# Inicializar o estado da sessão para controlar atualizações
if 'data' not in st.session_state:
    st.session_state.data = carregar_dados()

if 'dados_atualizados' not in st.session_state:
    st.session_state.dados_atualizados = False

# ========== Interface Principal ==========
st.title("💸 Gerenciador Inteligente de Despesas")

# Container para métricas - será atualizado dinamicamente
metricas_container = st.container()

# Calcular métricas iniciais
total_despesas, total_receitas, saldo = calcular_metricas(st.session_state.data)

# Exibir métricas iniciais
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
            # Formatar a data para o padrão brasileiro
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
            
            # Marcar que os dados foram atualizados
            st.session_state.dados_atualizados = True
            
            # Mensagem de sucesso
            st.markdown(f"""
            <div class="success-message">
                <strong>Adicionado:</strong> {description} - R$ {amount:.2f} ({category})
            </div>
            """, unsafe_allow_html=True)
            
            # Recalcular métricas
            novo_total_despesas, novo_total_receitas, novo_saldo = calcular_metricas(st.session_state.data)
            
            # Atualizar as métricas na interface
            with metricas_container:
                st.empty()  # Limpar o container
                exibir_metricas(novo_total_despesas, novo_total_receitas, novo_saldo)
    
    st.markdown('</div>', unsafe_allow_html=True)

# === Aba de Análise ===
with tab2:
    if st.session_state.data.empty:
        st.info("Adicione algumas despesas para visualizar a análise.")
    else:
        # Análise por categoria
        st.subheader("📈 Análise de Despesas por Categoria")
        
        # Filtro de período
        col1, col2 = st.columns(2)
        with col1:
            periodo = st.selectbox("Período", ["Tudo", "Este Mês", "Últimos 3 Meses"])
        
        with col2:
            tipo_analise = st.selectbox("Tipo", ["Despesas", "Receitas", "Ambos"])
        
        # Filtrar dados com base na seleção
        filtered_data = st.session_state.data.copy()
        
        if periodo != "Tudo":
            # Converter coluna de data para datetime
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
            # Agrupar por categoria
            category_totals = filtered_data.groupby('Categoria')['Valor'].sum().sort_values(ascending=False)
            
            # Cores personalizadas
            cores = plt.cm.viridis(np.linspace(0, 1, len(category_totals)))
            
            # Gráfico de Barras
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = category_totals.plot(kind="bar", ax=ax, color=cores)
            ax.set_ylabel("Valor (R$)")
            ax.set_title("Total por Categoria")
            
            # Adicionar valores no topo das barras
            for i, bar in enumerate(bars.patches):
                valor = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width()/2., 
                    valor + 5, 
                    f'R$ {valor:.2f}', 
                    ha='center', 
                    va='bottom',
                    fontweight='bold'
                )
                
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)

            # Gráfico de Pizza
            st.subheader("🥧 Distribuição por Categoria")
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            
            wedges, texts, autotexts = ax2.pie(
                category_totals, 
                labels=None, 
                autopct="%1.1f%%",
                shadow=True,
                colors=cores,
                startangle=90,
                wedgeprops={'linewidth': 1, 'edgecolor': 'white'}
            )
            
            # Melhorar a aparência dos percentuais
            for autotext in autotexts:
                autotext.set_fontsize(10)
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                
            ax2.set_title("Proporção por Categoria")
            
            # Adicionar legenda fora do gráfico
            ax2.legend(
                wedges, 
                category_totals.index,
                title="Categorias",
                loc="center left",
                bbox_to_anchor=(1, 0, 0.5, 1)
            )
            
            plt.tight_layout()
            st.pyplot(fig2)
            
            # Tabela de resumo
            st.subheader("📊 Resumo por Categoria")
            resumo = pd.DataFrame({
                'Categoria': category_totals.index,
                'Valor Total (R$)': category_totals.values,
                'Porcentagem (%)': (category_totals.values / category_totals.values.sum() * 100).round(2)
            })
            st.dataframe(resumo, hide_index=True)

# === Aba de Registros ===
with tab3:
    st.subheader("📋 Todos os Registros")
    
    # Filtro e ordenação
    col1, col2 = st.columns(2)
    
    with col1:
        filtro_categoria = st.multiselect(
            "Filtrar por Categoria", 
            options=["Todas"] + sorted(st.session_state.data['Categoria'].unique().tolist() if not st.session_state.data.empty else []),
            default="Todas"
        )
    
    with col2:
        ordenar_por = st.selectbox(
            "Ordenar por", 
            options=["Data (mais recente)", "Data (mais antiga)", "Valor (maior)", "Valor (menor)"]
        )
    
    # Aplicar filtros e ordenação
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
    
    # Estilizar o DataFrame
    if not filtered_data.empty:
        # Função para colorir apenas a coluna Tipo
        def colorir_tipo(val):
            if val == 'Despesa':
                return 'color: red; font-weight: bold'
            elif val == 'Receita':
                return 'color: green; font-weight: bold'
            return ''
        
        # Aplicar estilo apenas à coluna Tipo
        styled_df = filtered_data.style.applymap(
            colorir_tipo, 
            subset=['Tipo']
        )
        
        st.dataframe(
            styled_df,
            height=400,
            hide_index=True
        )
    else:
        st.info("Sem registros para mostrar.")

# ========== Footer ==========
st.markdown("""
<div class="footer">
    💰 Gerenciador Inteligente de Despesas - Desenvolvido com Streamlit - 2023
</div>
""", unsafe_allow_html=True)