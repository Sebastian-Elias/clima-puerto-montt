import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from load.weather_loader import get_connection

CIUDAD = "Puerto Montt"

# --- Paleta "editorial cálida" ---------------------------------------------
CANVAS = "#A6907C"        # taupe/marrón ceniza (fondo principal)
CARD = "#FAF5E9"          # crema/beige (fondo de tarjetas)
BORDER = "#E8DFCF"        # líneas y grillas, muy atenuadas
TEXT_PRIMARY = "#2C241D"  # texto sobre tarjetas
TEXT_MUTED = "#8B7B6B"    # texto secundario sobre tarjetas
JADE = "#3F6C56"          # verde jade/pino — éxito, óptimo
JADE_BG = "#E1EAE3"
TERRACOTTA = "#C97C5D"    # salmón/terracota — alerta, calor
TERRACOTTA_BG = "#F3DED2"
MUSTARD = "#C99A44"       # ocre/mostaza — foco secundario
MUSTARD_BG = "#F2E7D3"

FONT_SERIF = "Playfair Display, Georgia, serif"
FONT_SANS = "Inter, -apple-system, sans-serif"

ICON_TREND = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"
    stroke-linecap="round" stroke-linejoin="round">
    <polyline points="3 17 9 11 13 15 21 6"></polyline>
    <polyline points="15 6 21 6 21 12"></polyline>
</svg>"""

ICON_FLAME = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"
    stroke-linecap="round" stroke-linejoin="round">
    <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.07-2.14-.22-4.05 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.15.43-2.29 1-3a2.5 2.5 0 0 0 2.5 2.5z"></path>
</svg>"""

ICON_SNOWFLAKE = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"
    stroke-linecap="round" stroke-linejoin="round">
    <line x1="2" y1="12" x2="22" y2="12"></line>
    <line x1="12" y1="2" x2="12" y2="22"></line>
    <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line>
    <line x1="19.07" y1="4.93" x2="4.93" y2="19.07"></line>
