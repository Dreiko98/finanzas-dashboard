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

st.set_page_config(page_title="Finanzas Personales", layout="wide")
st.title("📊 Dashboard Finanzas Personales")

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
    fig.update_layout(showlegend=True)
    st.plotly_chart(fig, use_container_width=True)


def plot_saldo(df):
    saldo = df.sort_values("Fecha").copy()
    saldo["Saldo"] = saldo["Signo"].cumsum()
    fig = px.area(saldo, x="Fecha", y="Saldo", title="Saldo acumulado (corriente + ahorro)")
    st.plotly_chart(fig, use_container_width=True)


def plot_obj_inversion(df):
    inv = df[df["Tipo"] == "Inversión"].groupby("Mes")["Importe"].sum().reset_index()
    inv["Objetivo"] = OBJ_INVERSION
    fig = go.Figure()
    fig.add_trace(go.Bar(x=inv["Mes"], y=inv["Importe"], name="Inversión", marker_color=COLOR_MAP["Inversión"]))
    fig.add_trace(go.Scatter(x=inv["Mes"], y=inv["Objetivo"], name="Objetivo", mode="lines", line=dict(color="#f1c40f", dash="dash")))
    fig.update_layout(title="Inversión mensual vs objetivo", height=350)
    st.plotly_chart(fig, use_container_width=True)


def plot_distribucion_mes(df, importe_col):
    mes_actual = df["Mes"].max()
    dist = df[df["Mes"] == mes_actual].groupby("Tipo")[importe_col].sum().reset_index()
    fig = px.pie(dist, names="Tipo", values=importe_col, color="Tipo", color_discrete_map=COLOR_MAP,
                 title=f"Distribución {mes_actual}")
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

    # KPIs
    col1, col2, col3, col4, col5 = st.columns(5)
    total_ing = df_f[df_f["Tipo"] == "Ingreso"][importe_col].sum()
    total_gas = df_f[df_f["Tipo"] == "Gasto"][importe_col].sum()
    total_aho = df_f[df_f["Tipo"] == "Ahorro"][importe_col].sum()
    total_inv = df_f[df_f["Tipo"] == "Inversión"][importe_col].sum()
    cuenta_corr = total_ing - total_gas - total_aho - total_inv

    col1.metric("💰 Ingresos",  f"{total_ing:.2f} €")
    col2.metric("💸 Gastos",    f"{total_gas:.2f} €")
    col3.metric("🏦 Ahorro",    f"{total_aho:.2f} €")
    col4.metric("📈 Inversión", f"{total_inv:.2f} €")
    col5.metric("🏛️ Corriente", f"{cuenta_corr:.2f} €")

    # Sección de gráficos ----------------------------------------------------------------
    st.markdown("---")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        resumen = df_f.groupby(["Mes", "Tipo"])[importe_col].sum().reset_index()
        plot_cashflow(resumen, importe_col)
        plot_obj_inversion(df_f)
    with col_g2:
        plot_distribucion_mes(df_f, importe_col)
        plot_saldo(df_f)

    st.markdown("---")
    st.subheader("📄 Detalle de movimientos")
    st.dataframe(df_f.sort_values("Fecha", ascending=False))


if __name__ == "__main__":
    main()