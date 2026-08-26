
import io
import re
import hashlib
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
from supabase import create_client
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None


st.set_page_config(
    page_title="Respaldo Industrial ERP",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_VERSION = "3.6 - Compras PDF"


st.markdown("""
<style>
/* ===== Mobile responsive adjustments ===== */
@media (max-width: 768px) {
    .block-container {
        padding-top: 1rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        padding-bottom: 2rem !important;
    }

    h1, .stHeading h1 {
        font-size: 2rem !important;
        line-height: 1.1 !important;
    }

    /* Tabs: allow horizontal scrolling instead of clipping */
    div[data-baseweb="tab-list"] {
        overflow-x: auto !important;
        flex-wrap: nowrap !important;
        scrollbar-width: thin;
        gap: 0.25rem !important;
    }
    button[data-baseweb="tab"] {
        white-space: nowrap !important;
        min-width: max-content !important;
        padding-left: 0.55rem !important;
        padding-right: 0.55rem !important;
        font-size: 0.88rem !important;
    }

    /* Make metrics/cards breathe less on phones */
    div[data-testid="stMetric"] {
        padding: 0.4rem 0.2rem !important;
    }

    /* Form controls */
    .stButton > button,
    .stDownloadButton > button {
        min-height: 2.8rem !important;
        font-size: 0.95rem !important;
    }

    /* Dataframes remain usable if shown */
    div[data-testid="stDataFrame"] {
        overflow-x: auto !important;
    }

    /* Quote mobile cards */
    .quote-mobile-card {
        border: 1px solid #E5E7EB;
        border-radius: 14px;
        padding: 0.9rem;
        margin-bottom: 0.75rem;
        background: white;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    .quote-mobile-top {
        display: flex;
        justify-content: space-between;
        gap: 0.75rem;
        align-items: flex-start;
    }
    .quote-mobile-number {
        font-weight: 700;
        font-size: 1rem;
    }
    .quote-mobile-client {
        font-size: 1.02rem;
        font-weight: 700;
        margin-top: 0.25rem;
    }
    .quote-mobile-meta {
        font-size: 0.86rem;
        color: #64748B;
        margin-top: 0.25rem;
    }
    .quote-mobile-total {
        font-weight: 800;
        font-size: 1rem;
        margin-top: 0.5rem;
    }
    .quote-mobile-badge {
        display: inline-block;
        padding: 0.18rem 0.55rem;
        border-radius: 999px;
        background: #F1F5F9;
        font-size: 0.75rem;
        font-weight: 700;
    }
}

/* Desktop-only and mobile-only helpers */
.mobile-only { display: none; }
@media (max-width: 768px) {
    .desktop-only { display: none !important; }
    .mobile-only { display: block !important; }
}
</style>
""", unsafe_allow_html=True)



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
        client = create_client(url, key)

        # Streamlit reconstruye el script en cada interacción.
        # Restauramos la sesión autenticada para que las consultas usen
        # el rol "authenticated" y no vuelvan a ejecutarse como "anon".
        if "auth_access_token" in st.session_state and "auth_refresh_token" in st.session_state:
            access_token = st.session_state.get("auth_access_token")
            refresh_token = st.session_state.get("auth_refresh_token")
            if access_token and refresh_token:
                try:
                    client.auth.set_session(access_token, refresh_token)
                except Exception:
                    pass
        return client
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
    if "auth_access_token" not in st.session_state:
        st.session_state.auth_access_token = None
    if "auth_refresh_token" not in st.session_state:
        st.session_state.auth_refresh_token = None

    if st.session_state.auth_user is not None:
        # Reaplica la sesión al cliente actual después de cada rerun.
        if st.session_state.auth_access_token and st.session_state.auth_refresh_token:
            try:
                supabase.auth.set_session(
                    st.session_state.auth_access_token,
                    st.session_state.auth_refresh_token
                )
            except Exception:
                pass
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
            st.session_state.auth_access_token = res.session.access_token
            st.session_state.auth_refresh_token = res.session.refresh_token
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
    st.session_state.auth_access_token = None
    st.session_state.auth_refresh_token = None
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
        "quote_items": [
            {"Descripción": "", "Cantidad": 1.0, "Unidad": "und", "Precio Unitario": 0.0}
        ],
        "quote_costs": [
            {"Categoría": "Materiales", "Descripción": "", "Cantidad": 1.0, "Costo Unitario": 0.0, "Factor": 1.70}
        ],
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
# PRESUPUESTOS V3.4
# ============================================================
QUOTE_STATES = ["Borrador", "Enviado", "Aprobado", "Rechazado"]

def pyg(value):
    try:
        return "Gs. " + f"{float(value):,.0f}".replace(",", ".")
    except Exception:
        return "Gs. 0"

def next_quote_number():
    try:
        rows = supabase.table("presupuestos").select("numero").execute().data or []
        nums = []
        for row in rows:
            m = re.search(r"RI[- ]?(\d{4})-", str(row.get("numero", "")))
            if m:
                nums.append(int(m.group(1)))
        seq = max(nums, default=0) + 1
    except Exception:
        seq = 1
    now = datetime.now()
    year_code = "0" + str(now.year)[-2:]
    return f"RI-{seq:04d}-{year_code}-{now.month:02d}"

def fetch_quotes():
    try:
        resp = supabase.table("presupuestos").select("*").order("fecha", desc=True).execute()
        return pd.DataFrame(resp.data or [])
    except Exception as exc:
        st.warning(f"No se pudieron leer los presupuestos: {exc}")
        return pd.DataFrame()

def fetch_quote_items(quote_id):
    try:
        resp = supabase.table("presupuesto_items").select("*").eq("presupuesto_id", quote_id).order("orden").execute()
        return pd.DataFrame(resp.data or [])
    except Exception:
        return pd.DataFrame()

def fetch_quote_costs(quote_id):
    try:
        resp = supabase.table("presupuesto_costos").select("*").eq("presupuesto_id", quote_id).order("orden").execute()
        return pd.DataFrame(resp.data or [])
    except Exception:
        return pd.DataFrame()

def save_quote_db(payload, items_df):
    quote_id = payload.get("id")
    clean = {k: v for k, v in payload.items() if k != "id"}
    if quote_id:
        supabase.table("presupuestos").update(clean).eq("id", quote_id).execute()
        supabase.table("presupuesto_items").delete().eq("presupuesto_id", quote_id).execute()
    else:
        resp = supabase.table("presupuestos").insert(clean).execute()
        quote_id = resp.data[0]["id"]

    item_rows = []
    for order, (_, row) in enumerate(items_df.iterrows(), 1):
        desc = str(row.get("Descripción", "") or "").strip()
        qty = float(row.get("Cantidad", 0) or 0)
        price = float(row.get("Precio Unitario", 0) or 0)
        unit = str(row.get("Unidad", "und") or "und").strip()
        if not desc or qty <= 0:
            continue
        item_rows.append({
            "presupuesto_id": quote_id,
            "orden": order,
            "descripcion": desc,
            "cantidad": qty,
            "unidad": unit,
            "precio_unitario": price,
            "total": qty * price,
        })
    if item_rows:
        supabase.table("presupuesto_items").insert(item_rows).execute()
    return quote_id

def save_costs_db(quote_id, costs_df):
    supabase.table("presupuesto_costos").delete().eq("presupuesto_id", quote_id).execute()
    rows = []
    for order, (_, row) in enumerate(costs_df.iterrows(), 1):
        desc = str(row.get("Descripción", "") or "").strip()
        cat = str(row.get("Categoría", "Otros") or "Otros").strip()
        qty = float(row.get("Cantidad", 0) or 0)
        cost = float(row.get("Costo Unitario", 0) or 0)
        factor = float(row.get("Factor", 1) or 1)
        if not desc or qty <= 0:
            continue
        total_cost = qty * cost
        rows.append({
            "presupuesto_id": quote_id,
            "orden": order,
            "categoria": cat,
            "descripcion": desc,
            "cantidad": qty,
            "costo_unitario": cost,
            "factor": factor,
            "costo_total": total_cost,
            "venta_sugerida": total_cost * factor,
        })
    if rows:
        supabase.table("presupuesto_costos").insert(rows).execute()

def quote_pdf_bytes(quote, items_df):
    import io as _io
    buff = _io.BytesIO()
    doc = SimpleDocTemplate(
        buff, pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=12*mm, bottomMargin=14*mm
    )
    styles = getSampleStyleSheet()
    normal = ParagraphStyle("RI_Normal", parent=styles["Normal"], fontName="Helvetica", fontSize=9.3, leading=12)
    small = ParagraphStyle("RI_Small", parent=normal, fontSize=8.3, leading=10)
    bold = ParagraphStyle("RI_Bold", parent=normal, fontName="Helvetica-Bold")
    title = ParagraphStyle("RI_Title", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=14, leading=16, alignment=TA_RIGHT, spaceAfter=2)

    story = []
    logo_path = Path(__file__).with_name("respaldo_logo.png")
    if logo_path.exists():
        story.append(RLImage(str(logo_path), width=105*mm, height=23*mm))
    else:
        story.append(Paragraph("<b>RESPALDO INDUSTRIAL</b>", styles["Title"]))

    story.append(Paragraph(f"COTIZACIÓN Nº &nbsp; <b>{quote.get('numero','')}</b>", title))
    story.append(Paragraph(f"FECHA &nbsp; <b>{quote.get('fecha','')}</b>", ParagraphStyle("date", parent=normal, alignment=TA_RIGHT)))
    story.append(Spacer(1, 5*mm))

    client_tbl = Table([
        [Paragraph("<b>CLIENTE:</b>", normal), Paragraph(str(quote.get("cliente_nombre","")), bold),
         Paragraph("<b>RUC:</b>", normal), Paragraph(str(quote.get("ruc","") or ""), bold)],
        [Paragraph("<b>ATENCIÓN:</b>", normal), Paragraph(str(quote.get("atencion","") or ""), normal), "", ""],
    ], colWidths=[23*mm, 89*mm, 18*mm, 45*mm])
    client_tbl.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("BOTTOMPADDING",(0,0),(-1,-1),3),("TOPPADDING",(0,0),(-1,-1),2)]))
    story.append(client_tbl)
    story.append(Spacer(1, 5*mm))

    if quote.get("tipo","Producto") == "Servicio":
        intro = quote.get("introduccion") or "Por medio de la presente ponemos a su consideración la siguiente propuesta comercial."
        story.append(Paragraph(str(intro), normal))
        story.append(Spacer(1, 5*mm))
        if quote.get("titulo"):
            story.append(Paragraph(f"<b>{quote.get('titulo')}</b>", normal))
            story.append(Spacer(1, 3*mm))
        for label, key in [("Trabajos a ser Realizados:", "trabajos"), ("INCLUYE","incluye"), ("No Incluye","no_incluye")]:
            if quote.get(key):
                story.append(Paragraph(f"<b>{label}</b>", normal))
                for line in str(quote.get(key)).splitlines():
                    if line.strip():
                        story.append(Paragraph("• " + line.strip().lstrip("*•- "), normal))
                story.append(Spacer(1, 3*mm))

    if not items_df.empty:
        table_data = [[Paragraph("<b>Cantidad</b>", small), Paragraph("<b>Descripción</b>", small),
                       Paragraph("<b>Precio Unit. IVA Incl.</b>", small), Paragraph("<b>Precio Total IVA Incl.</b>", small)]]
        for _, r in items_df.iterrows():
            qty = float(r.get("cantidad", r.get("Cantidad", 0)) or 0)
            desc = str(r.get("descripcion", r.get("Descripción", "")) or "")
            unit_price = float(r.get("precio_unitario", r.get("Precio Unitario", 0)) or 0)
            total = float(r.get("total", qty*unit_price) or 0)
            table_data.append([f"{qty:g}", Paragraph(desc, small),
                               f"{unit_price:,.0f}".replace(",", ".") + " Gs.",
                               f"{total:,.0f}".replace(",", ".") + " Gs."])
        tbl = Table(table_data, colWidths=[22*mm, 91*mm, 31*mm, 34*mm], repeatRows=1)
        tbl.setStyle(TableStyle([
            ("GRID",(0,0),(-1,-1),0.7,colors.black),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#F2F2F2")),
            ("VALIGN",(0,0),(-1,-1),"TOP"),("ALIGN",(0,0),(0,-1),"CENTER"),("ALIGN",(2,1),(-1,-1),"RIGHT"),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)
        ]))
        story.append(tbl)
        story.append(Spacer(1, 4*mm))

    subtotal = float(quote.get("subtotal",0) or 0)
    discount = float(quote.get("descuento",0) or 0)
    total = float(quote.get("total",0) or 0)
    iva = float(quote.get("iva",0) or 0)
    totals = [["Total GUARANÍES IVA inc.", pyg(subtotal)], ["DESCUENTO", pyg(discount)], ["TOTAL CON DESCUENTO", pyg(total)]] if discount > 0 else [["TOTAL IVA INCLUIDO", pyg(total)], ["IVA", pyg(iva)]]
    t = Table(totals, colWidths=[105*mm,55*mm], hAlign="RIGHT")
    t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.7,colors.black),("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),("ALIGN",(1,0),(1,-1),"RIGHT"),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story.append(t)
    story.append(Spacer(1, 5*mm))

    terms = [
        f"<b>Cotización hecha por:</b> {quote.get('creado_por','') or ''}",
        "<b>Esta cotización está sujeta a los siguientes términos y condiciones:</b>",
        f"<b>Forma de Pago:</b> {quote.get('forma_pago','') or ''}",
        f"<b>Plazo de entrega:</b> {quote.get('plazo_entrega','') or ''}",
        f"<b>Lugar de Entrega:</b> {quote.get('lugar_entrega','') or ''}",
        f"<b>Validez de la Oferta:</b> {quote.get('validez_dias',3)} días. Oferta válida por las cantidades ofertadas.",
        "Esta cotización es válida con firma y sello de aceptada:"
    ]
    for x in terms:
        story.append(Paragraph(x, normal)); story.append(Spacer(1,1.2*mm))
    story.append(Spacer(1,4*mm))
    story.append(Paragraph("<b>Gracias por hacer negocios con nosotros!</b>", ParagraphStyle("thanks", parent=normal, alignment=TA_RIGHT)))

    doc.build(story)
    return buff.getvalue()


# ============================================================
# MATERIALES / PROVEEDORES V3.5
# ============================================================
MATERIAL_CATEGORIES = [
    "Contactor", "Relé", "Transmisor", "Bornera", "Interruptor",
    "Disyuntor", "Sensor", "Variador", "PLC", "HMI", "Fuente",
    "Cable", "Protección", "Instrumentación", "Neumática",
    "Mecánica", "Otro"
]

def fetch_suppliers():
    try:
        return pd.DataFrame(supabase.table("proveedores").select("*").order("nombre").execute().data or [])
    except Exception as exc:
        st.warning(f"No se pudieron leer los proveedores: {exc}")
        return pd.DataFrame()

def fetch_materials():
    try:
        return pd.DataFrame(supabase.table("materiales").select("*").order("nombre").execute().data or [])
    except Exception as exc:
        st.warning(f"No se pudieron leer los materiales: {exc}")
        return pd.DataFrame()

def fetch_material_supplier():
    try:
        resp = supabase.table("material_proveedor").select(
            "id,material_id,proveedor_id,prioridad,codigo_proveedor,plazo_dias,observacion,"
            "materiales(nombre,marca,modelo,categoria),proveedores(nombre)"
        ).execute()
        rows = []
        for r in resp.data or []:
            m = r.get("materiales") or {}
            p = r.get("proveedores") or {}
            rows.append({
                "id": r.get("id"),
                "material_id": r.get("material_id"),
                "proveedor_id": r.get("proveedor_id"),
                "Material": m.get("nombre","") if isinstance(m, dict) else "",
                "Marca": m.get("marca","") if isinstance(m, dict) else "",
                "Modelo": m.get("modelo","") if isinstance(m, dict) else "",
                "Categoría": m.get("categoria","") if isinstance(m, dict) else "",
                "Proveedor": p.get("nombre","") if isinstance(p, dict) else "",
                "Prioridad": r.get("prioridad", 3),
                "Código proveedor": r.get("codigo_proveedor","") or "",
                "Plazo días": r.get("plazo_dias"),
                "Observación": r.get("observacion","") or "",
            })
        return pd.DataFrame(rows)
    except Exception as exc:
        st.warning(f"No se pudieron leer las relaciones material-proveedor: {exc}")
        return pd.DataFrame()

def fetch_latest_prices():
    try:
        return pd.DataFrame(supabase.rpc("ultimos_precios_materiales").execute().data or [])
    except Exception:
        return pd.DataFrame()

def material_search_catalog(search_text="", category=None, brand=None):
    rel = fetch_material_supplier()
    latest = fetch_latest_prices()
    if rel.empty:
        return pd.DataFrame()
    out = rel.copy()
    if not latest.empty:
        latest = latest.rename(columns={
            "precio":"Último precio","moneda":"Moneda","fecha":"Actualizado","fuente":"Fuente precio"
        })
        keep = [c for c in ["material_id","proveedor_id","Último precio","Moneda","Actualizado","Fuente precio"] if c in latest.columns]
        out = out.merge(latest[keep], on=["material_id","proveedor_id"], how="left")

    if search_text.strip():
        terms = [t.strip().lower() for t in search_text.split() if t.strip()]
        searchable = (
            out["Material"].fillna("").astype(str) + " " +
            out["Marca"].fillna("").astype(str) + " " +
            out["Modelo"].fillna("").astype(str) + " " +
            out["Categoría"].fillna("").astype(str) + " " +
            out["Proveedor"].fillna("").astype(str) + " " +
            out["Código proveedor"].fillna("").astype(str)
        ).str.lower()
        mask = pd.Series(True, index=out.index)
        for term in terms:
            mask &= searchable.str.contains(re.escape(term), na=False)
        out = out[mask]

    if category:
        out = out[out["Categoría"].astype(str).eq(category)]
    if brand:
        out = out[out["Marca"].astype(str).str.contains(brand, case=False, na=False)]
    return out.sort_values(["Prioridad","Material","Proveedor"], na_position="last")

def upsert_supplier(name, ruc="", contacto="", telefono="", correo="", observacion=""):
    return supabase.table("proveedores").upsert({
        "nombre": name.strip(), "ruc": ruc.strip() or None,
        "contacto": contacto.strip() or None, "telefono": telefono.strip() or None,
        "correo": correo.strip() or None, "observacion": observacion.strip() or None,
        "activo": True
    }, on_conflict="nombre").execute()

def insert_material(name, category, brand="", model="", description=""):
    return supabase.table("materiales").insert({
        "nombre": name.strip(), "categoria": category,
        "marca": brand.strip() or None, "modelo": model.strip() or None,
        "descripcion": description.strip() or None, "activo": True
    }).execute()

def add_material_supplier(material_id, supplier_id, priority=3, supplier_code="", lead_time=None, note=""):
    return supabase.table("material_proveedor").upsert({
        "material_id": material_id, "proveedor_id": supplier_id,
        "prioridad": int(priority), "codigo_proveedor": supplier_code.strip() or None,
        "plazo_dias": int(lead_time) if lead_time is not None else None,
        "observacion": note.strip() or None, "activo": True
    }, on_conflict="material_id,proveedor_id").execute()

def add_price(material_id, supplier_id, price, currency="PYG", date_value=None, source="Carga manual", note=""):
    return supabase.table("historial_precios").insert({
        "material_id": material_id, "proveedor_id": supplier_id,
        "precio": float(price), "moneda": currency,
        "fecha": (date_value or date.today()).isoformat(),
        "fuente": source, "observacion": note.strip() or None,
        "registrado_por": getattr(st.session_state.auth_user, "email", "") or ""
    }).execute()


# ============================================================
# COMPRAS / OCR V3.6 - PDF DIGITAL + VALIDACIÓN HUMANA
# ============================================================
SUPPLIER_ALIASES = {
    "ELECTROPAR": ["ELECTROPAR", "ELECTROPAR.COM.PY"],
    "COMAGRO": ["COMAGRO"],
    "CCP": ["PRESUP CHILE", "PRESUP. CHILE", "COMPAÑIA COMERCIAL DEL PARAGUAY", "COMPANIA COMERCIAL DEL PARAGUAY"],
    "TECNO ELECTRIC": ["TECNOELECTRIC", "TECNO ELECTRIC", "TECNOELECTRIC.ODOO.COM"],
    "RECORD ELECTRIC": ["RECORD ELECTRIC"],
}


def normalize_text(value):
    text = str(value or "").upper().strip()
    repl = {"Á":"A","É":"E","Í":"I","Ó":"O","Ú":"U","Ñ":"N"}
    for a,b in repl.items():
        text=text.replace(a,b)
    return re.sub(r"\s+", " ", text)


def parse_money(value):
    """Convierte 1.507.000 / 1,507,000 / 110.733,00 a float."""
    if value is None:
        return 0.0
    text = re.sub(r"[^0-9,.-]", "", str(value))
    if not text:
        return 0.0
    # Si hay punto y coma, el último separador decide los decimales.
    if "." in text and "," in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif text.count(".") > 1:
        text = text.replace(".", "")
    elif text.count(",") > 1:
        text = text.replace(",", "")
    elif "," in text:
        tail=text.split(",")[-1]
        text = text.replace(".", "")
        text = text.replace(",", "." if len(tail) <= 2 else "")
    elif "." in text:
        tail=text.split(".")[-1]
        if len(tail)==3:
            text=text.replace(".", "")
    try:
        return float(text)
    except Exception:
        return 0.0


def extract_pdf_text(uploaded_file):
    if PdfReader is None:
        raise RuntimeError("Falta instalar pypdf. Subí también el requirements.txt V3.6.")
    reader = PdfReader(io.BytesIO(uploaded_file.getvalue()))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def guess_supplier_name(text):
    n = normalize_text(text)
    for canonical, aliases in SUPPLIER_ALIASES.items():
        if any(normalize_text(alias) in n for alias in aliases):
            return canonical
    return ""


def match_supplier_row(suggested, suppliers_df):
    if suppliers_df is None or suppliers_df.empty:
        return None
    target = normalize_text(suggested)
    # Coincidencia exacta/contiene.
    for _, row in suppliers_df.iterrows():
        name = normalize_text(row.get("nombre", ""))
        if target and (name == target or target in name or name in target):
            return row.to_dict()
    # Alias conocido: CCP puede luego llamarse Compañía Comercial del Paraguay.
    for canonical, aliases in SUPPLIER_ALIASES.items():
        if target == normalize_text(canonical):
            needles=[normalize_text(canonical)] + [normalize_text(x) for x in aliases]
            for _, row in suppliers_df.iterrows():
                name=normalize_text(row.get("nombre", ""))
                if any(x and (x in name or name in x) for x in needles):
                    return row.to_dict()
    return None


def extract_doc_number(text, filename=""):
    patterns = [
        r"([0-9]{4,})\s*Cotizaci[oó]n\s*N[º°o.:\s]*",
        r"Cotizaci[oó]n\s*N[º°o.:\s]*([A-Z0-9-]+)",
        r"PRESUP\.?\s*Chile\s*Nro\.?\s*[:\s]*([A-Z0-9-]+)",
        r"\bNRO\s*[:\s]+([A-Z0-9-]+)",
        r"NOTA DE PRESUPUESTO.*?\n\s*([0-9]{5,})",
        r"Presupuesto\s*N[º°o.:\s]*([A-Z0-9-]+)",
    ]
    for pat in patterns:
        m=re.search(pat, text, re.I|re.S)
        if m:
            return m.group(1).strip()
    m=re.search(r"(\d{4,})", filename or "")
    return m.group(1) if m else Path(filename or "documento").stem[:60]


def extract_doc_date(text):
    patterns=[
        r"([0-3]?\d/[01]?\d/20\d{2})\s*Fecha de Cotizaci[oó]n",
        r"Fecha de Cotizaci[oó]n\s*[:\s]*([0-3]?\d/[01]?\d/20\d{2})",
        r"Emisi[oó]n\s*([0-3]?\d)\s+de\s+([A-Za-zÁÉÍÓÚáéíóú]+)\s+de\s+(20\d{2})",
        r"Fecha\s*[:\s]*([0-3]?\d[./-][01]?\d[./-]20\d{2})",
        r"Asunci[oó]n,?\s*\n?\s*([0-3]?\d)\s+de\s+([A-Za-zÁÉÍÓÚáéíóú]+)\s+de\s+(20\d{2})",
    ]
    months={"ENERO":1,"FEBRERO":2,"MARZO":3,"ABRIL":4,"MAYO":5,"JUNIO":6,"JULIO":7,"AGOSTO":8,"SEPTIEMBRE":9,"SETIEMBRE":9,"OCTUBRE":10,"NOVIEMBRE":11,"DICIEMBRE":12}
    for pat in patterns:
        m=re.search(pat, text, re.I)
        if not m: continue
        if len(m.groups())==1:
            raw=m.group(1).replace(".","/").replace("-","/")
            try:
                return datetime.strptime(raw, "%d/%m/%Y").date()
            except Exception: pass
        else:
            try:
                return date(int(m.group(3)), months[normalize_text(m.group(2))], int(m.group(1)))
            except Exception: pass
    return date.today()


def extract_doc_total(text):
    patterns=[
        r"TOTAL\s+GS\s*([\d.]+(?:,\d+)?)",
        r"Total General\s*([\d.]+(?:,\d+)?)",
        r"Total \(IVA incluido\)\s*:\s*([\d.]+(?:,\d+)?)",
        r"TOTAL IVA INCLUIDO\s*([\d.]+(?:,\d+)?)",
        r"TOTAL[^\n]{0,25}?([\d.]{4,}(?:,\d+)?)\s*(?:Gs\.|₲|GS)",
    ]
    for pat in patterns:
        ms=list(re.finditer(pat, text, re.I))
        if ms:
            return parse_money(ms[-1].group(1))
    return 0.0


def detect_brand(desc):
    upper=normalize_text(desc)
    brands=["LOVATO","ABB","FINDER","FMF","DELTA","SCHNEIDER","SIEMENS","OMRON","WEG","SICK","TURCK","PEPPERL+FUCHS","FESTO","AVENTICS","DANFOSS","LENZE","HANYOUNG","NUX"]
    for b in brands:
        if b in upper:
            return b
    return ""


def guess_category(desc):
    t=normalize_text(desc)
    mapping=[
        ("CONTACTOR","Contactor"),("RELE","Relé"),("BORNER","Bornera"),("TRANSMIS","Transmisor"),
        ("SENSOR","Sensor"),("VARIADOR","Variador"),("CONV DE FREC","Variador"),("VFD","Variador"),
        (" PLC ","PLC"),("PLC ","PLC"),("HMI","HMI"),("FUENTE","Fuente"),("CABLE","Cable"),
        ("DISY","Disyuntor"),("INTERRUPTOR","Interruptor"),("TERMOMAG","Interruptor"),
        ("NEUM","Neumática"),("PRESION","Instrumentación"),("PT100","Instrumentación"),
    ]
    padded=f" {t} "
    for key,cat in mapping:
        if key in padded:
            return cat
    return "Otro"


def parse_items_comagro(text):
    rows=[]
    # Ej.: 1 VFD022EL43W-1 ... 1 UN 1.507.000 Gs. 1.507.000 Gs.
    pat=re.compile(r"(?m)^\s*(\d+)\s+([A-Z0-9_./-]+)\s+(.+?)\s+(\d+(?:[.,]\d+)?)\s+([A-Za-z.]+)\s+([\d.]+(?:,\d+)?)\s*Gs\.\s+([\d.]+(?:,\d+)?)\s*Gs\.")
    for m in pat.finditer(text):
        desc=m.group(3).strip()
        rows.append({"orden":int(m.group(1)),"codigo_proveedor":m.group(2),"descripcion":desc,"marca":detect_brand(desc),"modelo":"","cantidad":parse_money(m.group(4)),"unidad":m.group(5),"precio_unitario":parse_money(m.group(6)),"subtotal":parse_money(m.group(7)),"confirmado":True})
    return rows


def parse_items_tecno(text):
    lines=[x.strip() for x in text.splitlines() if x.strip()]
    rows=[]; i=0
    while i < len(lines):
        m=re.match(r"^(\d+)\s*$", lines[i])
        if m and i+1 < len(lines) and lines[i+1].startswith("["):
            order=int(m.group(1)); desc=lines[i+1]; j=i+2
            # Descripción puede continuar antes de cantidad.
            while j < len(lines) and not re.fullmatch(r"\d+(?:[.,]\d+)?", lines[j]) and j-i < 6:
                desc += " " + lines[j]; j+=1
            if j+3 < len(lines):
                qty=parse_money(lines[j]); unit=lines[j+1]
                price=parse_money(lines[j+2]); total=parse_money(lines[j+3])
                code=""
                cm=re.match(r"^\[([^]]+)\]\s*(.*)$", desc)
                if cm:
                    code=cm.group(1); desc=cm.group(2).strip()
                rows.append({"orden":order,"codigo_proveedor":code,"descripcion":desc,"marca":detect_brand(desc),"modelo":code,"cantidad":qty,"unidad":unit,"precio_unitario":price,"subtotal":total,"confirmado":True})
                i=j+4; continue
        i+=1
    return rows


def parse_items_ccp(text):
    rows=[]
    lines=[x.strip() for x in text.splitlines() if x.strip()]
    starts=[]
    for idx,line in enumerate(lines):
        if re.match(r"^\d+\s+[A-Z]{1,4}\d{4,}\s+", line):
            starts.append(idx)
    for pos,idx in enumerate(starts):
        end=starts[pos+1] if pos+1<len(starts) else len(lines)
        block=lines[idx:end]
        if not block: continue
        first=re.match(r"^(\d+)\s+(\S+)\s+(.+)$", block[0])
        if not first: continue
        order=int(first.group(1)); code=first.group(2); parts=[first.group(3)]
        qty=price=subtotal=0.0; unit="und"
        for line in block[1:]:
            mm=re.match(r"^(\d+(?:[.,]\d+)?)\s+([\d.]+(?:,\d+)?)\s+([\d.]+(?:,\d+)?)$", line)
            if mm:
                qty=parse_money(mm.group(1)); price=parse_money(mm.group(2)); subtotal=parse_money(mm.group(3)); break
            if line.lower().startswith("total bruto"): break
            parts.append(line)
        desc=" ".join(parts).strip()
        if qty and price:
            brand=detect_brand(desc)
            rows.append({"orden":order,"codigo_proveedor":code,"descripcion":desc,"marca":brand,"modelo":"","cantidad":qty,"unidad":unit,"precio_unitario":price,"subtotal":subtotal or qty*price,"confirmado":True})
    return rows


def parse_items_electropar(text):
    rows=[]
    # El extractor PDF de Electropar coloca subtotal antes de precio y luego descripción.
    pat=re.compile(r"IVA_10GS\s+([\d.]+(?:,\d+)?)GS\s+([\d.]+(?:,\d+)?)\s*(.+?)\n(\d{5,})\s+(\d+)\s+(\d+)\s*\n", re.S)
    for m in pat.finditer(text):
        subtotal=parse_money(m.group(1)); price=parse_money(m.group(2)); desc=re.sub(r"\s+"," ",m.group(3)).strip()
        code=m.group(4); qty=parse_money(m.group(5)); order=int(m.group(6))
        # Corta descripción si arrastró contenido de cabecera de siguiente bloque.
        desc=re.split(r"\s+IVA_10GS\s+",desc)[0].strip()
        rows.append({"orden":order,"codigo_proveedor":code,"descripcion":desc,"marca":detect_brand(desc),"modelo":"","cantidad":qty,"unidad":"und","precio_unitario":price,"subtotal":subtotal or qty*price,"confirmado":True})
    return rows


def parse_items_generic(text):
    rows=[]
    for line in [re.sub(r"\s+"," ",x).strip() for x in text.splitlines()]:
        m=re.match(r"^(\d+)\s+([A-Z0-9_./-]{3,})\s+(.+?)\s+(\d+(?:[.,]\d+)?)\s+(?:UN|UND|UNIDAD(?:ES)?|PCS?)\s+([\d.]+(?:,\d+)?)\s*(?:GS\.?|₲)?\s+([\d.]+(?:,\d+)?)", line, re.I)
        if m:
            desc=m.group(3).strip()
            rows.append({"orden":int(m.group(1)),"codigo_proveedor":m.group(2),"descripcion":desc,"marca":detect_brand(desc),"modelo":"","cantidad":parse_money(m.group(4)),"unidad":"und","precio_unitario":parse_money(m.group(5)),"subtotal":parse_money(m.group(6)),"confirmado":True})
    return rows


def parse_supplier_pdf(uploaded_file):
    raw=extract_pdf_text(uploaded_file)
    supplier=guess_supplier_name(raw)
    n=normalize_text(raw)
    if "COMAGRO" in n:
        items=parse_items_comagro(raw)
    elif "ELECTROPAR" in n:
        items=parse_items_electropar(raw)
    elif "PRESUP CHILE" in n or "PRESUP. CHILE" in n:
        items=parse_items_ccp(raw)
    elif "TECNOELECTRIC" in n or "TECNO ELECTRIC" in n:
        items=parse_items_tecno(raw)
    else:
        items=parse_items_generic(raw)
    currency="USD" if re.search(r"\bUSD\b|US\$|D[ÓO]LAR", raw, re.I) else "PYG"
    meta={
        "tipo_documento":"Presupuesto",
        "proveedor_sugerido":supplier,
        "numero_documento":extract_doc_number(raw, uploaded_file.name),
        "fecha":extract_doc_date(raw),
        "moneda":currency,
        "total":extract_doc_total(raw),
        "archivo_nombre":uploaded_file.name,
        "texto_extraido":raw,
    }
    return meta, pd.DataFrame(items)


def find_material_exact(description, brand="", model=""):
    mats=fetch_materials()
    if mats.empty: return None
    nd=normalize_text(description); nb=normalize_text(brand); nm=normalize_text(model)
    for _,r in mats.iterrows():
        candidates=[r.get("descripcion",""), r.get("nombre","")]
        if nd and any(normalize_text(x)==nd for x in candidates if x):
            rb=normalize_text(r.get("marca","")); rm=normalize_text(r.get("modelo",""))
            if (not nb or rb==nb) and (not nm or rm==nm):
                return r.to_dict()
    return None


def create_material_from_item(row):
    desc=str(row.get("descripcion","") or "").strip()
    brand=str(row.get("marca","") or "").strip()
    model=str(row.get("modelo","") or "").strip()
    existing=find_material_exact(desc,brand,model)
    if existing: return existing["id"]
    # Para la carga automática, nombre = descripción completa (máx. 180) para preservar trazabilidad.
    payload={"nombre":desc[:180] or "Material importado","categoria":guess_category(desc),"marca":brand or None,"modelo":model or None,"descripcion":desc or None,"activo":True}
    res=supabase.table("materiales").insert(payload).execute()
    return (res.data or [{}])[0].get("id")


def save_purchase_document(meta, items_df, supplier_id, auto_create_materials=True):
    number=str(meta.get("numero_documento","") or "").strip()
    dtype=str(meta.get("tipo_documento","Presupuesto") or "Presupuesto")
    if number:
        existing=supabase.table("documentos_compra").select("id,estado,archivo_nombre").eq("proveedor_id",supplier_id).eq("numero_documento",number).eq("tipo_documento",dtype).limit(1).execute().data or []
        if existing:
            raise ValueError(f"Documento duplicado: ya existe {dtype} Nº {number} para este proveedor.")
    payload={
        "tipo_documento":dtype,"proveedor_id":supplier_id,"proveedor_nombre":meta.get("proveedor_nombre") or None,
        "numero_documento":number or None,"fecha":meta.get("fecha").isoformat() if hasattr(meta.get("fecha"),"isoformat") else meta.get("fecha"),
        "moneda":meta.get("moneda") or "PYG","total":float(meta.get("total",0) or 0),"estado":"Importado",
        "archivo_nombre":meta.get("archivo_nombre") or None,"observacion":meta.get("observacion") or None,
        "registrado_por":getattr(st.session_state.auth_user,"email","") or "",
    }
    res=supabase.table("documentos_compra").insert(payload).execute()
    doc_id=(res.data or [{}])[0].get("id")
    if not doc_id: raise RuntimeError("No se obtuvo el ID del documento guardado.")
    rows=[]
    for idx,r in items_df.iterrows():
        confirmed=bool(r.get("confirmado",True))
        desc=str(r.get("descripcion","") or "").strip()
        if not confirmed or not desc: continue
        material_id=None
        if auto_create_materials:
            material_id=create_material_from_item(r)
        qty=float(r.get("cantidad",0) or 0); price=float(r.get("precio_unitario",0) or 0); subtotal=float(r.get("subtotal",0) or 0)
        rows.append({
            "documento_id":doc_id,"orden":int(r.get("orden",idx+1) or idx+1),"codigo_proveedor":str(r.get("codigo_proveedor","") or "").strip() or None,
            "descripcion":desc,"marca":str(r.get("marca","") or "").strip() or None,"modelo":str(r.get("modelo","") or "").strip() or None,
            "cantidad":qty or 1,"unidad":str(r.get("unidad","") or "").strip() or None,"precio_unitario":price or None,"subtotal":subtotal or (qty*price),
            "material_id":material_id,"confirmado":True,
        })
        if material_id:
            try:
                add_material_supplier(material_id, supplier_id, 3, str(r.get("codigo_proveedor","") or ""), None, "Vinculado automáticamente desde PDF")
            except Exception:
                pass
            if price > 0:
                add_price(material_id, supplier_id, price, meta.get("moneda") or "PYG", meta.get("fecha") or date.today(), "Factura" if dtype=="Factura" else "Cotización", f"Documento {number}")
    if rows:
        supabase.table("documentos_compra_items").insert(rows).execute()
    return doc_id, len(rows)


def fetch_purchase_documents():
    try:
        data=supabase.table("documentos_compra").select("*").order("creado_en",desc=True).limit(200).execute().data or []
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()


def update_supplier(supplier_id, name, ruc="", contacto="", telefono="", correo="", observacion=""):
    return supabase.table("proveedores").update({
        "nombre":name.strip(),"ruc":ruc.strip() or None,"contacto":contacto.strip() or None,
        "telefono":telefono.strip() or None,"correo":correo.strip() or None,"observacion":observacion.strip() or None,
        "activo":True,
    }).eq("id",supplier_id).execute()


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
            "🏭 Proveedores / Materiales",
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
    page_header("Presupuestos", "Cotizaciones de productos y servicios vinculadas al CRM")

    quotes_df = fetch_quotes()
    clients_db, _ = fetch_crm_from_db()

    tab_list, tab_new, tab_cost, tab_pdf = st.tabs([
        "📋 Mis presupuestos", "➕ Nuevo presupuesto", "🧮 Costeo interno", "📄 Vista previa / PDF"
    ])

    with tab_list:
        if quotes_df.empty:
            st.info("Todavía no hay presupuestos guardados.")
        else:
            show = quotes_df.copy()
            cols = [c for c in ["numero","fecha","cliente_nombre","tipo","estado","total","creado_por"] if c in show.columns]
            show = show[cols].rename(columns={"numero":"N°","fecha":"Fecha","cliente_nombre":"Cliente","tipo":"Tipo","estado":"Estado","total":"Total","creado_por":"Responsable"})

            # Vista escritorio: tabla completa
            st.markdown('<div class="desktop-only">', unsafe_allow_html=True)
            desktop_show = show.copy()
            if "Total" in desktop_show:
                desktop_show["Total"] = desktop_show["Total"].apply(pyg)
            st.dataframe(desktop_show, hide_index=True, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Vista móvil: tarjetas
            st.markdown('<div class="mobile-only">', unsafe_allow_html=True)
            for i, row in show.iterrows():
                numero = str(row.get("N°",""))
                fecha = str(row.get("Fecha",""))
                cliente = str(row.get("Cliente",""))
                tipo = str(row.get("Tipo",""))
                estado = str(row.get("Estado",""))
                total = pyg(row.get("Total",0))
                st.markdown(
                    f"""
                    <div class="quote-mobile-card">
                        <div class="quote-mobile-top">
                            <div>
                                <div class="quote-mobile-number">{numero}</div>
                                <div class="quote-mobile-client">{cliente}</div>
                            </div>
                            <span class="quote-mobile-badge">{estado}</span>
                        </div>
                        <div class="quote-mobile-meta">{fecha} · {tipo}</div>
                        <div class="quote-mobile-total">{total}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if st.button("Ver presupuesto", key=f"mobile_view_quote_{i}", use_container_width=True):
                    st.session_state.mobile_selected_quote = numero
                    st.info("Abrí la pestaña **Vista previa / PDF** para ver o descargar este presupuesto.")
            st.markdown('</div>', unsafe_allow_html=True)

    with tab_new:
        if clients_db.empty:
            st.warning("Primero necesitás clientes cargados en Supabase.")
        else:
            st.markdown("### Datos generales")
            a,b,c = st.columns([1.1,1.5,1])
            quote_type = a.selectbox("Tipo", ["Producto","Servicio"], key="q34_type")
            client_name = b.selectbox("Cliente", sorted(clients_db["Cliente"].dropna().astype(str).unique()), key="q34_client")
            q_number = c.text_input("N° Cotización", value=next_quote_number(), key="q34_number")

            client_row = clients_db[clients_db["Cliente"].astype(str).eq(client_name)].iloc[0]
            ruc_default = "" if pd.isna(client_row.get("RUC")) else str(client_row.get("RUC") or "")

            c1,c2,c3 = st.columns(3)
            q_date = c1.date_input("Fecha", date.today(), key="q34_date")
            ruc = c2.text_input("RUC", value=ruc_default, key="q34_ruc")
            attention = c3.text_input("Atención", key="q34_attention")

            if quote_type == "Servicio":
                st.markdown("### Alcance")
                title_text = st.text_input("Título / sector", placeholder="Ej.: ADECUACIONES SECTOR TINTE", key="q34_title")
                intro = st.text_area("Introducción", value="Por medio de la presente le mando un cordial saludo y a su vez poner a su consideración la siguiente propuesta comercial.", key="q34_intro")
                works = st.text_area("Trabajos a ser realizados", height=110, key="q34_works")
                inc1,inc2 = st.columns(2)
                include = inc1.text_area("Incluye", height=100, key="q34_include")
                exclude = inc2.text_area("No incluye", height=100, key="q34_exclude")
            else:
                title_text = intro = works = include = exclude = ""

            st.markdown("### Ítems comerciales")
            items_edit = st.data_editor(
                pd.DataFrame(st.session_state.quote_items), hide_index=True, use_container_width=True, num_rows="dynamic",
                column_config={
                    "Descripción": st.column_config.TextColumn(width="large"),
                    "Cantidad": st.column_config.NumberColumn(min_value=0.0, step=1.0),
                    "Unidad": st.column_config.TextColumn(width="small"),
                    "Precio Unitario": st.column_config.NumberColumn(min_value=0.0, step=1000.0, format="%.0f"),
                }, key="quote_items_editor_v34"
            )
            st.session_state.quote_items = items_edit.to_dict("records")
            items_calc = items_edit.copy()
            for col in ["Cantidad","Precio Unitario"]:
                items_calc[col] = pd.to_numeric(items_calc[col], errors="coerce").fillna(0)
            subtotal = float((items_calc["Cantidad"] * items_calc["Precio Unitario"]).sum())

            st.markdown("### Condiciones comerciales")
            d1,d2,d3,d4 = st.columns(4)
            discount_pct = d1.number_input("Descuento %", min_value=0.0, max_value=100.0, value=0.0, step=1.0, key="q34_discount")
            payment = d2.text_input("Forma de pago", value="CONTADO", key="q34_payment")
            delivery = d3.text_input("Plazo de entrega", value="A convenir", key="q34_delivery")
            validity = d4.number_input("Validez (días)", min_value=1, value=3, step=1, key="q34_validity")
            place = st.text_input("Lugar de entrega", value="En oficinas del cliente", key="q34_place")

            discount = subtotal * (discount_pct/100.0)
            total = subtotal - discount
            iva = total/11 if total else 0

            k1,k2,k3,k4 = st.columns(4)
            k1.metric("Subtotal IVA incl.", pyg(subtotal)); k2.metric("Descuento", pyg(discount))
            k3.metric("Total", pyg(total)); k4.metric("IVA incluido", pyg(iva))
            q_state = st.selectbox("Estado", QUOTE_STATES, key="q34_state")

            if st.button("💾 Guardar presupuesto", type="primary", use_container_width=True):
                if not q_number.strip():
                    st.warning("Ingresá el número de cotización.")
                elif subtotal <= 0:
                    st.warning("Agregá al menos un ítem con cantidad y precio.")
                else:
                    try:
                        payload = {
                            "numero":q_number.strip(),"fecha":q_date.isoformat(),"cliente_id":client_row["id"],
                            "cliente_nombre":client_name,"ruc":ruc.strip() or None,"atencion":attention.strip() or None,
                            "tipo":quote_type,"titulo":title_text.strip() or None,"introduccion":intro.strip() or None,
                            "trabajos":works.strip() or None,"incluye":include.strip() or None,"no_incluye":exclude.strip() or None,
                            "forma_pago":payment.strip() or None,"plazo_entrega":delivery.strip() or None,"lugar_entrega":place.strip() or None,
                            "validez_dias":int(validity),"descuento_pct":float(discount_pct),"subtotal":subtotal,
                            "descuento":discount,"total":total,"iva":iva,"estado":q_state,
                            "creado_por":getattr(st.session_state.auth_user,"email","") or ""
                        }
                        quote_id = save_quote_db(payload, items_edit)
                        st.session_state.last_quote_id = quote_id
                        st.success(f"Presupuesto {q_number} guardado permanentemente.")
                        st.rerun()
                    except Exception as exc:
                        st.error("No se pudo guardar el presupuesto."); st.caption(str(exc))

    with tab_cost:
        quotes_df = fetch_quotes()
        if quotes_df.empty:
            st.info("Primero guardá un presupuesto.")
        else:
            label_map = {f"{r['numero']} · {r['cliente_nombre']}":r["id"] for _,r in quotes_df.iterrows()}
            chosen = st.selectbox("Presupuesto", list(label_map.keys()), key="cost_quote")
            quote_id = label_map[chosen]
            existing = fetch_quote_costs(quote_id)
            costs_seed = existing.rename(columns={"categoria":"Categoría","descripcion":"Descripción","cantidad":"Cantidad","costo_unitario":"Costo Unitario","factor":"Factor"})[["Categoría","Descripción","Cantidad","Costo Unitario","Factor"]] if not existing.empty else pd.DataFrame(st.session_state.quote_costs)
            cost_edit = st.data_editor(
                costs_seed, hide_index=True, use_container_width=True, num_rows="dynamic",
                column_config={
                    "Categoría": st.column_config.SelectboxColumn(options=["Herramientas","Mano de obra","Materiales","Viaje / Viático","Mecánico","Neumático","Instrumentación","Tercerizado","Programación","Otros"]),
                    "Descripción": st.column_config.TextColumn(width="large"),
                    "Cantidad": st.column_config.NumberColumn(min_value=0.0, step=1.0),
                    "Costo Unitario": st.column_config.NumberColumn(min_value=0.0, step=1000.0, format="%.0f"),
                    "Factor": st.column_config.NumberColumn(min_value=0.0, step=0.05, format="%.2f"),
                }, key="quote_cost_editor_v34"
            )
            calc = cost_edit.copy()
            for col in ["Cantidad","Costo Unitario","Factor"]:
                calc[col] = pd.to_numeric(calc[col], errors="coerce").fillna(0)
            calc["Costo Total"] = calc["Cantidad"]*calc["Costo Unitario"]
            calc["Venta Sugerida"] = calc["Costo Total"]*calc["Factor"]
            total_cost = float(calc["Costo Total"].sum()); suggested = float(calc["Venta Sugerida"].sum())
            qrow = quotes_df[quotes_df["id"].eq(quote_id)].iloc[0]
            sold = float(qrow.get("total",0) or 0); margin = sold-total_cost; margin_pct=(margin/sold*100) if sold else 0
            m1,m2,m3,m4=st.columns(4)
            m1.metric("Costo interno",pyg(total_cost)); m2.metric("Venta sugerida",pyg(suggested)); m3.metric("Precio cotizado",pyg(sold)); m4.metric("Margen bruto",f"{margin_pct:.1f}%")
            st.dataframe(calc, hide_index=True, use_container_width=True)
            if st.button("💾 Guardar costeo interno", type="primary", use_container_width=True):
                try:
                    save_costs_db(quote_id, cost_edit)
                    st.success("Costeo guardado. No se mostrará en el PDF del cliente."); st.rerun()
                except Exception as exc:
                    st.error("No se pudo guardar el costeo."); st.caption(str(exc))

    with tab_pdf:
        quotes_df = fetch_quotes()
        if quotes_df.empty:
            st.info("Todavía no hay presupuestos para generar PDF.")
        else:
            label_map={f"{r['numero']} · {r['cliente_nombre']}":r["id"] for _,r in quotes_df.iterrows()}
            labels = list(label_map.keys())
            default_index = 0
            selected_num = st.session_state.get("mobile_selected_quote")
            if selected_num:
                for idx, label in enumerate(labels):
                    if label.startswith(str(selected_num)):
                        default_index = idx
                        break
            chosen=st.selectbox("Seleccionar presupuesto",labels,index=default_index,key="pdf_quote")
            quote_id=label_map[chosen]
            qrow=quotes_df[quotes_df["id"].eq(quote_id)].iloc[0].to_dict()
            items=fetch_quote_items(quote_id)
            c1,c2,c3,c4=st.columns(4)
            c1.metric("N°",qrow.get("numero","")); c2.metric("Cliente",qrow.get("cliente_nombre","")); c3.metric("Tipo",qrow.get("tipo","")); c4.metric("Total",pyg(qrow.get("total",0)))
            if not items.empty:
                st.dataframe(items[["cantidad","descripcion","precio_unitario","total"]].rename(columns={"cantidad":"Cantidad","descripcion":"Descripción","precio_unitario":"Precio Unitario","total":"Total"}), hide_index=True, use_container_width=True)
            try:
                pdf=quote_pdf_bytes(qrow,items)
                filename=re.sub(r"[^A-Za-z0-9._-]+","_",f"{qrow.get('numero','cotizacion')}_{qrow.get('cliente_nombre','cliente')}")+".pdf"
                st.download_button("⬇️ Descargar PDF",data=pdf,file_name=filename,mime="application/pdf",type="primary",use_container_width=True)
                st.caption("El PDF comercial no incluye el costeo interno.")
            except Exception as exc:
                st.error("No se pudo generar el PDF."); st.caption(str(exc))


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
# COMPRAS / OCR V3.6
# ============================================================
elif page == "🔎 Compras / OCR":
    page_header("Compras / OCR", "Carga masiva de presupuestos y facturas PDF")
    st.success("V3.6: podés cargar varios PDF, revisar lo detectado y recién después guardarlo en Supabase.")

    tab_import, tab_history = st.tabs(["📄 Importar PDF", "🗂️ Documentos importados"])

    with tab_import:
        suppliers_pdf = fetch_suppliers()
        uploaded_pdfs = st.file_uploader(
            "Presupuestos / facturas PDF",
            type=["pdf"],
            accept_multiple_files=True,
            key="purchase_pdf_upload_v36",
            help="Podés seleccionar varios archivos al mismo tiempo. Los PDF digitales se leen directamente; los escaneados se marcarán para revisión/OCR posterior."
        )
        if not uploaded_pdfs:
            st.info("Seleccioná uno o varios PDF. Antes de guardar siempre vas a poder corregir proveedor, número, fecha, cantidades y precios.")
        else:
            st.caption(f"Archivos seleccionados: {len(uploaded_pdfs)}")
            for file_index, pdf_file in enumerate(uploaded_pdfs):
                digest=hashlib.sha1(pdf_file.getvalue()).hexdigest()[:12]
                with st.expander(f"📄 {pdf_file.name}", expanded=(file_index==0)):
                    try:
                        meta, parsed_items = parse_supplier_pdf(pdf_file)
                    except Exception as exc:
                        st.error(f"No se pudo leer este PDF: {exc}")
                        continue

                    if len((meta.get("texto_extraido") or "").strip()) < 40:
                        st.warning("Este archivo parece escaneado o no contiene texto extraíble. En esta V3.6 queda marcado para revisión; la siguiente etapa agregará OCR de imagen.")

                    matched=match_supplier_row(meta.get("proveedor_sugerido"), suppliers_pdf)
                    supplier_names=suppliers_pdf["nombre"].astype(str).tolist() if not suppliers_pdf.empty else []
                    default_supplier=matched.get("nombre") if matched else (supplier_names[0] if supplier_names else "")

                    a,b,c,d=st.columns([1.4,1,1,1])
                    doc_type=a.selectbox("Tipo", ["Presupuesto","Factura"], key=f"doctype_{digest}")
                    if supplier_names:
                        default_idx=supplier_names.index(default_supplier) if default_supplier in supplier_names else 0
                        supplier_name=b.selectbox("Proveedor", supplier_names, index=default_idx, key=f"supplier_{digest}")
                    else:
                        supplier_name=b.text_input("Proveedor", value=meta.get("proveedor_sugerido", ""), key=f"supplier_text_{digest}")
                    doc_number=c.text_input("Nº documento", value=str(meta.get("numero_documento", "")), key=f"num_{digest}")
                    doc_date=d.date_input("Fecha", value=meta.get("fecha") or date.today(), key=f"date_{digest}")

                    e,f,g=st.columns([1,1,2])
                    currency=e.selectbox("Moneda", ["PYG","USD"], index=0 if meta.get("moneda")!="USD" else 1, key=f"curr_{digest}")
                    total=e.number_input("Total documento", min_value=0.0, value=float(meta.get("total",0) or 0), step=1000.0, format="%.0f", key=f"total_{digest}")
                    f.metric("Ítems detectados", len(parsed_items))
                    f.caption(f"Proveedor sugerido: {meta.get('proveedor_sugerido') or 'No identificado'}")
                    observation=g.text_area("Observación", placeholder="Ej.: revisión 3, precio especial, factura escaneada...", key=f"obs_{digest}")

                    if parsed_items.empty:
                        st.warning("No pude separar ítems automáticamente. Podés agregarlos manualmente en la tabla de abajo o dejar este PDF para la etapa OCR de imagen.")
                        parsed_items=pd.DataFrame([{"orden":1,"codigo_proveedor":"","descripcion":"","marca":"","modelo":"","cantidad":1.0,"unidad":"und","precio_unitario":0.0,"subtotal":0.0,"confirmado":True}])

                    st.markdown("#### Validar ítems")
                    edited=st.data_editor(
                        parsed_items,
                        hide_index=True,
                        use_container_width=True,
                        num_rows="dynamic",
                        key=f"items_{digest}",
                        column_config={
                            "orden": st.column_config.NumberColumn("#", min_value=1, step=1),
                            "codigo_proveedor": st.column_config.TextColumn("Código proveedor"),
                            "descripcion": st.column_config.TextColumn("Descripción", width="large"),
                            "marca": st.column_config.TextColumn("Marca"),
                            "modelo": st.column_config.TextColumn("Modelo / Ref."),
                            "cantidad": st.column_config.NumberColumn("Cantidad", min_value=0.0, step=1.0),
                            "unidad": st.column_config.TextColumn("Unidad"),
                            "precio_unitario": st.column_config.NumberColumn("Precio unit.", min_value=0.0, step=1000.0, format="%.0f"),
                            "subtotal": st.column_config.NumberColumn("Subtotal", min_value=0.0, step=1000.0, format="%.0f"),
                            "confirmado": st.column_config.CheckboxColumn("Importar"),
                        }
                    )
                    auto_create=st.checkbox(
                        "Crear/vincular materiales automáticamente y actualizar historial de precios",
                        value=True,
                        key=f"auto_{digest}",
                        help="Si el material no existe, se crea desde la descripción del PDF. Luego podés normalizar nombre, marca o modelo desde Proveedores / Materiales."
                    )

                    if st.button("✅ Confirmar importación", type="primary", use_container_width=True, key=f"save_{digest}"):
                        if not supplier_names:
                            st.warning("Primero cargá al menos un proveedor en Proveedores / Materiales.")
                        elif not doc_number.strip():
                            st.warning("Revisá el número del documento antes de guardar.")
                        else:
                            supplier_row=suppliers_pdf[suppliers_pdf["nombre"].astype(str).eq(supplier_name)]
                            if supplier_row.empty:
                                st.warning("No se encontró el proveedor seleccionado.")
                            else:
                                meta_save={"tipo_documento":doc_type,"proveedor_nombre":supplier_name,"numero_documento":doc_number.strip(),"fecha":doc_date,"moneda":currency,"total":total,"archivo_nombre":pdf_file.name,"observacion":observation}
                                try:
                                    doc_id, count=save_purchase_document(meta_save, edited, supplier_row.iloc[0]["id"], auto_create)
                                    st.success(f"Documento guardado. {count} ítem(s) importados y precios actualizados.")
                                except Exception as exc:
                                    st.error("No se pudo importar el documento.")
                                    st.caption(str(exc))

                    with st.expander("Ver texto extraído (diagnóstico)"):
                        st.text((meta.get("texto_extraido") or "")[:12000])

    with tab_history:
        docs=fetch_purchase_documents()
        if docs.empty:
            st.info("Todavía no hay documentos importados.")
        else:
            view=docs.copy()
            if "total" in view.columns:
                view["total"]=view["total"].apply(lambda x: pyg(x) if pd.notna(x) else "")
            cols=[c for c in ["fecha","tipo_documento","proveedor_nombre","numero_documento","moneda","total","estado","archivo_nombre","registrado_por"] if c in view.columns]
            st.dataframe(view[cols], hide_index=True, use_container_width=True)


# ============================================================
# PROVEEDORES / MATERIALES
# ============================================================
elif page == "🏭 Proveedores / Materiales":
    page_header("Proveedores / Materiales", "Matriz de compra, marcas y último precio")

    suppliers = fetch_suppliers()
    materials = fetch_materials()

    tab_search, tab_suppliers, tab_materials, tab_link, tab_price = st.tabs([
        "🔎 Buscador", "🏭 Proveedores", "📦 Materiales", "🔗 Relacionar", "💲 Precios"
    ])

    with tab_search:
        q = st.text_input(
            "Buscar",
            placeholder="Ej.: contactor, lovato, bf26, ccp, relé 220v...",
            key="mat_search"
        )
        f1, f2 = st.columns(2)
        cats = sorted([x for x in materials.get("categoria", pd.Series(dtype=str)).dropna().astype(str).unique() if x]) if not materials.empty else []
        cat = f1.selectbox("Categoría", ["Todas"] + cats)
        brand = f2.text_input("Marca (opcional)")
        result = material_search_catalog(q, None if cat == "Todas" else cat, brand.strip() or None)

        if result.empty:
            st.info("No encontré coincidencias.")
        else:
            view = result.copy()
            if "Último precio" in view.columns:
                view["Último precio"] = view["Último precio"].apply(
                    lambda x: "Sin precio" if pd.isna(x) else pyg(x)
                )
            if "Actualizado" in view.columns:
                dates = pd.to_datetime(view["Actualizado"], errors="coerce")
                days = (pd.Timestamp(date.today()) - dates).dt.days
                view["Hace"] = days.apply(
                    lambda d: "" if pd.isna(d) else ("Hoy" if d == 0 else f"Hace {int(d)} día(s)")
                )
            cols = [c for c in [
                "Material","Marca","Modelo","Categoría","Proveedor","Prioridad",
                "Último precio","Actualizado","Hace","Plazo días","Código proveedor"
            ] if c in view.columns]
            st.dataframe(view[cols], hide_index=True, use_container_width=True)

    with tab_suppliers:
        if not suppliers.empty:
            cols = [c for c in ["nombre","contacto","telefono","correo","ruc","observacion"] if c in suppliers.columns]
            st.dataframe(suppliers[cols], hide_index=True, use_container_width=True)
        with st.expander("➕ Nuevo proveedor"):
            name = st.text_input("Nombre *", key="sup_name")
            ruc = st.text_input("RUC", key="sup_ruc")
            contact = st.text_input("Contacto", key="sup_contact")
            phone = st.text_input("Teléfono", key="sup_phone")
            email = st.text_input("Correo", key="sup_email")
            note = st.text_area("Observación", key="sup_note")
            if st.button("Guardar proveedor", type="primary", use_container_width=True):
                if not name.strip():
                    st.warning("Ingresá el nombre.")
                else:
                    try:
                        upsert_supplier(name, ruc, contact, phone, email, note)
                        st.success("Proveedor guardado.")
                        st.rerun()
                    except Exception as exc:
                        st.error("No se pudo guardar el proveedor.")
                        st.caption(str(exc))

        if not suppliers.empty:
            with st.expander("✏️ Editar proveedor existente"):
                supplier_options = suppliers["nombre"].astype(str).tolist()
                selected_name = st.selectbox("Proveedor a editar", supplier_options, key="edit_sup_select")
                sr = suppliers[suppliers["nombre"].astype(str).eq(selected_name)].iloc[0]
                ename = st.text_input("Nombre / razón social", value=str(sr.get("nombre","") or ""), key="edit_sup_name")
                eruc = st.text_input("RUC", value=str(sr.get("ruc","") or ""), key="edit_sup_ruc")
                econtact = st.text_input("Contacto", value=str(sr.get("contacto","") or ""), key="edit_sup_contact")
                ephone = st.text_input("Teléfono", value=str(sr.get("telefono","") or ""), key="edit_sup_phone")
                eemail = st.text_input("Correo", value=str(sr.get("correo","") or ""), key="edit_sup_email")
                enote = st.text_area("Observación", value=str(sr.get("observacion","") or ""), key="edit_sup_note")
                if st.button("Guardar cambios del proveedor", type="primary", use_container_width=True, key="edit_sup_save"):
                    if not ename.strip():
                        st.warning("El nombre no puede quedar vacío.")
                    else:
                        try:
                            update_supplier(sr["id"], ename, eruc, econtact, ephone, eemail, enote)
                            st.success("Proveedor actualizado sin perder materiales, precios ni documentos vinculados.")
                            st.rerun()
                        except Exception as exc:
                            st.error("No se pudo actualizar el proveedor.")
                            st.caption(str(exc))

    with tab_materials:
        if not materials.empty:
            cols = [c for c in ["nombre","categoria","marca","modelo","descripcion"] if c in materials.columns]
            st.dataframe(materials[cols], hide_index=True, use_container_width=True)
        with st.expander("➕ Nuevo material"):
            name = st.text_input("Material *", placeholder="Ej.: Contactor", key="mat_name")
            cat = st.selectbox("Categoría", MATERIAL_CATEGORIES, key="mat_cat")
            brand = st.text_input("Marca", placeholder="Ej.: LOVATO", key="mat_brand")
            model = st.text_input("Modelo / referencia", placeholder="Ej.: BF26", key="mat_model")
            desc = st.text_area("Descripción", key="mat_desc")
            if st.button("Guardar material", type="primary", use_container_width=True):
                if not name.strip():
                    st.warning("Ingresá el material.")
                else:
                    try:
                        insert_material(name, cat, brand, model, desc)
                        st.success("Material guardado.")
                        st.rerun()
                    except Exception as exc:
                        st.error("No se pudo guardar el material.")
                        st.caption(str(exc))

    with tab_link:
        if suppliers.empty or materials.empty:
            st.info("Primero cargá al menos un proveedor y un material.")
        else:
            mat_labels = {f"{r.get('nombre','')} · {r.get('marca','') or ''} · {r.get('modelo','') or ''}": r["id"] for _, r in materials.iterrows()}
            sup_labels = {r["nombre"]: r["id"] for _, r in suppliers.iterrows()}
            material_label = st.selectbox("Material", list(mat_labels.keys()), key="link_mat")
            supplier_label = st.selectbox("Proveedor", list(sup_labels.keys()), key="link_sup")
            c1,c2 = st.columns(2)
            priority = c1.number_input("Prioridad", min_value=1, max_value=9, value=1, step=1)
            lead = c2.number_input("Plazo habitual (días)", min_value=0, value=0, step=1)
            supplier_code = st.text_input("Código del proveedor")
            note = st.text_area("Observación", placeholder="Ej.: proveedor preferido para LOVATO")
            if st.button("Guardar relación", type="primary", use_container_width=True):
                try:
                    add_material_supplier(mat_labels[material_label], sup_labels[supplier_label], priority, supplier_code, lead, note)
                    st.success("Relación material-proveedor guardada.")
                    st.rerun()
                except Exception as exc:
                    st.error("No se pudo guardar la relación.")
                    st.caption(str(exc))

    with tab_price:
        if suppliers.empty or materials.empty:
            st.info("Primero cargá proveedores y materiales.")
        else:
            mat_labels = {f"{r.get('nombre','')} · {r.get('marca','') or ''} · {r.get('modelo','') or ''}": r["id"] for _, r in materials.iterrows()}
            sup_labels = {r["nombre"]: r["id"] for _, r in suppliers.iterrows()}
            material_label = st.selectbox("Material", list(mat_labels.keys()), key="price_mat")
            supplier_label = st.selectbox("Proveedor", list(sup_labels.keys()), key="price_sup")
            c1,c2,c3 = st.columns(3)
            price = c1.number_input("Precio", min_value=0.0, step=1000.0, format="%.0f")
            currency = c2.selectbox("Moneda", ["PYG","USD"])
            pdate = c3.date_input("Fecha", date.today())
            source = st.selectbox("Origen", ["Carga manual","Cotización","OCR","Compra"])
            note = st.text_area("Observación")
            if st.button("Registrar precio", type="primary", use_container_width=True):
                if price <= 0:
                    st.warning("Ingresá un precio mayor a cero.")
                else:
                    try:
                        add_price(mat_labels[material_label], sup_labels[supplier_label], price, currency, pdate, source, note)
                        st.success("Precio agregado al historial.")
                        st.rerun()
                    except Exception as exc:
                        st.error("No se pudo registrar el precio.")
                        st.caption(str(exc))


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
    '<div class="footer">© 2026 Respaldo Industrial SRL · ERP V3.6 Compras PDF</div>',
    unsafe_allow_html=True,
)