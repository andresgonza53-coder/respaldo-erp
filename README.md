# Respaldo Industrial ERP — V3 Dashboard

Primer prototipo funcional del ERP web.

## Incluye
- Dashboard.
- Menú completo del futuro ERP.
- CRM editable.
- Productos y stock.
- Presupuestos básicos.
- Apertura/movimientos/cierre de caja.
- Importación y previsualización de ESTADISTICAS.xlsx.
- Importación y previsualización de FLUJO RI SRL.xlsx.
- Estructura preparada para integrar Compras/OCR.

## Importante
Esta versión usa `st.session_state`: los datos creados dentro de la app son temporales y pueden perderse cuando Streamlit reinicia la aplicación.

La siguiente etapa debe incorporar una base de datos persistente, por ejemplo PostgreSQL/Supabase.

## Actualizar tu aplicación actual
Recomendación: crear una NUEVA app/repo para el ERP V3 y dejar Presupuestos OCR funcionando aparte mientras probamos.

1. Crear un repositorio nuevo, por ejemplo `respaldo-erp`.
2. Subir `app.py`, `requirements.txt` y la carpeta `.streamlit`.
3. En Streamlit Community Cloud crear una nueva app.
4. Seleccionar `app.py`.
5. Desplegar.

No subas ESTADISTICAS.xlsx ni FLUJO RI SRL.xlsx al repositorio público. La propia aplicación permite cargarlos desde la pantalla "Importar Excel".
