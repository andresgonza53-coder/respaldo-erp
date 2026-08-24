
import io
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Respaldo Industrial ERP",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_VERSION = "3.0 - Prototipo"


# ============================================================
# ESTILO
# ============================================================
st.markdown("""
<style>
    .block-container {
        max-width: 1550px;
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #071a33 0%, #082543 100%);
    }

    [data-testid="stSidebar"] * {
        color: #f8fafc;
    }

    [data-testid="stSidebar"] .stRadio label {
        padding: .30rem 0;
    }

    .brand {
        font-size: 1.35rem;
        font-weight: 800;
        line-height: 1.15;
        margin-bottom: .2rem;
    }

    .brand-sub {
        opacity: .72;
        font-size: .82rem;
        margin-bottom: 1.2rem;
    }

    .page-title {
        font-size: 2.05rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: .1rem;
    }

    .page-sub {
        font-size: .98rem;
        color: #64748b;
        margin-bottom: 1.2rem;
    }

    .kpi-card {
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1rem 1.05rem;
        background: #ffffff;
        min-height: 124px;
        box-shadow: 0 2px 12px rgba(15, 23, 42, .045);
    }

    .kpi-label {
        font-size: .77rem;
        font-weight: 700;
        letter-spacing: .04em;
        color: #64748b;
        text-transform: uppercase;
    }

    .kpi-value {
        margin-top: .35rem;
        font-size: 1.55rem;
        font-weight: 800;
        color: #0f172a;
    }

    .kpi-detail {
        margin-top: .35rem;
        font-size: .82rem;
        color: #64748b;
    }

    .panel-title {
        font-weight: 750;
        font-size: 1.04rem;
        color: #0f172a;
        margin-bottom: .55rem;
    }

    .soft-panel {
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1rem 1.1rem;
        background: white;
        box-shadow: 0 2px 12px rgba(15, 23, 42, .035);
    }

    .badge {
        display: inline-block;
        padding: .2rem .55rem;
        border-radius: 999px;
        background: #eff6ff;
        color: #1d4ed8;
        font-size: .76rem;
        font-weight: 700;
    }

    .muted {
        color: #64748b;
        font-size: .86rem;
    }

    .footer {
        color: #94a3b8;
        text-align: center;
        margin-top: 2rem;
        font-size: .82rem;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# ESTADO / DEMO
# ============================================================
def init_state():
    defaults = {
        "cash_open": False,
        "cash_opening": 0.0,
        "cash_movements": [],
        "products": [
            {"Código": "ABB-AF26", "Descripción": "Contactor ABB AF26-30-00", "Marca": "ABB", "Stock": 12, "Mínimo": 5, "Costo": 425000, "Precio": 535000},
            {"Código": "TF42-29", "Descripción": "Relé térmico ABB TF42-29", "Marca": "ABB", "Stock": 4, "Mínimo": 5, "Costo": 315000, "Precio": 410000},
            {"Código": "3P32A", "Descripción": "Interruptor termomagnético 3P 32A", "Marca": "ABB", "Stock": 18, "Mínimo": 6, "Costo": 118000, "Precio": 155000},
            {"Código": "NYA4", "Descripción": "Cable NYA 4 mm²", "Marca": "Genérico", "Stock": 120, "Mínimo": 50, "Costo": 7200, "Precio": 9800},
        ],
        "crm": [
            {"Cliente": "Agrofértil S.A.", "Etapa": "Visita", "Próxima acción": "Visita técnica", "Fecha": date.today() + timedelta(days=1), "Responsable": "Andrés"},
            {"Cliente": "Molinos del Paraguay", "Etapa": "Seguimiento", "Próxima acción": "Llamar", "Fecha": date.today() + timedelta(days=1), "Responsable": "Andrés"},
            {"Cliente": "Industrias Metalúrgicas", "Etapa": "Presupuesto", "Próxima acción": "Enviar presupuesto", "Fecha": date.today() + timedelta(days=2), "Responsable": "Andrés"},
            {"Cliente": "Frigorífico Concepción", "Etapa": "Seguimiento", "Próxima acción": "Seguimiento", "Fecha": date.today() + timedelta(days=3), "Responsable": "Andrés"},
        ],
        "quotes": [
            {"N°": "PRE-0001", "Fecha": date.today(), "Cliente": "Cliente Demo", "Estado": "Borrador", "Total": 5500000},
        ],
        "imported_stats": None,
        "imported_flow": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()


def gs(value):
    try:
        return "Gs. " + f"{float(value):,.0f}".replace(",", ".")
    except Exception:
        return str(value)


def kpi(label, value, detail=""):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(title, subtitle):
    st.markdown(f'<div class="page-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-sub">{subtitle}</div>', unsafe_allow_html=True)


def current_cash_balance():
    balance = float(st.session_state.cash_opening or 0)
    for mov in st.session_state.cash_movements:
        value = float(mov.get("Monto", 0) or 0)
        balance += value if mov.get("Tipo") == "Ingreso" else -value
    return balance


# ============================================================
# IMPORTACIÓN
# ============================================================
def load_excel(uploaded_file):
    return pd.ExcelFile(io.BytesIO(uploaded_file.getvalue()))


def preview_excel(uploaded_file):
    xls = load_excel(uploaded_file)
    previews = {}
    for sheet in xls.sheet_names:
        try:
            previews[sheet] = pd.read_excel(xls, sheet_name=sheet, nrows=15)
        except Exception:
            previews[sheet] = pd.DataFrame()
    return xls.sheet_names, previews


def discover_crm_metrics(uploaded_file):
    """Detección flexible para ESTADISTICAS.xlsx sin imponer un esquema."""
    xls = load_excel(uploaded_file)
    result = {"sheets": xls.sheet_names, "clientes": None, "contactos": None, "etapas": {}}

    for sheet in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=sheet)
        except Exception:
            continue

        name = sheet.upper()
        if "CLIENT" in name:
            result["clientes"] = max(0, len(df.dropna(how="all")))
        if "CONTACT" in name:
            result["contactos"] = max(0, len(df.dropna(how="all")))

        # Busca columnas que parezcan etapas CRM.
        for col in df.columns:
            c = str(col).strip().upper()
            mapping = {
                "ACERCAMIENTO": "Acercamiento",
                "VISITA": "Visita",
                "RELEVAMIENTO": "Relevamiento",
                "PRESUPUESTO": "Presupuesto",
                "CIERRE": "Cierre",
                "SEGUIMIENTO": "Seguimiento",
            }
            for token, label in mapping.items():
                if token in c:
                    ser = df[col].astype(str).str.upper().str.strip()
                    count = ser.isin(["SI", "SÍ", "YES", "1", "TRUE", "X"]).sum()
                    result["etapas"][label] = result["etapas"].get(label, 0) + int(count)

    return result


def discover_flow_metrics(uploaded_file):
    """Lectura inicial y conservadora del libro financiero."""
    xls = load_excel(uploaded_file)
    result = {"sheets": xls.sheet_names, "rows": {}, "numeric_totals": {}}

    for sheet in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=sheet)
        except Exception:
            continue
        result["rows"][sheet] = int(len(df.dropna(how="all")))

        # Solo sumar columnas cuyo nombre sea claramente monetario.
        for col in df.columns:
            label = str(col).strip()
            upper = label.upper()
            if any(token in upper for token in ["TOTAL", "IMPORTE", "MONTO", "INGRESO", "EGRESO"]):
                values = pd.to_numeric(df[col], errors="coerce")
                if values.notna().sum() > 0:
                    result["numeric_totals"][f"{sheet} · {label}"] = float(values.sum())

    return result


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown('<div class="brand">⚡ Respaldo<br>Industrial SRL</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="brand-sub">{APP_VERSION}</div>', unsafe_allow_html=True)

    page = st.radio(
        "Navegación",
        [
            "🏠 Inicio",
            "🤝 CRM",
            "👥 Clientes",
            "📄 Presupuestos",
            "🛒 Ventas",
            "📦 Productos",
            "🏷️ Stock",
            "🔎 Compras / OCR",
            "🏭 Proveedores",
            "💵 Caja",
            "💳 Cuentas",
            "📊 Reportes",
            "⬆️ Importar Excel",
            "⚙️ Configuración",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption("Prototipo web")
    st.caption("Datos no persistentes todavía")


# ============================================================
# DASHBOARD
# ============================================================
if page == "🏠 Inicio":
    page_header("Dashboard", "Resumen general del negocio")

    imported_crm = st.session_state.imported_stats
    crm_total = imported_crm.get("clientes") if imported_crm else None
    products_count = len(st.session_state.products)
    low_stock = sum(1 for p in st.session_state.products if float(p["Stock"]) <= float(p["Mínimo"]))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi("Ventas del mes", gs(0), "Se conectará con Ventas")
    with c2:
        kpi("Compras del mes", gs(0), "Se conectará con Compras / OCR")
    with c3:
        kpi("Saldo en caja", gs(current_cash_balance()), "Caja actual")
    with c4:
        kpi("Productos en stock", str(products_count), f"{low_stock} con stock bajo")

    st.write("")
    left, middle, right = st.columns([1.2, 1, 0.9])

    with left:
        st.markdown('<div class="soft-panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Ventas de los últimos 6 meses</div>', unsafe_allow_html=True)
        sales_demo = pd.DataFrame({
            "Mes": ["Mar", "Abr", "May", "Jun", "Jul", "Ago"],
            "Ventas": [0, 0, 0, 0, 0, 0],
        }).set_index("Mes")
        st.bar_chart(sales_demo, height=285)
        st.caption("Se poblará automáticamente cuando conectemos el módulo Ventas.")
        st.markdown('</div>', unsafe_allow_html=True)

    with middle:
        st.markdown('<div class="soft-panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Embudo CRM</div>', unsafe_allow_html=True)

        stages = ["Acercamiento", "Visita", "Relevamiento", "Presupuesto", "Cierre", "Seguimiento"]
        if imported_crm and imported_crm.get("etapas"):
            vals = [imported_crm["etapas"].get(x, 0) for x in stages]
        else:
            vals = [0, 0, 0, 0, 0, 0]

        crm_chart = pd.DataFrame({"Etapa": stages, "Cantidad": vals}).set_index("Etapa")
        st.bar_chart(crm_chart, height=285)
        if crm_total is not None:
            st.caption(f"Clientes detectados en el Excel cargado: {crm_total}")
        else:
            st.caption("Importá ESTADISTICAS.xlsx para alimentar el CRM.")
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="soft-panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Actividades pendientes</div>', unsafe_allow_html=True)
        for item in sorted(st.session_state.crm, key=lambda x: x["Fecha"]):
            st.markdown(f"**{item['Próxima acción']}**")
            st.caption(f"{item['Cliente']} · {item['Fecha'].strftime('%d/%m')}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    a, b = st.columns([1, 1.25])

    with a:
        st.markdown('<div class="soft-panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Alertas</div>', unsafe_allow_html=True)
        if low_stock:
            st.warning(f"{low_stock} producto(s) están en stock mínimo o por debajo.")
        else:
            st.success("No hay productos con stock bajo.")
        if not st.session_state.cash_open:
            st.info("Caja todavía no está abierta.")
        if st.session_state.imported_stats is None:
            st.info("CRM aún no importado desde Excel.")
        st.markdown('</div>', unsafe_allow_html=True)

    with b:
        st.markdown('<div class="soft-panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Estado de implementación</div>', unsafe_allow_html=True)
        progress_df = pd.DataFrame({
            "Módulo": ["Dashboard", "CRM", "Presupuestos", "Caja", "Productos/Stock", "Compras/OCR", "Base de datos"],
            "Estado": ["Prototipo", "Prototipo", "Prototipo", "Prototipo", "Prototipo", "Pendiente integración", "Pendiente"],
        })
        st.dataframe(progress_df, hide_index=True, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# CRM
# ============================================================
elif page == "🤝 CRM":
    page_header("CRM", "Seguimiento comercial desde acercamiento hasta cierre")

    c1, c2 = st.columns([1.7, 1])
    with c1:
        crm_df = pd.DataFrame(st.session_state.crm)
        edited = st.data_editor(
            crm_df,
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Etapa": st.column_config.SelectboxColumn(
                    "Etapa",
                    options=["Acercamiento", "Visita", "Relevamiento", "Presupuesto", "Cierre", "Seguimiento"],
                ),
                "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
            },
        )
        st.session_state.crm = edited.to_dict("records")

    with c2:
        st.markdown("### Nueva actividad")
        cliente = st.text_input("Cliente")
        etapa = st.selectbox("Etapa", ["Acercamiento", "Visita", "Relevamiento", "Presupuesto", "Cierre", "Seguimiento"])
        accion = st.text_input("Próxima acción")
        fecha = st.date_input("Fecha", date.today())
        responsable = st.text_input("Responsable", "Andrés")
        if st.button("Agregar actividad", type="primary", use_container_width=True):
            if cliente and accion:
                st.session_state.crm.append({
                    "Cliente": cliente,
                    "Etapa": etapa,
                    "Próxima acción": accion,
                    "Fecha": fecha,
                    "Responsable": responsable,
                })
                st.success("Actividad agregada.")
                st.rerun()
            else:
                st.warning("Completá Cliente y Próxima acción.")


# ============================================================
# CLIENTES
# ============================================================
elif page == "👥 Clientes":
    page_header("Clientes", "Base comercial y datos de contacto")
    if st.session_state.imported_stats:
        st.success("El Excel de CRM fue importado para análisis inicial.")
        st.json(st.session_state.imported_stats, expanded=False)
    else:
        st.info("En la siguiente etapa migraremos la hoja CLIENTES de ESTADISTICAS.xlsx a una base de datos.")
    st.dataframe(
        pd.DataFrame([
            {"Cliente": "Cliente Demo", "RUC": "", "Teléfono": "", "Correo": "", "Estado": "Activo"},
        ]),
        hide_index=True,
        use_container_width=True,
    )


# ============================================================
# PRESUPUESTOS
# ============================================================
elif page == "📄 Presupuestos":
    page_header("Presupuestos", "Crear, revisar y convertir presupuestos en ventas")

    left, right = st.columns([1.25, 1])
    with left:
        st.markdown("### Presupuestos")
        qdf = pd.DataFrame(st.session_state.quotes)
        st.data_editor(qdf, hide_index=True, use_container_width=True, num_rows="dynamic")

    with right:
        st.markdown("### Crear presupuesto")
        q_cliente = st.text_input("Cliente", key="q_cliente")
        q_total = st.number_input("Total estimado (Gs.)", min_value=0.0, step=100000.0)
        q_estado = st.selectbox("Estado", ["Borrador", "Enviado", "Aprobado", "Rechazado"])
        if st.button("Crear presupuesto", type="primary", use_container_width=True):
            next_num = len(st.session_state.quotes) + 1
            st.session_state.quotes.append({
                "N°": f"PRE-{next_num:04d}",
                "Fecha": date.today(),
                "Cliente": q_cliente or "Sin cliente",
                "Estado": q_estado,
                "Total": q_total,
            })
            st.success("Presupuesto creado.")
            st.rerun()

    st.info("En la próxima iteración agregaremos productos, cantidades, precios, IVA y generación de PDF.")


# ============================================================
# VENTAS
# ============================================================
elif page == "🛒 Ventas":
    page_header("Ventas", "Registro de ventas y descuento automático de stock")
    st.info("Módulo preparado en el menú. Se implementará después de cerrar Presupuestos + Stock.")


# ============================================================
# PRODUCTOS
# ============================================================
elif page == "📦 Productos":
    page_header("Productos", "Catálogo, costos y precios de venta")
    df = pd.DataFrame(st.session_state.products)
    edited = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Stock": st.column_config.NumberColumn(min_value=0),
            "Mínimo": st.column_config.NumberColumn(min_value=0),
            "Costo": st.column_config.NumberColumn(format="%d"),
            "Precio": st.column_config.NumberColumn(format="%d"),
        },
    )
    st.session_state.products = edited.to_dict("records")


# ============================================================
# STOCK
# ============================================================
elif page == "🏷️ Stock":
    page_header("Stock", "Existencias, mínimos y alertas de reposición")
    df = pd.DataFrame(st.session_state.products)
    if not df.empty:
        df["Estado"] = df.apply(
            lambda r: "BAJO" if float(r["Stock"]) <= float(r["Mínimo"]) else "OK", axis=1
        )
        st.dataframe(df, hide_index=True, use_container_width=True)
        low = df[df["Estado"] == "BAJO"]
        if not low.empty:
            st.warning(f"{len(low)} producto(s) requieren revisión de stock.")
    else:
        st.info("No hay productos registrados.")


# ============================================================
# COMPRAS / OCR
# ============================================================
elif page == "🔎 Compras / OCR":
    page_header("Compras / OCR", "Cotizaciones de proveedores y comparación")
    st.success("El módulo OCR que ya probaste seguirá formando parte del sistema.")
    st.markdown(
        """
        En la siguiente integración esta pantalla tendrá:

        - carga de uno o varios presupuestos;
        - reconocimiento de Electro System, Electropar y Compañía Comercial;
        - comparación de precios;
        - selección de oferta;
        - conversión a orden de compra;
        - entrada posterior al stock.
        """
    )
    st.info("Esta V3 se concentra primero en la interfaz y la estructura del ERP. El código OCR se integrará como módulo interno después.")


# ============================================================
# PROVEEDORES
# ============================================================
elif page == "🏭 Proveedores":
    page_header("Proveedores", "Ficha, contactos, compras y condiciones comerciales")
    st.info("Se implementará junto con Compras / OCR.")


# ============================================================
# CAJA
# ============================================================
elif page == "💵 Caja":
    page_header("Caja", "Apertura, movimientos y cierre")

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi("Estado", "ABIERTA" if st.session_state.cash_open else "CERRADA")
    with c2:
        kpi("Saldo inicial", gs(st.session_state.cash_opening))
    with c3:
        kpi("Saldo actual", gs(current_cash_balance()))

    st.write("")
    left, right = st.columns([1, 1.2])

    with left:
        if not st.session_state.cash_open:
            st.markdown("### Abrir caja")
            opening = st.number_input("Saldo inicial (Gs.)", min_value=0.0, step=10000.0)
            if st.button("Abrir caja", type="primary", use_container_width=True):
                st.session_state.cash_open = True
                st.session_state.cash_opening = opening
                st.session_state.cash_movements = []
                st.success("Caja abierta.")
                st.rerun()
        else:
            st.markdown("### Registrar movimiento")
            tipo = st.selectbox("Tipo", ["Ingreso", "Egreso"])
            concepto = st.text_input("Concepto")
            monto = st.number_input("Monto (Gs.)", min_value=0.0, step=10000.0)
            medio = st.selectbox("Medio", ["Efectivo", "Transferencia", "Tarjeta", "Otro"])

            if st.button("Registrar", type="primary", use_container_width=True):
                if monto > 0 and concepto:
                    st.session_state.cash_movements.append({
                        "Fecha/Hora": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "Tipo": tipo,
                        "Concepto": concepto,
                        "Medio": medio,
                        "Monto": monto,
                    })
                    st.success("Movimiento registrado.")
                    st.rerun()

            if st.button("Cerrar caja", use_container_width=True):
                st.session_state.cash_open = False
                st.success("Caja cerrada.")
                st.rerun()

    with right:
        st.markdown("### Movimientos")
        if st.session_state.cash_movements:
            st.dataframe(pd.DataFrame(st.session_state.cash_movements), hide_index=True, use_container_width=True)
        else:
            st.info("Todavía no hay movimientos.")


# ============================================================
# CUENTAS
# ============================================================
elif page == "💳 Cuentas":
    page_header("Cuentas", "Cuentas por cobrar y por pagar")
    st.info("Este módulo se conectará con FLUJO RI SRL.xlsx y luego con Ventas/Compras.")


# ============================================================
# REPORTES
# ============================================================
elif page == "📊 Reportes":
    page_header("Reportes", "Ventas, compras, caja, stock y desempeño comercial")
    st.info("Los reportes se habilitarán cuando conectemos los módulos a la base de datos.")


# ============================================================
# IMPORTAR
# ============================================================
elif page == "⬆️ Importar Excel":
    page_header("Importar datos actuales", "Usaremos tus Excel como punto de partida para la migración")

    st.warning(
        "En este prototipo la importación sirve para analizar y previsualizar. "
        "Los datos todavía no quedan guardados permanentemente en una base de datos."
    )

    crm_file = st.file_uploader("ESTADISTICAS.xlsx (CRM)", type=["xlsx"], key="crm_upload")
    if crm_file:
        try:
            sheets, previews = preview_excel(crm_file)
            st.success("Archivo CRM leído correctamente.")
            st.write("Hojas detectadas:", ", ".join(sheets))
            metrics = discover_crm_metrics(crm_file)
            st.session_state.imported_stats = metrics

            selected = st.selectbox("Vista previa CRM", sheets, key="crm_sheet")
            st.dataframe(previews[selected], use_container_width=True)

            st.markdown("**Resumen detectado**")
            st.json(metrics)
        except Exception as exc:
            st.error(f"No se pudo leer el archivo CRM: {exc}")

    st.markdown("---")

    flow_file = st.file_uploader("FLUJO RI SRL.xlsx (finanzas)", type=["xlsx"], key="flow_upload")
    if flow_file:
        try:
            sheets, previews = preview_excel(flow_file)
            st.success("Archivo financiero leído correctamente.")
            st.write("Hojas detectadas:", ", ".join(sheets))
            metrics = discover_flow_metrics(flow_file)
            st.session_state.imported_flow = metrics

            selected = st.selectbox("Vista previa financiera", sheets, key="flow_sheet")
            st.dataframe(previews[selected], use_container_width=True)

            with st.expander("Resumen técnico detectado"):
                st.json(metrics)
        except Exception as exc:
            st.error(f"No se pudo leer el archivo financiero: {exc}")


# ============================================================
# CONFIG
# ============================================================
elif page == "⚙️ Configuración":
    page_header("Configuración", "Parámetros generales del sistema")
    st.text_input("Empresa", "Respaldo Industrial SRL")
    st.selectbox("Moneda principal", ["PYG - Guaraní", "USD - Dólar"])
    st.selectbox("Formato de fecha", ["DD/MM/YYYY"])
    st.info(
        "Antes de usar el ERP en producción agregaremos usuarios, contraseñas, permisos y una base de datos persistente."
    )


st.markdown(
    '<div class="footer">© 2026 Respaldo Industrial SRL · Prototipo ERP V3</div>',
    unsafe_allow_html=True,
)
