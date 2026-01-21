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

# SEÇÃO DE IMPORTAÇÃO
st.sidebar.write("### 📂 Importar Planilha")
arquivo_upload = st.sidebar.file_uploader("Carregar arquivo .xlsx", type=["xlsx"])

if arquivo_upload is not None:
    if st.sidebar.button("Confirmar Importação"):
        try:
            df_importado = pd.read_excel(arquivo_upload)
            # Garantir que as colunas batem com o esperado
            colunas_esperadas = ['Data', 'Tipo', 'Categoria', 'Descrição', 'Valor']
            if all(col in df_importado.columns for col in colunas_esperadas):
                # Converter coluna Data para datetime e depois apenas data
                df_importado['Data'] = pd.to_datetime(df_importado['Data']).dt.date
                st.session_state['data'] = pd.concat([st.session_state['data'], df_importado], ignore_index=True)
                st.sidebar.success("Dados importados com sucesso!")
                st.rerun()
            else:
                st.sidebar.error("A planilha deve conter as colunas: Data, Tipo, Categoria, Descrição e Valor")
        except Exception as e:
            st.sidebar.error(f"Erro ao ler o arquivo: {e}")

st.sidebar.markdown("---")

# FORMULÁRIO DE LANÇAMENTO
st.sidebar.write("### 📝 Novo Registro")
tipo_sel = st.sidebar.selectbox("Tipo", ["Despesa", "Receita"])

# Definir opções de categoria base
if tipo_sel == "Despesa":
    cat_base = ["Moradia", "Alimentação", "Transporte", "Lazer", "Saúde", "Educação", "Assinaturas", "Cartão de Crédito"]
else:
    cat_base = ["Salário", "Investimentos", "Vendas", "Freelance"]

cat_opcoes = cat_base + ["Outra (Digitar nova...)"]

with st.sidebar.form("form_registro", clear_on_submit=True):
    data_sel = st.date_input("Data", date.today())
    categoria_pre = st.selectbox("Categoria", cat_opcoes)
    
    # Campo extra que aparece apenas se "Outra" for selecionada
    categoria_custom = st.text_input("Se escolheu 'Outra', digite o nome aqui:")
    
    desc_sel = st.text_input("Descrição")
    valor_sel = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
    
    btn_enviar = st.form_submit_button("Lançar Agora")
    
    if btn_enviar:
        # Lógica para definir qual categoria usar
        categoria_final = categoria_custom if categoria_pre == "Outra (Digitar nova...)" else categoria_pre
        
        if not categoria_final:
            st.error("Por favor, defina uma categoria.")
        elif not desc_sel:
            st.error("Por favor, preencha a descrição.")
        else:
            adicionar_item(data_sel, tipo_sel, categoria_final, desc_sel, valor_sel)
            st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("Limpar Todos os Dados"):
    st.session_state['data'] = pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Descrição', 'Valor'])
    st.rerun()

# --- ÁREA PRINCIPAL ---
st.title("Painel de Controle Financeiro")

df = st.session_state['data']

if not df.empty:
    # Métricas
    receitas = df[df['Tipo'] == 'Receita']['Valor'].sum()
    despesas = df[df['Tipo'] == 'Despesa']['Valor'].sum()
    saldo = receitas - despesas
    
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-card">
            <div class="metric-label">TOTAL RECEITAS</div>
            <div class="metric-value" style="color: #28a745;">R$ {receitas:,.2f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">TOTAL DESPESAS</div>
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
        st.subheader("Distribuição por Categoria (%)")
        df_despesas = df[df['Tipo'] == 'Despesa']
        
        if not df_despesas.empty:
            df_grafico = df_despesas.groupby("Categoria")["Valor"].sum().reset_index()
            
            fig = px.pie(
                df_grafico, 
                values='Valor', 
                names='Categoria', 
                hole=0.5,
                color='Categoria',
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            # Adiciona as porcentagens dentro do gráfico
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Cadastre despesas para visualizar o gráfico percentual.")

    with col_tab:
        st.subheader("Registros Atuais")
        df_display = df.sort_values(by='Data', ascending=False)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        excel_file = converter_para_excel(df)
        st.download_button(
            label="📥 Baixar Planilha Atualizada (.xlsx)",
            data=excel_file,
            file_name=f"financeiro_atualizado_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Arraste uma planilha para a barra lateral ou comece a digitar seus gastos!")
