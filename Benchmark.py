import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- 1. CSS para Fira Sans y estilo general ---
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

# --- 2. Paleta de colores corporativa ---
COLORES = [
    "#BF1B18",  # 50%
    "#FBAF3A",  # 20%
    "#FF7502",  # 20%
    "#1E87C1",  # 5%
    "#50D2FF"   # 5%
]

# --- 3. Cargar datos ---
@st.cache_data
def load_data():
    url = "https://storage.googleapis.com/capitalia-datos-publicos/empresas.csv"
    return pd.read_csv(url, sep=',', encoding="utf-8")
df = load_data()

# --- 4. Variables y nombres ---
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
DIVISOR = 1_000  # Para mostrar valores en miles de millones
variables_porcentaje = {"ROE", "ROA", "margen_ebitda", "deuda_/_activos", "crecimiento_ingresos"}

# --- LOGO Y TÍTULO ---
st.image("logo_capitalia.png", width=220)
st.markdown("<h1 style='text-align:center; font-family: Fira Sans, sans-serif;'>Benchmark Financiero entre Empresas</h1>", unsafe_allow_html=True)

# --- 5. Selección de año ---
anios = sorted(df['anio'].unique(), reverse=True)
anio_sel = st.selectbox("Selecciona el año a analizar:", anios)
df_anio = df[df['anio'] == anio_sel]

# --- 6. Selección de empresa principal con autocompletar (nombre/NIT) ---
empresas_list = df_anio[["razon_social", "nit"]].drop_duplicates()
empresas_list["selector"] = empresas_list["razon_social"] + " (" + empresas_list["nit"].astype(str) + ")"
empresa_sel = st.selectbox("Busca y selecciona la empresa a analizar:", empresas_list["selector"].sort_values())
if empresa_sel:
    nit_foco = empresa_sel.split("(")[-1].replace(")", "").strip()
    # Asegúrate de que ambos sean string para la comparación
    nit_foco = str(nit_foco)
    df_anio["nit"] = df_anio["nit"].astype(str)
    empresa_foco_df = df_anio[df_anio["nit"] == nit_foco]
    if empresa_foco_df.empty:
        st.error("No se encontró la empresa seleccionada para el año elegido. Verifica el NIT o selecciona otro año/empresa.")
        st.stop()
    df_foco = empresa_foco_df.iloc[0]
else:
    st.stop()

# --- Mostrar los datos de la empresa seleccionada de forma clara y compacta ---
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

# --- 7. Selección del universo comparativo y vista en columnas ---
st.markdown("<h3 style='font-family: Fira Sans, sans-serif;'>Selecciona el universo de comparación</h3>", unsafe_allow_html=True)
opciones_comp = [
    "Industria: Top 5 ventas",
    "Industria: 5 más cercanas en ventas",
    "Subindustria: Top 5 ventas",
    "Subindustria: 5 más cercanas en ventas",
    "CIIU: Top 5 ventas",
    "CIIU: 5 más cercanas en ventas",
    "Manual: escoger NIT"
]

col_sel, col_peers = st.columns([2, 1])
with col_sel:
    tipo_comp = st.radio(
        "Tipo de comparación:", 
        opciones_comp, 
        horizontal=False,
        key="radio_tipo_comparacion"
    )
# ----------- BLOQUE DE TABLA DE EMPRESAS COMPARABLES ------------

# 1. Texto del criterio
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

# 2. Formateo de miles
def formato_miles(x):
    try:
        return "{:,.0f}".format(x).replace(",", ".")
    except:
        return ""

# 3. Obtiene los 5 peers (sin empresa foco)
df_peers = empresas_cmp[["razon_social", "nit", "ingresos"]].copy()
df_peers = df_peers[df_peers["nit"].astype(str) != str(df_foco["nit"])]
df_peers = df_peers.sort_values("ingresos", ascending=False)
peers_tabla = df_peers.head(5)

# 4. Agrega la empresa foco como sexta fila (solo una vez)
df_foco_row = pd.DataFrame([{
    "razon_social": df_foco["razon_social"] + " (Empresa Analizada)",
    "nit": df_foco["nit"],
    "ingresos": df_foco["ingresos"]
}])
df_tabla = pd.concat([peers_tabla, df_foco_row], ignore_index=True)

# 5. Aplica formato de miles
df_tabla["Ingresos"] = df_tabla["ingresos"].apply(formato_miles)
df_tabla = df_tabla[["razon_social", "nit", "Ingresos"]]
df_tabla = df_tabla.rename(columns={
    "razon_social": "Empresa",
    "nit": "NIT"
})

