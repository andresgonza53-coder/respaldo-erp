
import io
import re
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
from supabase import create_client


st.set_page_config(
    page_title="Respaldo Industrial ERP",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_VERSION = "3.3 - Supabase"


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
# SUPABASE / AUTENTICACIÓN
# ============================================================
def get_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as exc:
        st.error("No se pudo inicializar Supabase. Revisá los Secrets de Streamlit.")
        st.exception(exc)
        st.stop()

supabase = get_supabase()

def ensure_login():
    if "auth_user" not in st.session_state:
        st.session_state.auth_user = None
    if "auth_session" not in st.session_state:
        st.session_state.auth_session = None

    if st.session_state.auth_user is not None:
        return

    st.markdown("## 🔐 Acceso al ERP")
    st.caption("Ingresá con el usuario creado en Supabase Authentication.")
    email = st.text_input("Correo")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar", type="primary", use_container_width=True):
        try:
            res = supabase.auth.sign_in_with_password({
                "email": email.strip(),
                "password": password
            })
            st.session_state.auth_user = res.user
            st.session_state.auth_session = res.session
            st.success("Acceso correcto.")
            st.rerun()
        except Exception as exc:
            st.error("No se pudo iniciar sesión. Revisá correo/contraseña o las políticas de Supabase.")
            st.caption(str(exc))
    st.stop()

ensure_login()

def logout():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.auth_user = None
    st.session_state.auth_session = None
    st.rerun()

def fetch_crm_from_db():
    """Devuelve clientes y oportunidades desde Supabase."""
    try:
        clients_resp = supabase.table("clientes").select("*").order("nombre").execute()
        opp_resp = supabase.table("oportunidades").select(
            "id,cliente_id,etapa,estado,responsable,proxima_accion,fecha_proxima,observacion,origen,clientes(nombre)"
        ).execute()

        clients = clients_resp.data or []
        opps = opp_resp.data or []

        client_df = pd.DataFrame([{
            "id": c.get("id"),
            "Cliente": c.get("nombre",""),
            "RUC": c.get("ruc",""),
            "Ciudad": c.get("ciudad",""),
            "Dirección": c.get("direccion",""),
            "Teléfono": c.get("telefono",""),
            "Correo": c.get("correo",""),
            "Estado": c.get("estado","Activo"),
        } for c in clients])

        crm_rows = []
        for o in opps:
            cliente = o.get("clientes") or {}
            crm_rows.append({
                "id": o.get("id"),
                "cliente_id": o.get("cliente_id"),
                "Cliente": cliente.get("nombre","") if isinstance(cliente, dict) else "",
                "Etapa": o.get("etapa","Acercamiento"),
                "Última gestión": o.get("observacion","") or "",
                "Próxima acción": o.get("proxima_accion","") or "",
                "Fecha próxima": o.get("fecha_proxima"),
                "Responsable": o.get("responsable","") or "",
                "Estado": o.get("estado","Activo"),
                "Origen": o.get("origen","CRM"),
            })
        return client_df, pd.DataFrame(crm_rows)
    except Exception as exc:
        st.error("No se pudieron leer los datos desde Supabase.")
        st.caption(str(exc))
        return pd.DataFrame(), pd.DataFrame()

def db_upsert_client(record):
    payload = {
        "nombre": str(record.get("Cliente","")).strip(),
        "ruc": str(record.get("RUC","")).strip() or None,
        "ciudad": str(record.get("Ciudad","")).strip() or None,
        "direccion": str(record.get("Dirección","")).strip() or None,
        "telefono": str(record.get("Teléfono","")).strip() or None,
        "correo": str(record.get("Correo","")).strip() or None,
        "estado": str(record.get("Estado","Activo")).strip() or "Activo",
        "origen": "ESTADISTICAS.xlsx",
    }
    res = supabase.table("clientes").upsert(payload, on_conflict="nombre").execute()
    return (res.data or [None])[0]

def db_get_client_id_by_name(name):
    res = supabase.table("clientes").select("id").ilike("nombre", name.strip()).limit(1).execute()
    rows = res.data or []
    return rows[0]["id"] if rows else None

def db_upsert_opportunity(record, client_id):
    payload = {
        "cliente_id": client_id,
        "etapa": record.get("Etapa") or "Acercamiento",
        "estado": record.get("Estado") or "Activo",
        "responsable": record.get("Responsable") or None,
        "proxima_accion": record.get("Próxima acción") or None,
        "fecha_proxima": (
            pd.to_datetime(record.get("Fecha próxima")).date().isoformat()
            if pd.notna(record.get("Fecha próxima")) and str(record.get("Fecha próxima")).strip()
            else None
        ),
        "observacion": record.get("Última gestión") or None,
        "origen": record.get("Origen") or "CRM",
    }

    # Si existe una oportunidad para el cliente, la actualiza.
    existing = supabase.table("oportunidades").select("id").eq("cliente_id", client_id).limit(1).execute()
    if existing.data:
        return supabase.table("oportunidades").update(payload).eq("id", existing.data[0]["id"]).execute()
    return supabase.table("oportunidades").insert(payload).execute()

def db_add_gestion(client_id, opportunity_id, tipo, descripcion, resultado, proxima_accion, fecha_proxima, responsable):
    payload = {
        "cliente_id": client_id,
        "oportunidad_id": opportunity_id,
        "tipo": tipo,
        "descripcion": descripcion or None,
        "resultado": resultado or None,
        "proxima_accion": proxima_accion or None,
        "fecha_proxima": fecha_proxima.isoformat() if fecha_proxima else None,
        "responsable": responsable or None,
    }
    return supabase.table("gestiones_crm").insert(payload).execute()

def db_timeline(client_id):
    try:
        res = supabase.table("gestiones_crm").select(
            "tipo,descripcion,resultado,proxima_accion,fecha_proxima,responsable,creado_en"
        ).eq("cliente_id", client_id).order("creado_en", desc=True).execute()
        return pd.DataFrame(res.data or [])
    except Exception:
        return pd.DataFrame()

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
        "crm_import": None,
        "crm_clients": [],
        "crm_activities": [],
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
# CRM V3.1 - IMPORTACIÓN, FILTROS Y MÉTRICAS
# ============================================================
CRM_STAGES = ["Acercamiento", "Visita", "Relevamiento", "Presupuesto", "Cierre", "Seguimiento"]

def norm_col(value):
    text = str(value or "").strip().upper()
    replacements = {
        "Á":"A", "É":"E", "Í":"I", "Ó":"O", "Ú":"U", "Ñ":"N"
    }
    for a, b in replacements.items():
        text = text.replace(a, b)
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def first_matching_column(df, tokens):
    normalized = {col: norm_col(col) for col in df.columns}
    for token_group in tokens:
        for col, name in normalized.items():
            if all(tok in name for tok in token_group):
                return col
    return None

def read_crm_excel(uploaded_file):
    """
    Importador flexible para ESTADISTICAS.xlsx.
    Mantiene la lógica actual aunque los encabezados cambien ligeramente.
    """
    xls = pd.ExcelFile(io.BytesIO(uploaded_file.getvalue()))
    result = {
        "sheets": xls.sheet_names,
        "clients": pd.DataFrame(),
        "contacts": pd.DataFrame(),
        "measurements": pd.DataFrame(),
        "activities": pd.DataFrame(),
    }

    # Hojas observadas en el archivo actual: CLIENTES, CONTACTOS, MEDICIONES, DUDAS.
    sheet_map = {norm_col(s): s for s in xls.sheet_names}

    for normalized, original in sheet_map.items():
        try:
            df = pd.read_excel(xls, sheet_name=original, header=1 if "CLIENT" in normalized else 0)
        except Exception:
            continue
        df = df.dropna(how="all")

        if "CLIENT" in normalized:
            result["clients"] = df
        elif "CONTACT" in normalized:
            result["contacts"] = df
        elif "MEDIC" in normalized:
            result["measurements"] = df

    # Construcción de actividades desde CLIENTES:
    clients = result["clients"]
    activities = []

    if not clients.empty:
        client_col = first_matching_column(
            clients,
            [
                ["CLIENTE"],
                ["EMPRESA"],
                ["RAZON", "SOCIAL"],
                ["NOMBRE"],
            ]
        )

        # Columnas reales del Excel: A, V, R, P, C.
        stage_alias = {
            "Acercamiento": "A", "Visita": "V", "Relevamiento": "R",
            "Presupuesto": "P", "Cierre": "C"
        }
        stage_cols = {}
        for stage, alias in stage_alias.items():
            for col in clients.columns:
                if norm_col(col) == alias:
                    stage_cols[stage] = col
                    break

        for idx, row in clients.iterrows():
            client_name = ""
            if client_col is not None:
                client_name = clean_excel_value(row.get(client_col, ""))
            if not client_name:
                # Evita crear actividades fantasma.
                continue

            detected_stages = []
            for stage, col in stage_cols.items():
                value = row.get(col, "")
                if is_positive_excel_mark(value):
                    detected_stages.append(stage)

            current_stage = detected_stages[-1] if detected_stages else "Acercamiento"

            activities.append({
                "Cliente": client_name,
                "Etapa": current_stage,
                "Última gestión": "",
                "Próxima acción": "",
                "Fecha próxima": pd.NaT,
                "Responsable": "",
                "Estado": "Activo",
                "Origen": "ESTADISTICAS.xlsx",
            })

    result["activities"] = pd.DataFrame(activities)
    return result

def clean_excel_value(value):
    if pd.isna(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()

def is_positive_excel_mark(value):
    if pd.isna(value):
        return False
    if isinstance(value, (int, float)):
        return value != 0
    text = norm_col(value)
    return text in {"SI", "S", "YES", "TRUE", "X", "OK", "1", "HECHO", "REALIZADO"} or "SI" == text

def enrich_contacts(clients_df, contacts_df):
    """Une CLIENTES con CONTACTOS usando el nombre de empresa."""
    if clients_df.empty:
        return pd.DataFrame(columns=["Cliente", "Ciudad", "Contacto", "Área", "Teléfono", "Correo", "Estado"])

    client_col = first_matching_column(clients_df, [["CLIENTE"], ["EMPRESA"], ["RAZON", "SOCIAL"], ["NOMBRE"]])
    city_col = first_matching_column(clients_df, [["CIUDAD"], ["LOCALIDAD"]])

    rows = []
    for _, r in clients_df.iterrows():
        name = clean_excel_value(r.get(client_col, "")) if client_col else ""
        if not name:
            continue
        rows.append({
            "Cliente": name,
            "Ciudad": clean_excel_value(r.get(city_col, "")) if city_col else "",
            "Contacto": "", "Área": "", "Teléfono": "", "Correo": "", "Estado": "Activo",
        })
    out = pd.DataFrame(rows).drop_duplicates(subset=["Cliente"], keep="first")

    if not contacts_df.empty:
        cc = first_matching_column(contacts_df, [["CLIENTES"], ["CLIENTE"], ["EMPRESA"]])
        ac = first_matching_column(contacts_df, [["AREA"]])
        nc = first_matching_column(contacts_df, [["CONTACTO"]])
        pc = first_matching_column(contacts_df, [["CELULAR"], ["TELEF"]])
        ec = first_matching_column(contacts_df, [["CORREO"], ["EMAIL"]])
        grouped = {}
        for _, r in contacts_df.iterrows():
            company = clean_excel_value(r.get(cc, "")) if cc else ""
            if not company: continue
            key = norm_col(company)
            grouped.setdefault(key, {"contact": [], "area": [], "phone": [], "email": []})
            vals = grouped[key]
            for k, col in [("contact", nc), ("area", ac), ("phone", pc), ("email", ec)]:
                v = clean_excel_value(r.get(col, "")) if col else ""
                if v and v not in vals[k]: vals[k].append(v)
        for i, r in out.iterrows():
            vals = grouped.get(norm_col(r["Cliente"]))
            if vals:
                out.at[i,"Contacto"] = " | ".join(vals["contact"])
                out.at[i,"Área"] = " | ".join(vals["area"])
                out.at[i,"Teléfono"] = " | ".join(vals["phone"])
                out.at[i,"Correo"] = " | ".join(vals["email"])
    return out.reset_index(drop=True)

def crm_kpis(df):
    if df is None or df.empty:
        return {
            "total": 0, "pending": 0, "overdue": 0,
            "quotes": 0, "closed": 0
        }

    today = pd.Timestamp(date.today())
    dates = pd.to_datetime(df.get("Fecha próxima"), errors="coerce")
    active = df.get("Estado", pd.Series(["Activo"] * len(df))).astype(str).str.upper().eq("ACTIVO")
    pending = dates.notna() & active
    overdue = pending & (dates < today)

    return {
        "total": int(len(df)),
        "pending": int(pending.sum()),
        "overdue": int(overdue.sum()),
        "quotes": int(df.get("Etapa", pd.Series()).astype(str).eq("Presupuesto").sum()),
        "closed": int(df.get("Etapa", pd.Series()).astype(str).eq("Cierre").sum()),
    }

def create_timeline(client_name, crm_df):
    if crm_df is None or crm_df.empty:
        return pd.DataFrame()
    return crm_df[crm_df["Cliente"].astype(str) == str(client_name)].copy()

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
    try:
        user_email = st.session_state.auth_user.email
    except Exception:
        user_email = ""
    st.caption(f"👤 {user_email}")
    if st.button("Cerrar sesión", use_container_width=True):
        logout()
    st.caption("✅ Supabase conectado")


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
    page_header("CRM", "Seguimiento comercial persistente en Supabase")

    clients_db, crm_df = fetch_crm_from_db()

    if crm_df.empty:
        st.info("Todavía no hay oportunidades guardadas en Supabase. Importá ESTADISTICAS.xlsx desde **Importar Excel**.")
        crm_df = pd.DataFrame(columns=[
            "id","cliente_id","Cliente","Etapa","Última gestión","Próxima acción",
            "Fecha próxima","Responsable","Estado","Origen"
        ])

    crm_df["Fecha próxima"] = pd.to_datetime(crm_df["Fecha próxima"], errors="coerce")
    metrics = crm_kpis(crm_df)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: kpi("Clientes / oportunidades", metrics["total"])
    with c2: kpi("Pendientes con fecha", metrics["pending"])
    with c3: kpi("Seguimientos vencidos", metrics["overdue"])
    with c4: kpi("En presupuesto", metrics["quotes"])
    with c5: kpi("En cierre", metrics["closed"])

    st.write("")
    f1, f2, f3, f4 = st.columns([1.4, 1, 1, 1])
    search = f1.text_input("Buscar cliente", placeholder="Empresa, cliente...")
    stage_filter = f2.multiselect("Etapa", CRM_STAGES, default=[])
    owner_values = sorted([x for x in crm_df["Responsable"].dropna().astype(str).unique() if x.strip()])
    owner_filter = f3.multiselect("Responsable", owner_values, default=[])
    status_filter = f4.multiselect("Estado", ["Activo", "Pausado", "Ganado", "Perdido"], default=[])

    filtered = crm_df.copy()
    if search:
        filtered = filtered[filtered["Cliente"].astype(str).str.contains(search, case=False, na=False)]
    if stage_filter:
        filtered = filtered[filtered["Etapa"].isin(stage_filter)]
    if owner_filter:
        filtered = filtered[filtered["Responsable"].isin(owner_filter)]
    if status_filter:
        filtered = filtered[filtered["Estado"].isin(status_filter)]

    tab_pipeline, tab_actions, tab_client, tab_new = st.tabs([
        "📌 Pipeline", "📅 Próximas acciones", "🏢 Ficha del cliente", "➕ Nueva gestión"
    ])

    with tab_pipeline:
        st.markdown("#### Oportunidades")
        display_cols = ["Cliente","Etapa","Última gestión","Próxima acción","Fecha próxima","Responsable","Estado","Origen"]
        edited = st.data_editor(
            filtered[display_cols],
            hide_index=True,
            use_container_width=True,
            num_rows="fixed",
            column_config={
                "Cliente": st.column_config.TextColumn(disabled=True),
                "Etapa": st.column_config.SelectboxColumn("Etapa", options=CRM_STAGES),
                "Fecha próxima": st.column_config.DateColumn("Fecha próxima", format="DD/MM/YYYY"),
                "Estado": st.column_config.SelectboxColumn("Estado", options=["Activo","Pausado","Ganado","Perdido"]),
                "Origen": st.column_config.TextColumn(disabled=True),
            },
            key="crm_pipeline_editor_db",
        )

        if st.button("💾 Guardar cambios del CRM", type="primary"):
            with st.spinner("Guardando en Supabase..."):
                try:
                    for idx, row in edited.iterrows():
                        client_name = str(row["Cliente"])
                        orig = filtered[filtered["Cliente"].astype(str).eq(client_name)]
                        if orig.empty:
                            continue
                        opportunity_id = orig.iloc[0]["id"]
                        payload = {
                            "etapa": row["Etapa"],
                            "estado": row["Estado"],
                            "responsable": row["Responsable"] or None,
                            "proxima_accion": row["Próxima acción"] or None,
                            "fecha_proxima": (
                                pd.to_datetime(row["Fecha próxima"]).date().isoformat()
                                if pd.notna(row["Fecha próxima"]) else None
                            ),
                            "observacion": row["Última gestión"] or None,
                        }
                        supabase.table("oportunidades").update(payload).eq("id", opportunity_id).execute()
                    st.success("Cambios guardados permanentemente.")
                    st.rerun()
                except Exception as exc:
                    st.error("No se pudieron guardar los cambios.")
                    st.caption(str(exc))

    with tab_actions:
        actions = crm_df[crm_df["Fecha próxima"].notna()].sort_values("Fecha próxima").copy()
        if actions.empty:
            st.info("No hay acciones con fecha asignada.")
        else:
            today_ts = pd.Timestamp(date.today())
            actions["Situación"] = actions["Fecha próxima"].apply(
                lambda x: "VENCIDA" if x < today_ts else ("HOY" if x == today_ts else "PRÓXIMA")
            )
            st.dataframe(
                actions[["Situación","Fecha próxima","Cliente","Etapa","Próxima acción","Responsable","Estado"]],
                hide_index=True, use_container_width=True
            )

    with tab_client:
        client_options = sorted(filtered["Cliente"].dropna().astype(str).unique())
        if not client_options:
            st.info("No hay clientes para mostrar con los filtros actuales.")
        else:
            selected_client = st.selectbox("Cliente", client_options)
            row = filtered[filtered["Cliente"].astype(str).eq(selected_client)].iloc[0]
            a,b,c = st.columns(3)
            a.metric("Etapa actual", str(row.get("Etapa","")))
            b.metric("Estado", str(row.get("Estado","")))
            if pd.notna(row.get("Fecha próxima")):
                c.metric("Próxima fecha", pd.to_datetime(row["Fecha próxima"]).strftime("%d/%m/%Y"))
            else:
                c.metric("Próxima fecha", "Sin fecha")

            info = clients_db[clients_db["Cliente"].astype(str).eq(selected_client)] if not clients_db.empty else pd.DataFrame()
            if not info.empty:
                st.markdown("#### Datos del cliente")
                st.dataframe(info.drop(columns=["id"], errors="ignore"), hide_index=True, use_container_width=True)

            st.markdown("#### Historial de gestiones")
            timeline = db_timeline(row["cliente_id"])
            if timeline.empty:
                st.caption("Todavía no hay gestiones registradas.")
            else:
                st.dataframe(timeline, hide_index=True, use_container_width=True)

    with tab_new:
        if clients_db.empty:
            st.info("Primero importá clientes a Supabase.")
        else:
            client_name = st.selectbox("Cliente *", sorted(clients_db["Cliente"].dropna().astype(str).unique()))
            tipo = st.selectbox("Tipo", ["Llamada","WhatsApp","Correo","Visita","Relevamiento","Presupuesto","Seguimiento","Otro"])
            stage = st.selectbox("Etapa actual", CRM_STAGES)
            descripcion = st.text_area("Gestión realizada")
            resultado = st.text_area("Resultado")
            next_action = st.text_area("Próxima acción")
            next_date = st.date_input("Fecha próxima", date.today())
            owner = st.text_input("Responsable", "Andrés")

            if st.button("Guardar gestión", type="primary", use_container_width=True):
                try:
                    client_row = clients_db[clients_db["Cliente"].astype(str).eq(client_name)].iloc[0]
                    client_id = client_row["id"]

                    opp = supabase.table("oportunidades").select("id").eq("cliente_id", client_id).limit(1).execute()
                    if opp.data:
                        opportunity_id = opp.data[0]["id"]
                        supabase.table("oportunidades").update({
                            "etapa": stage,
                            "responsable": owner or None,
                            "proxima_accion": next_action or None,
                            "fecha_proxima": next_date.isoformat() if next_action else None,
                            "observacion": resultado or descripcion or None,
                        }).eq("id", opportunity_id).execute()
                    else:
                        created = supabase.table("oportunidades").insert({
                            "cliente_id": client_id,
                            "etapa": stage,
                            "estado": "Activo",
                            "responsable": owner or None,
                            "proxima_accion": next_action or None,
                            "fecha_proxima": next_date.isoformat() if next_action else None,
                            "observacion": resultado or descripcion or None,
                            "origen": "CRM",
                        }).execute()
                        opportunity_id = created.data[0]["id"]

                    db_add_gestion(
                        client_id, opportunity_id, tipo, descripcion, resultado,
                        next_action, next_date if next_action else None, owner
                    )
                    st.success("Gestión guardada permanentemente.")
                    st.rerun()
                except Exception as exc:
                    st.error("No se pudo guardar la gestión.")
                    st.caption(str(exc))


# ============================================================
# CLIENTES
# ============================================================
elif page == "👥 Clientes":
    page_header("Clientes", "Base comercial persistente en Supabase")
    clients_df, _ = fetch_crm_from_db()

    if clients_df.empty:
        st.info("Todavía no hay clientes guardados. Usá **Importar Excel** para migrar la base inicial.")
    else:
        search = st.text_input("Buscar", placeholder="Cliente, RUC, teléfono, correo...")
        view = clients_df.copy()
        if search:
            mask = pd.Series(False, index=view.index)
            for col in view.columns:
                mask = mask | view[col].astype(str).str.contains(search, case=False, na=False)
            view = view[mask]
        st.dataframe(view.drop(columns=["id"], errors="ignore"), hide_index=True, use_container_width=True)

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
    page_header("Importar datos actuales", "Migración inicial hacia Supabase")

    st.success("Esta versión permite migrar el CRM a la base de datos permanente.")

    crm_file = st.file_uploader("ESTADISTICAS.xlsx (CRM)", type=["xlsx"], key="crm_upload_v33")

    if crm_file:
        try:
            parsed = read_crm_excel(crm_file)
            clients_normalized = enrich_contacts(parsed["clients"], parsed["contacts"])

            c1,c2,c3 = st.columns(3)
            c1.metric("Clientes detectados", len(clients_normalized))
            c2.metric("Contactos origen", len(parsed["contacts"]))
            c3.metric("Oportunidades detectadas", len(parsed["activities"]))

            tab1,tab2 = st.tabs(["Vista previa clientes","Vista previa pipeline"])
            with tab1:
                st.dataframe(clients_normalized.head(100), hide_index=True, use_container_width=True)
            with tab2:
                st.dataframe(parsed["activities"].head(100), hide_index=True, use_container_width=True)

            st.warning("La migración hace upsert por nombre de cliente para evitar duplicados por reintentos.")

            if st.button("🚀 Migrar CRM a Supabase", type="primary", use_container_width=True):
                progress = st.progress(0)
                status = st.empty()
                errors = []

                total = max(len(clients_normalized), 1)
                for i, (_, client_row) in enumerate(clients_normalized.iterrows(), 1):
                    try:
                        client_record = {
                            "Cliente": client_row.get("Cliente",""),
                            "Ciudad": client_row.get("Ciudad",""),
                            "Teléfono": client_row.get("Teléfono",""),
                            "Correo": client_row.get("Correo",""),
                            "Estado": "Activo",
                        }
                        inserted = db_upsert_client(client_record)
                        client_id = inserted.get("id") if inserted else db_get_client_id_by_name(client_record["Cliente"])
                        if not client_id:
                            raise RuntimeError("No se pudo obtener cliente_id")

                        act = parsed["activities"][
                            parsed["activities"]["Cliente"].astype(str).eq(str(client_record["Cliente"]))
                        ]
                        if not act.empty:
                            db_upsert_opportunity(act.iloc[0].to_dict(), client_id)
                        else:
                            db_upsert_opportunity({
                                "Etapa":"Acercamiento","Estado":"Activo","Origen":"ESTADISTICAS.xlsx"
                            }, client_id)

                    except Exception as exc:
                        errors.append(f"{client_row.get('Cliente','')}: {exc}")

                    progress.progress(i / total)
                    status.write(f"Migrando {i} de {total}...")

                if errors:
                    st.warning(f"Migración terminada con {len(errors)} observaciones.")
                    with st.expander("Ver observaciones"):
                        st.write(errors[:50])
                else:
                    st.success("Migración completada correctamente.")

                st.info("Entrá en **CRM** o **Clientes** para verificar los datos guardados.")

        except Exception as exc:
            st.error(f"No se pudo preparar la migración: {exc}")

    st.markdown("---")
    flow_file = st.file_uploader("FLUJO RI SRL.xlsx (finanzas)", type=["xlsx"], key="flow_upload_v33")
    if flow_file:
        st.info("La migración financiera se implementará después de estabilizar CRM + Clientes.")


# ============================================================
# CONFIG
# ============================================================
elif page == "⚙️ Configuración":
    page_header("Configuración", "Parámetros generales del sistema")
    st.text_input("Empresa", "Respaldo Industrial SRL")
    st.selectbox("Moneda principal", ["PYG - Guaraní", "USD - Dólar"])
    st.selectbox("Formato de fecha", ["DD/MM/YYYY"])
    st.success("Supabase está configurado para CRM + Clientes.")
    st.info("Los próximos módulos en migrarse serán Productos/Stock, Presupuestos, Caja y Compras.")


st.markdown(
    '<div class="footer">© 2026 Respaldo Industrial SRL · ERP V3.3 Supabase</div>',
    unsafe_allow_html=True,
)