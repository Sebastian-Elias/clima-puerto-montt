import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from load.weather_loader import get_engine

CIUDAD = "Puerto Montt"

# Paleta limpia, inspirada en clima austral.
CANVAS = "#F4F7F8"
CARD = "#FFFFFF"
BORDER = "#D9E4E8"
TEXT_PRIMARY = "#1F2D35"
TEXT_MUTED = "#61717A"
BLUE = "#2F6F9F"
BLUE_BG = "#E2EEF7"
GREEN = "#2F7D69"
GREEN_BG = "#E1F0EB"
CORAL = "#D86A4A"
CORAL_BG = "#F8E4DD"
AMBER = "#B7791F"
AMBER_BG = "#F4E7CF"

FONT_SERIF = "Playfair Display, Georgia, serif"
FONT_SANS = "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"

ICON_TREND = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
    stroke-linecap="round" stroke-linejoin="round">
    <polyline points="3 17 9 11 13 15 21 6"></polyline>
    <polyline points="15 6 21 6 21 12"></polyline>
</svg>"""

ICON_FLAME = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
    stroke-linecap="round" stroke-linejoin="round">
    <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.07-2.14-.22-4.05 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.15.43-2.29 1-3a2.5 2.5 0 0 0 2.5 2.5z"></path>
</svg>"""

ICON_SNOWFLAKE = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
    stroke-linecap="round" stroke-linejoin="round">
    <line x1="2" y1="12" x2="22" y2="12"></line>
    <line x1="12" y1="2" x2="12" y2="22"></line>
    <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line>
    <line x1="19.07" y1="4.93" x2="4.93" y2="19.07"></line>
