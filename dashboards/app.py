import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from load.weather_loader import get_connection

CIUDAD = "Puerto Montt"

COLOR_SERIES = "#2a78d6"
COLOR_TREND = "#898781"
COLOR_GRID = "#e1e0d9"
COLOR_MUTED = "#898781"
COLOR_SURFACE = "#fcfcfb"
COLOR_MAX = "#e34948"
COLOR_MIN = "#2a78d6"


@st.cache_data(ttl=3600)
def cargar_datos():
    conn = get_connection()
    try:
        query = """
            SELECT date, temperature_2m_max, temperature_2m_min, temperature_2m_mean
            FROM weather_daily
            WHERE city = %s
            ORDER BY date;
        """
        df = pd.read_sql(query, conn, params=(CIUDAD,))
    finally:
        conn.close()

    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["decada"] = (df["year"] // 10) * 10
    return df


def calcular_promedio_anual(df):
    return df.groupby("year", as_index=False)[
        ["temperature_2m_max", "temperature_2m_min", "temperature_2m_mean"]
    ].mean()


def calcular_extremos_anuales(df):
    maximas = df.groupby("year", as_index=False)["temperature_2m_max"].max()
    minimas = df.groupby("year", as_index=False)["temperature_2m_min"].min()
    return maximas.merge(minimas, on="year")


def calcular_records_historicos(df):
    fila_max = df.loc[df["temperature_2m_max"].idxmax()]
    fila_min = df.loc[df["temperature_2m_min"].idxmin()]
    return fila_max, fila_min


def calcular_promedio_decada(df):
    resumen = df.groupby("decada", as_index=False)["temperature_2m_mean"].mean()
    resumen["label"] = resumen["decada"].astype(int).astype(str) + "s"
    return resumen


ALTURA_GRAFICO = 260


def grafico_con_tendencia(anios, valores, color, nombre):
    pendiente, intercepto = np.polyfit(anios, valores, 1)
    tendencia = pendiente * anios + intercepto

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=anios,
            y=valores,
            mode="lines",
            line=dict(color=color, width=2),
            name=nombre,
            showlegend=False,
            hovertemplate="%{x}: %{y:.1f} °C<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=anios,
            y=tendencia,
            mode="lines",
            line=dict(color=COLOR_TREND, width=2, dash="dash"),
            name=f"Tendencia ({pendiente * 10:+.2f} °C/década)",
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[anios[-1]],
            y=[valores[-1]],
            mode="markers+text",
            marker=dict(color=color, size=9, line=dict(color=COLOR_SURFACE, width=2)),
            text=[f"{valores[-1]:.1f} °C"],
            textposition="top center",
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.update_layout(
        title=dict(text=nombre, x=0, font=dict(size=13)),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="right", x=1, font=dict(size=10)),
        xaxis=dict(showgrid=False, color=COLOR_MUTED),
        yaxis=dict(showgrid=True, gridcolor=COLOR_GRID, gridwidth=1, color=COLOR_MUTED, title="°C"),
        margin=dict(t=30, b=10, l=10, r=10),
        height=ALTURA_GRAFICO,
    )
    return fig


st.set_page_config(page_title=f"Clima {CIUDAD}", layout="wide")
st.markdown(f"#### ¿Está cambiando el clima en {CIUDAD}? · 1940-2025")

df = cargar_datos()
anual = calcular_promedio_anual(df)
extremos = calcular_extremos_anuales(df)
decadas = calcular_promedio_decada(df)
record_max, record_min = calcular_records_historicos(df)

primera_decada = decadas.iloc[0]
ultima_decada = decadas.iloc[-1]
delta_decadas = ultima_decada["temperature_2m_mean"] - primera_decada["temperature_2m_mean"]

col_a, col_b, col_c = st.columns(3)
with col_a:
    st.metric(
        label=f"Temp. media, década de {ultima_decada['label']}",
        value=f"{ultima_decada['temperature_2m_mean']:.1f} °C",
        delta=f"{delta_decadas:+.1f} °C vs {primera_decada['label']}",
    )
with col_b:
    st.metric(
        label="Temp. más alta registrada",
        value=f"{record_max['temperature_2m_max']:.1f} °C",
        delta=record_max["date"].strftime("%d-%m-%Y"),
        delta_color="off",
    )
with col_c:
    st.metric(
        label="Temp. más baja registrada",
        value=f"{record_min['temperature_2m_min']:.1f} °C",
        delta=record_min["date"].strftime("%d-%m-%Y"),
        delta_color="off",
    )

fig_linea = grafico_con_tendencia(
    anual["year"].to_numpy(),
    anual["temperature_2m_mean"].to_numpy(),
    COLOR_SERIES,
    "Temperatura media anual",
)
fig_barras = go.Figure()
fig_barras.add_trace(
    go.Bar(
        x=decadas["label"],
        y=decadas["temperature_2m_mean"],
        marker_color=COLOR_SERIES,
        text=[f"{v:.1f}" for v in decadas["temperature_2m_mean"]],
        textposition="outside",
        hovertemplate="%{x}: %{y:.1f} °C<extra></extra>",
        width=0.6,
    )
)
fig_barras.update_layout(
    title=dict(text="Promedio por década", x=0, font=dict(size=13)),
    showlegend=False,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=False, color=COLOR_MUTED),
    yaxis=dict(showgrid=True, gridcolor=COLOR_GRID, gridwidth=1, color=COLOR_MUTED, title="°C"),
    margin=dict(t=30, b=10, l=10, r=10),
    height=ALTURA_GRAFICO,
)
fig_max = grafico_con_tendencia(
    extremos["year"].to_numpy(),
    extremos["temperature_2m_max"].to_numpy(),
    COLOR_MAX,
    "Máxima anual (día más caluroso)",
)
fig_min = grafico_con_tendencia(
    extremos["year"].to_numpy(),
    extremos["temperature_2m_min"].to_numpy(),
    COLOR_MIN,
    "Mínima anual (día más frío)",
)

fila1_izq, fila1_der = st.columns(2)
with fila1_izq:
    st.plotly_chart(fig_linea, width="stretch")
with fila1_der:
    st.plotly_chart(fig_barras, width="stretch")

fila2_izq, fila2_der = st.columns(2)
with fila2_izq:
    st.plotly_chart(fig_max, width="stretch")
with fila2_der:
    st.plotly_chart(fig_min, width="stretch")

with st.expander("Notas y datos"):
    st.caption(
        "La variabilidad año a año de la temperatura media también crece con el tiempo (la "
        "década de 1940 es la más 'plana' de toda la serie). Esto puede ser una señal climática "
        "real, pero también puede reflejar que el archivo histórico de Open-Meteo (basado en "
        "ERA5) tenía muchas menos observaciones antes de la era satelital (~1979), lo que "
        "suaviza artificialmente los años más antiguos. Con una sola ciudad y variable no se "
        "puede separar ambos efectos."
    )
    st.caption("Promedio anual")
    st.dataframe(anual, width="stretch")
    st.caption("Extremos anuales")
    st.dataframe(extremos, width="stretch")
    st.caption("Promedio por década")
    st.dataframe(decadas.drop(columns="label"), width="stretch")
