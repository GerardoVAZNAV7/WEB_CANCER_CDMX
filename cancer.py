import streamlit as st
import pandas as pd
import plotly.express as px
from mapa_municipios import cargar_shapefile, mostrar_mapa_interactivo
 
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from branca.colormap import linear
from tasa_por_poblacion import mostrar_tasa
st.set_page_config(page_title="Cáncer en CDMX", layout="wide")
st.title("📊 Dashboard de Defunciones por Cáncer en CDMX (2004–2023)")

# 📁 Cargar datos
@st.cache_data
def cargar_datos():
    df = pd.read_csv("datos_cancer_categorizado_mun.csv", encoding='latin1')
    municipios = pd.read_csv("diccionario_municipios.csv", encoding='latin1')
    ocupaciones = pd.read_csv("diccionario_ocupacion.csv", encoding='latin1')

    # Limpiar nombres de columnas
    municipios.columns = municipios.columns.str.strip().str.lower()
    municipios.rename(columns={"codigo": "codigo", "descripcion": "nombre"}, inplace=True)

    ocupaciones.columns = ocupaciones.columns.str.strip().str.lower()
    ocupaciones.rename(columns={"codigo": "codigo", "descripcion": "descripcion"}, inplace=True)

    # Asegurar que los códigos sean strings con ceros a la izquierda
    df["MUN_RESID"] = df["MUN_RESID"].astype(str).str.zfill(3)
    municipios["codigo"] = municipios["codigo"].astype(str).str.zfill(3)

    # Unir el nombre del municipio
    df = df.merge(municipios, left_on="MUN_RESID", right_on="codigo", how="left")
    df = df.rename(columns={"nombre": "MUNICIPIO_NOMBRE"})

    # Mapear sexo a etiquetas
    df["SEXO"] = df["SEXO"].map({1: "Masculino", 2: "Femenino"})

    # Mapear asistencia médica
    df["ASIST_MEDI"] = df["ASIST_MEDI"].map({1: "Sí recibió", 2: "No recibió"}).fillna("No especificado")

    # Mapear derechohabiencia
    derechohabiencia_dict = pd.read_csv("diccionario_derecho_habiencia.csv", encoding='latin1')
    derechohabiencia_dict.columns = derechohabiencia_dict.columns.str.strip().str.lower()
    derechohabiencia_dict.rename(columns={"codigo": "codigo", "descripcion": "descripcion"}, inplace=True)
    derechohabiencia_dict["codigo"] = derechohabiencia_dict["codigo"].astype(int)
    df = df.merge(derechohabiencia_dict, left_on="DERECHOHAB", right_on="codigo", how="left")
    df = df.rename(columns={"descripcion": "DERECHOHAB_NOMBRE"})

    # Mapear ocupación
    ocupaciones["codigo"] = ocupaciones["codigo"].astype(int)
    df = df.merge(ocupaciones, left_on="OCUPACION", right_on="codigo", how="left")
    df = df.rename(columns={"descripcion": "OCUPACION_NOMBRE"})

    return df

df = cargar_datos()


# 🎚️ Filtros en la barra lateral
st.sidebar.header("🔎 Filtros")

anios = sorted(df["ANIO"].dropna().unique())
anio = st.sidebar.selectbox("Selecciona el año", anios)

sexos = df["SEXO"].dropna().unique()
sexo = st.sidebar.multiselect("Sexo", sexos, default=sexos)

min_edad, max_edad = int(df["EDAD"].min()), int(df["EDAD"].max())
rango_edad = st.sidebar.slider("Rango de edad", min_edad, max_edad, (min_edad, max_edad))


# Filtrado por nombres de municipios
municipios = df["MUNICIPIO_NOMBRE"].dropna().unique()
municipio = st.sidebar.multiselect("Municipio de residencia", sorted(municipios), default=sorted(municipios))

# 🔍 Aplicar filtros
df_filtrado = df[
    (df["ANIO"] == anio) &
    (df["SEXO"].isin(sexo)) &
    (df["EDAD"].between(rango_edad[0], rango_edad[1])) &
    (df["MUNICIPIO_NOMBRE"].isin(municipio))
]

# 🧾 Mostrar tabla con datos filtrados
st.subheader(f"📄 Datos filtrados ({len(df_filtrado)} registros)")
st.dataframe(df_filtrado.head(), use_container_width=True)

# 📈 Gráfica por tipo de cáncer
conteo_cancer = df_filtrado["TIPO_CANCER"].value_counts().reset_index()
conteo_cancer.columns = ["Tipo de Cáncer", "Número de Casos"]

