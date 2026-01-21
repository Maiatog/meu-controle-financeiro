import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import date

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Controle Financeiro Pessoal", layout="wide", page_icon="💰")

# --- CSS PERSONALIZADO (Para deixar bonito) ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #333;
    }
    .metric-label {
        font-size: 14px;
        color: #666;
    }
    /* Corrigir espaçamento do topo */
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES ---

# Inicializar o Session State (Memória temporária do navegador)
if 'data' not in st.session_state:
    st.session_state['data'] = pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Descrição', 'Valor'])

def adicionar_transacao(data, tipo, categoria, descricao, valor):
    nova_linha = pd.DataFrame({
        'Data': [data],
        'Tipo': [tipo],
        'Categoria': [categoria],
        'Descrição': [descricao],
        'Valor': [valor]
    })
    st.session_state['data'] = pd.concat([st.session_state['data'], nova_linha], ignore_index=True)

def converter_para_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Lançamentos')
    processed_data = output.getvalue()
    return processed_data

# --- BARRA LATERAL (ENTRADA DE DADOS) ---
st.sidebar.header("📝 Novo Lançamento")

with st.sidebar.form("form_financeiro", clear_on_submit=True):
    data_input = st.date_input("Data", date.today())
    tipo_input = st.selectbox("Tipo", ["Despesa", "Receita"])
    cat_opcoes = ["Moradia", "Alimentação", "Transporte", "Lazer", "Saúde", "Educação", "Investimentos", "Salário", "Outros"]
    categoria_input = st.selectbox("Categoria", cat_opcoes)
    desc_input = st.text_input("Descrição (Ex: Aluguel)")
    valor_input = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
    
    submitted = st.form_submit_button("Adicionar")
    if submitted:
        adicionar_transacao(data_input, tipo_input, categoria_input, desc_input, valor_input)
        st.success("Lançamento adicionado!")

# --- ÁREA PRINCIPAL ---
st.title("📊 Painel de Controle Financeiro")

df = st.session_state['data']

if not df.empty:
    # --- CÁLCULOS ---
    total_receitas = df[df['Tipo'] == 'Receita']['Valor'].sum()
    total_despesas = df[df['Tipo'] == 'Despesa']['Valor'].sum()
    saldo = total_receitas - total_despesas
    
    # --- EXIBIÇÃO DE CARDS (HTML/CSS INJETADO) ---
    col1, col2, col3 = st.columns(3)
    
    col1.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Entradas</div>
        <div class="metric-value" style="color: green;">R$ {total_receitas:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)
    
    col2.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Saídas</div>
        <div class="metric-value" style="color: red;">R$ {total_despesas:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)
    
    col3.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Saldo Atual</div>
        <div class="metric-value" style="color: {'blue' if saldo >= 0 else 'red'};">R$ {saldo:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # --- GRÁFICOS E TABELA ---
    c1, c2 = st.columns([2, 3])

    with c1:
        st.subheader("Onde o dinheiro está indo?")
        # Filtrar apenas despesas para o gráfico
        df_despesas = df[df['Tipo'] == 'Despesa']
        
        if not df_despesas.empty:
            fig = px.donut(df_despesas, values='Valor', names='Categoria', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(showlegend=True, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Cadastre despesas para ver o gráfico.")

    with c2:
        st.subheader("Histórico de Lançamentos")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # --- BOTÃO DE DOWNLOAD EXCEL ---
        excel_data = converter_para_excel(df)
        st.download_button(
            label="📥 Baixar Planilha Excel (.xlsx)",
            data=excel_data,
            file_name='meu_controle_financeiro.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

else:
    st.info("👈 Comece adicionando seus ganhos e gastos na barra lateral!")