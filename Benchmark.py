import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


# ----------- CONFIGURACIÓN DE ESTILO Y COLORES -----------

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Sans:wght@400;700&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Fira Sans', sans-serif !important;
    }
    .stTable, .stSelectbox, .stRadio, .stButton, .stMarkdown, .stCaption, .stDataFrame {
        font-family: 'Fira Sans', sans-serif !important;
    }
    </style>
""", unsafe_allow_html=True)

COLORES = [
    "#BF1B18",  # principal
    "#FBAF3A",  # secundario
    "#FF7502",
    "#1E87C1",
    "#50D2FF"
]

# ----------- CARGA DE DATOS -----------
@st.cache_data
def load_data():
    url = "https://storage.googleapis.com/capitalia-datos-publicos/empresas.csv"
    return pd.read_csv(url, sep=',', encoding="utf-8")
df = load_data()

# Normaliza los nombres de las columnas por si varían en el dataset
if "ciiu largo" not in df.columns and "ciiu_largo" in df.columns:
    df = df.rename(columns={"ciiu_largo": "ciiu largo"})

# ----------- VARIABLES DISPONIBLES -----------
variables = {
    "Ingresos": "ingresos",
    "Utilidad Neta": "utilidad_neta",
    "Total de Activos": "total_de_activos",
    "Total Pasivos": "total_pasivos",
    "Patrimonio Total": "patrimonio_total",
    "Flujo de Caja Libre": "flujo_de_caja_libre",
    "Total Capex": "total_capex",
    "EBITDA": "ebitda",
    "ROE": "ROE",
    "ROA": "ROA",
    "Deuda Financiera": "deuda_financiera",
    "Margen EBITDA": "margen_ebitda",
    "Deuda / Activos": "deuda_/_activos",
    "Crecimiento Ingresos": "crecimiento_ingresos"
}

variables_porcentaje = {"ROE", "ROA", "margen_ebitda", "deuda_/_activos", "crecimiento_ingresos"}

# ----------- TÍTULO Y LOGO (opcional) -----------
st.markdown("<h1 style='text-align:center; font-family: Fira Sans, sans-serif;'>Benchmark Financiero entre Empresas</h1>", unsafe_allow_html=True)

# ----------- SELECCIÓN DE AÑO Y EMPRESA FOCO -----------
anios = sorted(df['anio'].unique(), reverse=True)
anio_sel = st.selectbox("Selecciona el año a analizar:", anios)
df_anio = df[df['anio'] == anio_sel]

# Modo de búsqueda inicial
modo_busqueda = st.radio(
    "¿Cómo deseas buscar la empresa a analizar?",
    ("Por NIT", "Por Industria/Subindustria/Sector/CIIU")
)

empresa_sel = None
if modo_busqueda == "Por NIT":
    empresas_list = df_anio[["razon_social", "nit"]].drop_duplicates()
    empresas_list["selector"] = empresas_list["razon_social"] + " (" + empresas_list["nit"].astype(str) + ")"
    empresa_sel = st.selectbox(
        "Busca y selecciona la empresa a analizar:",
        empresas_list["selector"].sort_values(),
        key="selector_nit"
    )
    df_filtrado = df_anio.copy()
else:
    st.markdown(
        "Selecciona los niveles deseados. Puedes dejar cualquier paso en 'Todas' para incluir todas las opciones."
    )

    industria_opts = ["Todas"] + sorted(df_anio["industria"].dropna().unique())
    industria_sel = st.selectbox("Industria", industria_opts)
    df_filtrado = df_anio.copy()
    if industria_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["industria"] == industria_sel]

    subind_opts = ["Todas"]
    if industria_sel != "Todas":
        subind_opts += sorted(df_filtrado["subindustria"].dropna().unique())
    subindustria_sel = st.selectbox("Subindustria", subind_opts)
    if subindustria_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["subindustria"] == subindustria_sel]

    sector_opts = ["Todas"]
    if subindustria_sel != "Todas":
        sector_opts += sorted(df_filtrado["sector"].dropna().unique())
    sector_sel = st.selectbox("Sector", sector_opts)
    if sector_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["sector"] == sector_sel]

    ciiu_opts = ["Todas"]
    if sector_sel != "Todas":
        ciiu_df = df_filtrado[["ciiu", "ciiu largo"]].drop_duplicates()
        ciiu_opts += [f"{row['ciiu largo']} ({row['ciiu']})" for _, row in ciiu_df.iterrows()]
    ciiu_disp = st.selectbox("CIIU", ciiu_opts)
    if ciiu_disp != "Todas":
        ciiu_sel = ciiu_disp.split("(")[-1].replace(")", "").strip()
        df_filtrado = df_filtrado[df_filtrado["ciiu"] == ciiu_sel]

    empresas_list = df_filtrado[["razon_social", "nit"]].drop_duplicates()
    empresas_list["selector"] = empresas_list["razon_social"] + " (" + empresas_list["nit"].astype(str) + ")"
    if empresas_list.empty:
        st.error("No se encontraron empresas con los filtros seleccionados.")
        st.stop()
    empresa_sel = st.selectbox(
        "Busca y selecciona la empresa a analizar:",
        empresas_list["selector"].sort_values(),
        key="selector_industria"
    )



if empresa_sel:
    nit_foco = empresa_sel.split("(")[-1].replace(")", "").strip()
    df_anio["nit"] = df_anio["nit"].astype(str)
    empresa_foco_df = df_anio[df_anio["nit"] == nit_foco]
    if empresa_foco_df.empty:
        st.error(
            "No se encontró la empresa seleccionada para el año elegido. Verifica el NIT o selecciona otro año/empresa."
        )
        st.stop()
    df_foco = empresa_foco_df.iloc[0]
    if 'industria_sel' not in locals():
        industria_sel = df_foco.get("industria", "Todas")
    if 'subindustria_sel' not in locals():
        subindustria_sel = df_foco.get("subindustria", "Todas")
    if 'sector_sel' not in locals():
        sector_sel = df_foco.get("sector", "Todas")
    if 'ciiu_disp' not in locals():
        ciiu_disp = df_foco.get("ciiu", "Todas")
else:
    st.stop()

# ----------- INFO DE LA EMPRESA FOCO -----------
st.markdown("""
<div style='background:#F9F9F9; border-radius:10px; padding:12px 18px; margin-bottom:18px; width:90%; max-width:480px;'>
    <div style='font-family: Fira Sans, sans-serif; font-size:16px; color:#222; font-weight:600; margin-bottom:2px;'>
        <span style='display:inline-block; width:110px;'>Industria:</span>
        <span style='font-weight:400;'>{industria}</span>
    </div>
    <div style='font-family: Fira Sans, sans-serif; font-size:16px; color:#222; font-weight:600; margin-bottom:2px;'>
        <span style='display:inline-block; width:110px;'>Subindustria:</span>
        <span style='font-weight:400;'>{subindustria}</span>
    </div>
    <div style='font-family: Fira Sans, sans-serif; font-size:16px; color:#222; font-weight:600;'>
        <span style='display:inline-block; width:110px;'>CIIU:</span>
        <span style='font-weight:400;'>{ciiu}</span>
    </div>
