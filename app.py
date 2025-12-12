import streamlit as st
import uuid
from datetime import datetime
from db import load_table, append_row, overwrite_table, sheet

st.set_page_config(page_title="Finanças Pessoais", layout="wide")

# Funções auxiliares

def to_float(valor):
    if isinstance(valor, (int, float)):
        return float(valor)
    if not valor:
        return 0.0
    valor = str(valor).strip().replace(",", ".")
    try:
        return float(valor)
    except:
        return 0.0


def safe_extract(table, key):
    if not table:
        return []
    return [row.get(key, "").strip() for row in table if row.get(key, "").strip() != ""]


def get_value(item, index, default="—"):
    keys = ["id", "nome", "valor", "categoria", "usuario", "data", "hora"]
    if isinstance(item, dict):
        return item.get(keys[index], default) or default
    if isinstance(item, list):
        return item[index] if index < len(item) else default
    return default


def mes_extenso(mes):
    nomes = [
        "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
        "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"
    ]
    return nomes[mes - 1]


def registrar_em_aba_mensal(item):
    ano = int(item["data"][0:4])
    mes = int(item["data"][5:7])
    nome_aba = f"{mes_extenso(mes)} - {ano}"

    try:
        ws = sheet.worksheet(nome_aba)
    except:
        ws = sheet.add_worksheet(title=nome_aba, rows=2000, cols=20)
        ws.append_row(["id", "nome", "valor", "categoria", "usuario", "data", "hora"])

    ws.append_row([
        item.get("id", ""),
        item.get("nome", ""),
        item.get("valor", ""),
        item.get("categoria", ""),
        item.get("usuario", ""),
        item.get("data", ""),
        item.get("hora", "")
    ])

# FILTRAR MÊS ATUAL

def filtrar_mes_atual(tabela):
    agora = datetime.now()
    mes_atual = agora.month
    ano_atual = agora.year

    filtrado = []
    for item in tabela:
        data_str = get_value(item, 5)
        try:
            ano = int(data_str[0:4])
            mes = int(data_str[5:7])
            if ano == ano_atual and mes == mes_atual:
                filtrado.append(item)
        except:
            pass
    return filtrado

def gerar_mes_atual():
    agora = datetime.now()
    mes_ref = f"{agora.year}-{str(agora.month).zfill(2)}"

    meses_processados = load_table("processed_months")
    meses_prontos = {m["month"] for m in meses_processados}

    if mes_ref in meses_prontos:
        return 

    fx_templates = load_table("fixed_templates")
    income_templates = load_table("income_templates")

    for t in fx_templates:
        item = {
            "id": str(uuid.uuid4()),
            "nome": t["nome"],
            "valor": t["valor"],
            "categoria": t["categoria"],
            "usuario": t["usuario"],
            "data": agora.strftime("%Y-%m-%d"),
            "hora": agora.strftime("%H:%M:%S")
        }
        append_row("fixed_expenses", item)
        registrar_em_aba_mensal(item)

    for t in income_templates:
        item = {
            "id": str(uuid.uuid4()),
            "nome": t["nome"],
            "valor": t["valor"],
            "data": agora.strftime("%Y-%m-%d"),
            "hora": agora.strftime("%H:%M:%S")
        }
        append_row("incomes", item)

    append_row("processed_months", {
        "month": mes_ref,
        "generated_at": agora.strftime("%Y-%m-%d %H:%M:%S")
    })

gerar_mes_atual()

users = safe_extract(load_table("users"), "name")
categories = safe_extract(load_table("categories"), "name")

fixed_expenses = filtrar_mes_atual(load_table("fixed_expenses"))
personal_expenses = filtrar_mes_atual(load_table("personal_expenses"))
incomes = filtrar_mes_atual(load_table("incomes"))

# INTERFACE

st.sidebar.title("Configurações")

st.sidebar.subheader("Usuários")
new_user = st.sidebar.text_input("Adicionar novo usuário")
if st.sidebar.button("Salvar usuário"):
    if new_user.strip():
        append_row("users", {"name": new_user})
        st.rerun()
    else:
        st.sidebar.error("Digite um nome!")

st.sidebar.subheader("Categorias")
new_cat = st.sidebar.text_input("Criar nova categoria")
if st.sidebar.button("Salvar Categoria"):
    if new_cat.strip():
        append_row("categories", {"name": new_cat})
        st.rerun()
    else:
        st.sidebar.error("Digite uma categoria!")