</svg>"""


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


ALTURA_GRAFICO = 220


def grafico_con_tendencia(anios, valores, color, nombre):
    pendiente, intercepto = np.polyfit(anios, valores, 1)
    tendencia = pendiente * anios + intercepto

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=anios,
            y=valores,
            mode="lines",
            line=dict(color=color, width=2.5),
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
            line=dict(color=TEXT_MUTED, width=1.5, dash="dot"),
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
    fig.update_layout(
        title=dict(text=nombre, x=0, font=dict(size=15, family=FONT_SERIF, color=TEXT_PRIMARY)),
        plot_bgcolor=CARD,
        paper_bgcolor=CARD,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="right", x=1,
                    font=dict(size=10, family=FONT_SANS, color=TEXT_MUTED)),
        xaxis=dict(showgrid=False, color=TEXT_MUTED, tickfont=dict(family=FONT_SANS, size=10)),
        yaxis=dict(showgrid=True, gridcolor=BORDER, gridwidth=1, color=TEXT_MUTED,
                    title="°C", tickfont=dict(family=FONT_SANS, size=10)),
        margin=dict(t=34, b=10, l=5, r=5),
        height=ALTURA_GRAFICO,
        hoverlabel=dict(font=dict(family=FONT_SANS, color=TEXT_PRIMARY), bgcolor=CARD,
                         bordercolor=BORDER),
    )
    return fig


st.set_page_config(page_title=f"Clima {CIUDAD}", layout="wide")

st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --nm-light: rgba(255, 248, 235, 0.6);
            --nm-light-strong: rgba(255, 250, 240, 0.8);
            --nm-dark: rgba(53, 40, 27, 0.4);
            --nm-dark-strong: rgba(48, 36, 24, 0.5);
        }
        .stApp {
            background-color: #A6907C;
            background-image: repeating-linear-gradient(105deg, rgba(255,255,255,0.035) 0px, rgba(255,255,255,0.035) 1px, transparent 1px, transparent 4px);
            font-family: 'Inter', sans-serif;
        }
        header[data-testid="stHeader"] {
            background: #A6907C;
        }
        header[data-testid="stHeader"] button {
            background: #A6907C;
            border: none;
            border-radius: 10px;
            box-shadow: -3px -3px 6px var(--nm-light), 3px 3px 7px var(--nm-dark);
            color: #2C241D;
            transition: box-shadow .15s ease;
        }
        header[data-testid="stHeader"] button:hover {
            background: #A6907C;
            box-shadow: inset 3px 3px 6px var(--nm-dark), inset -3px -3px 6px var(--nm-light);
            color: #2C241D;
        }
        header[data-testid="stHeader"] svg {
            fill: #2C241D;
        }
        .block-container {
            padding-top: 4.6rem;
            padding-bottom: 1.5rem;
            max-width: 1400px;
            min-height: calc(100vh - 4.6rem);
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .block-container > div[data-testid="stVerticalBlock"] {
            flex-grow: 0;
        }
        div[data-testid="stVerticalBlock"] {
            gap: 0.8rem;
        }

        /* --- Encabezado sobre el canvas taupe --- */
        .dashboard-eyebrow {
            font-family: 'Inter', sans-serif;
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.13em;
            text-transform: uppercase;
            color: #E9CE94;
            margin-bottom: 0.15rem;
        }
        .dashboard-title {
            font-family: 'Playfair Display', Georgia, serif;
            font-weight: 700;
            font-size: 1.9rem;
            line-height: 1.2;
            color: #F8F2E6;
            margin: 0 0 0.2rem 0;
        }
        .dashboard-subtitle {
            font-family: 'Inter', sans-serif;
            font-size: 0.88rem;
            color: #DCCDBC;
            margin-bottom: 1rem;
        }

        /* --- Tarjetas bento genéricas (gráficos) --- */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #FAF5E9;
            border-radius: 22px;
            border: none;
            box-shadow:
                -11px -11px 22px var(--nm-light),
                11px 11px 26px var(--nm-dark),
                inset 0 1px 0 rgba(255, 255, 255, 0.3);
            padding: 0.2rem 0.4rem;
        }

        /* --- Tarjetas de métricas (HTML custom) --- */
        .bento-metric {
            background: #FAF5E9;
            border-radius: 22px;
            box-shadow:
                -10px -10px 20px var(--nm-light),
                10px 10px 24px var(--nm-dark),
                inset 0 1px 0 rgba(255, 255, 255, 0.3);
            padding: 1rem 1.25rem 1.1rem 1.25rem;
        }
        .bento-metric.featured {
            box-shadow:
                -13px -13px 26px var(--nm-light-strong),
                13px 13px 30px var(--nm-dark-strong),
                inset 0 1px 0 rgba(255, 255, 255, 0.35),
                inset 0 0 0 1px rgba(201, 124, 93, 0.3);
        }
        .bento-metric-head {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            margin-bottom: 0.4rem;
        }
        .bento-icon-wrap {
            width: 32px;
            height: 32px;
            min-width: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            background-image: repeating-linear-gradient(115deg, rgba(255,255,255,0.4) 0px, rgba(255,255,255,0.4) 1px, transparent 1px, transparent 3px);
            background-blend-mode: soft-light;
            box-shadow:
                -3px -3px 6px rgba(255, 255, 255, 0.55),
                3px 3px 7px rgba(53, 40, 27, 0.3),
                inset 0 1px 1px rgba(255, 255, 255, 0.45);
        }
        .bento-icon-wrap svg { width: 16px; height: 16px; }
        .bento-metric-label {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 0.95rem;
            font-weight: 600;
            color: #2C241D;
            line-height: 1.2;
        }
        .bento-metric-value {
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            font-size: 1.9rem;
            color: #2C241D;
            letter-spacing: -0.01em;
        }
        .bento-metric-delta {
            font-family: 'Inter', sans-serif;
            font-size: 0.78rem;
            font-weight: 500;
            margin-top: 0.2rem;
        }

        /* --- Expander de notas --- */
        div[data-testid="stExpander"] {
            background: #FAF5E9;
            border-radius: 22px;
            border: none;
            box-shadow:
                -10px -10px 20px var(--nm-light),
                10px 10px 24px var(--nm-dark),
                inset 0 1px 0 rgba(255, 255, 255, 0.3);
        }
        div[data-testid="stExpander"] summary {
            font-family: 'Playfair Display', Georgia, serif;
            font-weight: 600;
            font-size: 0.85rem;
            color: #2C241D !important;
            min-height: 0;
            padding: 0.9rem 1.3rem;
            border-radius: 22px;
            transition: box-shadow .15s ease;
        }
        div[data-testid="stExpander"] summary:hover {
            box-shadow:
                inset 4px 4px 8px rgba(53, 40, 27, 0.18),
                inset -4px -4px 8px rgba(255, 248, 235, 0.5);
        }
        div[data-testid="stExpander"] * {
            color: #2C241D;
        }
        div[data-testid="stExpander"] p {
            font-family: 'Inter', sans-serif;
            color: #6B5D4F !important;
        }
    </style>
""", unsafe_allow_html=True)

df = cargar_datos()
anual = calcular_promedio_anual(df)
extremos = calcular_extremos_anuales(df)
decadas = calcular_promedio_decada(df)
record_max, record_min = calcular_records_historicos(df)

primera_decada = decadas.iloc[0]
ultima_decada = decadas.iloc[-1]
delta_decadas = ultima_decada["temperature_2m_mean"] - primera_decada["temperature_2m_mean"]

st.markdown(
    f"""
    <div class="dashboard-eyebrow">Reporte climático · Chile</div>
    <div class="dashboard-title">¿Está cambiando el clima en {CIUDAD}?</div>
    <div class="dashboard-subtitle">Serie histórica 1940–2025 · datos ERA5 vía Open-Meteo</div>
    """,
    unsafe_allow_html=True,
)


