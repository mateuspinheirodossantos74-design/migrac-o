import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from modulos.conexao import get_connection


# ==========================
# BASE COM JOIN
# ==========================
def base_from():
    return """
    FROM base_operacional b
    LEFT JOIN (
        SELECT box, MAX(setor) as setor
        FROM mapa_box_setor
        GROUP BY box
    ) m ON b.box = m.box
    LEFT JOIN (
        SELECT wave, MAX(demanda) as demanda
        FROM demanda
        GROUP BY wave
    ) d ON b.wave = d.wave
    WHERE 1=1
    """


# ==========================
# BUILD FILTROS SQL
# ==========================
def montar_where(filtros):
    where = []

    if filtros["wave"]:
        waves = ",".join([f"'{w}'" for w in filtros["wave"]])
        where.append(f"b.wave IN ({waves})")

    if filtros["setor"]:
        valores = ",".join([f"'{v}'" for v in filtros["setor"]])
        where.append(f"m.setor IN ({valores})")

    if filtros["demanda"]:
        valores = ",".join([f"'{v}'" for v in filtros["demanda"]])
        where.append(f"d.demanda IN ({valores})")

    return " AND ".join(where)


# ==========================
# QUERIES
# ==========================
@st.cache_data(ttl=60)
def get_grupos(where_sql=""):
    conn = get_connection()

    query = f"""
    SELECT
        b.grupo_tarefa,
        COUNT(DISTINCT b.tarefa) as qtde_tarefas,
        SUM(b.qtde_pecas_item) as qtde_pecas_pendentes,
        COUNT(DISTINCT b.local_picking) as qtde_locais
    {base_from()}
    AND b.status_olpn = 'Created'
    {f"AND {where_sql}" if where_sql else ""}
    GROUP BY b.grupo_tarefa
    ORDER BY qtde_pecas_pendentes DESC
    """

    df = pd.read_sql(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=60)
def get_detalhamento(grupo, where_sql=""):
    conn = get_connection()

    query = f"""
    SELECT
        b.tarefa,
        COUNT(DISTINCT b.local_picking) as qtde_locais,
        SUM(b.qtde_pecas_item) as qtde_pecas,
        b.status_olpn
    {base_from()}
    AND b.status_olpn = 'Created'
    AND b.grupo_tarefa = '{grupo}'
    {f"AND {where_sql}" if where_sql else ""}
    GROUP BY b.tarefa, b.status_olpn
    ORDER BY qtde_pecas DESC
    """

    df = pd.read_sql(query, conn)
    conn.close()
    return df


@st.cache_data(ttl=60)
def get_metricas(where_sql=""):
    conn = get_connection()

    query = f"""
    SELECT
        SUM(CASE WHEN b.status_olpn = 'Created' THEN b.qtde_pecas_item ELSE 0 END) as created,
        SUM(CASE WHEN b.status_olpn = 'Packed' THEN b.qtde_pecas_item ELSE 0 END) as packed,
        SUM(b.qtde_pecas_item) as total
    {base_from()}
    {f"AND {where_sql}" if where_sql else ""}
    """

    result = pd.read_sql(query, conn).iloc[0]
    conn.close()
    return result


@st.cache_data(ttl=60)
def get_pecas(where_sql=""):
    conn = get_connection()

    query = f"""
    SELECT
        b.grupo_tarefa,
        SUM(b.qtde_pecas_item) as qtde_pecas_separadas
    {base_from()}
    AND b.status_olpn = 'Packed'
    {f"AND {where_sql}" if where_sql else ""}
    GROUP BY b.grupo_tarefa
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
