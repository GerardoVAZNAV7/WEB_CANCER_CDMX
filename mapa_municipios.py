import geopandas as gpd
import folium
from branca.colormap import linear
from streamlit_folium import st_folium
import streamlit as st
import pandas as pd

def cargar_shapefile():
    gdf = gpd.read_file("poligonos_alcaldias_cdmx.shp")
    gdf["CVE_MUN"] = gdf["CVE_MUN"].astype(str).str.zfill(3)
    return gdf

def mostrar_mapa_interactivo(df_filtrado, gdf):
    conteo_mapa = df_filtrado.groupby("MUN_RESID").size().reset_index(name="Defunciones")
    gdf_mapa = gdf.merge(conteo_mapa, left_on="CVE_MUN", right_on="MUN_RESID", how="left")
    gdf_mapa["Defunciones"] = gdf_mapa["Defunciones"].fillna(0)

    m = folium.Map(location=[19.4, -99.15], zoom_start=10, tiles="cartodbpositron")
    colormap = linear.Blues_09.scale(
        gdf_mapa["Defunciones"].min(), 
        gdf_mapa["Defunciones"].max()
    ).to_step(10)
    colormap.caption = 'Número de defunciones por municipio'

    folium.GeoJson(
        gdf_mapa,
        style_function=lambda feature: {
            'fillColor': colormap(feature['properties']['Defunciones']),
            'color': 'black', 'weight': 0.5, 'fillOpacity': 0.7
        },
        tooltip=folium.features.GeoJsonTooltip(
            fields=['NOMGEO', 'Defunciones'],
            aliases=['Municipio:', 'Defunciones:'],
            localize=True
        )
    ).add_to(m)

    colormap.add_to(m)
    st_folium(m, width=1000, height=400)