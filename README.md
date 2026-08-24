# Respaldo Industrial ERP — V3.1 CRM

Esta actualización desarrolla el primer módulo real del ERP: **Clientes + CRM**.

## Lo nuevo
- importación de `ESTADISTICAS.xlsx`;
- reconocimiento de las hojas CLIENTES, CONTACTOS y MEDICIONES;
- transformación inicial a una base de clientes;
- pipeline CRM basado en las etapas:
  Acercamiento → Visita → Relevamiento → Presupuesto → Cierre → Seguimiento;
- filtros por cliente, etapa, responsable y estado;
- próxima acción y fecha;
- seguimientos vencidos;
- ficha de cliente;
- nueva gestión comercial;
- KPIs CRM en pantalla;
- integración con el Dashboard.

## Importante
La estructura actual del Excel se toma como punto de partida, pero esta V3.1 todavía guarda los cambios de la app en memoria de Streamlit.

La siguiente versión debe incorporar una base de datos PostgreSQL/Supabase para persistencia.

## Actualización
Reemplazá en el repositorio `respaldo-erp`:
- `app.py`
- `requirements.txt`
- `.streamlit/config.toml`

Hacé Commit changes. Streamlit reconstruirá la misma app.
