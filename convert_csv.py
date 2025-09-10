import pandas as pd
import locale
from datetime import datetime

# Tentar configurar o locale para português do Brasil
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except:
        print("Não foi possível configurar o locale para português.")

# Carregar os dados
df = pd.read_csv('expense_data_1.csv')

# Dicionário de tradução para categorias
categoria_traducao = {
    'Food': 'Alimentação',
    'Transportation': 'Transporte',
    'Social Life': 'Vida Social',
    'Household': 'Doméstico',
    'Apparel': 'Vestuário',
    'Beauty': 'Beleza',
    'Education': 'Educação',
    'Gift': 'Presente',
    'Petty cash': 'Dinheiro',
    'Self-development': 'Autodesenvolvimento',
    'Salary': 'Salário',
    'Allowance': 'Mesada',
    'Other': 'Outros'
}

# Dicionário de tradução para tipo de transação
tipo_traducao = {
    'Expense': 'Despesa',
    'Income': 'Receita'
}

# Nova estrutura do DataFrame
novo_df = pd.DataFrame(columns=[
    "Data", "Descrição", "Categoria", "Valor", "Tipo"
])

# Converter e adicionar cada linha
for _, row in df.iterrows():
    try:
        # Se já tiver dados em português, use-os
        if pd.notna(row.get('Data')) and pd.notna(row.get('Descrição')):
            nova_linha = {
                "Data": row.get('Data'),
                "Descrição": row.get('Descrição'),
                "Categoria": row.get('Categoria'),
                "Valor": row.get('Valor'),
                "Tipo": "Despesa"  # Assumindo despesa por padrão
            }
        else:
            # Converter a data para formato brasileiro
            data = None
            if pd.notna(row.get('Date')):
                try:
                    # Tentar converter a data
                    data_obj = datetime.strptime(str(row.get('Date')), '%m/%d/%Y %H:%M')
                    data = data_obj.strftime('%d/%m/%Y')
                except:
                    # Se falhar, manter o valor original
                    data = str(row.get('Date'))
            
            # Pegar a descrição da nota ou descrição
            descricao = row.get('Note') if pd.notna(row.get('Note')) else row.get('Description')
            if not pd.notna(descricao):
                descricao = "Sem descrição"
            
            # Converter categoria
            categoria = row.get('Category')
            if pd.notna(categoria) and categoria in categoria_traducao:
                categoria = categoria_traducao[categoria]
            else:
                categoria = "Outros"
            
            # Valor e tipo
            valor = row.get('Amount') if pd.notna(row.get('Amount')) else 0.0
            tipo = row.get('Income/Expense')
            if pd.notna(tipo) and tipo in tipo_traducao:
                tipo = tipo_traducao[tipo]
            else:
                tipo = "Despesa"  # Padrão
            
            # Criar nova linha
            nova_linha = {
                "Data": data,
                "Descrição": descricao,
                "Categoria": categoria,
                "Valor": valor,
                "Tipo": tipo
            }
        
        # Adicionar ao novo DataFrame
        novo_df = pd.concat([novo_df, pd.DataFrame([nova_linha])], ignore_index=True)
    
    except Exception as e:
        print(f"Erro ao processar linha: {e}")
        continue

# Ordenar por data (mais recente primeiro)
novo_df = novo_df.sort_values(by="Data", ascending=False)

# Salvar em um novo arquivo
novo_df.to_csv('despesas_br.csv', index=False)
print(f"Arquivo 'despesas_br.csv' criado com sucesso com {len(novo_df)} registros.")

# Mostrar as primeiras linhas para verificação
print("\nPrimeiras linhas do novo arquivo:")
print(novo_df.head())