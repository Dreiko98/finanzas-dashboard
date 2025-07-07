import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from notion_client import Client
from dotenv import load_dotenv

# ------------------------------------------------------------------
# CONFIGURACIÓN -----------------------------------------------------
# ------------------------------------------------------------------
load_dotenv()
CSV_FILE = "notion_data.csv"

# Configuración para desarrollo local y producción
try:
    # Intenta usar secrets de Streamlit Cloud primero
    NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
    DATABASE_ID = st.secrets["NOTION_DATABASE_ID"]
    OBJ_INVERSION = float(st.secrets.get("INVERSION_MES_OBJ", 115))
    META_ERASMUS = float(st.secrets.get("ERASMUS_META", 4000))
except (KeyError, FileNotFoundError):
    # Fallback a variables de entorno para desarrollo local
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
    OBJ_INVERSION = float(os.getenv("INVERSION_MES_OBJ", 115))
    META_ERASMUS = float(os.getenv("ERASMUS_META", 4000))

COLOR_MAP = {
    "Ingreso": "#2ecc71",
    "Gasto": "#e74c3c",
    "Ahorro": "#3498db",
    "Inversión": "#9b59b6",
}

st.set_page_config(
    page_title="Finanzas Personales", 
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        'About': "Dashboard de Finanzas Personales - Conectado con Notion"
    }
)
st.title("📊 Dashboard Finanzas Personales")

