import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import date

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Finanças Pro - Controle Pessoal",
    layout="wide",
    page_icon="💰"
)

# --- CSS PERSONALIZADO ---
st.markdown("""
<style>
    .metric-container {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e6e9ef;
        border-radius: 12px;
        padding: 20px;
        flex: 1;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .metric-label {
        color: #5f6368;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 26px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DOS DADOS ---
if 'data' not in st.session_state:
    st.session_state['data'] = pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Descrição', 'Valor'])

# --- FUNÇÕES ---
def converter_para_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Meus Lancamentos')
    return output.getvalue()

def adicionar_item(data, tipo, categoria, descricao, valor):
    nova_linha = pd.DataFrame({
        'Data': [pd.to_datetime(data).date()],
        'Tipo': [tipo],
        'Categoria': [categoria],
        'Descrição': [descricao.strip().title()],
        'Valor': [float(valor)]
    })
    st.session_state['data'] = pd.concat([st.session_state['data'], nova_linha], ignore_index=True)

# --- BARRA LATERAL ---
st.sidebar.title("💰 Gerenciador")

# 1. TIPO FORA DO FORMULÁRIO (Para atualizar as categorias instantaneamente)
st.sidebar.write("### Passo 1: Escolha o Tipo")
tipo_sel = st.sidebar.selectbox("Tipo de Lançamento", ["Despesa", "Receita"])

# Definir categorias baseadas no tipo selecionado
if tipo_sel == "Despesa":
    cat_opcoes = ["Moradia", "Alimentação", "Transporte", "Lazer", "Saúde", "Educação", "Assinaturas", "Outros"]
else:
    cat_opcoes = ["Salário", "Investimentos", "Vendas", "Freelance", "Outros"]

# 2. RESTANTE DOS DADOS DENTRO DO FORMULÁRIO
with st.sidebar.form("form_registro", clear_on_submit=True):
    st.write("### Passo 2: Detalhes")
    data_sel = st.date_input("Data", date.today())
    categoria_sel = st.selectbox("Categoria", cat_opcoes)
    desc_sel = st.text_input("Descrição")
    valor_sel = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
    
    btn_enviar = st.form_submit_button("Lançar Agora")
    
    if btn_enviar:
        if desc_sel:
            adicionar_item(data_sel, tipo_sel, categoria_sel, desc_sel, valor_sel)
            st.sidebar.success(f"{tipo_sel} adicionada!")
            # Força o app a recarregar para atualizar o gráfico imediatamente
            st.rerun()
        else:
            st.sidebar.error("Por favor, preencha a descrição.")

st.sidebar.markdown("---")
if st.sidebar.button("Limpar Todos os Dados"):
    st.session_state['data'] = pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Descrição', 'Valor'])
    st.rerun()

# --- ÁREA PRINCIPAL ---
st.title("Painel de Controle Financeiro")

df = st.session_state['data']

if not df.empty:
    # Cálculo das métricas
    receitas = df[df['Tipo'] == 'Receita']['Valor'].sum()
    despesas = df[df['Tipo'] == 'Despesa']['Valor'].sum()
    saldo = receitas - despesas
    
    # Exibição dos Cards
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-card">
            <div class="metric-label">TOTAL RECEITAS (ENTRADAS)</div>
            <div class="metric-value" style="color: #28a745;">R$ {receitas:,.2f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">TOTAL DESPESAS (SAÍDAS)</div>
            <div class="metric-value" style="color: #dc3545;">R$ {despesas:,.2f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">SALDO LÍQUIDO</div>
            <div class="metric-value" style="color: {'#007bff' if saldo >= 0 else '#dc3545'};">R$ {saldo:,.2f}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_graf, col_tab = st.columns([1, 1.2])

    with col_graf:
        st.subheader("Onde você está gastando?")
        df_despesas = df[df['Tipo'] == 'Despesa']
        
        if not df_despesas.empty:
            # AGRUPAMENTO: Soma os valores por categoria para garantir cores diferentes no gráfico
            df_grafico = df_despesas.groupby("Categoria")["Valor"].sum().reset_index()
            
            fig = px.pie(
                df_grafico, 
                values='Valor', 
                names='Categoria', 
                hole=0.5,
                color='Categoria', # Garante que cada categoria tenha sua cor
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig.update_layout(
                margin=dict(t=30, b=0, l=0, r=0),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Ainda não há despesas cadastradas para gerar o gráfico.")

    with col_tab:
        st.subheader("Histórico de Registros")
        # Exibe a tabela ordenada pela data mais recente
        df_display = df.sort_values(by='Data', ascending=False)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Botão para baixar Excel
        excel_file = converter_para_excel(df)
        st.download_button(
            label="📥 Baixar Planilha (.xlsx)",
            data=excel_file,
            file_name=f"meu_financeiro_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("👋 Olá! Use a barra lateral para inserir seu primeiro ganho ou gasto. Os gráficos e resumos aparecerão aqui assim que você começar!")
    st.image("https://img.freepik.com/free-vector/saving-money-concept-illustration_114360-3183.jpg", width=500)
