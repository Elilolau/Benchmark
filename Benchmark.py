
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ============================================================
# Configuración de página
# ============================================================
st.set_page_config(page_title="Benchmark Capitalia", layout="wide")

# ----------- ESTILOS ------------- #
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Sans:wght@400;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Fira Sans', sans-serif !important; }
    .titulo-seccion { font-weight: 700; font-size: 20px; margin-top: 30px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# Utilidades
# ============================================================
@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    """Carga la base de datos y convierte columnas numéricas en float."""
    url = "https://storage.googleapis.com/capitalia-datos-publicos/empresas.csv"
    df = pd.read_csv(url, sep=",", encoding="utf-8")

    num_cols = [
        "ingresos",
        "utilidad_neta",
        "total_de_activos",
        "total_pasivos",
        "ebitda",
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(r"[\.\s]", "", regex=True)  # quita puntos de miles
                .str.replace(",", ".")  # cambia coma decimal
                .astype(float, errors="ignore")
            )
    # Normaliza strings
    for c in ["industria", "subindustria", "sector"]:
        if c in df.columns:
            df[c] = df[c].str.strip()
    df["nit"] = df["nit"].astype(str).str.strip()
    return df


def peers(df_base: pd.DataFrame, df_foco: pd.Series, mode: str = "top", n: int = 5) -> pd.DataFrame:
    """Devuelve n empresas comparables de acuerdo al modo."""
    df_cmp = df_base[df_base["nit"] != df_foco["nit"]].copy()

    if df_cmp.empty:
        return pd.DataFrame()

    if mode == "top":
        df_cmp = df_cmp.sort_values("ingresos", ascending=False)
    else:
        ventas_foco = df_foco["ingresos"]
        df_cmp["dist"] = (df_cmp["ingresos"] - ventas_foco).abs()
        df_cmp = df_cmp.sort_values("dist")

    return df_cmp.head(n)


def formatea_miles(valor: float) -> str:
    try:
        return f"{valor:,.0f}".replace(",", ".")
    except Exception:
        return valor


# ============================================================
# Carga de datos
# ============================================================
df_all = load_data()

anios = sorted(df_all["anio"].dropna().unique(), reverse=True)
anio_sel = st.selectbox("Año a analizar", anios, index=0)

df_anio = df_all[df_all["anio"] == anio_sel].copy()

# ============================================================
# Selección de Empresa Foco
# ============================================================
st.markdown(
    '<p class="titulo-seccion">1. Busca y selecciona la empresa a analizar:</p>',
    unsafe_allow_html=True,
)

empresas_disp = (
    df_anio[["razon_social", "nit"]]
    .drop_duplicates()
    .assign(label=lambda d: d["razon_social"] + " (" + d["nit"] + ")")
    .sort_values("label")
)
empresa_sel = st.selectbox("Empresa foco", empresas_disp["label"])

df_foco = df_anio[df_anio["nit"] == empresa_sel.split("(")[-1].replace(")", "")].iloc[0]

# ============================================================
# Jerarquía de filtros
# ============================================================
st.markdown(
    '<p class="titulo-seccion">2. Selecciona el universo de comparación</p>',
    unsafe_allow_html=True,
)

nivel_final = None  # para saber hasta dónde llegó el usuario
df_nivel = df_anio.copy()

# ---------- NIVEL INDUSTRIA ----------
industria_opts = sorted(df_nivel["industria"].dropna().unique())
industria_sel = st.selectbox("Industria", industria_opts)
df_nivel = df_nivel[df_nivel["industria"] == industria_sel]
nivel_final = "industria"

# ---------- Subindustria ----------
if st.checkbox("Filtrar por Subindustria"):
    subindustria_opts = sorted(df_nivel["subindustria"].dropna().unique())
    subind_sel = st.selectbox("Subindustria", subindustria_opts)
    df_nivel = df_nivel[df_nivel["subindustria"] == subind_sel]
    nivel_final = "subindustria"

    # ---------- Sector ----------
    if st.checkbox("Filtrar por Sector"):
        sector_opts = sorted(df_nivel["sector"].dropna().unique())
        sector_sel = st.selectbox("Sector", sector_opts)
        df_nivel = df_nivel[df_nivel["sector"] == sector_sel]
        nivel_final = "sector"

        # ---------- CIIU ----------
        if st.checkbox("Filtrar por CIIU"):
            ciiu_opts = (
                df_nivel[["ciiu", "ciiu largo"]]
                .drop_duplicates()
                .assign(combo=lambda d: d["ciiu largo"] + " (" + d["ciiu"] + ")")
                .sort_values("combo")
            )
            ciiu_sel = st.selectbox("Código CIIU", ciiu_opts["combo"])
            codigo_ciiu = ciiu_sel.split("(")[-1].replace(")", "")
            df_nivel = df_nivel[df_nivel["ciiu"] == codigo_ciiu]
            nivel_final = "ciiu"

st.markdown(f"**Universo de comparación definido a nivel de:** {nivel_final.capitalize()}")
st.write(f"Empresas en universo: {df_nivel.shape[0]:,}")

# ============================================================
# Selección de Peers
# ============================================================
tipo_peer = st.radio(
    "Elige el criterio para seleccionar comparables", ("Top 5 ventas", "5 más cercanas en ventas")
)
modo = "top" if "Top" in tipo_peer else "near"

df_peers = peers(df_nivel, df_foco, mode=modo, n=5)

# Si la empresa foco aparece en Top 5, tomamos la 6ª para mantener 5 peers
if df_foco["nit"] in df_peers["nit"].values:
    df_peers = peers(df_nivel, df_foco, mode=modo, n=6)

# Añadimos empresa foco abajo
df_final_tabla = pd.concat([df_peers, df_foco.to_frame().T], ignore_index=True)
df_final_tabla["ingresos"] = df_final_tabla["ingresos"].apply(formatea_miles)

# ============================================================
# Visualización
# ============================================================
st.markdown(
    '<p class="titulo-seccion">3. Empresas comparables seleccionadas</p>',
    unsafe_allow_html=True,
)
st.dataframe(
    df_final_tabla[["razon_social", "nit", "ingresos"]].rename(
        columns={"razon_social": "Empresa", "nit": "NIT", "ingresos": "Ingresos"}
    ),
    hide_index=True,
)
