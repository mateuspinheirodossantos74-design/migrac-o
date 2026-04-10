import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from modulos.conexao import conectar


# ==========================
# BUILD FILTROS SQL
# ==========================
def montar_where(filtros):
    where = []

    if filtros["wave"]:
        waves = ",".join([f"'{w}'" for w in filtros["wave"]])
        where.append(f"bo.wave IN ({waves})")

    if filtros["setor"]:
        valores = ",".join([f"'{v}'" for v in filtros["setor"]])
        where.append(f"ms.setor IN ({valores})")

    if filtros["demanda"]:
        valores = ",".join([f"'{v}'" for v in filtros["demanda"]])
        where.append(f"d.demanda IN ({valores})")

    return " AND ".join(where)


# ==========================
# BASE COM JOIN (PADRÃO)
# ==========================
BASE_FROM = """
FROM base_operacional bo
LEFT JOIN mapa_box_setor ms ON bo.box = ms.box
LEFT JOIN demanda d ON bo.wave = d.wave
"""


# ==========================
# QUERIES
# ==========================
@st.cache_data(ttl=60)
def get_grupos(where_sql=""):
    conn = conectar()

    query = f"""
    SELECT
        bo.grupo_tarefa,
        COUNT(DISTINCT bo.tarefa) as qtde_tarefas,
        SUM(bo.qtde_pecas_item) as qtde_pecas_pendentes,
        COUNT(DISTINCT bo.local_picking) as qtde_locais
    {BASE_FROM}
    WHERE bo.status_olpn = 'Created'
    {f"AND {where_sql}" if where_sql else ""}
    GROUP BY bo.grupo_tarefa
    ORDER BY qtde_pecas_pendentes DESC
    """

    df = pd.read_sql(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=60)
def get_detalhamento(grupo, where_sql=""):
    conn = conectar()

    query = f"""
    SELECT
        bo.tarefa,
        COUNT(DISTINCT bo.local_picking) as qtde_locais,
        SUM(bo.qtde_pecas_item) as qtde_pecas,
        bo.status_olpn
    {BASE_FROM}
    WHERE bo.status_olpn = 'Created'
    AND bo.grupo_tarefa = '{grupo}'
    {f"AND {where_sql}" if where_sql else ""}
    GROUP BY bo.tarefa, bo.status_olpn
    ORDER BY qtde_pecas DESC
    """

    df = pd.read_sql(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=60)
def get_metricas(where_sql=""):
    conn = conectar()

    query = f"""
    SELECT
        SUM(CASE WHEN bo.status_olpn = 'Created' THEN bo.qtde_pecas_item ELSE 0 END) as created,
        SUM(CASE WHEN bo.status_olpn = 'Packed' THEN bo.qtde_pecas_item ELSE 0 END) as packed,
        SUM(bo.qtde_pecas_item) as total
    {BASE_FROM}
    {f"WHERE {where_sql}" if where_sql else ""}
    """

    df = pd.read_sql(query, conn)
    conn.close()

    return df.iloc[0].to_dict() if not df.empty else {"created": 0, "packed": 0, "total": 0}


@st.cache_data(ttl=60)
def get_pecas(where_sql=""):
    conn = conectar()

    query = f"""
    SELECT
        bo.grupo_tarefa,
        SUM(bo.qtde_pecas_item) as qtde_pecas_separadas
    {BASE_FROM}
    WHERE bo.status_olpn = 'Packed'
    {f"AND {where_sql}" if where_sql else ""}
    GROUP BY bo.grupo_tarefa
    ORDER BY qtde_pecas_separadas DESC
    """

    df = pd.read_sql(query, conn)
    conn.close()
    return df


# ==========================
# RENDER
# ==========================
def render():
    st_autorefresh(interval=600000, key="auto_refresh")

    st.title("📋 Acompanhamento de Tarefas")

    # ==========================
    # FILTROS
    # ==========================
    st.sidebar.header("🔎 Filtros")

    filtros = {
        "wave": st.sidebar.text_input("Wave (ex: 123,456)").split(","),
        "setor": st.sidebar.multiselect("Setor", []),
        "demanda": st.sidebar.multiselect("Demanda", [])
    }

    filtros["wave"] = [w.strip() for w in filtros["wave"] if w.strip()]

    where_sql = montar_where(filtros)

    # ==========================
    # ABAS
    # ==========================
    aba1, aba2 = st.tabs(["🏠 Início", "📦 Peças"])

    # ==========================
    # INICIO
    # ==========================
    with aba1:
        df = get_grupos(where_sql)

        st.dataframe(df, use_container_width=True)

        if not df.empty:
            grupo = st.selectbox("Grupo", df["grupo_tarefa"])
            df_det = get_detalhamento(grupo, where_sql)
            st.dataframe(df_det, use_container_width=True)

    # ==========================
    # PEÇAS
    # ==========================
    with aba2:
        m = get_metricas(where_sql)

        col1, col2, col3 = st.columns(3)
        col1.metric("Created", int(m["created"] or 0))
        col2.metric("Packed", int(m["packed"] or 0))
        col3.metric("Total", int(m["total"] or 0))

        df = get_pecas(where_sql)
        st.dataframe(df, use_container_width=True)
