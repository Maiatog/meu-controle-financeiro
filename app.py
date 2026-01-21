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
        'Categoria': [categoria.strip().title()],
        'Descrição': [descricao.strip().title()],
        'Valor': [float(valor)]
    })
    st.session_state['data'] = pd.concat([st.session_state['data'], nova_linha], ignore_index=True)

# --- BARRA LATERAL ---
st.sidebar.title("💰 Gerenciador")

# 1. SEÇÃO DE IMPORTAÇÃO
st.sidebar.write("### 📂 Importar Planilha")
arquivo_upload = st.sidebar.file_uploader("Carregar arquivo .xlsx", type=["xlsx"])

if arquivo_upload is not None:
    if st.sidebar.button("Confirmar Importação"):
        try:
            df_importado = pd.read_excel(arquivo_upload)
            colunas_esperadas = ['Data', 'Tipo', 'Categoria', 'Descrição', 'Valor']
            if all(col in df_importado.columns for col in colunas_esperadas):
                df_importado['Data'] = pd.to_datetime(df_importado['Data']).dt.date
                st.session_state['data'] = pd.concat([st.session_state['data'], df_importado], ignore_index=True)
                st.sidebar.success("Importado!")
                st.rerun()
            else:
                st.sidebar.error("Colunas inválidas na planilha.")
        except Exception as e:
            st.sidebar.error(f"Erro: {e}")

st.sidebar.markdown("---")

# 2. FORMULÁRIO DE LANÇAMENTO
st.sidebar.write("### 📝 Novo Registro")
tipo_sel = st.sidebar.selectbox("Tipo", ["Despesa", "Receita"])

if tipo_sel == "Despesa":
    cat_base = ["Moradia", "Alimentação", "Transporte", "Lazer", "Saúde", "Educação", "Assinaturas", "Cartão de Crédito"]
else:
    cat_base = ["Salário", "Investimentos", "Vendas", "Freelance"]

cat_opcoes = cat_base + ["Outra (Digitar nova...)"]

with st.sidebar.form("form_registro", clear_on_submit=True):
    data_sel = st.date_input("Data", date.today())
    categoria_pre = st.selectbox("Categoria", cat_opcoes)
    categoria_custom = st.text_input("Se outra, digite o nome:")
    desc_sel = st.text_input("Descrição")
    valor_sel = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
    
    if st.form_submit_button("Lançar Agora"):
        categoria_final = categoria_custom if categoria_pre == "Outra (Digitar nova...)" else categoria_pre
        if categoria_final and desc_sel:
            adicionar_item(data_sel, tipo_sel, categoria_final, desc_sel, valor_sel)
            st.rerun()
        else:
            st.error("Preencha todos os campos.")

st.sidebar.markdown("---")

# 3. SEÇÃO DE EXCLUSÃO
if not st.session_state['data'].empty:
    st.sidebar.write("### 🗑️ Remover Lançamento")
    df_remover = st.session_state['data'].copy()
    # Criar uma lista legível para o usuário escolher
    df_remover['info'] = df_remover['Data'].astype(str) + " | " + df_remover['Descrição'] + " | R$ " + df_remover['Valor'].astype(str)
    
    item_para_remover = st.sidebar.selectbox("Selecione o item para apagar:", df_remover['info'].tolist())
    
    if st.sidebar.button("❌ Excluir Selecionado"):
        idx = df_remover[df_remover['info'] == item_para_remover].index[0]
        st.session_state['data'] = st.session_state['data'].drop(idx).reset_index(drop=True)
        st.sidebar.warning("Item removido!")
        st.rerun()

if st.sidebar.button("Limpar Tudo (Reset)"):
    st.session_state['data'] = pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Descrição', 'Valor'])
    st.rerun()

# --- ÁREA PRINCIPAL ---
st.title("Painel de Controle Financeiro")

df = st.session_state['data']

if not df.empty:
    # --- FILTRO POR MÊS ---
    df['Data'] = pd.to_datetime(df['Data'])
    df['Mes_Ano'] = df['Data'].dt.strftime('%m/%Y')
    
    meses_disponiveis = ["Todos"] + sorted(df['Mes_Ano'].unique().tolist(), reverse=True)
    mes_selecionado = st.selectbox("📅 Filtrar por Mês/Ano:", meses_disponiveis)
    
    # Filtrar o DataFrame de acordo com a seleção
    if mes_selecionado != "Todos":
        df_filtrado = df[df['Mes_Ano'] == mes_selecionado]
    else:
        df_filtrado = df

    # Cálculos baseados no filtro
    receitas = df_filtrado[df_filtrado['Tipo'] == 'Receita']['Valor'].sum()
    despesas = df_filtrado[df_filtrado['Tipo'] == 'Despesa']['Valor'].sum()
    saldo = receitas - despesas
    
    # Métricas
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-card">
            <div class="metric-label">RECEITAS NO PERÍODO</div>
            <div class="metric-value" style="color: #28a745;">R$ {receitas:,.2f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">DESPESAS NO PERÍODO</div>
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
        st.subheader("Distribuição do Mês (%)")
        df_despesas = df_filtrado[df_filtrado['Tipo'] == 'Despesa']
        
        if not df_despesas.empty:
            df_grafico = df_despesas.groupby("Categoria")["Valor"].sum().reset_index()
            fig = px.pie(
                df_grafico, values='Valor', names='Categoria', hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem despesas neste período.")

    with col_tab:
        st.subheader("Registros Filtrados")
        # Mostrar apenas as colunas originais
        df_display = df_filtrado[['Data', 'Tipo', 'Categoria', 'Descrição', 'Valor']].sort_values(by='Data', ascending=False)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        excel_file = converter_para_excel(df_filtrado)
        st.download_button(
            label="📥 Baixar Excel deste Período",
            data=excel_file,
            file_name=f"financeiro_{mes_selecionado.replace('/', '_') if mes_selecionado != 'Todos' else 'completo'}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Utilize a barra lateral para inserir dados ou importar uma planilha!")