</svg>"""


@st.cache_data(ttl=3600)
def cargar_datos():
    engine = get_engine()
    query = """
        SELECT date, temperature_2m_max, temperature_2m_min, temperature_2m_mean
        FROM weather_daily
        WHERE city = %(ciudad)s
        ORDER BY date;
    """
    df = pd.read_sql(query, engine, params={"ciudad": CIUDAD})

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


def aplicar_layout_grafico(fig, titulo, altura):
    fig.update_layout(
        title=dict(text=titulo, x=0, font=dict(size=16, family=FONT_SERIF, color=TEXT_PRIMARY)),
        plot_bgcolor=CARD,
        paper_bgcolor=CARD,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, family=FONT_SANS, color=TEXT_MUTED),
        ),
        xaxis=dict(
            showgrid=False,
            color=TEXT_MUTED,
            tickfont=dict(family=FONT_SANS, size=11, color=TEXT_PRIMARY),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=BORDER,
            gridwidth=1,
            color=TEXT_MUTED,
            title="°C",
            tickfont=dict(family=FONT_SANS, size=11, color=TEXT_PRIMARY),
        ),
        margin=dict(t=46, b=18, l=12, r=12),
        height=altura,
        font=dict(family=FONT_SANS, color=TEXT_PRIMARY),
        hoverlabel=dict(
            font=dict(family=FONT_SANS, color=TEXT_PRIMARY),
            bgcolor=CARD,
            bordercolor=BORDER,
        ),
    )
    return fig


def grafico_con_tendencia(anios, valores, color, nombre, altura=300):
    pendiente, intercepto = np.polyfit(anios, valores, 1)
    tendencia = pendiente * anios + intercepto

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=anios,
            y=valores,
            mode="lines",
            line=dict(color=color, width=2.6),
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
            line=dict(color=TEXT_MUTED, width=1.7, dash="dot"),
            name=f"Tendencia ({pendiente * 10:+.2f} °C/década)",
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[anios[-1]],
            y=[valores[-1]],
            mode="markers+text",
            marker=dict(color=color, size=9, line=dict(color=CARD, width=2)),
            text=[f"{valores[-1]:.1f} °C"],
            textposition="top center",
            textfont=dict(family=FONT_SANS, color=TEXT_PRIMARY, size=13),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    return aplicar_layout_grafico(fig, nombre, altura)


def tarjeta_metrica(icono, icono_bg, icono_fg, etiqueta, valor, detalle, detalle_color):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-head">
                <div class="metric-icon" style="background-color:{icono_bg}; color:{icono_fg};">{icono}</div>
                <div class="metric-label">{etiqueta}</div>
            </div>
            <div class="metric-value">{valor}</div>
            <div class="metric-detail" style="color:{detalle_color};">{detalle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(page_title=f"¿Clima inestable? · {CIUDAD}", layout="wide")

st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        .stApp {
            background: #F4F7F8;
            color: #1F2D35;
            font-family: 'Inter', sans-serif;
        }
        header[data-testid="stHeader"] {
            background: rgba(244, 247, 248, 0.92);
            border-bottom: 1px solid rgba(217, 228, 232, 0.75);
        }
        .block-container {
            padding-top: 3.25rem;
            padding-bottom: 2rem;
            padding-left: 3rem;
            padding-right: 3rem;
            max-width: 1440px;
        }
        div[data-testid="stVerticalBlock"] {
            gap: 1rem;
        }
        div[data-testid="stHorizontalBlock"] {
            gap: 1rem;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #FFFFFF;
            border: 1px solid #D9E4E8;
            border-radius: 8px;
            box-shadow: 0 10px 26px rgba(31, 45, 53, 0.06);
            padding: 0.25rem 0.45rem;
        }
        .dashboard-header {
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 0.25rem;
        }
        .dashboard-eyebrow {
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.13em;
            text-transform: uppercase;
            color: #2F6F9F;
            margin-bottom: 0.25rem;
        }
        .dashboard-title {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.12;
            color: #1F2D35;
            margin: 0;
        }
        .dashboard-subtitle {
            color: #61717A;
            font-size: 0.92rem;
            line-height: 1.45;
            margin-top: 0.4rem;
        }
        .dashboard-analysis-link {
            display: inline-block;
            margin-top: 0.6rem;
            color: #2F6F9F;
            font-size: 0.85rem;
            font-weight: 600;
            text-decoration: none;
        }
        .dashboard-analysis-link:hover {
            text-decoration: underline;
        }
        .dashboard-range {
            color: #61717A;
            font-size: 0.82rem;
            font-weight: 600;
            text-align: right;
            white-space: nowrap;
            padding-bottom: 0.25rem;
        }
        .metric-card {
            min-height: 138px;
            background: #FFFFFF;
            border: 1px solid #D9E4E8;
            border-radius: 8px;
            box-shadow: 0 10px 26px rgba(31, 45, 53, 0.06);
            padding: 1rem 1.1rem;
        }
        .metric-head {
            display: flex;
            align-items: center;
            gap: 0.65rem;
            margin-bottom: 0.8rem;
        }
        .metric-icon {
            width: 34px;
            height: 34px;
            min-width: 34px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .metric-icon svg {
            width: 17px;
            height: 17px;
        }
        .metric-label {
            color: #61717A;
            font-size: 0.8rem;
            font-weight: 700;
            line-height: 1.25;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .metric-value {
            color: #1F2D35;
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: 0;
            line-height: 1.05;
        }
        .metric-detail {
            font-size: 0.84rem;
            font-weight: 600;
            line-height: 1.35;
            margin-top: 0.55rem;
        }
        div[data-testid="stExpander"] {
            background: #FFFFFF;
            border: 1px solid #D9E4E8;
            border-radius: 8px;
            box-shadow: 0 10px 26px rgba(31, 45, 53, 0.05);
        }
        div[data-testid="stExpander"] summary {
            color: #1F2D35 !important;
            background: transparent !important;
            font-size: 0.9rem;
            font-weight: 700;
            padding: 0.9rem 1.1rem;
        }
        div[data-testid="stExpander"] summary:hover,
        div[data-testid="stExpander"] summary:focus,
        div[data-testid="stExpander"] details[open] summary {
            color: #1F2D35 !important;
            background: transparent !important;
        }
        div[data-testid="stExpanderDetails"] p,
        div[data-testid="stExpanderDetails"] span {
            color: #61717A;
            font-family: 'Inter', sans-serif;
        }
        @media (max-width: 900px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
                padding-top: 2.75rem;
            }
            .dashboard-header {
                align-items: flex-start;
                flex-direction: column;
            }
            .dashboard-range {
                text-align: left;
                white-space: normal;
            }
            .dashboard-title {
                font-size: 1.65rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

df = cargar_datos()
anual = calcular_promedio_anual(df)
extremos = calcular_extremos_anuales(df)
decadas = calcular_promedio_decada(df)
record_max, record_min = calcular_records_historicos(df)

primera_decada = decadas.iloc[0]
ultima_decada = decadas.iloc[-1]
delta_decadas = ultima_decada["temperature_2m_mean"] - primera_decada["temperature_2m_mean"]
inicio_serie = int(anual["year"].min())
fin_serie = int(anual["year"].max())

rango_extremo = extremos["temperature_2m_max"] - extremos["temperature_2m_min"]

st.markdown(
    f"""
    <section class="dashboard-header">
        <div>
            <div class="dashboard-eyebrow">Análisis de estabilidad climática · Chile</div>
            <h1 class="dashboard-title">¿Se está volviendo más inestable el clima en {CIUDAD}?</h1>
            <div class="dashboard-subtitle">El promedio anual se mantiene casi plano — la pregunta es qué pasa con sus extremos. 85 años de temperatura diaria, {inicio_serie}-{fin_serie}.</div>
            <a class="dashboard-analysis-link" href="app/static/estabilidad_climatica.html" target="_blank">
                Ver el análisis estadístico completo →
            </a>
        </div>
        <div class="dashboard-range">Serie histórica {inicio_serie}-{fin_serie}<br>Datos ERA5 vía Open-Meteo</div>
    </section>
    """,
    unsafe_allow_html=True,
)

color_delta_decada = CORAL if delta_decadas > 0 else GREEN
col_kpi_1, col_kpi_2, col_kpi_3 = st.columns(3, gap="medium")

with col_kpi_1:
    tarjeta_metrica(
        ICON_TREND,
        AMBER_BG,
        AMBER,
        f"Media década {ultima_decada['label']}",
        f"{ultima_decada['temperature_2m_mean']:.1f} °C",
        f"{delta_decadas:+.1f} °C vs {primera_decada['label']}",
        color_delta_decada,
    )

with col_kpi_2:
    tarjeta_metrica(
        ICON_FLAME,
        CORAL_BG,
        CORAL,
        "Récord de calor histórico",
        f"{record_max['temperature_2m_max']:.1f} °C",
        f"Registrado el {record_max['date'].strftime('%d-%m-%Y')}",
        TEXT_MUTED,
    )

with col_kpi_3:
    tarjeta_metrica(
        ICON_SNOWFLAKE,
        BLUE_BG,
        BLUE,
        "Récord de frío histórico",
        f"{record_min['temperature_2m_min']:.1f} °C",
        f"Registrado el {record_min['date'].strftime('%d-%m-%Y')}",
        TEXT_MUTED,
    )

fig_linea = grafico_con_tendencia(
    anual["year"].to_numpy(),
    anual["temperature_2m_mean"].to_numpy(),
    BLUE,
    "Temperatura media anual",
    altura=390,
)

fig_rango = grafico_con_tendencia(
    extremos["year"].to_numpy(),
    rango_extremo.to_numpy(),
    AMBER,
    "Amplitud térmica anual (máx - mín)",
    altura=285,
)

fig_max = grafico_con_tendencia(
    extremos["year"].to_numpy(),
    extremos["temperature_2m_max"].to_numpy(),
    CORAL,
    "Máxima anual (día más caluroso)",
    altura=285,
)

fig_min = grafico_con_tendencia(
    extremos["year"].to_numpy(),
    extremos["temperature_2m_min"].to_numpy(),
    GREEN,
    "Mínima anual (día más frío)",
    altura=285,
)

with st.container(border=True):
    st.plotly_chart(fig_linea, use_container_width=True)

col_graf_1, col_graf_2, col_graf_3 = st.columns(3, gap="medium")

with col_graf_1:
    with st.container(border=True):
        st.plotly_chart(fig_rango, use_container_width=True)

with col_graf_2:
    with st.container(border=True):
        st.plotly_chart(fig_max, use_container_width=True)

with col_graf_3:
    with st.container(border=True):
        st.plotly_chart(fig_min, use_container_width=True)

with st.expander("Notas y datos"):
    st.caption(
        "El promedio anual muestra una tendencia casi plana, pero la amplitud térmica "
        "(máxima menos mínima de cada año) se ha ido ampliando con el tiempo: la señal de "
        "inestabilidad aparece en los extremos, no en el promedio. Esto puede ser una tendencia "
        "climática real, pero también puede reflejar que el archivo histórico de Open-Meteo, "
        "basado en ERA5, tenía muchas menos observaciones antes de la era satelital "
        "(alrededor de 1979), lo que suaviza artificialmente los años más antiguos. El análisis "
        "estadístico completo — metodología, cifras y limitaciones — está en "
        "`analysis/estabilidad_climatica.ipynb`."
    )
    st.caption("Promedio anual")
    st.dataframe(anual, use_container_width=True, height=150)
    st.caption("Extremos anuales")
    st.dataframe(extremos, use_container_width=True, height=150)
    st.caption("Promedio por década")
    st.dataframe(decadas.drop(columns="label"), use_container_width=True, height=150)