# 6. Muestra el criterio y la tabla
st.markdown(
    f"<div style='font-size:18px; margin-bottom:12px;'><b>{criterio}</b><br>{detalle}</div>",
    unsafe_allow_html=True
)
st.markdown("<h3 style='font-family: Fira Sans, sans-serif;'>Empresas comparables seleccionadas:</h3>", unsafe_allow_html=True)
st.dataframe(df_tabla, hide_index=True)



# --- 8. Selección de variable de comparación ---
st.markdown("<h3 style='font-family: Fira Sans, sans-serif;'>Selecciona la variable a comparar</h3>", unsafe_allow_html=True)
variable_sel = st.selectbox("Variable:", list(variables.keys()))
col_var = variables[variable_sel]

# --- 9. Armar la tabla de comparación ---
df_result = empresas_cmp[["razon_social", "nit", col_var]].copy()
df_result = df_result.append({
    "razon_social": df_foco["razon_social"] + " (Empresa Analizada)",
    "nit": df_foco["nit"],
    col_var: df_foco[col_var]
}, ignore_index=True)
df_result = df_result.drop_duplicates(subset=["nit"])
df_result = df_result.sort_values(col_var, ascending=False)

# --- 10. Mostrar advertencias si hay datos faltantes ---
if df_result[col_var].isnull().any():
    st.warning("⚠️ Una o más empresas no tienen datos para la variable seleccionada. Revise la tabla para más detalle.")

# --- 11. Formatear valores ---
def formato_valor(x):
    try:
        if col_var in variables_porcentaje:
            return f"{x*100:.2f}%"
        else:
            return f"{x/DIVISOR:,.0f}"
    except:
        return ""
df_result["Valor"] = df_result[col_var].apply(formato_valor)
df_result = df_result[["razon_social", "nit", "Valor"]]

# --- 12. Mostrar tabla ---
st.markdown("<h3 style='font-family: Fira Sans, sans-serif;'>Tabla comparativa</h3>", unsafe_allow_html=True)
st.dataframe(df_result.rename(columns={
    "razon_social": "Empresa",
    "nit": "NIT",
    "Valor": variable_sel
}), hide_index=True)

# --- 13. Gráfica comparativa ---
st.markdown("<h3 style='font-family: Fira Sans, sans-serif;'>Gráfica comparativa</h3>", unsafe_allow_html=True)
fig = px.bar(
    df_result,
    x="Valor",
    y="Empresa",
    orientation="h",
    color_discrete_sequence=[COLORES[0]],
    labels={"Empresa": "Empresa", "Valor": variable_sel},
    title=""
)
fig.update_layout(
    margin=dict(t=40, b=40),
    font=dict(family="Fira Sans, sans-serif"),
    plot_bgcolor='white',
    paper_bgcolor='white'
)
st.plotly_chart(fig, use_container_width=True)

# --- 14. Botón de descarga de tabla ---
csv = df_result.rename(columns={
    "razon_social": "Empresa",
    "nit": "NIT",
    "Valor": variable_sel
}).to_csv(index=False).encode('utf-8')
st.download_button(
    "Descargar tabla CSV",
    data=csv,
    file_name=f'benchmark_{anio_sel}_{variable_sel}.csv',
    mime='text/csv'
)

# --- 15. Banner y branding final ---
st.markdown("""
<div style='background:#FBAF3A22; border-radius:14px; padding:24px 16px; margin:30px 0; text-align:center; box-shadow: 0 2px 12px #00000022;'>
    <h2 style='color:#BF1B18; margin-bottom:12px; font-size:28px;'>Compara tu empresa y toma mejores decisiones</h2>
    <div style='max-width:650px; margin:0 auto; font-size:17px; color:#222; text-align:center; line-height:1.5;'>
        <b>Reporte Capitalia:</b> Benchmark financiero de miles de empresas en Colombia.<br>
        <div style='margin:14px 0 4px 0; text-align:center; font-size:17px;'>
            <span style='display:block; margin:2px 0;'><b style='color:#BF1B18;'>✔️</b> Selecciona tu peer group y compara variables clave</span>
            <span style='display:block; margin:2px 0;'><b style='color:#BF1B18;'>✔️</b> Descarga los resultados y úsalos en tus informes</span>
        </div>
        <a href="https://reportecapitalia.ai/" target="_blank">
            <button style='background:#BF1B18; color:white; font-size:18px; border:none; padding:10px 34px; border-radius:8px; cursor:pointer; margin-top:10px; font-weight:600; box-shadow:0 2px 8px #bf1b1822;'>
                Ir al sitio web
            </button>
        </a>
    </div>
</div>
""", unsafe_allow_html=True)