st.title("💰 Controle de Finanças Pessoais")
tab1, tab2, tab3, tab4 = st.tabs(
    ["Gastos Fixos", "Gastos Pessoais", "Rendas", "📈 Gráficos"]
)

# TAB 1 — GASTOS FIXOS

with tab1:
    st.header("Gastos Fixos")

    nome = st.text_input("Nome do gasto fixo")
    valor = st.number_input("Valor (R$)", min_value=0.0)
    categoria = st.selectbox("Categoria", categories)
    usuario = st.selectbox("Usuário responsável", users)

    if st.button("Adicionar gasto fixo"):
        if nome and valor > 0:
            agora = datetime.now()
            item = {
                "id": str(uuid.uuid4()),
                "nome": nome,
                "valor": valor,
                "categoria": categoria,
                "usuario": usuario,
                "data": agora.strftime("%Y-%m-%d"),
                "hora": agora.strftime("%H:%M:%S")
            }

            append_row("fixed_templates", {
                "id": item["id"],
                "nome": nome,
                "valor": valor,
                "categoria": categoria,
                "usuario": usuario
            })

            append_row("fixed_expenses", item)
            registrar_em_aba_mensal(item)

            st.rerun()

    st.subheader("Lista de gastos fixos")
    for item in fixed_expenses:
        nome = get_value(item, 1)
        valor = get_value(item, 2)
        categoria = get_value(item, 3)
        usuario = get_value(item, 4)
        data = get_value(item, 5)
        hora = get_value(item, 6)
        item_id = get_value(item, 0)

        with st.expander(f"{nome} — R${valor}"):
            st.write(f"Categoria: **{categoria}**")
            st.write(f"Usuário: **{usuario}**")
            st.write(f"Data: **{data}**   Hora: **{hora}**")

            if st.button("Excluir", key=f"fx_{item_id}"):
                fixed_expenses = [i for i in fixed_expenses if get_value(i, 0) != item_id]
                overwrite_table("fixed_expenses", fixed_expenses)
                st.rerun()

# TAB 2 — GASTOS PESSOAIS

with tab2:
    st.header("Gastos Pessoais")

    nome = st.text_input("Descrição do gasto pessoal")
    valor = st.number_input("Valor (R$)", min_value=0.0, key="vp")
    categoria = st.selectbox("Categoria", categories, key="cat2")
    usuario = st.selectbox("Quem fez a compra?", users, key="user2")

    if st.button("Adicionar gasto pessoal"):
        if nome and valor > 0:
            agora = datetime.now()
            item = {
                "id": str(uuid.uuid4()),
                "nome": nome,
                "valor": valor,
                "categoria": categoria,
                "usuario": usuario,
                "data": agora.strftime("%Y-%m-%d"),
                "hora": agora.strftime("%H:%M:%S")
            }

            append_row("personal_expenses", item)
            registrar_em_aba_mensal(item)
            st.rerun()

    st.subheader("Lista de gastos pessoais")
    for item in personal_expenses:
        nome = get_value(item, 1)
        valor = get_value(item, 2)
        categoria = get_value(item, 3)
        usuario = get_value(item, 4)
        data = get_value(item, 5)
        hora = get_value(item, 6)
        item_id = get_value(item, 0)

        with st.expander(f"{nome} — R${valor}"):
            st.write(f"Categoria: **{categoria}**")
            st.write(f"Usuário: **{usuario}**")
            st.write(f"Data: **{data}**   Hora: **{hora}**")

            if st.button("Excluir", key=f"ps_{item_id}"):
                personal_expenses = [i for i in personal_expenses if get_value(i, 0) != item_id]
                overwrite_table("personal_expenses", personal_expenses)
                st.rerun()

# TAB 3 — RENDAS

