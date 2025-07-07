# 📊 Dashboard Finanzas Personales

Dashboard interactivo **responsive** para el seguimiento de finanzas personales conectado con Notion.

## 🚀 Características

- 📈 **Visualización completa**: Ingresos, gastos, ahorros e inversiones
- 🎯 **Seguimiento de objetivos**: Monitoreo de metas de inversión
- 📊 **Gráficos interactivos**: Visualizaciones dinámicas con Plotly
- 🔄 **Sincronización automática**: Conectado con base de datos de Notion
- 💰 **Cálculo en tiempo real**: Saldo en cuenta corriente actualizado
- 📅 **Análisis temporal**: Vistas mensual y acumulada
- 📱 **Diseño responsive**: Optimizado para móviles, tablets y desktop
- 🎨 **UX moderna**: Animaciones suaves y hover effects

## 📱 Responsive Design

✅ **Móvil** (< 768px): Layout adaptativo con métricas apiladas  
✅ **Tablet** (768px - 1024px): Distribución optimizada en columnas  
✅ **Desktop** (> 1024px): Aprovechamiento completo del espacio horizontal  

### Características móviles:
- Métricas reorganizadas automáticamente
- Gráficos con márgenes optimizados
- Tabla adaptativa con scroll horizontal
- Sidebar compacto para pantallas táctiles

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