def tarjeta_metrica(icono, icono_bg, icono_fg, etiqueta, valor, delta_texto, delta_color, featured=False):
    clase = "bento-metric featured" if featured else "bento-metric"
    st.markdown(
        f"""
        <div class="{clase}">
            <div class="bento-metric-head">
                <div class="bento-icon-wrap" style="background-color:{icono_bg}; color:{icono_fg};">{icono}</div>
                <div class="bento-metric-label">{etiqueta}</div>
            </div>
            <div class="bento-metric-value">{valor}</div>
            <div class="bento-metric-delta" style="color:{delta_color};">{delta_texto}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


fig_linea = grafico_con_tendencia(
    anual["year"].to_numpy(),
    anual["temperature_2m_mean"].to_numpy(),
    MUSTARD,
    "Temperatura media anual",
)
fig_barras = go.Figure()
fig_barras.add_trace(
    go.Bar(
        x=decadas["label"],
        y=decadas["temperature_2m_mean"],
        marker_color=JADE,
        text=[f"{v:.1f}" for v in decadas["temperature_2m_mean"]],
        textposition="outside",
        textfont=dict(family=FONT_SANS, color=TEXT_PRIMARY, size=12),
        hovertemplate="%{x}: %{y:.1f} °C<extra></extra>",
        width=0.6,
    )
)
fig_barras.update_layout(
    title=dict(text="Promedio por década", x=0, font=dict(size=14, family=FONT_SERIF, color=TEXT_PRIMARY)),
    plot_bgcolor=CARD,
    paper_bgcolor=CARD,
    showlegend=False,
    xaxis=dict(showgrid=False, color=TEXT_PRIMARY, tickfont=dict(family=FONT_SANS, size=11, color=TEXT_PRIMARY)),
    yaxis=dict(showgrid=True, gridcolor=BORDER, gridwidth=1, color=TEXT_MUTED,
                title="°C", tickfont=dict(family=FONT_SANS, size=10)),
    margin=dict(t=34, b=10, l=5, r=5),
    height=ALTURA_GRAFICO,
    font=dict(family=FONT_SANS, color=TEXT_PRIMARY),
    hoverlabel=dict(font=dict(family=FONT_SANS, color=TEXT_PRIMARY), bgcolor=CARD, bordercolor=BORDER),
)
fig_max = grafico_con_tendencia(
    extremos["year"].to_numpy(),
    extremos["temperature_2m_max"].to_numpy(),
    TERRACOTTA,
    "Máxima anual (día más caluroso)",
)
fig_min = grafico_con_tendencia(
    extremos["year"].to_numpy(),
    extremos["temperature_2m_min"].to_numpy(),
    JADE,
    "Mínima anual (día más frío)",
)

col_metricas, col_graficos = st.columns([1, 2.4], gap="medium")

with col_metricas:
    color_delta_decada = TERRACOTTA if delta_decadas > 0 else JADE
    tarjeta_metrica(
        ICON_TREND, MUSTARD_BG, "#8A6A2E",
        f"Temp. media, década {ultima_decada['label']}",
        f"{ultima_decada['temperature_2m_mean']:.1f} °C",
        f"{delta_decadas:+.1f} °C vs {primera_decada['label']}",
        color_delta_decada,
    )
    tarjeta_metrica(
        ICON_FLAME, TERRACOTTA_BG, "#A85A3C",
        "Récord de calor histórico",
        f"{record_max['temperature_2m_max']:.1f} °C",
        f"Registrado el {record_max['date'].strftime('%d-%m-%Y')}",
        TEXT_MUTED,
        featured=True,
    )
    tarjeta_metrica(
        ICON_SNOWFLAKE, JADE_BG, "#2F5645",
        "Récord de frío histórico",
        f"{record_min['temperature_2m_min']:.1f} °C",
        f"Registrado el {record_min['date'].strftime('%d-%m-%Y')}",
        TEXT_MUTED,
    )

    with st.expander("Notas y datos"):
        st.caption(
            "La variabilidad año a año de la temperatura media también crece con el tiempo (la "
            "década de 1940 es la más 'plana' de toda la serie). Esto puede ser una señal "
            "climática real, pero también puede reflejar que el archivo histórico de Open-Meteo "
            "(basado en ERA5) tenía muchas menos observaciones antes de la era satelital "
            "(~1979), lo que suaviza artificialmente los años más antiguos."
        )
        st.caption("Promedio anual")
        st.dataframe(anual, width="stretch", height=150)
        st.caption("Extremos anuales")
        st.dataframe(extremos, width="stretch", height=150)
        st.caption("Promedio por década")
        st.dataframe(decadas.drop(columns="label"), width="stretch", height=150)

with col_graficos:
    fila1_izq, fila1_der = st.columns(2, gap="small")
    with fila1_izq:
        with st.container(border=True):
            st.plotly_chart(fig_linea, width="stretch")
    with fila1_der:
        with st.container(border=True):
            st.plotly_chart(fig_barras, width="stretch")

    fila2_izq, fila2_der = st.columns(2, gap="small")
    with fila2_izq:
        with st.container(border=True):
            st.plotly_chart(fig_max, width="stretch")
    with fila2_der:
        with st.container(border=True):
            st.plotly_chart(fig_min, width="stretch")