</div>
""".format(
    industria=df_foco.get("industria", "N/D"),
    subindustria=df_foco.get("subindustria", "N/D"),
    ciiu=df_foco.get("ciiu", "N/D")
), unsafe_allow_html=True)

# ----------- UNIVERSO DE COMPARACIÓN -----------
st.markdown("<h3 style='font-family: Fira Sans, sans-serif;'>Selecciona el universo de comparación</h3>", unsafe_allow_html=True)

# Determina el último nivel seleccionado por el usuario para ajustar las opciones
nivel_cmp = "Industria"
if 'ciiu_disp' in locals() and ciiu_disp != "Todas":
    nivel_cmp = "CIIU"
elif 'sector_sel' in locals() and sector_sel != "Todas":
    nivel_cmp = "Sector"
elif 'subindustria_sel' in locals() and subindustria_sel != "Todas":
    nivel_cmp = "Subindustria"
    
opciones_comp = [
    f"{nivel_cmp}: Top 5 ventas",
    f"{nivel_cmp}: 5 más cercanas en ventas",
    "Manual: escoger NIT"
]
tipo_comp = st.radio(
    "Tipo de comparación:", opciones_comp, horizontal=False, key="radio_tipo_comparacion"
)
# ----------- ARMA EL UNIVERSO DE EMPRESAS COMPARABLES -----------

if tipo_comp.startswith("Industria"):
    col_ref = "industria"
    val_ref = df_foco["industria"]
    ventas_foco = df_foco["ingresos"]
    if "Top" in tipo_comp:
        empresas_cmp = df_anio[df_anio[col_ref] == val_ref].copy()
        empresas_cmp = empresas_cmp[empresas_cmp["ingresos"] > 0]
        empresas_cmp = empresas_cmp.sort_values("ingresos", ascending=False)
    else:
        empresas_cmp = df_anio[df_anio[col_ref] == val_ref].copy()
        empresas_cmp = empresas_cmp[empresas_cmp["ingresos"] > 0]
        empresas_cmp["dist_ventas"] = (empresas_cmp["ingresos"] - ventas_foco).abs()
        empresas_cmp = empresas_cmp.sort_values("dist_ventas")
elif tipo_comp.startswith("Subindustria"):
    col_ref = "subindustria"
    val_ref = df_foco.get("subindustria", None)
    ventas_foco = df_foco["ingresos"]
    if pd.isnull(val_ref):
        empresas_cmp = pd.DataFrame()
    elif "Top" in tipo_comp:
        empresas_cmp = df_anio[df_anio[col_ref] == val_ref].copy()
        empresas_cmp = empresas_cmp[empresas_cmp["ingresos"] > 0]
        empresas_cmp = empresas_cmp.sort_values("ingresos", ascending=False)
    else:
        empresas_cmp = df_anio[df_anio[col_ref] == val_ref].copy()
        empresas_cmp = empresas_cmp[empresas_cmp["ingresos"] > 0]
        empresas_cmp["dist_ventas"] = (empresas_cmp["ingresos"] - ventas_foco).abs()
        empresas_cmp = empresas_cmp.sort_values("dist_ventas")
elif tipo_comp.startswith("Sector"):
    col_ref = "sector"
    val_ref = df_foco.get("sector", None)
    ventas_foco = df_foco["ingresos"]
    if pd.isnull(val_ref):
        empresas_cmp = pd.DataFrame()
    elif "Top" in tipo_comp:
        empresas_cmp = df_anio[df_anio[col_ref] == val_ref].copy()
        empresas_cmp = empresas_cmp[empresas_cmp["ingresos"] > 0]
        empresas_cmp = empresas_cmp.sort_values("ingresos", ascending=False)
    else:
        empresas_cmp = df_anio[df_anio[col_ref] == val_ref].copy()
        empresas_cmp = empresas_cmp[empresas_cmp["ingresos"] > 0]
        empresas_cmp["dist_ventas"] = (empresas_cmp["ingresos"] - ventas_foco).abs()
        empresas_cmp = empresas_cmp.sort_values("dist_ventas")
elif tipo_comp.startswith("CIIU"):
    col_ref = "ciiu"
    val_ref = df_foco["ciiu"]
    ventas_foco = df_foco["ingresos"]
    if "Top" in tipo_comp:
        empresas_cmp = df_anio[df_anio[col_ref] == val_ref].copy()
        empresas_cmp = empresas_cmp[empresas_cmp["ingresos"] > 0]
        empresas_cmp = empresas_cmp.sort_values("ingresos", ascending=False)
    else:
        empresas_cmp = df_anio[df_anio[col_ref] == val_ref].copy()
        empresas_cmp = empresas_cmp[empresas_cmp["ingresos"] > 0]
        empresas_cmp["dist_ventas"] = (empresas_cmp["ingresos"] - ventas_foco).abs()
        empresas_cmp = empresas_cmp.sort_values("dist_ventas")
elif tipo_comp.startswith("Manual"):
    # Este bloque debe tener tu lógica de multiselección manual.
    empresas_cmp = df_anio[df_anio["nit"].isin([])]  # Deja vacío si no implementas aún
else:
    empresas_cmp = pd.DataFrame()

# ----------- TABLA DE EMPRESAS COMPARABLES (5 peers + empresa foco) -----------

# Texto del criterio
if tipo_comp.startswith("Industria"):
    criterio = f"Industria: {df_foco.get('industria', 'N/D')}"
    if "Top" in tipo_comp:
        detalle = "Top 5 en ventas"
    else:
        detalle = "5 más cercanas en ventas"
elif tipo_comp.startswith("Subindustria"):
    criterio = f"Subindustria: {df_foco.get('subindustria', 'N/D')}"
    if "Top" in tipo_comp:
        detalle = "Top 5 en ventas"
    else:
        detalle = "5 más cercanas en ventas"
elif tipo_comp.startswith("Sector"):
    criterio = f"Sector: {df_foco.get('sector', 'N/D')}"
    if "Top" in tipo_comp:
        detalle = "Top 5 en ventas"
    else:
        detalle = "5 más cercanas en ventas"
elif tipo_comp.startswith("CIIU"):
    criterio = f"CIIU: {df_foco.get('ciiu', 'N/D')}"
    if "Top" in tipo_comp:
        detalle = "Top 5 en ventas"
    else:
        detalle = "5 más cercanas en ventas"
elif tipo_comp.startswith("Manual"):
    criterio = "Selección manual"
    detalle = "Empresas seleccionadas por el usuario"
else:
    criterio = "Criterio desconocido"
    detalle = ""

def formato_miles(x):
    try:
        return "{:,.0f}".format(x).replace(",", ".")
    except:
        return ""

# Obtén los 5 peers (sin empresa foco)
df_peers = empresas_cmp[["razon_social", "nit", "ingresos"]].copy()
df_peers = df_peers[df_peers["nit"].astype(str) != str(df_foco["nit"])]
df_peers = df_peers.sort_values("ingresos", ascending=False)
peers_tabla = df_peers.head(5)

# Agrega la empresa foco como sexta fila
df_foco_row = pd.DataFrame([{
    "razon_social": df_foco["razon_social"] + " (Empresa Analizada)",
    "nit": df_foco["nit"],
    "ingresos": df_foco["ingresos"]
}])
df_tabla = pd.concat([peers_tabla, df_foco_row], ignore_index=True)
df_tabla["Ingresos"] = df_tabla["ingresos"].apply(formato_miles)
df_tabla = df_tabla[["razon_social", "nit", "Ingresos"]]
df_tabla = df_tabla.rename(columns={
    "razon_social": "Empresa",
    "nit": "NIT"
})
st.markdown("<h3 style='font-family: Fira Sans, sans-serif;'>Empresas comparables seleccionadas:</h3>", unsafe_allow_html=True)
st.markdown(
    f"<div style='font-size:18px; margin-bottom:12px;'><b>{criterio}</b><br>{detalle}</div>",
    unsafe_allow_html=True
)
st.dataframe(df_tabla, hide_index=True)

# -------------- AQUÍ SIGUE TU LÓGICA DE VARIABLE, GRÁFICA, ETC. ----------------