# CSS personalizado para mejorar la responsividad
st.markdown("""
<style>
    /* Responsive design para móviles */
    @media (max-width: 768px) {
        .stColumns > div {
            padding: 0 0.25rem !important;
        }
        
        .metric-container {
            margin-bottom: 1rem;
        }
        
        /* Hacer las métricas más compactas en móvil */
        [data-testid="metric-container"] {
            padding: 0.5rem !important;
            margin: 0.25rem 0 !important;
        }
        
        /* Reducir espaciado en gráficos */
        .plotly-graph-div {
            margin: 0.5rem 0 !important;
        }
        
        /* Ajustar sidebar en móvil */
        .css-1d391kg {
            padding: 1rem !important;
        }
        
        /* Hacer el título más pequeño en móvil */
        .main h1 {
            font-size: 1.5rem !important;
        }
        
        /* Adaptar el dataframe para móvil */
        .dataframe {
            font-size: 0.8rem !important;
        }
    }
    
    /* Mejorar apariencia general */
    .main > div {
        padding-top: 2rem;
    }
    
    /* Estilo para métricas */
    [data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* Responsive para tablets */
    @media (max-width: 1024px) and (min-width: 769px) {
        .stColumns > div {
            padding: 0 0.5rem !important;
        }
    }
    
    /* Ocultar algunos elementos en móvil muy pequeño */
    @media (max-width: 480px) {
        .css-1rs6os.edgvbvh3 {
            display: none;
        }
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# RESPONSIVE HELPERS ------------------------------------------------
# ------------------------------------------------------------------

def is_mobile():
    """
    Función auxiliar para detectar si el usuario está en móvil
    basándose en el ancho de la ventana usando JavaScript
    """
    return False  # Por defecto asumimos desktop, se puede mejorar con JavaScript

def get_responsive_columns(mobile_cols=1, tablet_cols=2, desktop_cols=3):
    """
    Retorna el número de columnas basado en el dispositivo
    """
    # Para esta implementación simple, usamos desktop por defecto
    # Se puede mejorar detectando el user agent o usando JavaScript
    return desktop_cols

# ------------------------------------------------------------------
# EXTRACT & SYNC ----------------------------------------------------
# ------------------------------------------------------------------

def safe_text(obj, path):
    for key in path:
        if isinstance(obj, list):
            obj = obj[0] if obj else {}
        obj = obj.get(key, {}) if isinstance(obj, dict) else {}
    return obj or ""


def actualizar_csv():
    if not NOTION_TOKEN or not DATABASE_ID:
        st.error("⚠️  Falta NOTION_TOKEN o NOTION_DATABASE_ID en .env")
        st.stop()

    notion = Client(auth=NOTION_TOKEN)
    rows = []
    cursor = None
    while True:
        resp = notion.databases.query(database_id=DATABASE_ID, start_cursor=cursor)
        rows.extend(resp["results"])
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")

    registros = []
    for row in rows:
        p = row["properties"]
        concepto = safe_text(p.get("Concepto", {}), ["title", "plain_text"])
        tipo = safe_text(p.get("Tipo", {}), ["select", "name"])
        fecha_raw = safe_text(p.get("Fecha", {}), ["date", "start"])
        importe = p.get("Importe (€)", {}).get("number", None)
        mes_notion = safe_text(p.get("Mes", {}), ["rich_text", "plain_text"])
        if not mes_notion and fecha_raw:
            mes_notion = pd.to_datetime(fecha_raw).to_period("M").strftime("%Y-%m")

        registros.append({
            "Concepto": concepto,
            "Tipo": tipo,
            "Fecha": fecha_raw,
            "Importe": importe,
            "Mes": mes_notion,
        })

    df_new = pd.DataFrame(registros)

    if not os.path.exists(CSV_FILE) or not df_new.equals(pd.read_csv(CSV_FILE)):
        df_new.to_csv(CSV_FILE, index=False)
        st.sidebar.success("🔄 CSV actualizado desde Notion")
    else:
        st.sidebar.info("✅ CSV ya estaba actualizado")

# ------------------------------------------------------------------
# LOAD & PREP -------------------------------------------------------
# ------------------------------------------------------------------

def load_data():
    if not os.path.exists(CSV_FILE):
        st.error("No se encontró el archivo notion_data.csv")
        return pd.DataFrame()

    df = pd.read_csv(CSV_FILE)
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df["Mes"] = df["Fecha"].dt.to_period("M").astype(str)
    df["Signo"] = df["Tipo"].map({"Ingreso": 1, "Ahorro": 1, "Gasto": -1, "Inversión": -1}) * df["Importe"].fillna(0)
    return df

# ------------------------------------------------------------------
# PLOT HELPERS ------------------------------------------------------
# ------------------------------------------------------------------

def plot_cashflow(resumen, importe_col):
    fig = px.bar(
        resumen,
        x="Mes",
        y=importe_col,
        color="Tipo",
        color_discrete_map=COLOR_MAP,
        title="Cash-flow mensual por categoría",
        barmode="relative",
        height=400,
    )
    fig.update_layout(
        showlegend=True,
        font=dict(size=12),
        margin=dict(l=50, r=50, t=50, b=50),
        # Responsive para móviles
        autosize=True,
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_saldo(df):
    saldo = df.sort_values("Fecha").copy()
    saldo["Saldo"] = saldo["Signo"].cumsum()
    fig = px.area(saldo, x="Fecha", y="Saldo", title="Saldo acumulado (corriente + ahorro)")
    fig.update_layout(
        font=dict(size=12),
        margin=dict(l=50, r=50, t=50, b=50),
        autosize=True,
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_obj_inversion(df):
    inv = df[df["Tipo"] == "Inversión"].groupby("Mes")["Importe"].sum().reset_index()
    inv["Objetivo"] = OBJ_INVERSION
    fig = go.Figure()
    fig.add_trace(go.Bar(x=inv["Mes"], y=inv["Importe"], name="Inversión", marker_color=COLOR_MAP["Inversión"]))
    fig.add_trace(go.Scatter(x=inv["Mes"], y=inv["Objetivo"], name="Objetivo", mode="lines", line=dict(color="#f1c40f", dash="dash")))
    fig.update_layout(
        title="Inversión mensual vs objetivo", 
        height=350,
        font=dict(size=12),
        margin=dict(l=50, r=50, t=50, b=50),
        autosize=True,
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_distribucion_mes(df, importe_col):
    mes_actual = df["Mes"].max()
    dist = df[df["Mes"] == mes_actual].groupby("Tipo")[importe_col].sum().reset_index()
    fig = px.pie(dist, names="Tipo", values=importe_col, color="Tipo", color_discrete_map=COLOR_MAP,
                 title=f"Distribución {mes_actual}")
    fig.update_layout(
        font=dict(size=12),
        margin=dict(l=50, r=50, t=50, b=50),
        autosize=True,
    )
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------------
# MAIN --------------------------------------------------------------
# ------------------------------------------------------------------

def main():
    actualizar_csv()
    df = load_data()
    if df.empty:
        return

    importe_col = "Importe"

    # Filtros
    tipo_sel = st.sidebar.multiselect("Filtrar por tipo", df["Tipo"].unique(), default=df["Tipo"].unique())
    mes_sel = st.sidebar.multiselect("Filtrar por mes", df["Mes"].unique(), default=df["Mes"].unique())
    df_f = df[df["Tipo"].isin(tipo_sel) & df["Mes"].isin(mes_sel)]

    # KPIs - Responsivo para móviles
    st.subheader("💰 Resumen Financiero")
    
    # Detectar si es móvil usando la longitud del viewport
    # En móvil, usar 2 filas de métricas en lugar de 5 columnas
    col1, col2, col3 = st.columns(3)
    col4, col5 = st.columns(2)
    
    total_ing = df_f[df_f["Tipo"] == "Ingreso"][importe_col].sum()
    total_gas = df_f[df_f["Tipo"] == "Gasto"][importe_col].sum()
    total_aho = df_f[df_f["Tipo"] == "Ahorro"][importe_col].sum()
    total_inv = df_f[df_f["Tipo"] == "Inversión"][importe_col].sum()
    cuenta_corr = total_ing - total_gas - total_aho - total_inv

    with col1:
        st.metric("💰 Ingresos", f"{total_ing:.2f} €")
    with col2:
        st.metric("💸 Gastos", f"{total_gas:.2f} €")
    with col3:
        st.metric("🏦 Ahorro", f"{total_aho:.2f} €")
    with col4:
        st.metric("📈 Inversión", f"{total_inv:.2f} €")
    with col5:
        st.metric("🏛️ Corriente", f"{cuenta_corr:.2f} €")

    # Sección de gráficos ----------------------------------------------------------------
    st.markdown("---")
    st.subheader("📊 Análisis Gráfico")
    
    # Layout responsivo para gráficos
    # En móvil se apilan verticalmente, en desktop side by side
    
    # Primer par de gráficos
    col_g1, col_g2 = st.columns([1, 1])
    with col_g1:
        resumen = df_f.groupby(["Mes", "Tipo"])[importe_col].sum().reset_index()
        plot_cashflow(resumen, importe_col)
    with col_g2:
        plot_distribucion_mes(df_f, importe_col)
    
    # Segundo par de gráficos  
    col_g3, col_g4 = st.columns([1, 1])
    with col_g3:
        plot_obj_inversion(df_f)
    with col_g4:
        plot_saldo(df_f)

    st.markdown("---")
    st.subheader("📄 Detalle de movimientos")
    
    # Hacer la tabla responsiva
    df_display = df_f.sort_values("Fecha", ascending=False)
    
    # Configuración responsiva para la tabla
    st.dataframe(
        df_display,
        use_container_width=True,
        height=400,
        column_config={
            "Fecha": st.column_config.DateColumn(
                "Fecha",
                format="DD/MM/YYYY",
                width="medium"
            ),
            "Concepto": st.column_config.TextColumn(
                "Concepto",
                width="large"
            ),
            "Tipo": st.column_config.SelectboxColumn(
                "Tipo",
                width="small"
            ),
            "Importe": st.column_config.NumberColumn(
                "Importe (€)",
                format="%.2f €",
                width="small"
            ),
            "Mes": st.column_config.TextColumn(
                "Mes",
                width="small"
            )
        }
    )


if __name__ == "__main__":
    main()