with tab3:
    st.header("💵 Minhas Rendas")

    nome_renda = st.text_input("Descrição da renda")
    valor_renda = st.number_input("Valor recebido (R$)", min_value=0.0)
    renda_fixa = st.checkbox("Essa renda deve repetir todo mês?")

    if st.button("Adicionar renda"):
        if nome_renda and valor_renda > 0:
            agora = datetime.now()

            item = {
                "id": str(uuid.uuid4()),
                "nome": nome_renda,
                "valor": valor_renda,
                "data": agora.strftime("%Y-%m-%d"),
                "hora": agora.strftime("%H:%M:%S")
            }

            append_row("incomes", item)

            # Se for renda fixa → vira template mensal
            if renda_fixa:
                append_row("income_templates", {
                    "id": item["id"],
                    "nome": nome_renda,
                    "valor": valor_renda
                })

            st.rerun()

    st.subheader("Lista de rendas")
    for item in incomes:
        nome = get_value(item, 1)
        valor = get_value(item, 2)
        data = get_value(item, 5)
        hora = get_value(item, 6)
        item_id = get_value(item, 0)

        with st.expander(f"{nome} — R${valor}"):
            st.write(f"Data: **{data}**   Hora: **{hora}**")

            if st.button("Excluir", key="inc_" + item_id):
                incomes = [i for i in incomes if get_value(i, 0) != item_id]
                overwrite_table("incomes", incomes)
                st.rerun()

    st.divider()

    # RESUMO (APENAS MÊS ATUAL)
    
    total_rendas = sum(to_float(get_value(i, 2, 0)) for i in incomes)
    total_fixos = sum(to_float(get_value(i, 2, 0)) for i in fixed_expenses)
    total_pessoais = sum(to_float(get_value(i, 2, 0)) for i in personal_expenses)

    total_gastos = total_fixos + total_pessoais
    saldo_final = total_rendas - total_gastos

    st.subheader("📊 RESUMO GERAL (MÊS ATUAL)")
    st.write(f"**Total de rendas:** R$ {total_rendas:.2f}")
    st.write(f"**Gastos fixos:** R$ {total_fixos:.2f}")
    st.write(f"**Gastos pessoais:** R$ {total_pessoais:.2f}")
    st.write(f"### 💸 Total gasto: R$ {total_gastos:.2f}")
    st.write(f"## ✅ Saldo restante: **R$ {saldo_final:.2f}**")

# TAB 4 — GRÁFICOS E DEMONSTRAÇÕES

with tab4:
    st.header("📈 Demonstrações Gráficas (Mês Atual)")

    
    # KPIs PRINCIPAIS
    
    total_rendas = sum(to_float(get_value(i, 2, 0)) for i in incomes)
    total_fixos = sum(to_float(get_value(i, 2, 0)) for i in fixed_expenses)
    total_pessoais = sum(to_float(get_value(i, 2, 0)) for i in personal_expenses)

    total_gastos = total_fixos + total_pessoais
    saldo = total_rendas - total_gastos

    col1, col2, col3 = st.columns(3)
    col1.metric("💵 Rendas", f"R$ {total_rendas:.2f}")
    col2.metric("💸 Gastos", f"R$ {total_gastos:.2f}")
    col3.metric("✅ Saldo", f"R$ {saldo:.2f}")

    st.divider()

    # GRÁFICO — FIXOS x PESSOAIS
    
    st.subheader("📊 Gastos Fixos x Gastos Pessoais")

    gastos_tipo = {
        "Gastos Fixos": total_fixos,
        "Gastos Pessoais": total_pessoais
    }

    st.bar_chart(gastos_tipo)

    st.divider()

    # GRÁFICO — GASTOS POR CATEGORIA
    
    st.subheader("📊 Gastos por Categoria")

    categorias = {}

    for item in fixed_expenses + personal_expenses:
        categoria = get_value(item, 3, "Outros")
        valor = to_float(get_value(item, 2, 0))
        categorias[categoria] = categorias.get(categoria, 0) + valor

    if categorias:
        st.bar_chart(categorias)
    else:
        st.info("Nenhum gasto registrado no mês.")

    st.divider()

    # GRÁFICO — EVOLUÇÃO DIÁRIA

    st.subheader("📈 Evolução diária de gastos")

    gastos_dia = {}

    for item in fixed_expenses + personal_expenses:
        data = get_value(item, 5)
        valor = to_float(get_value(item, 2, 0))
        gastos_dia[data] = gastos_dia.get(data, 0) + valor

    if gastos_dia:
        gastos_dia = dict(sorted(gastos_dia.items()))
        st.line_chart(gastos_dia)
    else:
        st.info("Nenhum gasto registrado para gerar o gráfico.")

    st.divider()

    # GRÁFICO — GASTOS POR USUÁRIO

    st.subheader("👤 Gastos por Usuário")

    gastos_usuario = {}

    for item in fixed_expenses + personal_expenses:
        usuario = get_value(item, 4, "Não informado")
        valor = to_float(get_value(item, 2, 0))
        gastos_usuario[usuario] = gastos_usuario.get(usuario, 0) + valor

    if gastos_usuario:
        st.bar_chart(gastos_usuario)
    else:
        st.info("Nenhum gasto encontrado para usuários.")