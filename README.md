# 📊 Dashboard Finanzas Personales

Dashboard interactivo para el seguimiento de finanzas personales conectado con Notion.

## 🚀 Características

- 📈 Visualización de ingresos, gastos, ahorros e inversiones
- 🎯 Seguimiento de objetivos de inversión
- 📊 Gráficos interactivos con Plotly
- 🔄 Sincronización automática con base de datos de Notion
- 💰 Cálculo de saldo en cuenta corriente
- 📅 Análisis mensual y acumulado

## 🛠️ Tecnologías

- **Streamlit** - Framework de aplicaciones web
- **Plotly** - Gráficos interactivos
- **Pandas** - Manipulación de datos
- **Notion API** - Conexión con base de datos de Notion

## 📋 Configuración

### Variables de entorno necesarias:

- `NOTION_TOKEN`: Token de integración de Notion
- `NOTION_DATABASE_ID`: ID de la base de datos de Notion
- `INVERSION_MES_OBJ`: Objetivo mensual de inversión (opcional, default: 115)
- `ERASMUS_META`: Meta de ahorro Erasmus (opcional, default: 4000)

### Para ejecutar localmente:

1. Clona el repositorio
2. Instala las dependencias: `pip install -r requirements.txt`
3. Crea un archivo `.env` con las variables de entorno
4. Ejecuta: `streamlit run main.py`

## 🌐 Demo

La aplicación está desplegada en Streamlit Cloud: [Ver Dashboard](tu-url-aqui)

## 📄 Licencia

MIT License
