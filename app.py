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
    /* Estilização dos Cards de Métrica */
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
    /* Estilo do botão de download */
    .stDownloadButton button {
        width: 100%;
        background-color: #007bff;
        color: white;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DOS DADOS (SESSION STATE) ---
if 'data' not in st.session_state:
    # Criando um DataFrame vazio com as colunas necessárias
    st.session_state['data'] = pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Descrição', 'Valor'])

# --- FUNÇÕES AUXILIARES ---

def converter_para_excel(df):
    """Converte o DataFrame para um arquivo Excel em memória."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Meus Lancamentos')
    return output.getvalue()

def adicionar_item(data, tipo, categoria, descricao, valor):
    """Adiciona uma nova linha ao DataFrame no Session State."""
    nova_linha = pd.DataFrame({
        'Data': [pd.to_datetime(data).date()],
        'Tipo': [tipo],
        'Categoria': [categoria],
        'Descrição': [descricao.strip().title()], # Padroniza texto
        'Valor': [float(valor)]
    })
    st.session_state['data'] = pd.concat([st.session_state['data'], nova_linha], ignore_index=True)

# --- BARRA LATERAL (INPUT) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/1611/1611154.png", width=80)
st.sidebar.title("Gerenciador")

with st.sidebar.form("form_registro", clear_on_submit=True):
    st.write("### Novo Registro")
    data_sel = st.date_input("Data", date.today())
    tipo_sel = st.selectbox("Tipo", ["Despesa", "Receita"])
    
    # Categorias inteligentes baseadas no tipo
    if tipo_sel == "Despesa":
        cat_opcoes = ["Moradia", "Alimentação", "Transporte", "Lazer", "Saúde", "Educação", "Assinaturas", "Outros"]
    else:
        cat_opcoes = ["Salário", "Investimentos", "Vendas", "Freelance", "Outros"]
        
    categoria_sel = st.selectbox("Categoria", cat_opcoes)
    desc_sel = st.text_input("Descrição (Ex: Aluguel)")
    valor_sel = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
    
    btn_add = st.form_submit_button("Lançar Agora")
    
    if btn_add:
        if desc_sel == "":
            st.sidebar.error("Por favor, preencha a descrição.")
        else:
            adicionar_item(data_sel, tipo_sel, categoria_sel, desc_sel, valor_sel)
            st.sidebar.success("Adicionado com sucesso!")

# Botão de reset na sidebar (fora do form)
if st.sidebar.button("Limpar Tudo (Reset)"):
    st.session_state['data'] = pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Descrição', 'Valor'])
    st.rerun()

# --- ÁREA PRINCIPAL ---
st.title("💰 Meu Controle Financeiro")

df = st.session_state['data']

if not df.empty:
    # --- CÁLCULOS ---
    receitas = df[df['Tipo'] == 'Receita']['Valor'].sum()
    despesas = df[df['Tipo'] == 'Despesa']['Valor'].sum()
    saldo = receitas - despesas
    
    # --- EXIBIÇÃO DOS CARDS ---
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-card">
            <div class="metric-label">ENTRADAS</div>
            <div class="metric-value" style="color: #28a745;">R$ {receitas:,.2f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">SAÍDAS</div>
            <div class="metric-value" style="color: #dc3545;">R$ {despesas:,.2f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">SALDO ATUAL</div>
            <div class="metric-value" style="color: {'#007bff' if saldo >= 0 else '#dc3545'};">R$ {saldo:,.2f}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_graf, col_tab = st.columns([1, 1.2])

    with col_graf:
        st.subheader("Distribuição de Gastos")
        df_despesas = df[df['Tipo'] == 'Despesa']
        
        if not df_despesas.empty:
                fig = px.pie(
                df_despesas, 
                values='Valor', 
                names='Categoria', 
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig.update_layout(
                margin=dict(t=30, b=0, l=0, r=0),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhuma despesa para exibir no gráfico.")

    with col_tab:
        st.subheader("Registros Recentes")
        # Mostrar tabela formatada
        st.dataframe(
            df.sort_values(by='Data', ascending=False), 
            use_container_width=True, 
            hide_index=True
        )
        
        # Botão de Download
        excel_file = converter_para_excel(df)
        st.download_button(
            label="📊 Baixar Planilha Excel Atualizada",
            data=excel_file,
            file_name=f"financeiro_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    # Mensagem caso a planilha esteja vazia
    st.info("### Bem-vindo! \n\nPara começar, utilize o formulário na **barra lateral esquerda** para inserir suas receitas ou despesas. Assim que você inserir o primeiro dado, o painel e os gráficos aparecerão aqui automaticamente.")
    
    # Ilustração de placeholder
    st.image("https://img.freepik.com/free-vector/personal-finance-concept-illustration_114360-5125.jpg", width=400)
