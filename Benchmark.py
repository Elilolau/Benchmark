
import streamlit as st
import pandas as pd
import numpy as np

# ------------------------------------------------------------
# Configuración de página
# ------------------------------------------------------------
st.set_page_config(page_title="Benchmark Capitalia", layout="wide")

# ------------------------------------------------------------
# ESTILOS
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# Funciones utilitarias
# ------------------------------------------------------------
@st.cache_data(show_spinner=True)
def load_data() -> pd.DataFrame:
    """Carga la base pública y convierte columnas numéricas a float."""
    url = "https://storage.googleapis.com/capitalia-datos-publicos/empresas.csv"
    df = pd.read_csv(url, sep=",", encoding="utf-8")

    # Limpieza numérica
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
                .str.replace(r"[.\s]", "", regex=True)   # quita puntos y espacios
                .str.replace(",", ".")                   # cambia coma decimal
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Limpieza strings
    for c in ["industria", "subindustria", "sector"]:
        if c in df.columns:
            df[c] = df[c].fillna("").str.strip()

    df["nit"] = df["nit"].astype(str).str.strip()

    # Asegura que ciiu exista como string
    if "ciiu" in df.columns:
        df["ciiu"] = df["ciiu"].astype(str).str.strip()

    return df


def format_miles(x):
    try:
        return f"{x:,.0f}".replace(",", ".")
    except Exception:
        return x


def get_peers(universe: pd.DataFrame, focus_row: pd.Series, mode: str, n: int = 5):
    """Devuelve los peers según el modo ('top' o 'near')."""
    universe = universe[universe["nit"] != focus_row["nit"]].copy()

    if universe.empty:
        return pd.DataFrame()

    if mode == "top":
        peers_df = universe.sort_values("ingresos", ascending=False).head(n)
    else:
        ventas_foco = focus_row["ingresos"]
        universe["dist"] = (universe["ingresos"] - ventas_foco).abs()
        peers_df = universe.sort_values("dist").head(n)

    return peers_df


# ------------------------------------------------------------
# Carga de datos y selección de año
# ------------------------------------------------------------
df_all = load_data()

years = sorted(df_all["anio"].dropna().unique(), reverse=True)
year_sel = st.selectbox("Año a analizar", years, index=0)

df_year = df_all[df_all["anio"] == year_sel].copy()

# ------------------------------------------------------------
# Selección de empresa foco
# ------------------------------------------------------------
st.markdown('<p class="titulo-seccion">1. Empresa foco</p>', unsafe_allow_html=True)

empresas_disp = (
    df_year[["razon_social", "nit"]]
    .drop_duplicates()
    .assign(label=lambda d: d["razon_social"] + " (" + d["nit"] + ")")
    .sort_values("label")
)
empresa_sel = st.selectbox("Busca la empresa", empresas_disp["label"])
nit_foco = empresa_sel.split("(")[-1].replace(")", "")
row_foco = df_year[df_year["nit"] == nit_foco].iloc[0]

# ------------------------------------------------------------
# Filtros anidados
# ------------------------------------------------------------
st.markdown('<p class="titulo-seccion">2. Universo de comparación</p>', unsafe_allow_html=True)

# Nivel Industria (SIEMPRE obligatorio)
industria_opts = sorted(df_year["industria"].dropna().unique())
industria_sel = st.selectbox("Industria", industria_opts)
df_universe = df_year[df_year["industria"] == industria_sel]

# Nivel Subindustria (permite TODAS)
subind_opts = ["TODAS"] + sorted(df_universe["subindustria"].dropna().unique())
subind_sel = st.selectbox("Subindustria", subind_opts)

if subind_sel != "TODAS":
    df_universe = df_universe[df_universe["subindustria"] == subind_sel]

    # Nivel Sector (permite TODAS)
    sector_opts = ["TODAS"] + sorted(df_universe["sector"].dropna().unique())
    sector_sel = st.selectbox("Sector", sector_opts)

    if sector_sel != "TODAS":
        df_universe = df_universe[df_universe["sector"] == sector_sel]

        # Nivel CIIU (permite TODAS)
        ciiu_opts = ["TODAS"] + sorted(df_universe["ciiu"].dropna().unique())
        ciiu_sel = st.selectbox("CIIU", ciiu_opts)

        if ciiu_sel != "TODAS":
            df_universe = df_universe[df_universe["ciiu"] == ciiu_sel]

# Si el usuario marcó TODAS en algún nivel, los niveles inferiores no aparecen (porque no fueron renderizados)

st.info(f"Empresas en universo filtrado: {df_universe.shape[0]:,}")

# ------------------------------------------------------------
# Botón para calcular peers
# ------------------------------------------------------------
st.markdown('<p class="titulo-seccion">3. Seleccionar comparables</p>', unsafe_allow_html=True)

tipo_peer = st.radio(
    "Elige el criterio:", ["Top 5 ventas", "5 más cercanas en ventas"], horizontal=True
)
modo_peer = "top" if tipo_peer.startswith("Top") else "near"

if st.button("Calcular comparables"):
    if df_universe.shape[0] < 2:
        st.error("El universo de comparación no tiene suficientes empresas.")
    else:
        df_peers = get_peers(df_universe, row_foco, modo_peer, n=5)

        if df_peers.empty:
            st.warning("No se encontraron empresas comparables bajo los criterios seleccionados.")
        else:
            # Si la empresa foco se cuela en TOP5, tomar una extra
            if row_foco["nit"] in df_peers["nit"].values:
                df_peers = get_peers(df_universe, row_foco, modo_peer, n=6)

            # Tabla final
            tabla_final = pd.concat([df_peers, row_foco.to_frame().T], ignore_index=True)
            tabla_final["ingresos"] = tabla_final["ingresos"].apply(format_miles)

            st.markdown(
                '<p class="titulo-seccion">4. Resultado</p>',
                unsafe_allow_html=True,
            )
            st.dataframe(
                tabla_final[["razon_social", "nit", "ingresos"]].rename(
                    columns={
                        "razon_social": "Empresa",
                        "nit": "NIT",
                        "ingresos": "Ingresos",
                    }
                ),
                hide_index=True,
            )
