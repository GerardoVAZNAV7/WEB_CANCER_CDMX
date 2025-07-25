# tasa_por_poblacion.py
import pandas as pd
import plotly.express as px
import numpy as np
from sklearn.linear_model import LinearRegression
import streamlit as st

def mostrar_tasa(df, anio):
    poblacion_cdmx = [
        8700000, 8720916, 8756000, 8795000, 8827000,
        8839000, 8851080, 8878000, 8896000, 8908000,
        8915000, 8918653, 9013000, 9108000, 9159000,
        9194000, 9209944, 9230000, 9265000, 9300000
    ]

    cancer_por_anio = df.groupby("ANIO").size().reset_index(name="Defunciones").sort_values("ANIO").reset_index(drop=True)
    cancer_por_anio["Poblacion"] = poblacion_cdmx
    cancer_por_anio["Tasa por 100k"] = (cancer_por_anio["Defunciones"] / cancer_por_anio["Poblacion"]) * 100000

    if anio in cancer_por_anio["ANIO"].values:
        tasa_anio = cancer_por_anio[cancer_por_anio["ANIO"] == anio]["Tasa por 100k"].values[0]
        st.info(f"📌 En el año {anio}, hubo {tasa_anio:.2f} defunciones por cada 100,000 habitantes en CDMX.")

    # Predicción
    X = cancer_por_anio["ANIO"].values.reshape(-1, 1)
    y = cancer_por_anio["Tasa por 100k"].values
    modelo = LinearRegression().fit(X, y)
    anios_futuros = np.array([2024, 2025, 2026, 2027, 2028, 2029, 2030]).reshape(-1, 1)
    tasa_predicha = modelo.predict(anios_futuros)

    df_pred = pd.DataFrame({"ANIO": anios_futuros.flatten(), "Tasa por 100k": tasa_predicha, "Tipo": "Predicción"})
    cancer_por_anio["Tipo"] = "Histórico"

    df_total = pd.concat([cancer_por_anio[["ANIO", "Tasa por 100k", "Tipo"]], df_pred], ignore_index=True)

    fig = px.line(
        df_total,
        x="ANIO",
        y="Tasa por 100k",
        color="Tipo",
        markers=True,
        line_dash="Tipo",
        title="📈 Tasa anual de defunciones por cada 100,000 habitantes (con predicción hasta 2030)"
    )
    fig.update_layout(yaxis=dict(tickformat=".2f"))
    st.plotly_chart(fig, use_container_width=True)