st.subheader("📌 Defunciones por tipo de cáncer")
if not conteo_cancer.empty:
    fig1 = px.bar(
        conteo_cancer,
        x="Tipo de Cáncer",
        y="Número de Casos",
        text_auto=True,
        title=f"Distribución de tipos de cáncer en {anio}"
    )
    fig1.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig1, use_container_width=True)
else:
    st.warning("⚠️ No hay datos para mostrar defunciones por tipo de cáncer.")

st.markdown("#### 🏥 Defunciones por Derechohabiencia")
derechohab_counts = df_filtrado["DERECHOHAB_NOMBRE"].value_counts().reset_index()
derechohab_counts.columns = ["Derechohabiencia", "Cantidad"]
fig_derechohab = px.bar(
derechohab_counts,
x="Derechohabiencia",
y="Cantidad",
labels={"Cantidad": "Número de defunciones"},
color="Derechohabiencia",
color_discrete_sequence=px.colors.qualitative.Set2
    )
st.plotly_chart(fig_derechohab, use_container_width=True)

# 📉 Gráfica por municipio
st.subheader("🏙️ Defunciones por municipio de residencia")
conteo_municipio = df_filtrado["MUNICIPIO_NOMBRE"].value_counts().reset_index()
conteo_municipio.columns = ["Municipio", "Número de Casos"]

if not conteo_municipio.empty:
    fig2 = px.bar(
        conteo_municipio,
        x="Municipio",
        y="Número de Casos",
        text_auto=True,
        title=f"Distribución por municipio de residencia en {anio}"
    )
    fig2.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.warning("⚠️ No hay datos para mostrar defunciones por municipio.")

with st.expander("📦 Información General (Resumen)", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📈 Tendencia general de defunciones por cáncer")
        cancer_por_anio = df.groupby("ANIO").size().reset_index(name="Defunciones")
        fig_linea = px.line(cancer_por_anio, x="ANIO", y="Defunciones", markers=True)
        st.plotly_chart(fig_linea, use_container_width=True)

        st.markdown("### 🧬 Total acumulado por tipo de cáncer")
        tipo_acumulado = df["TIPO_CANCER"].value_counts().reset_index()
        tipo_acumulado.columns = ["Tipo de Cáncer", "Número de Casos"]
        fig_bar_total = px.bar(tipo_acumulado, x="Tipo de Cáncer", y="Número de Casos", text_auto=True)
        fig_bar_total.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_bar_total, use_container_width=True)

       

        

    with col2:
        st.markdown("### 🧑‍🤝‍🧑 Distribución por género")
        genero_total = df["SEXO"].value_counts().reset_index()
        genero_total.columns = ["Sexo", "Cantidad"]
        fig_pie = px.pie(genero_total, names="Sexo", values="Cantidad", title="Proporción por género")
        st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("### 🚫 Defunciones sin asistencia médica")
        sin_asistencia = df[df["ASIST_MEDI"] == "No recibió"]
        conteo_sin_asistencia = sin_asistencia.shape[0]
        st.metric(label="Nº de defunciones sin asistencia médica", value=conteo_sin_asistencia)

      

        st.markdown("### 📊 Incremento promedio anual")
        cancer_por_anio_sorted = cancer_por_anio.sort_values("ANIO")
        incrementos = cancer_por_anio_sorted["Defunciones"].diff().dropna()
        prom_incremento = round(incrementos.mean(), 2)
        porcentaje = round((prom_incremento / cancer_por_anio_sorted["Defunciones"].iloc[0]) * 100, 2)
        st.info(f"Promedio anual: {prom_incremento} defunciones (+{porcentaje}%)")
st.markdown("### 🛠️ Ocupaciones sin asistencia médica")
ocupaciones_sin_asistencia = sin_asistencia["OCUPACION_NOMBRE"].value_counts().reset_index()
ocupaciones_sin_asistencia.columns = ["Ocupación", "Número de Casos"]
fig_ocupaciones = px.bar(ocupaciones_sin_asistencia, x="Ocupación", y="Número de Casos", text_auto=True)
fig_ocupaciones.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig_ocupaciones, use_container_width=True)
cancer_por_anio = df.groupby("ANIO").size().reset_index(name="Defunciones")
mostrar_tasa(df, anio)
gdf = cargar_shapefile()
mostrar_mapa_interactivo(df, gdf)        