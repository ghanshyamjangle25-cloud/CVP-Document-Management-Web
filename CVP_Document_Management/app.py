import streamlit as st
import contextlib
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import date, datetime, timedelta
import hashlib
import io
import os
import shutil
import zipfile
import qrcode
import base64
import json
import re
from html import escape
from demo_data import load_demo_data

APP_NAME = "C. V. Patil & Associates"
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
ARCHIVE_DIR = BASE_DIR / "archive"
BACKUP_DIR = BASE_DIR / "backups"
DB_PATH = DATA_DIR / "cvp_dms.db"

for p in [DATA_DIR, UPLOAD_DIR / "documents", UPLOAD_DIR / "insurance", UPLOAD_DIR / "contracts", UPLOAD_DIR / "employees", ARCHIVE_DIR, BACKUP_DIR]:
    p.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title=APP_NAME, page_icon="📁", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
:root{
  --cvp-bg:#f4f7f8; --cvp-surface:#ffffff; --cvp-sidebar:#142126; --cvp-sidebar2:#0e181c;
  --cvp-teal:#19867e; --cvp-teal2:#27a99d; --cvp-ink:#17313d; --cvp-muted:#6f828b;
  --cvp-line:#dde7ea; --cvp-soft:#e9f4f2; --cvp-warn:#d18a2d;
}
.stApp{background:
  radial-gradient(circle at 12% 18%,#2fb2a755 0,transparent 38%),
  radial-gradient(circle at 88% 82%,#1b5e8a55 0,transparent 40%),
  linear-gradient(135deg,#0d2c3a 0%,#134a56 55%,#17776f 100%) fixed;color:var(--cvp-ink)}
.block-container{padding:2.1rem 2.2rem 2.8rem;max-width:1480px}
/* light text directly on the gradient; white cards keep dark text */
section.main h1,section.main h2,section.main h3,section.main h4,[data-testid="stMain"] h1,[data-testid="stMain"] h2,[data-testid="stMain"] h3,[data-testid="stMain"] h4,
.cvp-section-band h2,.panel-title,.dn-legend,.dn-ring span{color:#fff!important}
.cvp-sub,.cvp-section-band p,.dn-ring small,[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] *{color:#b9d6d6!important}
.cvp-page-heading{border-bottom-color:#ffffff30!important}
[data-testid="stMain"] [data-testid="stWidgetLabel"],[data-testid="stMain"] [data-testid="stWidgetLabel"] p,[data-testid="stMain"] [data-testid="stWidgetLabel"] span,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] p,[data-testid="stMain"] [data-testid="stMarkdownContainer"] li,[data-testid="stMain"] label{color:#e8f4f3!important}
.stTabs [role="tab"]{color:#d6ebea!important}
.stTabs [role="tab"][aria-selected="true"]{background:#ffffff22;color:#fff!important}
.stTabs [role="tablist"]{border-bottom-color:#ffffff30!important}
.stTabs [data-baseweb="tab-highlight"]{background-color:#5fe0d2!important}
.dn-ring::before{background:#134a56!important}
.stButton button,.stDownloadButton button{background:#ffffff1c!important;border:1px solid #ffffff55!important;color:#fff!important}
.stButton button:hover,.stDownloadButton button:hover{background:#ffffff33!important;color:#fff!important}
/* anything on a white card goes back to dark */
.cvp-topbar *,.kpi *,.module-card *,.emp-card *,.cvp-login-note *,
[data-testid="stMain"] div[data-testid="stForm"] *,[data-testid="stMain"] div[data-testid="stMetric"] *,[data-testid="stMain"] [data-testid="stExpander"] *,[data-testid="stMain"] [data-testid="stAlert"] *,
[data-testid="stMain"] div[data-testid="stForm"] [data-testid="stMarkdownContainer"] p,[data-testid="stMain"] [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
[data-testid="stMain"] div[data-testid="stForm"] [data-testid="stWidgetLabel"] p,[data-testid="stMain"] [data-testid="stExpander"] [data-testid="stWidgetLabel"] p{color:var(--cvp-ink)!important}
.cvp-topbar-kicker,.cvp-topbar-sub,.cvp-user-role,.kpi-label,.module-card-sub,.emp-row span,.emp-card-title{color:var(--cvp-muted)!important}
.cvp-topbar-kicker{color:#43827c!important}.emp-card-title{color:#176f69!important}
.cvp-avatar{color:#fff!important}.kpi .kpi-icon{color:#fff!important;background:var(--accent)!important;border-color:var(--accent)!important;font-weight:800}.module-card .module-card-icon{color:#0f4f4a!important;background:#cfe8e4!important;font-weight:800}
[data-testid="stMain"] div[data-testid="stForm"] .stFormSubmitButton button,[data-testid="stMain"] div[data-testid="stForm"] .stFormSubmitButton button *{color:#fff!important}
div[data-testid="stForm"] .stButton button,[data-testid="stExpander"] .stButton button,[data-testid="stExpander"] .stDownloadButton button{background:#fff!important;color:var(--cvp-ink)!important;border:1px solid #cedde1!important}
[data-testid="stExpander"] .stButton button:hover,[data-testid="stExpander"] .stDownloadButton button:hover{background:#edf6f4!important;color:#135f5a!important;border-color:#6ca9a3!important}
[data-testid="stExpander"] .stButton button *,[data-testid="stExpander"] .stDownloadButton button *{color:inherit!important}
[data-testid="stHeader"]{background:transparent}
[data-testid="stHeader"] *,[data-testid="stToolbar"] *,[data-testid="stStatusWidget"] *{color:#fff!important;fill:#fff!important}
#MainMenu, footer{visibility:hidden}
h1,h2,h3{color:var(--cvp-ink);letter-spacing:-.025em}
p{line-height:1.55}

/* LEFT NAVIGATION — intentionally closer in structure to the Asset app, but CVP-specific */
section[data-testid="stSidebar"]{display:block!important;background:linear-gradient(180deg,var(--cvp-sidebar) 0%,var(--cvp-sidebar2) 100%);border-right:1px solid #263940;min-width:270px!important}
section[data-testid="stSidebar"] [data-testid="stSidebarContent"]{padding:1rem .75rem 1.1rem}
section[data-testid="stSidebar"] *{color:#eaf4f3!important}
[data-testid="stSidebarCollapsedControl"],[data-testid="collapsedControl"]{display:flex!important}
.sidebar-brand-card{padding:15px 14px 14px;border:1px solid #2c454c;background:linear-gradient(145deg,#1b3037,#16272d);border-radius:14px;box-shadow:0 9px 24px #00000025;margin-bottom:13px}
.sidebar-brand-row{display:flex;align-items:center;gap:10px}
.sidebar-brand-mark{width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;background:linear-gradient(145deg,#2fb2a7,#16736e);font-weight:900;font-size:.75rem;letter-spacing:.05em;color:white!important;box-shadow:0 6px 14px #00000030}
.sidebar-brand-logo{width:60px;height:60px;border-radius:50%;background:#fff;padding:8px;object-fit:contain;flex:none;box-shadow:0 0 0 3px #ffffff1f,0 6px 14px #00000040}
.sidebar-brand-card{border-top:3px solid #2fb2a7!important}
.sidebar-brand-title{font-size:.96rem;font-weight:800;line-height:1.15;color:white!important;letter-spacing:-.015em}
.sidebar-brand-sub{font-size:.69rem;color:#9db4b8!important;margin-top:4px}
.sidebar-section-label{font-size:.65rem;font-weight:800;letter-spacing:.14em;color:#7f9ba1!important;margin:15px 8px 7px;text-transform:uppercase}
.sidebar-user-card{padding:11px 12px;border-radius:12px;background:#1d343a;border:1px solid #2c4c53;margin:4px 0 10px}
.sidebar-user-name{font-weight:750;font-size:.84rem;color:#fff!important}
.sidebar-user-role{font-size:.70rem;color:#9ec8c4!important;margin-top:2px}
.sidebar-foot{font-size:.66rem;color:#718e94!important;text-align:center;margin-top:14px;line-height:1.45}
section[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"]{display:flex;flex-direction:column;gap:.24rem;border:0;background:transparent;overflow:visible;margin:0}
section[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label{flex:none;justify-content:flex-start;padding:.62rem .68rem;border:1px solid transparent;border-radius:9px;transition:.16s ease;font-size:.80rem;background:transparent}
section[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label > *{display:flex!important}
section[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label [data-testid="stMarkdownContainer"] p{font-size:.80rem;white-space:normal;color:#d5e1e3!important}
section[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:#203b42;border-color:#294951}
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:linear-gradient(90deg,#1d5755,#22464c);border-color:#34716d;box-shadow:inset 3px 0 #34b7aa}
section[data-testid="stSidebar"] .stButton button{background:#1b3036!important;color:#dcebea!important;border:1px solid #315159!important;border-radius:9px!important}
section[data-testid="stSidebar"] .stButton button:hover{background:#26464d!important;border-color:#3f706e!important;color:white!important}
section[data-testid="stSidebar"] hr{border-color:#294148!important}

/* APP HEADER */
.cvp-topbar{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:17px 20px;background:#fff;border:1px solid var(--cvp-line);border-radius:14px;box-shadow:0 7px 22px #17313d0b;margin:0 0 18px}
.cvp-topbar-left{display:flex;align-items:center;gap:13px;min-width:0}
.cvp-topbar-logo{width:46px;height:46px;object-fit:contain;border:1px solid #e0e8ea;border-radius:12px;padding:5px;background:#fff}
.cvp-topbar-kicker{font-size:1rem;letter-spacing:.04em;text-transform:none;color:#43827c;font-weight:800;margin-bottom:3px}
.cvp-topbar-title{font-size:1.18rem;font-weight:800;color:var(--cvp-ink);letter-spacing:-.025em}
.cvp-topbar-sub{font-size:.76rem;color:var(--cvp-muted);margin-top:2px}
.cvp-user-chip{display:flex;align-items:center;gap:9px;background:#f1f7f6;border:1px solid #d4e8e5;border-radius:12px;padding:8px 10px;white-space:nowrap}
.cvp-avatar{width:34px;height:34px;border-radius:9px;display:flex;align-items:center;justify-content:center;color:white;font-weight:800;font-size:.75rem;background:linear-gradient(145deg,#2ca99e,#146e69)}
.cvp-user-name{font-weight:750;font-size:.82rem;color:var(--cvp-ink)}
.cvp-user-role{font-size:.68rem;color:var(--cvp-muted);margin-top:1px}

/* PAGE TITLES */
.cvp-page-heading{padding:7px 0 14px;margin-bottom:18px;border-bottom:1px solid var(--cvp-line)}
.cvp-title{font-size:.95rem;font-weight:600;letter-spacing:.01em;color:#b9d6d6!important;margin-top:2px}
.cvp-sub{color:var(--cvp-muted);font-size:.9rem;margin-top:6px;max-width:800px}
.cvp-section-band{display:flex;justify-content:space-between;align-items:flex-end;gap:20px;margin:2px 0 16px}
.cvp-section-band h2{font-size:1.38rem;margin:0;color:var(--cvp-ink)}
.cvp-section-band p{font-size:.82rem;margin:4px 0 0;color:var(--cvp-muted)}
.cvp-date-badge{background:#e8f3f1;border:1px solid #cce4df;color:#286f69;border-radius:999px;padding:6px 10px;font-size:.72rem;font-weight:700}

/* DASHBOARD */
.kpi-grid{display:grid;grid-template-columns:repeat(6,minmax(125px,1fr));gap:13px;margin:0 0 18px}
.kpi{position:relative;background:#fff;border:1px solid var(--cvp-line);border-radius:12px;padding:14px 14px 13px;overflow:hidden;box-shadow:0 4px 13px #17313d0a}
.kpi::before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--accent)}
.kpi-icon{width:29px;height:29px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:.86rem;background:color-mix(in srgb,var(--accent) 13%,white);color:var(--accent);border:1px solid color-mix(in srgb,var(--accent) 30%,white)}
.kpi-value{font-size:1.45rem;font-weight:800;letter-spacing:-.035em;color:var(--cvp-ink);margin:8px 0 1px;line-height:1}
.kpi-label{color:var(--cvp-muted);font-size:.73rem;font-weight:600}
.module-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:0 0 22px}
.module-card{background:linear-gradient(145deg,#fff,#f9fbfb);border:1px solid var(--cvp-line);border-radius:12px;padding:14px 15px;box-shadow:0 4px 13px #17313d08}
.module-card-top{display:flex;align-items:center;justify-content:space-between;gap:12px}
.module-card-icon{width:34px;height:34px;border-radius:9px;background:#e5f3f0;color:#176f69;display:flex;align-items:center;justify-content:center;font-size:1rem}
.module-card-count{font-size:1.13rem;font-weight:850;color:var(--cvp-ink)}
.module-card-title{font-size:.79rem;font-weight:800;color:var(--cvp-ink);margin-top:9px}
.module-card-sub{font-size:.70rem;color:var(--cvp-muted);margin-top:3px}
.panel-title{display:flex;align-items:center;gap:9px;font-size:.86rem;font-weight:800;color:var(--cvp-ink);margin:0 0 12px}
.panel-title::before{content:"";width:4px;height:15px;border-radius:3px;background:#19867e}
.dn-wrap{display:flex;align-items:center;gap:20px;height:230px;justify-content:center}
.dn-ring{position:relative;width:145px;height:145px;border-radius:50%;flex:none}
.dn-ring::before{content:"";position:absolute;inset:27px;border-radius:50%;background:#fff}
.dn-ring span{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:1.48rem;font-weight:800;color:var(--cvp-ink);line-height:1}
.dn-ring small{font-size:.66rem;font-weight:500;color:var(--cvp-muted);margin-top:3px}
.dn-legend{display:flex;flex-direction:column;gap:7px;font-size:.78rem;color:var(--cvp-ink)}
.dn-row{display:flex;align-items:center;gap:8px}.dn-row b{margin-left:auto;padding-left:12px}.dn-dot{width:9px;height:9px;border-radius:50%;flex:none}

/* WIDGETS */
div[data-testid="stForm"]{background:#fff;padding:22px;border:1px solid var(--cvp-line);border-radius:14px;box-shadow:0 5px 17px #17313d09}
div[data-testid="stMetric"]{background:#fff;padding:18px;border:1px solid var(--cvp-line);border-radius:12px}
[data-testid="stExpander"] details{background:#fff;border:1px solid var(--cvp-line);border-radius:12px}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-testid="stNumberInput"] input{color:var(--cvp-ink);background:#fbfcfd}
[data-baseweb="input"],[data-baseweb="textarea"],[data-baseweb="select"]>div{border-radius:9px}
[data-testid="stWidgetLabel"],[data-testid="stWidgetLabel"] p,[data-testid="stWidgetLabel"] span{color:#21353e!important;opacity:1!important}
.stButton button,.stDownloadButton button,.stFormSubmitButton button{border-radius:9px;font-weight:650;min-height:2.55rem}
.stButton button,.stDownloadButton button{background:#fff;border:1px solid #cedde1;color:var(--cvp-ink)}
.stButton button:hover,.stDownloadButton button:hover{background:#edf6f4;border-color:#6ca9a3;color:#135f5a}
.stFormSubmitButton button{background:#17776f;color:#fff;border-color:#17776f}
.stFormSubmitButton button:hover{background:#115d58;color:#fff;border-color:#115d58}
.stTabs [role="tablist"]{gap:.3rem;border-bottom:1px solid var(--cvp-line);padding-bottom:5px}
.stTabs [role="tab"]{padding:.58rem .85rem;border-radius:8px;height:auto;color:#d6ebea!important}
.stTabs [role="tab"] p{color:inherit!important}
.stTabs [role="tab"][aria-selected="true"]{background:#ffffff26;color:#fff!important}
.stTabs [data-baseweb="tab-highlight"]{background-color:#5fe0d2;height:3px}
div[data-testid="stDataFrame"]{border:1px solid var(--cvp-line);border-radius:11px;overflow:hidden;box-shadow:0 3px 12px #17313d07}
[data-testid="stAlert"]{border-radius:10px} hr{border-color:var(--cvp-line)}

/* LOGIN */
.cvp-brand{display:flex;align-items:center;gap:10px;margin-bottom:20px;font-weight:800;font-size:1.08rem;color:var(--cvp-ink)}
.cvp-mark{background:linear-gradient(145deg,#1c9288,#125e5a);color:white;border-radius:10px;padding:11px 9px;font-size:.75rem;letter-spacing:.08em}
.cvp-eyebrow{font-size:.67rem;font-weight:800;letter-spacing:.15em;text-transform:uppercase;color:#378078;margin-bottom:10px}
.cvp-login-heading{font-size:clamp(2rem,4vw,3.15rem);line-height:1.08;font-weight:820;letter-spacing:-.055em;margin:12px 0;color:var(--cvp-ink)}
.cvp-login-art{width:100%;border-radius:18px;margin:12px 0 20px;border:1px solid var(--cvp-line);background:#fff}
.cvp-login-feature-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin-top:16px}
.cvp-login-feature{padding:10px 11px;border:1px solid #dbe7ea;border-radius:10px;background:#fff;font-size:.75rem;color:#586f79}
.cvp-login-feature strong{display:block;color:#183448;margin-bottom:2px;font-size:.78rem}
.cvp-login-note{margin-top:12px;padding:12px 14px;border:1px solid #d4e5e6;border-radius:10px;background:#f7fbfb;color:#536e76;font-size:.79rem;line-height:1.5}

.emp-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px;margin:6px 0 20px}
.emp-card{background:#fff;border:1px solid var(--cvp-line);border-radius:13px;padding:17px 19px;box-shadow:0 5px 16px #17313d0b}
.emp-card-title{font-weight:800;color:#176f69;font-size:.9rem;margin-bottom:9px;padding-bottom:8px;border-bottom:1px solid #dce9e8}
.emp-row{display:flex;justify-content:space-between;gap:16px;padding:6px 0;border-bottom:1px dashed #e6eef1;font-size:.82rem}.emp-row:last-child{border-bottom:none}.emp-row span{color:var(--cvp-muted);flex:none}.emp-row b{color:var(--cvp-ink);font-weight:650;text-align:right;word-break:break-word}

/* ---------- COMPANY BRANDING ---------- */
.cvp-kicker{font-size:1.9rem;font-weight:850;letter-spacing:-.03em;line-height:1.1;color:#fff!important;margin-bottom:2px}
.cvp-hero{position:relative;overflow:hidden;display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap;padding:24px 28px;margin:0 0 20px;border-radius:22px;
  background:linear-gradient(120deg,#1c8f84 0%,#27a99d 55%,#3fc7b6 100%);box-shadow:0 18px 40px #00000040}
.cvp-hero::before{content:"";position:absolute;right:-60px;top:-90px;width:300px;height:300px;border-radius:50%;background:#ffffff1c}
.cvp-hero::after{content:"";position:absolute;right:140px;bottom:-110px;width:220px;height:220px;border-radius:50%;background:#ffffff12}
.cvp-hero-left,.cvp-hero-right{position:relative;z-index:1;display:flex;align-items:center;gap:18px}
.cvp-hero-logo{width:104px;height:104px;border-radius:50%;background:#fff;padding:14px;object-fit:contain;box-shadow:0 0 0 5px #ffffff30,0 10px 24px #00000040}
.cvp-hero-kicker{font-size:.85rem;font-weight:600;color:#e6fffa!important}
.cvp-hero-title{font-size:2.3rem;font-weight:850;letter-spacing:-.035em;color:#fff!important;line-height:1.1;margin-top:4px}
.cvp-hero-sub{font-size:.86rem;color:#e6fffa!important;margin-top:4px}
.cvp-hero-right{flex-direction:column;align-items:flex-end;gap:10px}
.cvp-hero-date{font-size:.78rem;font-weight:700;color:#fff!important;background:#ffffff26;border-radius:999px;padding:6px 14px}
.cvp-hero .cvp-user-chip{background:#ffffffee}
.cvp-footer{margin:34px 0 4px;padding-top:16px;border-top:1px solid #ffffff2e;display:flex;flex-direction:column;align-items:center;gap:4px;text-align:center}
.cvp-footer b{color:#fff!important;font-size:.88rem;letter-spacing:.02em}
.cvp-footer span{color:#a9d3d0!important;font-size:.72rem}
.kpi,.module-card,.emp-card{transition:transform .18s ease,box-shadow .18s ease}
.kpi:hover,.module-card:hover,.emp-card:hover{transform:translateY(-3px);box-shadow:0 14px 28px #0000002e}

@media(max-width:1100px){.kpi-grid{grid-template-columns:repeat(3,1fr)}.module-strip{grid-template-columns:repeat(2,1fr)}}
@media(max-width:760px){.block-container{padding:1.15rem .9rem 2rem}.cvp-topbar{align-items:flex-start;flex-direction:column}.cvp-user-chip{width:100%}.kpi-grid{grid-template-columns:repeat(2,1fr)}.module-strip{grid-template-columns:1fr}.cvp-login-feature-grid{grid-template-columns:1fr}}
</style>
""", unsafe_allow_html=True)

# ---------------------------- Database ----------------------------
def db_conn():
    # many users can be logged in at once: wait for locks instead of failing, and allow readers during writes (WAL)
    con = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA busy_timeout=30000")
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=NORMAL")
    except sqlite3.DatabaseError:
        pass
    return con

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def execute(sql, params=()):
    con = db_conn()
    try:
        with con:
            cur = con.execute(sql, params)
            return cur.lastrowid
    finally:
        con.close()

def df_query(sql, params=()):
    con = db_conn()
    try:
        return pd.read_sql_query(sql, con, params=params)
    finally:
        con.close()

def scalar(sql, params=(), default=0):
    con = db_conn()
    try:
        row = con.execute(sql, params).fetchone()
        return row[0] if row else default
    finally:
        con.close()

# Columns added for the CVPA Employee Form (migrated onto existing databases)
EMPLOYEE_FORM_COLUMNS = [
    "surname", "first_name", "father_name", "mother_name", "dob", "gender", "marital_status",
    "permanent_address", "local_address", "telephone", "aadhar", "education", "software_skills",
    "family_details", "vehicle_company", "vehicle_no", "license_no", "bank_address", "bank_branch",
    "photo_path", "pan_doc_path", "aadhar_doc_path", "passbook_doc_path", "declaration_at",
]

# Extra project fields (migrated onto existing databases)
PROJECT_EXTRA_COLUMNS = ["project_type", "client_contact", "work_order_no", "contract_value", "progress"]
PROJECT_STATUSES = ["Planning", "Active", "On Hold", "Completed", "Closed"]
PROJECT_TYPES = ["Design / Engineering", "Construction", "Consultancy", "Supervision", "Survey", "Other"]
# Standard document sets expected for every project file
PROJECT_DOC_CHECKLIST = ["Contract", "Drawing", "Engineering", "MDR", "Quality", "Accounts", "Insurance", "Admin"]

def init_db():
    with db_conn() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL,
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            hod TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            department TEXT,
            designation TEXT,
            manager TEXT,
            joining_date TEXT,
            mobile TEXT,
            email TEXT,
            employment_type TEXT,
            status TEXT,
            user_role TEXT,
            bank_name TEXT,
            account_number TEXT,
            ifsc TEXT,
            pan TEXT,
            uan TEXT,
            pf_number TEXT,
            esi_number TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            client TEXT,
            manager TEXT,
            start_date TEXT,
            end_date TEXT,
            status TEXT,
            location TEXT,
            description TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_no TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            category TEXT,
            doc_type TEXT,
            department TEXT,
            related_to TEXT,
            related_ref TEXT,
            project_code TEXT,
            owner TEXT,
            prepared_by TEXT,
            checked_by TEXT,
            approved_by TEXT,
            revision TEXT,
            issue_date TEXT,
            expiry_date TEXT,
            reminder_days INTEGER DEFAULT 30,
            version INTEGER DEFAULT 1,
            confidentiality TEXT,
            description TEXT,
            filename TEXT,
            filepath TEXT,
            status TEXT,
            approval_stage TEXT,
            checked_out_by TEXT,
            checked_out_at TEXT,
            is_deleted INTEGER DEFAULT 0,
            created_by TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER NOT NULL,
            reviewer_role TEXT,
            reviewer TEXT,
            status TEXT,
            comments TEXT,
            action_date TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS insurance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_no TEXT UNIQUE NOT NULL,
            policy_type TEXT,
            company TEXT,
            related_type TEXT,
            related_ref TEXT,
            start_date TEXT,
            expiry_date TEXT,
            premium REAL DEFAULT 0,
            sum_insured REAL DEFAULT 0,
            broker TEXT,
            reminder_days INTEGER DEFAULT 30,
            status TEXT,
            filename TEXT,
            filepath TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_no TEXT UNIQUE NOT NULL,
            title TEXT,
            counterparty TEXT,
            start_date TEXT,
            expiry_date TEXT,
            value REAL DEFAULT 0,
            owner TEXT,
            reminder_days INTEGER DEFAULT 30,
            status TEXT,
            filename TEXT,
            filepath TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_code TEXT UNIQUE NOT NULL,
            asset_type TEXT,
            description TEXT,
            assigned_to TEXT,
            location TEXT,
            purchase_date TEXT,
            value REAL DEFAULT 0,
            insurance_policy TEXT,
            status TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS salary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_code TEXT NOT NULL,
            salary_month TEXT NOT NULL,
            basic REAL DEFAULT 0,
            hra REAL DEFAULT 0,
            allowances REAL DEFAULT 0,
            bonus REAL DEFAULT 0,
            pf REAL DEFAULT 0,
            tax REAL DEFAULT 0,
            other_deductions REAL DEFAULT 0,
            gross REAL DEFAULT 0,
            deductions REAL DEFAULT 0,
            net REAL DEFAULT 0,
            created_at TEXT NOT NULL,
            UNIQUE(employee_code, salary_month)
        );
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT NOT NULL,
            entry_type TEXT,
            category TEXT,
            amount REAL DEFAULT 0,
            reference TEXT,
            party TEXT,
            description TEXT,
            created_by TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            module TEXT,
            record_ref TEXT,
            assignee TEXT,
            due_date TEXT,
            priority TEXT,
            status TEXT,
            escalation TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS generic_registers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module TEXT NOT NULL,
            record_no TEXT,
            title TEXT NOT NULL,
            project_code TEXT,
            owner TEXT,
            record_date TEXT,
            status TEXT,
            remarks TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            username TEXT,
            action TEXT,
            module TEXT,
            record_ref TEXT,
            details TEXT
        );
        """)
        existing = {r["name"] for r in con.execute("PRAGMA table_info(employees)")}
        for col in EMPLOYEE_FORM_COLUMNS:
            if col not in existing:
                con.execute(f"ALTER TABLE employees ADD COLUMN {col} TEXT")
        existing_p = {r["name"] for r in con.execute("PRAGMA table_info(projects)")}
        for col in PROJECT_EXTRA_COLUMNS:
            if col not in existing_p:
                con.execute(f"ALTER TABLE projects ADD COLUMN {col} TEXT")
        con.commit()

    if scalar("SELECT COUNT(*) FROM users") == 0:
        demo_users = [
            ("admin", "admin123", "CVP Administrator", "Admin"),
            ("hr", "cvp123", "CVP HR User", "HR"),
            ("manager", "cvp123", "CVP Project Manager", "Manager"),
            ("accounts", "cvp123", "CVP Accounts User", "Accounts"),
        ]
        for username, password, full_name, role in demo_users:
            execute("INSERT INTO users(username,password_hash,full_name,role,active,created_at) VALUES(?,?,?,?,1,?)",
                    (username, hash_password(password), full_name, role, now_str()))
    if scalar("SELECT COUNT(*) FROM departments") == 0:
        for name in ["Management","Engineering","Projects","Quality","HR","Accounts","Administration","IT"]:
            execute("INSERT INTO departments(name,hod,created_at) VALUES(?,?,?)", (name, "", now_str()))

init_db()

# ---------------------------- Helpers ----------------------------
def audit(action, module, record_ref="", details=""):
    username = st.session_state.get("username", "system")
    execute("INSERT INTO audit_log(timestamp,username,action,module,record_ref,details) VALUES(?,?,?,?,?,?)",
            (now_str(), username, action, module, str(record_ref), details))

def status_from_expiry(expiry_date, reminder_days=30):
    if not expiry_date:
        return "Active"
    try:
        exp = datetime.strptime(str(expiry_date)[:10], "%Y-%m-%d").date()
    except Exception:
        return "Active"
    delta = (exp - date.today()).days
    if delta < 0:
        return "Expired"
    if delta <= int(reminder_days or 30):
        return "Expiring Soon"
    return "Active"

def days_to(expiry_date):
    try:
        exp = datetime.strptime(str(expiry_date)[:10], "%Y-%m-%d").date()
        return (exp - date.today()).days
    except Exception:
        return None

def next_doc_no():
    year = date.today().year
    n = scalar("SELECT COUNT(*) FROM documents WHERE doc_no LIKE ?", (f"CVP-DOC-{year}-%",)) + 1
    return f"CVP-DOC-{year}-{n:04d}"

def next_record_no(prefix, table, field):
    year = date.today().year
    n = scalar(f"SELECT COUNT(*) FROM {table} WHERE {field} LIKE ?", (f"CVP-{prefix}-{year}-%",)) + 1
    return f"CVP-{prefix}-{year}-{n:04d}"

def save_uploaded_file(uploaded, folder: Path, prefix=""):
    if uploaded is None:
        return "", ""
    folder.mkdir(parents=True, exist_ok=True)
    safe = "".join(c for c in uploaded.name if c.isalnum() or c in "._-")
    fname = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{safe}" if prefix else f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{safe}"
    path = folder / fname
    path.write_bytes(uploaded.getbuffer())
    return uploaded.name, str(path)

def file_download_button(label, filepath, key):
    if filepath and Path(filepath).exists():
        data = Path(filepath).read_bytes()
        st.download_button(label, data=data, file_name=Path(filepath).name, key=key)

def create_qr_png(text_value):
    img = qrcode.make(text_value)
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()

def make_backup():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = BACKUP_DIR / f"CVP_DMS_Backup_{ts}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        if DB_PATH.exists(): z.write(DB_PATH, f"data/{DB_PATH.name}")
        for base in [UPLOAD_DIR, ARCHIVE_DIR]:
            for p in base.rglob("*"):
                if p.is_file(): z.write(p, p.relative_to(BASE_DIR))
    return out

def build_pdf_report(title, df, all_columns=False):
    from io import BytesIO
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    logo = BASE_DIR / "assets" / "logo.png"
    skip = ("path", "hash", "password")
    df = df[[c for c in df.columns if not any(s in c.lower() for s in skip)]]
    if not all_columns: df = df.iloc[:, :9]
    else: df = df.loc[:, [i < 2 or df[c].replace("", pd.NA).notna().any() for i, c in enumerate(df.columns)]]
    def on_page(canvas, doc):
        w, h = doc.pagesize
        if logo.exists():
            canvas.saveState(); canvas.setFillAlpha(0.22)
            canvas.drawImage(str(logo), w / 2 - 75 * mm, h / 2 - 83 * mm, 150 * mm, 166 * mm, mask="auto", preserveAspectRatio=True)
            canvas.restoreState()
        canvas.setFont("Helvetica", 7); canvas.setFillColor(colors.grey)
        canvas.drawRightString(w - 12 * mm, 8 * mm, f"Page {doc.page}")
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=14 * mm, rightMargin=14 * mm, topMargin=16 * mm, bottomMargin=14 * mm)
    ss = getSampleStyleSheet()
    ink = colors.HexColor("#1a1a1a"); line = colors.HexColor("#8aa4c4"); head_bg = colors.HexColor("#d3e4f1")
    today = date.today(); fy = today.year if today.month >= 4 else today.year - 1
    cell = ParagraphStyle("cell", parent=ss["BodyText"], fontName="Helvetica", fontSize=7, leading=9, textColor=ink)
    cell_r = ParagraphStyle("cell_r", parent=cell, alignment=2)
    head = ParagraphStyle("head", parent=cell, fontName="Helvetica-Bold")
    head_r = ParagraphStyle("head_r", parent=head, alignment=2)
    story = [Paragraph(f"{escape(title)} Report — FY {fy}-{str(fy + 1)[-2:]}", ParagraphStyle("t", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=14, alignment=0, textColor=ink, spaceAfter=10))]
    # With all_columns, wide tables are split into column groups; the first two columns repeat in each group.
    keys = list(df.columns[:2]) if all_columns else []
    rest = [c for c in df.columns if c not in keys]
    size = 7 if all_columns else len(rest) or 1
    groups = [keys + rest[i:i + size] for i in range(0, len(rest), size)] or [keys]
    avail = landscape(A4)[0] - 28 * mm
    for g, cols in enumerate(groups, start=1):
        part = df[cols]
        numeric = [pd.api.types.is_numeric_dtype(part[c]) for c in part.columns]
        label = f"{g}. {escape(title)}" + (f" — Part {g} of {len(groups)}" if len(groups) > 1 else "")
        story.append(Paragraph(label, ParagraphStyle("sec", parent=ss["Normal"], fontName="Helvetica-BoldOblique", fontSize=9, spaceBefore=8 if g > 1 else 0, spaceAfter=2, textColor=ink)))
        rows = [[Paragraph(escape(str(c)), head_r if n else head) for c, n in zip(part.columns, numeric)]]
        rows += [[Paragraph(escape("" if pd.isna(v) else str(v)), cell_r if n else cell) for v, n in zip(r, numeric)] for r in part.itertuples(index=False)]
        if len(rows) == 1: rows.append([Paragraph("No records.", cell)] + [""] * (len(part.columns) - 1))
        tbl = Table(rows, repeatRows=1, colWidths=[avail / len(part.columns)] * len(part.columns) if all_columns else None)
        tbl.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), head_bg),
                                 ("BOX", (0, 0), (-1, -1), 0.5, line), ("INNERGRID", (0, 0), (-1, -1), 0.4, line),
                                 ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                                 ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        story.append(tbl)
        if g < len(groups): story.append(PageBreak())
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return buf.getvalue()
def build_salary_slip_pdf(emp, sal):
    """Monthly salary slip (A4) for one employee/month. `emp` and `sal` are dicts."""
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from calendar import month_name

    def g(d, k, default="-"):
        v = d.get(k)
        return default if v is None or str(v).strip() == "" else str(v)

    def amt(k):
        try: return float(sal.get(k) or 0)
        except (TypeError, ValueError): return 0.0

    def rs(x): return f"Rs. {x:,.2f}"

    try:
        y, m = str(sal["salary_month"]).split("-"); period = f"{month_name[int(m)]} {y}"
    except Exception:
        period = str(sal.get("salary_month", ""))

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=16*mm, rightMargin=16*mm, topMargin=14*mm, bottomMargin=14*mm,
                            title=f"Salary Slip - {g(emp, 'name')} - {period}")
    ss = getSampleStyleSheet()
    teal = colors.HexColor("#17776f"); ink = colors.HexColor("#17313d")
    h = ParagraphStyle("h", parent=ss["Title"], fontSize=16, textColor=ink, spaceAfter=2, alignment=1)
    sub = ParagraphStyle("s", parent=ss["Normal"], fontSize=9, textColor=colors.HexColor("#586f79"), alignment=1)
    cell = ParagraphStyle("c", parent=ss["Normal"], fontSize=9, textColor=ink)
    story = []
    logo = BASE_DIR / "assets" / "logo.png"
    if logo.exists():
        story.append(Image(str(logo), width=18*mm, height=18*mm, hAlign="CENTER"))
    story += [Paragraph("C. V. Patil &amp; Associates", h), Paragraph(f"Salary Slip for {period}", sub), Spacer(1, 6*mm)]

    info = [
        ["Employee Code", g(emp, "employee_code"), "Employee Name", g(emp, "name")],
        ["Department", g(emp, "department"), "Designation", g(emp, "designation")],
        ["Date of Joining", g(emp, "joining_date"), "Salary Month", period],
        ["Bank", g(emp, "bank_name"), "Account No.", g(emp, "account_number")],
        ["PAN", g(emp, "pan"), "UAN / PF No.", f"{g(emp, 'uan')} / {g(emp, 'pf_number')}"],
    ]
    t = Table(info, colWidths=[32*mm, 52*mm, 32*mm, 52*mm])
    t.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), 9), ("TEXTCOLOR", (0, 0), (-1, -1), ink),
                           ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                           ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#c9d8dc")),
                           ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dde7ea")),
                           ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef6f5")), ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#eef6f5")),
                           ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    story += [t, Spacer(1, 6*mm)]

    earn = [("Basic", amt("basic")), ("HRA", amt("hra")), ("Allowances", amt("allowances")), ("Bonus", amt("bonus"))]
    ded = [("Provident Fund", amt("pf")), ("Tax", amt("tax")), ("Other Deductions", amt("other_deductions"))]
    rows = [["Earnings", "Amount", "Deductions", "Amount"]]
    for i in range(max(len(earn), len(ded))):
        e = earn[i] if i < len(earn) else ("", None); d = ded[i] if i < len(ded) else ("", None)
        rows.append([e[0], rs(e[1]) if e[1] is not None else "", d[0], rs(d[1]) if d[1] is not None else ""])
    gross = amt("gross") or sum(v for _, v in earn); deductions = amt("deductions") or sum(v for _, v in ded)
    rows.append(["Gross Earnings", rs(gross), "Total Deductions", rs(deductions)])
    s = Table(rows, colWidths=[42*mm, 40*mm, 42*mm, 40*mm])
    s.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), teal), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                           ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9),
                           ("ALIGN", (1, 0), (1, -1), "RIGHT"), ("ALIGN", (3, 0), (3, -1), "RIGHT"),
                           ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"), ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#eef6f5")),
                           ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#c9d8dc")),
                           ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dde7ea")),
                           ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story += [s, Spacer(1, 5*mm)]
    net = amt("net") or (gross - deductions)
    n = Table([["Net Salary Payable", rs(net)]], colWidths=[84*mm, 80*mm])
    n.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ink), ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                           ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 12),
                           ("ALIGN", (1, 0), (1, 0), "RIGHT"), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    story += [n, Spacer(1, 8*mm)]
    # Signature and stamp area is left blank on purpose: signed and stamped by hand after printing
    sig = Table([["", "", ""], ["Employee Signature", "Company Stamp", "Authorised Signatory"]],
                colWidths=[56*mm, 52*mm, 56*mm], rowHeights=[32*mm, 7*mm])
    sig.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), 9), ("TEXTCOLOR", (0, 0), (-1, -1), ink),
                             ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, 0), "BOTTOM"),
                             ("LINEABOVE", (0, 1), (0, 1), 0.6, ink), ("LINEABOVE", (2, 1), (2, 1), 0.6, ink),
                             ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold")]))
    story.append(sig)
    doc.build(story)
    return buf.getvalue()

def build_employee_form_pdf(emp):
    """Fill the C. V. Patil & Associates employee form (2 pages) from an employee record."""
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader, simpleSplit
    from reportlab.pdfgen import canvas as rl_canvas

    def val(key):
        v = emp.get(key)
        return "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v).strip()

    def rows_of(key):
        try: data = json.loads(val(key) or "[]")
        except ValueError: data = []
        return data if isinstance(data, list) else []

    parts = val("name").split()
    surname = val("surname") or (parts[-1] if len(parts) > 1 else "")
    first = val("first_name") or (parts[0] if parts else "")
    dob = val("dob")
    try: dob = datetime.strptime(dob[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError: pass
    joining = val("joining_date")
    try: joining = datetime.strptime(joining[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError: pass

    W, H = A4
    logo = BASE_DIR / "assets" / "logo.png"
    buf = BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"Employee Form - {val('name')}")

    def header():
        if logo.exists():
            c.saveState(); c.setFillAlpha(0.06)
            c.drawImage(str(logo), W / 2 - 150, H / 2 - 165, 300, 330, mask="auto", preserveAspectRatio=True)
            c.restoreState()
            c.drawImage(str(logo), 34, H - 86, 58, 58, mask="auto", preserveAspectRatio=True, anchor="sw")
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Times-Bold", 13); c.drawString(218, H - 52, "C. V. PATIL & ASSOCIATES,")
        c.setFont("Helvetica", 7.6); c.drawString(160, H - 66, "1002, Trident Business Centre, Oppo. Audi Showroom,Mumbai-Pune Highway,Baner, Pune-411045")
        c.setLineWidth(0.8); c.line(28, H - 90, W - 28, H - 90)

    def field(x, y, label, value, x_end):
        c.setFont("Helvetica-Bold", 8.5); c.drawString(x, y, label)
        lw = c.stringWidth(label, "Helvetica-Bold", 8.5) + 4
        c.setLineWidth(0.5); c.line(x + lw, y - 2, x_end, y - 2)
        c.setFont("Helvetica", 8.5); c.drawString(x + lw + 3, y, value[:int((x_end - x - lw) / 4.3)])

    def lines(x, y, label, value, x_end, count=2, gap=22):
        c.setFont("Helvetica-Bold", 8.5); c.drawString(x, y, label)
        lw = c.stringWidth(label, "Helvetica-Bold", 8.5) + 4
        wrapped = simpleSplit(value, "Helvetica", 8.5, x_end - x - lw - 6) if value else []
        for i in range(count):
            yy = y - i * gap
            c.setLineWidth(0.5); c.line(x + lw if i == 0 else x, yy - 2, x_end, yy - 2)
            if i < len(wrapped):
                c.setFont("Helvetica", 8.5); c.drawString((x + lw if i == 0 else x) + 3, yy, wrapped[i])

    def grid(x, y_top, widths, header_row, body, row_h=19):
        total = sum(widths); n = len(body) + 1
        c.setLineWidth(0.6); c.rect(x, y_top - n * row_h, total, n * row_h)
        for i in range(1, n): c.line(x, y_top - i * row_h, x + total, y_top - i * row_h)
        cx = x
        for w in widths[:-1]:
            cx += w; c.line(cx, y_top, cx, y_top - n * row_h)
        for r, cells in enumerate([header_row] + body):
            cx = x
            for w, text in zip(widths, cells):
                c.setFont("Helvetica" if r else "Helvetica", 7.5)
                c.drawString(cx + 4, y_top - r * row_h - 13, str(text)[:int(w / 3.9)])
                cx += w

    # ---------------- Page 1 ----------------
    header()
    c.setFont("Helvetica-Bold", 14); title = "EMPLOYEE FORM"
    c.drawCentredString(W / 2 - 40, H - 128, title)
    tw = c.stringWidth(title, "Helvetica-Bold", 14)
    c.setLineWidth(1); c.line(W / 2 - 40 - tw / 2, H - 131, W / 2 + tw / 2 - 40, H - 131)
    px, py, pw, ph = W - 28 - 99, H - 112 - 127, 99, 127
    c.setLineWidth(0.7); c.rect(px, py, pw, ph)
    photo = val("photo_path")
    if photo and Path(photo).exists():
        try: c.drawImage(ImageReader(photo), px + 1, py + 1, pw - 2, ph - 2, preserveAspectRatio=True, anchor="c")
        except Exception: photo = ""
    if not (photo and Path(photo).exists()):
        c.setFont("Helvetica", 6.5)
        for i, t_ in enumerate(["Please paste a passport", "size (3.5cm x 4.5cm)", "colored photograph here"]):
            c.drawCentredString(px + pw / 2, py + ph / 2 + 8 - i * 9, t_)
    c.setFont("Helvetica-Bold", 8.5); c.drawCentredString(W / 2 - 20, H - 248, "(*** Marked are compulsory.)")

    y = H - 275
    c.setFont("Helvetica-Bold", 8.5); c.drawString(40, y, "1.. FULL NAME:")
    c.setLineWidth(0.5); c.line(140, y - 4, W - 38, y - 4)
    for x_, v_, cap in [(150, surname, "Surname"), (252, first, "First Name"), (368, val("father_name"), "Father Name"), (485, val("mother_name"), "Mother Name")]:
        c.setFont("Helvetica", 8.5); c.drawString(x_ - 8, y + 1, v_[:18])
        c.setFont("Helvetica", 8); c.drawCentredString(x_ + 14, y - 14, cap)
    y -= 42
    field(40, y, "2.. Date of Birth:", dob, 215); field(300, y, "3.. Gender:", val("gender"), W - 38)
    y -= 28; field(40, y, "4.. Marital Status:", val("marital_status"), 215)
    y -= 32; lines(40, y, "5.. Permanent Address***:", val("permanent_address"), W - 38)
    y -= 50; lines(40, y, "6.. Local Address***:", val("local_address"), W - 38)
    y -= 50; field(40, y, "7.. Tel. Phone No.:", val("telephone"), 300); field(330, y, "8.. Cell No***.:", val("mobile"), W - 38)
    y -= 28; field(40, y, "9.. E-mail Address:", val("email"), 300)
    y -= 26; field(40, y, "10.. PAN Card No.:", val("pan"), 300)
    y -= 26; field(40, y, "11.. Aadhar Card No.:", val("aadhar"), 300)
    y -= 24; c.setFont("Helvetica-Bold", 8.5); c.drawString(40, y, "12.. Educational Qualification:")
    edu = rows_of("education"); body = []
    for i, deg in enumerate(["Post Graduation", "Graduation", "HSC / Diploma"]):
        r = next((e for e in edu if isinstance(e, dict) and e.get("Degree") == deg), {})
        body.append([i + 1, deg, r.get("Specialization", ""), r.get("Year of Passing", ""), r.get("% Marks / Grade", "")])
    grid(32, y - 6, [44, 100, 130, 110, 140], ["Sr.No.", "Degree", "Specialization", "Year of Passing", "% Marks / Grade"], body, 21)
    y -= 6 + 4 * 21 + 26
    lines(40, y, "13.. Software Skills:", val("software_skills"), W - 38)
    c.showPage()

    # ---------------- Page 2 ----------------
    header()
    y = H - 125; c.setFont("Helvetica-Bold", 8.5); c.drawString(40, y, "14.. Family Details:")
    fam = rows_of("family_details"); body = []
    for i in range(4):
        r = fam[i] if i < len(fam) and isinstance(fam[i], dict) else {}
        body.append([i + 1, r.get("Family Member", ""), r.get("Relation with you", ""), r.get("Contact Number", "")])
    grid(32, y - 20, [60, 220, 140, 110], ["Sr. No.", "Family Member", "Relation with you", "Contact Number"], body, 20)
    y -= 20 + 5 * 20 + 28
    c.setFont("Helvetica-Bold", 8.5); c.drawString(40, y, "15.. Vehicle Details:")
    for i, (lab, key) in enumerate([("1. Vehicle Company Name:", "vehicle_company"), ("2. Vehicle No.:", "vehicle_no"), ("3. License No.:", "license_no")]):
        field(56, y - 20 - i * 20, lab, val(key), W - 38)
    y -= 20 + 3 * 20 + 14
    c.setFont("Helvetica-Bold", 8.5); c.drawString(40, y, "16.. Bank Details***:")
    for i, (lab, key) in enumerate([("1. Bank Name:", "bank_name"), ("2. Address of Bank .:", "bank_address"), ("3. Branch Name :", "bank_branch"),
                                    ("4. Account No.:", "account_number"), ("5. IFSC Code:", "ifsc")]):
        field(56, y - 20 - i * 20, lab, val(key), W - 38)
    y -= 20 + 5 * 20 + 18
    field(40, y, "17..Joining Date***:", joining, W - 38)
    y -= 30; c.setFont("Helvetica", 8.5); c.drawString(40, y, "Declaration,")
    y -= 20; c.drawString(40, y, "I hereby declare the information furnished by me is correct. I bear the responsibility for all above information.")
    y -= 60; c.setLineWidth(2); c.line(W - 215, y, W - 38, y)
    c.setFont("Helvetica-Oblique", 8.5); c.drawCentredString(W - 126, y + 5, val("name"))
    c.setFont("Helvetica", 8.5); c.drawCentredString(W - 126, y - 12, "Applicant's Name & Signature")
    y -= 36; c.setFont("Helvetica-Bold", 14); c.drawString(40, y, "Compulsory Required Documents -")
    c.setLineWidth(1); c.line(40, y - 3, 40 + c.stringWidth("Compulsory Required Documents -", "Helvetica-Bold", 14), y - 3)
    for i, (lab, key) in enumerate([("PAN Card Copy", "pan_doc_path"), ("Aadhar Card Copy", "aadhar_doc_path"),
                                    ("Bank Passbook-1st page Copy", "passbook_doc_path"), ("Photo Attach", "photo_path")]):
        c.setFont("Helvetica", 8.5)
        ok = val(key) and Path(val(key)).exists()
        c.drawString(56, y - 22 - i * 16, f"{i + 1}. {lab}" + ("   (Attached)" if ok else ""))
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(72, y - 22 - 4 * 16 - 2, "(Note for Soft Copy-Please Send you Document in printable format with proper naming i.e.")
    c.drawString(72, y - 22 - 4 * 16 - 14, "Your Name _Document name)")
    c.showPage(); c.save()
    return buf.getvalue()
def money(x):
    try: return f"₹{float(x):,.2f}"
    except: return "₹0.00"

def ui_logo_uri():
    """Logo for on-screen use: the tightly cropped copy (bigger emblem) when available, else the original."""
    f = BASE_DIR / "assets" / "logo_tight.png"
    if not f.exists(): f = BASE_DIR / "assets" / "logo.png"
    return "data:image/png;base64," + base64.b64encode(f.read_bytes()).decode("ascii")

def asset_b64(name):
    f = BASE_DIR / "assets" / name
    return "data:image/jpeg;base64," + base64.b64encode(f.read_bytes()).decode("ascii") if f.exists() else ""

def section_title(title, subtitle=""):
    st.markdown(
        f'<div class="cvp-page-heading"><div class="cvp-kicker">C. V. Patil &amp; Associates</div>'
        f'<div class="cvp-title">{escape(title)}</div></div>',
        unsafe_allow_html=True,
    )

# ---------------------------- Authentication ----------------------------
def artwork_uri():
    artwork = (BASE_DIR / "assets" / "workspace.svg").read_bytes()
    return "data:image/svg+xml;base64," + base64.b64encode(artwork).decode("ascii")


def login_view():
    def _uri(name, mime):
        f = BASE_DIR / "assets" / name
        return f"data:{mime};base64," + base64.b64encode(f.read_bytes()).decode("ascii") if f.exists() else ""
    bg, mark = _uri("login_bg.jpg", "image/jpeg"), _uri("cvp_mark.png", "image/png")
    user_ico = "data:image/svg+xml;utf8," + "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%230b5cc4'%3E%3Cpath d='M12 12a5 5 0 1 0 0-10 5 5 0 0 0 0 10zm0 2c-4.4 0-8 2.2-8 5v2h16v-2c0-2.8-3.6-5-8-5z'/%3E%3C/svg%3E"
    lock_ico = "data:image/svg+xml;utf8," + "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%230b5cc4'%3E%3Cpath d='M18 8h-1V6a5 5 0 0 0-10 0v2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2zM9 6a3 3 0 0 1 6 0v2H9V6zm3 11a2 2 0 1 1 0-4 2 2 0 0 1 0 4z'/%3E%3C/svg%3E"
    st.markdown(f"""<style>
    html,body,.stApp{{background:#cfe6fb!important;animation:none!important}}
    .stApp::before,.stApp::after{{display:none!important}}
    section[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"]{{display:none!important}}
    [data-testid="stHeader"]{{background:transparent}}
    .lg-bg{{position:fixed;inset:0;z-index:0;background:#cfe6fb url("{bg}") center/cover no-repeat;filter:saturate(1.15) brightness(1.12) blur(1.5px);transform:scale(1.03)}}
    .lg-bg-glow{{position:fixed;inset:0;z-index:0;background:radial-gradient(ellipse 60% 45% at 50% 14%,#ffffffd9,#ffffff00 70%),linear-gradient(180deg,#ffffff40,#ffffff00 45%)}}
    .block-container{{position:fixed!important;left:max(4vw,calc(50vw - 240px));top:max(.6rem,calc(50vh - 345px));max-width:none!important;width:min(480px,92vw);margin:0!important;padding:0!important;z-index:1}}
    [data-testid="stMain"] [data-testid="stVerticalBlock"]{{gap:.55rem}}
    .lg-top{{position:relative;z-index:2;text-align:center;margin-bottom:26px}}
    .lg-mark{{height:62px;width:auto;display:block;margin:0 auto}}
    .lg-name{{font-size:1.32rem;font-weight:800;letter-spacing:.01em;color:#0b2f73!important;margin-top:10px;line-height:1.1}}
    .lg-addr{{font-size:.78rem;font-weight:600;color:#1d4560!important;margin-top:8px;line-height:1.45}}
    .lg-name-line{{width:44px;height:2px;background:#1a7fd8;margin:8px auto}}
    .lg-tag{{font-size:.7rem;letter-spacing:.1em;color:#2b4366!important}}
    div[data-testid="stForm"]{{position:relative;z-index:2;background:#ffffff55;backdrop-filter:blur(16px) saturate(1.2);-webkit-backdrop-filter:blur(16px) saturate(1.2);
        border:1px solid #ffffffb0;border-radius:26px;padding:26px 30px 24px;box-shadow:0 24px 60px #1a4f9a30}}
    div[data-testid="stForm"] [data-testid="stVerticalBlock"]{{gap:.6rem}}
    .lg-welcome{{text-align:center;font-size:1.75rem;font-weight:850;letter-spacing:-.02em;color:#0b2f73!important;margin:0}}
    .lg-sub{{text-align:center;font-size:.9rem;color:#3a5073!important;margin:2px 0 10px}}
    div[data-testid="stForm"] [data-testid="stTextInput"] [data-testid="stWidgetLabel"]{{display:none}}
    div[data-testid="stForm"] [data-testid="stCheckbox"] label>div:first-of-type{{background:#fff!important;border:1.5px solid #7fa6d8!important;border-radius:4px}}
    div[data-testid="stForm"] [data-testid="stTextInputRootElement"]{{background:#fff!important;border:0!important;border-radius:10px!important;box-shadow:0 3px 10px #1a4f9a1a;overflow:hidden}}
    div[data-testid="stForm"] [data-testid="stTextInputRootElement"] *{{background-color:#fff!important;color:#5d7480}}
    div[data-testid="stForm"] input{{color:#17313d!important;-webkit-text-fill-color:#17313d!important;padding:.85rem .9rem .85rem 2.9rem!important;font-size:.98rem}}
    div[data-testid="stForm"] input::placeholder{{color:#6b7c8d!important;-webkit-text-fill-color:#6b7c8d!important}}
    div[data-testid="stForm"] .st-key-lg_user [data-testid="stTextInputRootElement"]{{background:#fff url("{user_ico}") 14px center/20px no-repeat!important}}
    div[data-testid="stForm"] .st-key-lg_pass [data-testid="stTextInputRootElement"]{{background:#fff url("{lock_ico}") 14px center/20px no-repeat!important}}
    div[data-testid="stForm"] .st-key-lg_user [data-testid="stTextInputRootElement"] *,div[data-testid="stForm"] .st-key-lg_pass [data-testid="stTextInputRootElement"] *{{background-color:transparent!important}}
    div[data-testid="stForm"] [data-testid="stCheckbox"] p{{color:#0b2f73!important;font-weight:600;font-size:.88rem}}
    .lg-forgot{{text-align:right;font-size:.88rem;font-weight:700;color:#0b5cc4;padding-top:.2rem}}
    div[data-testid="stForm"] .stFormSubmitButton button{{background:linear-gradient(90deg,#0b4fb0,#1a8fe0)!important;border:0!important;border-radius:10px;min-height:3.1rem;font-size:1.05rem;font-weight:700;box-shadow:0 10px 22px #0b4fb055;transition:transform .15s}}
    div[data-testid="stForm"] .stFormSubmitButton button *{{color:#fff!important}}
    div[data-testid="stForm"] .stFormSubmitButton button:hover{{transform:translateY(-2px);background:linear-gradient(90deg,#093f90,#1380cc)!important}}
    .lg-foot{{display:none}}
    </style><div class="lg-bg"></div><div class="lg-bg-glow"></div>""", unsafe_allow_html=True)
    st.markdown(
        f'<div class="lg-top"><img class="lg-mark" src="{mark}" alt="CVP">'
        '<div class="lg-name">C. V. PATIL &amp; ASSOCIATES</div>'
        '<div class="lg-addr">1002, Trident Business Centre, Oppo. Audi Showroom,<br>Mumbai-Pune Highway, Baner, Pune-411045</div></div>',
        unsafe_allow_html=True)
    with st.form("login_form"):
        st.markdown('<div class="lg-welcome">Welcome</div><div class="lg-sub">Login to your account to continue</div>', unsafe_allow_html=True)
        username = st.text_input("Username", placeholder="Username", key="lg_user")
        password = st.text_input("Password", type="password", placeholder="Password", key="lg_pass")
        r1, r2 = st.columns([1, 1])
        r1.checkbox("Remember me", key="lg_remember")
        r2.markdown('<div class="lg-forgot" title="Please contact your administrator">Forget password?</div>', unsafe_allow_html=True)
        submit = st.form_submit_button("Login  →", use_container_width=True)
    if submit:
        clean_username = username.strip()
        row = df_query("SELECT * FROM users WHERE username=? AND active=1", (clean_username,))
        if not row.empty and row.iloc[0]["password_hash"] == hash_password(password):
            st.session_state.auth = True
            st.session_state.username = clean_username
            st.session_state.full_name = row.iloc[0]["full_name"]
            st.session_state.role = row.iloc[0]["role"]
            audit("LOGIN", "Security", clean_username, "Successful login")
            st.query_params["s"] = create_login_token(clean_username)
            st.rerun()
        else:
            execute("INSERT INTO audit_log(timestamp,username,action,module,record_ref,details) VALUES(?,?,?,?,?,?)",
                    (now_str(), clean_username or "(blank)", "LOGIN_FAILED", "Security", clean_username, "Invalid username or password"))
            st.error("Invalid username or password.")


# ---------------------------- Keep users signed in across browser refresh ----------------------------
import secrets
SESSION_HOURS = 12
execute("CREATE TABLE IF NOT EXISTS login_sessions (token TEXT PRIMARY KEY, username TEXT, created_at TEXT, expires_at TEXT)")

def create_login_token(username):
    token = secrets.token_urlsafe(24)
    execute("INSERT INTO login_sessions(token,username,created_at,expires_at) VALUES(?,?,?,?)",
            (token, username, now_str(), (datetime.now() + timedelta(hours=SESSION_HOURS)).strftime("%Y-%m-%d %H:%M:%S")))
    return token

def restore_login_from_url():
    token = st.query_params.get("s")
    if not token:
        return False
    row = df_query("""SELECT u.username,u.full_name,u.role FROM login_sessions s JOIN users u ON u.username=s.username
                      WHERE s.token=? AND s.expires_at>? AND u.active=1""", (token, now_str()))
    if row.empty:
        st.query_params.pop("s", None)
        return False
    st.session_state.auth = True
    st.session_state.username = row.iloc[0]["username"]
    st.session_state.full_name = row.iloc[0]["full_name"]
    st.session_state.role = row.iloc[0]["role"]
    return True

# Require authentication before rendering any company data.
if not st.session_state.get("auth"):
    restore_login_from_url()
if not st.session_state.get("auth"):
    login_view()
    st.stop()

ROLE = st.session_state.get("role", "Employee")
USER = st.session_state.get("username", "")
FULL_NAME = st.session_state.get("full_name", USER or "User")

# ---------------------------- Sidebar navigation ----------------------------
all_pages = [
    "Dashboard", "Documents", "Approvals", "Employees", "Projects", "Insurance",
    "Contracts", "Salary", "Accounts", "Plant Drawings",
    "Recycle Bin", "Administration"
]
role_pages = {
    "Admin": all_pages,
    "HR": ["Dashboard","Documents","Approvals","Employees","Insurance","Salary"],
    "Manager": ["Dashboard","Documents","Approvals","Projects","Insurance","Contracts","Plant Drawings"],
    "Accounts": ["Dashboard","Documents","Approvals","Insurance","Contracts","Salary","Accounts"],
    "Employee": ["Dashboard","Documents","Approvals"]
}
page_icons = {
    "Dashboard":"▦", "Documents":"▤", "Approvals":"✓", "Employees":"♙", "Projects":"◇",
    "Insurance":"◈", "Contracts":"▧", "Salary":"₹", "Accounts":"◉",
    "Plant Drawings":"⬡", "Recycle Bin":"♲", "Administration":"⚙"
}
ACCESS_ROLES = ["HR", "Manager", "Accounts", "Employee"]
execute("""CREATE TABLE IF NOT EXISTS plant_drawings (
    id INTEGER PRIMARY KEY AUTOINCREMENT, drawing_no TEXT UNIQUE NOT NULL, title TEXT NOT NULL, project_code TEXT,
    plant_area TEXT, discipline TEXT, drawing_type TEXT, revision TEXT, status TEXT, scale TEXT, sheet_size TEXT,
    prepared_by TEXT, checked_by TEXT, approved_by TEXT, issue_date TEXT, remarks TEXT, filename TEXT, filepath TEXT,
    is_deleted INTEGER DEFAULT 0, created_by TEXT, created_at TEXT, updated_at TEXT)""")
execute("""CREATE TABLE IF NOT EXISTS plant_drawing_revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT, drawing_id INTEGER, revision TEXT, filename TEXT, filepath TEXT,
    note TEXT, changed_by TEXT, changed_at TEXT)""")
execute("""CREATE TABLE IF NOT EXISTS project_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT, project_code TEXT, request_type TEXT, subject TEXT, details TEXT,
    requested_by TEXT, requested_role TEXT, status TEXT DEFAULT 'Pending', admin_reply TEXT, decided_by TEXT, decided_at TEXT, created_at TEXT)""")
execute("CREATE TABLE IF NOT EXISTS role_page_access (role TEXT NOT NULL, page TEXT NOT NULL, PRIMARY KEY(role, page))")

def pages_for_role(role):
    """Admin-granted pages if the Admin customised this role, otherwise the built-in defaults."""
    if role == "Admin":
        return all_pages
    custom = df_query("SELECT page FROM role_page_access WHERE role=?", (role,))["page"].tolist()
    if custom:
        return [p for p in all_pages if p in custom or p == "Dashboard"]
    return role_pages.get(role, role_pages["Employee"])

available_pages = pages_for_role(ROLE)
display_to_page = {f"{page_icons.get(name, '•')}  {name}": name for name in available_pages}

with st.sidebar:
    _side_logo = ui_logo_uri()
    st.markdown(
        '<div class="sidebar-brand-card"><div class="sidebar-brand-row">'
        f'<img class="sidebar-brand-logo" src="{_side_logo}" alt="logo">'
        '<div><div class="sidebar-brand-title">C. V. Patil<br>&amp; Associates</div>'
        '</div></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sidebar-section-label">Workspace</div>', unsafe_allow_html=True)
    if "side_nav" not in st.session_state:
        _want = st.query_params.get("p")
        if _want in available_pages:
            st.session_state["side_nav"] = nav_label(_want) if "nav_label" in globals() else next(k for k, v in display_to_page.items() if v == _want)
    selected_label = st.radio("Navigation", list(display_to_page.keys()), key="side_nav", label_visibility="collapsed")
    page = display_to_page[selected_label]
    if st.query_params.get("p") != page:
        st.query_params["p"] = page

# ---------------------------- Plant photo behind the dashboard banner ----------------------------
_hero_bg = BASE_DIR / "assets" / "login_bg.jpg"
if _hero_bg.exists():
    _hero_uri = "data:image/jpeg;base64," + base64.b64encode(_hero_bg.read_bytes()).decode("ascii")
    st.markdown(f"""<style>
    .stApp{{background:linear-gradient(135deg,#0a2f3ad9 0%,#0f4f58c7 55%,#12696fb3 100%),url("{_hero_uri}") center/cover no-repeat fixed!important}}
    section[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label div:has(+ [data-testid="stMarkdownContainer"]){{display:none!important}}
    section[data-testid="stSidebar"]{{background:linear-gradient(180deg,#0b1d24eb 0%,#0e2a33d1 50%,#0b1d24eb 100%),url("{_hero_uri}") 62% center/cover no-repeat!important}}
    /* banner uses the same fixed photo + tint as the page, so it merges with the background */
    .cvp-hero{{background:linear-gradient(90deg,#0a2f3a99 0%,#0a2f3a00 62%),linear-gradient(135deg,#0a2f3ad9 0%,#0f4f58c7 55%,#12696fb3 100%),url("{_hero_uri}") center/cover no-repeat!important;background-attachment:scroll,fixed,fixed!important;
        min-height:190px;box-shadow:none!important;border:1px solid #ffffff26}}
    .cvp-hero::before,.cvp-hero::after{{display:none}}
    .cvp-hero-title,.cvp-hero-kicker,.cvp-hero-sub{{text-shadow:0 2px 10px #00000066}}
    </style>""", unsafe_allow_html=True)

# ---------------------------- Glass tables over the photo ----------------------------
st.markdown("""<style>
div[data-testid="stDataFrame"]{background:#0a2f3a8c!important;backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);border:1px solid #ffffff3d!important;border-radius:14px!important;box-shadow:0 8px 24px #00000040;overflow:hidden}
/* page-level search / filter boxes: same teal glass look as the dropdowns (forms, expanders and the top search keep their own styles) */
:where([data-testid="stMain"]) :where([data-testid="stTextInput"]) [data-testid="stTextInputRootElement"],
:where([data-testid="stMain"]) :where([data-testid="stNumberInput"]) [data-testid="stNumberInputContainer"],
:where([data-testid="stMain"]) :where([data-testid="stDateInput"]) [data-baseweb="input"]{background:#0f4f58b3!important;border:1px solid #ffffff3d!important;border-radius:9px!important;backdrop-filter:blur(6px)}
:where([data-testid="stMain"]) :where([data-testid="stTextInput"]) input,:where([data-testid="stMain"]) :where([data-testid="stNumberInput"]) input,:where([data-testid="stMain"]) :where([data-testid="stDateInput"]) input{background:transparent!important;color:#fff!important;-webkit-text-fill-color:#fff!important}
:where([data-testid="stMain"]) :where([data-testid="stTextInput"]) input::placeholder{color:#cfe6e6!important;-webkit-text-fill-color:#cfe6e6!important}
:where([data-testid="stMain"]) :where([data-baseweb="select"]) > div{background:#0f4f58b3!important;border:1px solid #ffffff3d!important;border-radius:9px!important}
.pj-card{background:#fff;border:1px solid #dde7ea;border-radius:12px 12px 0 0;overflow:hidden;box-shadow:0 6px 18px #00000030}
.pj-img{height:130px;background-size:cover;background-position:center}
.pj-body{padding:12px 14px 12px}.pj-head{display:flex;justify-content:space-between;gap:8px;align-items:flex-start}
.pj-name{font-size:.92rem;font-weight:800;color:#17313d!important}.pj-client{font-size:.74rem;color:#5d7480!important;margin-top:2px}.pj-loc{font-size:.72rem;color:#5d7480!important;margin-top:2px}
.pj-pill{padding:2px 10px;border-radius:6px;font-size:.68rem;font-weight:700;white-space:nowrap}
.pj-pill.green{background:#dff5ea;color:#1e8a55!important}.pj-pill.blue{background:#e1effc;color:#1f6fc2!important}.pj-pill.red{background:#fde4e3;color:#c8393e!important}.pj-pill.teal{background:#dff3f7;color:#0d7a9c!important}.pj-pill.grey{background:#eceff3;color:#5d6e80!important}
.pj-bar{height:6px;border-radius:99px;background:#e3ebf0;margin:10px 0 2px;overflow:hidden}.pj-bar i{display:block;height:100%;background:linear-gradient(90deg,#0f9d7a,#1aa3c8)}
.pj-pct{text-align:right;font-size:.72rem;font-weight:700;color:#17313d!important}
.pj-stats{display:grid;grid-template-columns:repeat(4,1fr);text-align:center;gap:4px;margin-top:6px}
.pj-stats span{display:block;font-size:.62rem;color:#6f828b!important}.pj-stats b{display:block;font-size:.95rem;color:#17313d!important}.pj-stats .pend b{color:#d9822b!important}.pj-stats .over b{color:#d1383e!important}
[data-testid="stColumn"]:has([class*="st-key-pj_open_"]){position:relative;margin-bottom:.4rem}
[class*="st-key-pj_open_"]{position:absolute!important;inset:0;width:100%!important;height:100%!important;z-index:5;margin:0!important}
[class*="st-key-pj_open_"] [data-testid="stButton"],[class*="st-key-pj_open_"] [data-testid="stButton"] > div{height:100%!important;width:100%!important}
[class*="st-key-pj_open_"] button{width:100%;height:100%!important;min-height:100%!important;opacity:0;cursor:pointer;border:0}
[data-testid="stColumn"]:has([class*="st-key-pj_open_"]):hover .pj-card{transform:translateY(-4px);box-shadow:0 14px 30px #00000055}
.pj-card{transition:transform .15s,box-shadow .15s;border-radius:12px!important}
.pj-open{text-align:center;border-top:1px solid #e7eef1;margin-top:10px;padding-top:9px;font-size:.78rem;font-weight:700;color:#0d6a9a!important}
.pj-detail-hero{position:relative;height:210px;border-radius:14px;overflow:hidden;background-size:cover;background-position:center;box-shadow:0 8px 24px #00000040;margin-bottom:14px}
.pj-detail-hero::after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,#0a2f3acc,#0a2f3a22)}
.pj-detail-info{position:absolute;left:22px;bottom:18px;z-index:2;color:#fff}
.pj-detail-info h2{margin:0;font-size:1.6rem;color:#fff!important}.pj-detail-info div{font-size:.85rem;color:#e6f4f4!important;margin-top:3px}
/* file uploader: white text so Upload / size hint are readable on the teal box */
[data-testid="stFileUploader"] section,[data-testid="stFileUploaderDropzone"]{background:#0f4f58b3!important}
[data-testid="stFileUploader"] *,[data-testid="stFileUploaderDropzone"] *{color:#fff!important;-webkit-text-fill-color:#fff!important}
[data-testid="stFileUploader"] svg,[data-testid="stFileUploaderDropzone"] svg{fill:#fff!important}
[data-testid="stFileUploader"] button{background:#17776f!important;border:1px solid #ffffff66!important}
/* Approvals: compact spacing */
.st-key-appr_wrap [data-testid="stVerticalBlock"]{gap:.5rem}
[data-testid="stTabsContent"] [data-testid="stCaptionContainer"]{margin:0}
[data-testid="stTabsContent"] .panel-title{margin:2px 0 6px}
/* collapsible glass sections on the dashboard */
[class*="st-key-gx_"] [data-testid="stExpander"] details{background:#0a2f3a59!important;backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);border:1px solid #ffffff38!important;border-radius:14px!important;box-shadow:0 8px 24px #00000030}
[data-testid="stMain"] [class*="st-key-gx_"] [data-testid="stExpander"] summary,[data-testid="stMain"] [class*="st-key-gx_"] [data-testid="stExpander"] summary *,[data-testid="stMain"] [class*="st-key-gx_"] [data-testid="stExpander"] summary [data-testid="stMarkdownContainer"] p{color:#fff!important;font-weight:800;font-size:.92rem}
[class*="st-key-gx_"] [data-testid="stExpander"] svg{fill:#fff!important;color:#fff!important}
[class*="st-key-gx_"] [data-testid="stExpander"] [data-testid="stDataFrame"]{border:0!important;box-shadow:none;background:transparent!important}
[class*="st-key-gx_"] .dn-legend,[class*="st-key-gx_"] .dn-legend *,[class*="st-key-gx_"] .dn-ring span,[class*="st-key-gx_"] .dn-ring small,[class*="st-key-gx_"] [data-testid="stCaptionContainer"] *{color:#fff!important}
/* inputs inside white form / expander cards stay white with dark text */
div[data-testid="stForm"] [data-baseweb="select"] > div,div[data-testid="stForm"] [data-baseweb="input"],div[data-testid="stForm"] [data-baseweb="base-input"],
[data-testid="stExpander"] [data-baseweb="select"] > div,[data-testid="stExpander"] [data-baseweb="input"],[data-testid="stExpander"] [data-baseweb="base-input"]{background:#fff!important;color:#17313d!important;border-color:#cfdde1!important}
div[data-testid="stForm"] [data-baseweb="select"] *,[data-testid="stExpander"] [data-baseweb="select"] *,div[data-testid="stForm"] [data-testid="stDateInput"] *,[data-testid="stExpander"] [data-testid="stDateInput"] *,div[data-testid="stForm"] [data-testid="stNumberInput"] *,[data-testid="stExpander"] [data-testid="stNumberInput"] *{color:#17313d!important;background-color:#fff!important}
div[data-testid="stForm"] [data-baseweb="select"] svg,[data-testid="stExpander"] [data-baseweb="select"] svg{fill:#5d7480!important}
div[data-testid="stForm"] input,[data-testid="stExpander"] input,div[data-testid="stForm"] textarea,[data-testid="stExpander"] textarea{color:#17313d!important;-webkit-text-fill-color:#17313d!important;background:#fff!important}
div[data-testid="stForm"] input::placeholder,[data-testid="stExpander"] input::placeholder,div[data-testid="stForm"] textarea::placeholder{color:#7c8d96!important;-webkit-text-fill-color:#7c8d96!important}
div[data-testid="stForm"] [data-testid="stCheckbox"] label>div:first-of-type{background:#fff!important;border:1.5px solid #7fa6d8!important}
</style>""", unsafe_allow_html=True)

# ---------------------------- Collapsible sections everywhere ----------------------------
# Every data table / chart is shown as a closed bar with an arrow; click it to see the details.
from streamlit.delta_generator import DeltaGenerator
_AUTOWRAP = [True]
_EXP_DEPTH = [0]
_BOX_N = [0]
_orig_expander = DeltaGenerator.expander

class _TrackedExpander:
    def __init__(self, exp): self._exp = exp
    def __enter__(self):
        _EXP_DEPTH[0] += 1
        return self._exp.__enter__()
    def __exit__(self, *a):
        _EXP_DEPTH[0] -= 1
        return self._exp.__exit__(*a)
    def __getattr__(self, name): return getattr(self._exp, name)

def _tracked_expander(self, *a, **k):
    return _TrackedExpander(_orig_expander(self, *a, **k))
DeltaGenerator.expander = _tracked_expander
st.expander = lambda *a, **k: _TrackedExpander(_orig_expander(st._main, *a, **k))

def _collapsible(orig, noun):
    def wrapper(data=None, *a, **k):
        if not _AUTOWRAP[0] or _EXP_DEPTH[0] > 0:
            return orig(data, *a, **k)
        try: n = len(data)
        except Exception: n = None
        label = f"Show {noun}" + (f" ({n} rows)" if n is not None and noun == "details" else "")
        _BOX_N[0] += 1
        with st.container(key=f"gx_auto{_BOX_N[0]}").expander(label, expanded=False):
            return orig(data, *a, **k)
    return wrapper
st.dataframe = _collapsible(st.dataframe, "details")
st.bar_chart = _collapsible(st.bar_chart, "chart")

# ---------------------------- Global search bar ----------------------------
st.markdown("""<style>
.st-key-global_search{max-width:620px;margin:0}
.top-user{display:flex;align-items:center;gap:10px;background:#ffffffee;border:1px solid #ffffff;border-radius:999px;padding:5px 14px 5px 6px;box-shadow:0 6px 18px #00000026;min-height:40px}
.top-avatar{width:30px;height:30px;border-radius:50%;background:linear-gradient(145deg,#2ca99e,#146e69);color:#fff!important;font-weight:800;font-size:.7rem;display:flex;align-items:center;justify-content:center;flex:none}
.top-user-name{font-size:.8rem;font-weight:800;color:#17313d!important;line-height:1.1;white-space:nowrap}
.top-user-role{font-size:.66rem;color:#5d7480!important;line-height:1.2;white-space:nowrap}
[class*="st-key-top_logout_btn"] button{border-radius:999px!important;min-height:2.5rem;font-weight:700;background:#ffffffee!important;color:#17313d!important;border:1px solid #fff!important;white-space:nowrap;padding:0 .6rem}
[data-testid="stMain"] [class*="st-key-top_logout_btn"] button,[data-testid="stMain"] [class*="st-key-top_logout_btn"] button *{color:#17313d!important;-webkit-text-fill-color:#17313d!important}
.cvp-hero-right{display:none!important}
@media(max-width:900px){.top-user-role{display:none}}
.st-key-global_search [data-testid="stTextInputRootElement"]{background:#fff!important;border:1px solid #cfe0e3!important;border-radius:999px!important;box-shadow:0 6px 18px #00000026;overflow:hidden}
.st-key-global_search [data-testid="stTextInputRootElement"] *{background-color:#fff!important;color:#17313d!important}
.st-key-global_search input{padding:.7rem 1rem .7rem 2.7rem!important;font-size:.95rem;-webkit-text-fill-color:#17313d!important}
.st-key-global_search input::placeholder{color:#7c8d96!important;-webkit-text-fill-color:#7c8d96!important}
.st-key-global_search [data-testid="stTextInputRootElement"]{background:#fff url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2317776f' stroke-width='2.4' stroke-linecap='round'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='M20 20l-3.5-3.5'/%3E%3C/svg%3E") 16px center/20px no-repeat!important}
.st-key-global_search [data-testid="stTextInputRootElement"] *{background-color:transparent!important}
</style>""", unsafe_allow_html=True)
_top_l, _top_r = st.columns([3, 1.5], gap="medium")
with _top_l:
    _gq = st.text_input("Search", placeholder="Search documents, projects, employees, policies, contracts...", key="global_search", label_visibility="collapsed").strip()
with _top_r:
    _uc, _ub = st.columns([2.2, 1], gap="small")
    _ini = "".join(w[0] for w in FULL_NAME.split()[:2]).upper() or "U"
    _uc.markdown(f'<div class="top-user"><div class="top-avatar">{escape(_ini)}</div><div><div class="top-user-name">{escape(FULL_NAME)}</div>'
                 f'<div class="top-user-role">{escape(ROLE)} · @{escape(USER)}</div></div></div>', unsafe_allow_html=True)
    if _ub.button("↪ Sign out", key="top_logout_btn", use_container_width=True):
        audit("LOGOUT", "Security", USER, "User logged out")
        execute("DELETE FROM login_sessions WHERE token=?", (st.query_params.get("s", ""),))
        st.query_params.clear()
        for key in ["auth", "username", "full_name", "role", "side_nav"]:
            st.session_state.pop(key, None)
        st.rerun()
if _gq:
    _AUTOWRAP[0] = False  # search results are shown directly
    _like = f"%{_gq}%"
    st.markdown(f'<div class="cvp-section-band"><div><h2>Search results for “{escape(_gq)}”</h2></div></div>', unsafe_allow_html=True)
    _searches = [
        ("Documents", "Documents", "SELECT doc_no AS Number, title AS Title, project_code AS Project, category AS Category, owner AS Owner, status AS Status FROM documents WHERE is_deleted=0 AND (doc_no LIKE ? OR title LIKE ? OR owner LIKE ? OR project_code LIKE ? OR description LIKE ?)", 5),
        ("Projects", "Projects", "SELECT project_code AS Code, name AS Project, client AS Client, manager AS Manager, location AS Location, status AS Status FROM projects WHERE project_code LIKE ? OR name LIKE ? OR client LIKE ? OR manager LIKE ? OR location LIKE ?", 5),
        ("Employees", "Employees", "SELECT employee_code AS Code, name AS Name, department AS Department, designation AS Designation, mobile AS Mobile, status AS Status FROM employees WHERE employee_code LIKE ? OR name LIKE ? OR department LIKE ? OR designation LIKE ? OR mobile LIKE ?", 5),
        ("Insurance", "Insurance", "SELECT policy_no AS Policy, policy_type AS Type, company AS Company, related_ref AS Linked, expiry_date AS Expiry, status AS Status FROM insurance WHERE policy_no LIKE ? OR policy_type LIKE ? OR company LIKE ? OR related_ref LIKE ? OR broker LIKE ?", 5),
        ("Contracts", "Contracts", "SELECT contract_no AS Contract, title AS Title, counterparty AS Party, expiry_date AS Expiry, status AS Status FROM contracts WHERE contract_no LIKE ? OR title LIKE ? OR counterparty LIKE ? OR owner LIKE ?", 4),
    ]
    _found = 0
    for _label, _needs, _sql, _n in _searches:
        if _needs not in available_pages: continue
        _res = df_query(_sql, (_like,) * _n)
        if _res.empty: continue
        _found += len(_res)
        st.markdown(f'<div class="panel-title">{_label} <span style="font-weight:500;opacity:.8">· {len(_res)}</span></div>', unsafe_allow_html=True)
        st.dataframe(_res, use_container_width=True, hide_index=True, height=min(38 + 35 * len(_res), 280))
    if not _found:
        st.info("No matching records found.")
    st.caption("Clear the search box to return to the page.")
    st.stop()

# ---------------------------- Dashboard ----------------------------
if page == "Dashboard":
    logo_uri = ui_logo_uri()
    initials = "".join(part[0] for part in FULL_NAME.split()[:2]).upper() or "CVP"
    _h = datetime.now().hour
    _greet = "Good morning" if _h < 12 else ("Good afternoon" if _h < 17 else "Good evening")
    st.markdown(
        f'<div class="cvp-hero"><div class="cvp-hero-left">'
        f'<img class="cvp-hero-logo" src="{logo_uri}" alt="C. V. Patil &amp; Associates logo">'
        f'<div><div class="cvp-hero-kicker">{_greet}, {escape(FULL_NAME.split()[0] if FULL_NAME else "there")}</div>'
        f'<div class="cvp-hero-title">C. V. Patil &amp; Associates</div>'
        f'<div class="cvp-hero-sub">1002, Trident Business Centre, Oppo. Audi Showroom, Mumbai-Pune Highway, Baner, Pune-411045</div></div></div>'
        f'<div class="cvp-hero-right">'
        f'<div class="cvp-user-chip"><div class="cvp-avatar">{escape(initials)}</div>'
        f'<div><div class="cvp-user-name">{escape(FULL_NAME)}</div><div class="cvp-user-role">{escape(ROLE)} · @{escape(USER)}</div></div></div></div></div>',
        unsafe_allow_html=True,
    )
    # Accounts users get their own dashboard only
    if ROLE == "Accounts":
        month = date.today().strftime("%Y-%m")
        def _amt(sql, params=()): return float(scalar(sql, params, default=0) or 0)
        receipts = _amt("SELECT COALESCE(SUM(amount),0) FROM accounts WHERE entry_type='Receipt'")
        payments = _amt("SELECT COALESCE(SUM(amount),0) FROM accounts WHERE entry_type='Payment'")
        m_rec = _amt("SELECT COALESCE(SUM(amount),0) FROM accounts WHERE entry_type='Receipt' AND entry_date LIKE ?", (month + "%",))
        m_pay = _amt("SELECT COALESCE(SUM(amount),0) FROM accounts WHERE entry_type='Payment' AND entry_date LIKE ?", (month + "%",))
        salary_m = _amt("SELECT COALESCE(SUM(net),0) FROM salary WHERE salary_month=?", (month,))
        entries_n = int(scalar("SELECT COUNT(*) FROM accounts"))
        st.markdown(
            f'<div class="cvp-section-band"><div><h2>Accounts Overview</h2></div>'
            f'<div class="cvp-date-badge">{date.today().strftime("%d %b %Y")}</div></div>',
            unsafe_allow_html=True,
        )
        kp = [("↓", f"₹ {receipts:,.0f}", "Total Receipts", "#238a5c"), ("↑", f"₹ {payments:,.0f}", "Total Payments", "#c9433f"),
              ("=", f"₹ {receipts - payments:,.0f}", "Net Balance", "#176f69"), ("◔", f"₹ {m_rec - m_pay:,.0f}", "This Month Net", "#2f6fb0"),
              ("₹", f"₹ {salary_m:,.0f}", "Salary This Month", "#6a47b8"), ("▤", entries_n, "Ledger Entries", "#d9822b")]
        st.markdown('<div class="kpi-grid">' + "".join(
            f'<div class="kpi" style="--accent:{col}"><div class="kpi-icon">{ico}</div><div class="kpi-value" style="font-size:1.15rem">{val}</div><div class="kpi-label">{lab}</div></div>'
            for ico, val, lab, col in kp) + '</div>', unsafe_allow_html=True)
        a1, a2 = st.columns([1.4, 1], gap="large")
        with a1:
            st.markdown('<div class="panel-title">Receipts vs Payments (last 6 months)</div>', unsafe_allow_html=True)
            ledger = df_query("SELECT substr(entry_date,1,7) AS month, entry_type, SUM(amount) AS total FROM accounts WHERE entry_type IN ('Receipt','Payment') GROUP BY 1,2 ORDER BY 1")
            if ledger.empty:
                st.caption("No ledger entries yet.")
            else:
                pv = ledger.pivot(index="month", columns="entry_type", values="total").fillna(0).tail(6)
                st.bar_chart(pv, color=["#c9433f", "#238a5c"][: len(pv.columns)] if list(pv.columns) == ["Payment", "Receipt"] else None, height=250)
        with a2:
            st.markdown('<div class="panel-title">Spending by Category</div>', unsafe_allow_html=True)
            cat = df_query("SELECT category AS Category, SUM(amount) AS Amount FROM accounts WHERE entry_type='Payment' GROUP BY category ORDER BY Amount DESC LIMIT 6")
            if cat.empty:
                st.caption("No payments recorded yet.")
            else:
                st.dataframe(cat, use_container_width=True, hide_index=True, height=38 + 35 * len(cat),
                             column_config={"Amount": st.column_config.NumberColumn("Amount (₹)", format="%.0f")})
        b1, b2 = st.columns(2, gap="large")
        with b1:
            st.markdown('<div class="panel-title">Recent Ledger Entries</div>', unsafe_allow_html=True)
            rec = df_query("SELECT entry_date AS Date, entry_type AS Type, category AS Category, amount AS Amount, party AS Party, reference AS Reference FROM accounts ORDER BY entry_date DESC, id DESC LIMIT 6")
            if rec.empty: st.caption("No entries yet.")
            else: st.dataframe(rec, use_container_width=True, hide_index=True, height=38 + 35 * len(rec))
        with b2:
            st.markdown('<div class="panel-title">Upcoming Insurance & Contract Expiries</div>', unsafe_allow_html=True)
            ex = df_query("""SELECT 'Insurance' AS Type, policy_no AS Reference, policy_type AS Title, expiry_date AS Expiry FROM insurance WHERE expiry_date<>'' AND status IN ('Expiring Soon','Expired')
                             UNION ALL SELECT 'Contract', contract_no, title, expiry_date FROM contracts WHERE expiry_date<>'' AND status IN ('Expiring Soon','Expired')
                             ORDER BY 4 LIMIT 6""")
            if ex.empty: st.caption("No expiries need attention.")
            else: st.dataframe(ex, use_container_width=True, hide_index=True, height=38 + 35 * len(ex))
        st.stop()

    def _role_header(title):
        st.markdown(
            f'<div class="cvp-section-band"><div><h2>{title}</h2></div>'
            f'<div class="cvp-date-badge">{date.today().strftime("%d %b %Y")}</div></div>', unsafe_allow_html=True)

    def _role_kpis(items):
        st.markdown('<div class="kpi-grid">' + "".join(
            f'<div class="kpi" style="--accent:{col}"><div class="kpi-icon">{ico}</div><div class="kpi-value">{val}</div><div class="kpi-label">{lab}</div></div>'
            for ico, val, lab, col in items) + '</div>', unsafe_allow_html=True)

    def _role_table(title, df, empty):
        st.markdown(f'<div class="panel-title">{title}</div>', unsafe_allow_html=True)
        if df.empty: st.caption(empty)
        else: st.dataframe(df, use_container_width=True, hide_index=True, height=38 + 35 * min(len(df), 6))

    # HR users get an HR-only dashboard
    if ROLE == "HR":
        month = date.today().strftime("%Y-%m")
        _role_header("HR Overview")
        _role_kpis([
            ("☻", scalar("SELECT COUNT(*) FROM employees WHERE status='Active'"), "Active Employees", "#2f6fb0"),
            ("○", scalar("SELECT COUNT(*) FROM employees WHERE status<>'Active'"), "Inactive Employees", "#8aa0ad"),
            ("+", scalar("SELECT COUNT(*) FROM employees WHERE joining_date LIKE ?", (month + "%",)), "Joined This Month", "#238a5c"),
            ("▤", scalar("SELECT COUNT(DISTINCT department) FROM employees WHERE status='Active' AND department<>''"), "Departments", "#176f69"),
            ("₹", scalar("SELECT COUNT(*) FROM salary WHERE salary_month=?", (month,)), "Salaries Processed", "#6a47b8"),
            ("☑", scalar("SELECT COUNT(*) FROM tasks WHERE status<>'Closed'"), "Open Tasks", "#d9822b"),
        ])
        h1, h2 = st.columns([1, 1.3], gap="large")
        with h1:
            st.markdown('<div class="panel-title">Employees by Department</div>', unsafe_allow_html=True)
            dep = df_query("SELECT COALESCE(NULLIF(department,''),'Unassigned') AS Department, COUNT(*) AS Employees FROM employees WHERE status='Active' GROUP BY 1 ORDER BY 2 DESC")
            if dep.empty: st.caption("No employees yet.")
            else: st.bar_chart(dep.set_index("Department"), color="#2f6fb0", height=250)
        with h2:
            _role_table("Recent Joiners", df_query("SELECT employee_code AS Code, name AS Name, department AS Department, designation AS Designation, joining_date AS Joined FROM employees ORDER BY joining_date DESC LIMIT 6"), "No employees yet.")
        h3, h4 = st.columns(2, gap="large")
        with h3:
            _role_table("Employee Insurance Expiring", df_query("SELECT policy_no AS Policy, policy_type AS Type, related_ref AS Employee, expiry_date AS Expiry, status AS Status FROM insurance WHERE related_type='Employee' AND status IN ('Expiring Soon','Expired') ORDER BY expiry_date LIMIT 6"), "No employee insurance needs attention.")
        with h4:
            _role_table("Open Tasks", df_query("SELECT title AS Task, assignee AS Assignee, due_date AS Due, priority AS Priority FROM tasks WHERE status<>'Closed' ORDER BY due_date LIMIT 6"), "No open tasks.")
        st.stop()

    # Employees get a personal dashboard (their own documents and requests only)
    if ROLE == "Employee":
        _role_header("My Workspace")
        _mine_n = lambda cond="": scalar(f"SELECT COUNT(*) FROM documents WHERE is_deleted=0 AND created_by=?{cond}", (USER,))
        _role_kpis([
            ("▤", _mine_n(), "My Documents", "#2f6fb0"),
            ("◔", _mine_n(" AND status='Pending Review'"), "Awaiting Approval", "#d9822b"),
            ("✓", _mine_n(" AND status='Approved'"), "Approved", "#238a5c"),
            ("!", _mine_n(" AND status IN ('Correction Required','Rejected')"), "Need Attention", "#c9433f"),
            ("◇", scalar("SELECT COUNT(*) FROM project_requests WHERE requested_by=?", (USER,)), "Project Requests", "#6a47b8"),
        ])
        _role_table("My Recent Documents", df_query("SELECT doc_no AS Document, title AS Title, COALESCE(NULLIF(project_code,''),'General') AS Project, status AS Status, approval_stage AS Stage, updated_at AS Updated FROM documents WHERE is_deleted=0 AND created_by=? ORDER BY updated_at DESC LIMIT 8", (USER,)), "You have not uploaded any documents yet.")
        st.stop()

    # Managers get a manager-only dashboard
    if ROLE == "Manager":
        _role_header("Manager Overview")
        _role_kpis([
            ("✓", scalar("SELECT COUNT(*) FROM documents WHERE is_deleted=0 AND status IN ('Pending Review','Correction Required')"), "Awaiting Approval", "#d9822b"),
            ("▤", scalar("SELECT COUNT(*) FROM documents WHERE is_deleted=0 AND status='Approved'"), "Approved Documents", "#238a5c"),
            ("◆", scalar("SELECT COUNT(*) FROM projects WHERE status IN ('Planning','Active','On Hold')"), "Live Projects", "#6a47b8"),
            ("◔", scalar("SELECT COUNT(*) FROM projects WHERE status='On Hold'"), "Projects On Hold", "#c9433f"),
            ("☑", scalar("SELECT COUNT(*) FROM tasks WHERE status<>'Closed'"), "Open Tasks", "#2f6fb0"),
            ("◈", scalar("SELECT COUNT(*) FROM contracts WHERE status IN ('Expiring Soon','Expired')"), "Contract Alerts", "#176f69"),
        ])
        m1, m2 = st.columns([1.3, 1], gap="large")
        with m1:
            _role_table("Documents Awaiting Approval", df_query("SELECT doc_no AS Document, title AS Title, revision AS Rev, owner AS Owner, status AS Status, approval_stage AS Stage FROM documents WHERE is_deleted=0 AND status IN ('Pending Review','Correction Required') ORDER BY updated_at DESC LIMIT 6"), "Nothing waiting for approval.")
        with m2:
            st.markdown('<div class="panel-title">Documents by Status</div>', unsafe_allow_html=True)
            ds = df_query("SELECT status AS Status, COUNT(*) AS Documents FROM documents WHERE is_deleted=0 GROUP BY status")
            if ds.empty: st.caption("No document data yet.")
            else: st.bar_chart(ds.set_index("Status"), color="#176f69", height=250)
        m3, m4 = st.columns([1.3, 1], gap="large")
        with m3:
            pj = df_query("""SELECT project_code AS Code, name AS Project, client AS Client, status AS Status, end_date AS "End Date", COALESCE(progress,'0') AS Progress FROM projects WHERE status IN ('Planning','Active','On Hold') ORDER BY end_date LIMIT 6""")
            st.markdown('<div class="panel-title">Live Projects</div>', unsafe_allow_html=True)
            if pj.empty: st.caption("No live projects.")
            else:
                pj["Progress"] = pd.to_numeric(pj["Progress"], errors="coerce").fillna(0).clip(0, 100).astype(int)
                st.dataframe(pj, use_container_width=True, hide_index=True, height=38 + 35 * len(pj),
                             column_config={"Progress": st.column_config.ProgressColumn("Progress", min_value=0, max_value=100, format="%d%%")})
        with m4:
            _role_table("Tasks Due", df_query("SELECT title AS Task, assignee AS Assignee, due_date AS Due, priority AS Priority FROM tasks WHERE status<>'Closed' ORDER BY due_date LIMIT 6"), "No open tasks.")
        st.stop()

    # Refresh derived statuses
    ins = df_query("SELECT id,expiry_date,reminder_days,status FROM insurance")
    for _, r in ins.iterrows():
        s = status_from_expiry(r["expiry_date"], r["reminder_days"])
        if s != r["status"]:
            execute("UPDATE insurance SET status=?,updated_at=? WHERE id=?", (s, now_str(), int(r["id"])))
    con = df_query("SELECT id,expiry_date,reminder_days,status FROM contracts")
    for _, r in con.iterrows():
        s = status_from_expiry(r["expiry_date"], r["reminder_days"])
        if s != r["status"]:
            execute("UPDATE contracts SET status=? WHERE id=?", (s, int(r["id"])))

    docs = scalar("SELECT COUNT(*) FROM documents WHERE is_deleted=0")
    pending = scalar("SELECT COUNT(*) FROM documents WHERE is_deleted=0 AND status IN ('Pending Review','Correction Required')")
    employees = scalar("SELECT COUNT(*) FROM employees WHERE status='Active'")
    expiring = scalar("SELECT COUNT(*) FROM insurance WHERE status IN ('Expiring Soon','Expired')")
    projects = scalar("SELECT COUNT(*) FROM projects WHERE status IN ('Planning','Active','On Hold')")
    open_tasks = scalar("SELECT COUNT(*) FROM tasks WHERE status<>'Closed'")
    st.markdown(
        f'<div class="cvp-section-band"><div><h2>Management Overview</h2>'
        f'</div>'
        f'<div class="cvp-date-badge">{date.today().strftime("%d %b %Y")}</div></div>',
        unsafe_allow_html=True,
    )
    kpis = [("▤", docs, "Active Documents", "#176f69"), ("◔", pending, "Pending / Correction", "#d9822b"),
            ("☻", employees, "Active Employees", "#2f6fb0"), ("◈", expiring, "Insurance Alerts", "#c9433f"),
            ("◆", projects, "Live Projects", "#6a47b8"), ("✔", open_tasks, "Open Tasks", "#238a5c")]
    st.markdown('<div class="kpi-grid">' + "".join(
        f'<div class="kpi" style="--accent:{col}"><div class="kpi-icon">{ico}</div>'
        f'<div class="kpi-value">{val}</div><div class="kpi-label">{lab}</div></div>'
        for ico, val, lab, col in kpis) + '</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="module-strip">'
        f'<div class="module-card"><div class="module-card-top"><div class="module-card-icon">▤</div><div class="module-card-count">{docs}</div></div><div class="module-card-title">Document Control</div></div>'
        f'<div class="module-card"><div class="module-card-top"><div class="module-card-icon">✓</div><div class="module-card-count">{pending}</div></div><div class="module-card-title">Approval Queue</div></div>'
        f'<div class="module-card"><div class="module-card-top"><div class="module-card-icon">◈</div><div class="module-card-count">{expiring}</div></div><div class="module-card-title">Compliance Alerts</div></div>'
        f'<div class="module-card"><div class="module-card-top"><div class="module-card-icon">◇</div><div class="module-card-count">{projects}</div></div><div class="module-card-title">Project Records</div></div>'
        '</div>', unsafe_allow_html=True,
    )

    # Three panels side by side with fixed heights so the whole dashboard fits one screen.
    alert_rows = []
    for table, label, ref_col in [("insurance","Insurance","policy_no"),("contracts","Contract","contract_no"),("documents","Document","doc_no")]:
        sql = f"SELECT {ref_col} AS ref, title AS title, expiry_date, reminder_days FROM {table} WHERE expiry_date IS NOT NULL AND expiry_date<>''"
        if table == "insurance": sql = f"SELECT {ref_col} AS ref, policy_type AS title, expiry_date, reminder_days FROM {table} WHERE expiry_date IS NOT NULL AND expiry_date<>''"
        if table == "documents": sql += " AND is_deleted=0"
        d = df_query(sql)
        for _, r in d.iterrows():
            dd = days_to(r["expiry_date"])
            if dd is not None and dd <= max(int(r["reminder_days"] or 30), 30):
                alert_rows.append({"Module": label, "Reference": r["ref"], "Title": r["title"], "Expiry": r["expiry_date"], "Days Left": dd})
    c1,c2,c3 = st.columns([1.25,1,1.25], gap="large")
    with c1, st.container(key="gx_alerts").expander("Expiry & Renewal Alerts", expanded=False):
        if alert_rows:
            ad = pd.DataFrame(alert_rows).sort_values("Days Left")
            st.dataframe(ad, use_container_width=True, hide_index=True, height=min(38 + 35 * len(ad), 230))
        else:
            st.success("No urgent expiry alerts.")
    with c2, st.container(key="gx_status").expander("Documents by Status", expanded=False):
        d = df_query("SELECT status,COUNT(*) AS count FROM documents WHERE is_deleted=0 GROUP BY status")
        if not d.empty:
            palette = ["#176f69","#e0922f","#3b82c4","#d9534f","#7c5cc4","#2f9e6e","#8aa0ad"]
            total = int(d["count"].sum()); acc = 0; stops = []; legend = []
            for i, (st_name, cnt) in enumerate(zip(d["status"], d["count"])):
                col = palette[i % len(palette)]
                stops.append(f"{col} {acc / total * 100:.2f}% {(acc + cnt) / total * 100:.2f}%"); acc += cnt
                legend.append(f'<div class="dn-row"><span class="dn-dot" style="background:{col}"></span>{escape(str(st_name))}<b>{int(cnt)}</b></div>')
            st.markdown(
                f'<div class="dn-wrap"><div class="dn-ring" style="background:conic-gradient({",".join(stops)})"><span>{total}<small>Total</small></span></div>'
                f'<div class="dn-legend">{"".join(legend)}</div></div>', unsafe_allow_html=True)
        else: st.caption("No document data yet.")
    with c3, st.container(key="gx_tasks").expander("Tasks Due", expanded=False):
        td = df_query("SELECT title,assignee,due_date,priority,status FROM tasks WHERE status<>'Closed' ORDER BY due_date LIMIT 10")
        if not td.empty:
            st.dataframe(td, use_container_width=True, hide_index=True, height=min(38 + 35 * len(td), 230))
        else: st.caption("No open tasks.")
    with st.container(key="gx_projects").expander("Project Records", expanded=False):
        pj = df_query("""SELECT p.project_code AS Code, p.name AS Project, p.client AS Client, p.manager AS Manager, p.status AS Status,
                         p.end_date AS "End Date", COALESCE(p.progress,'0') AS Progress,
                         (SELECT COUNT(*) FROM documents d WHERE d.project_code=p.project_code AND d.is_deleted=0) AS Documents
                         FROM projects p WHERE p.status IN ('Planning','Active','On Hold') ORDER BY p.end_date LIMIT 8""")
        if pj.empty:
            st.caption("No live projects.")
        else:
            pj["Progress"] = pd.to_numeric(pj["Progress"], errors="coerce").fillna(0).clip(0, 100).astype(int)
            st.dataframe(pj, use_container_width=True, hide_index=True, height=38 + 35 * len(pj),
                         column_config={"Progress": st.column_config.ProgressColumn("Progress", min_value=0, max_value=100, format="%d%%")})
# ---------------------------- Documents ----------------------------
elif page == "Documents":
    section_title("Document Register", "Upload, number, classify, approve, revise, search and control files")
    tabs = st.tabs(["Register / Search","Upload New","Delete Document"])

    with tabs[0]:
        c1,c2,c3,c4 = st.columns(4)
        q = c1.text_input("Search", placeholder="title, document no., owner...")
        category = c2.selectbox("Category", ["All","Engineering","HR","Accounts","Insurance","Contract","Quality","Admin","Drawing","MDR","Other"])
        status = c3.selectbox("Status", ["All","Draft","Pending Review","Approved","Rejected","Correction Required","Expired","Archived"])
        dept = c4.selectbox("Department", ["All"] + df_query("SELECT name FROM departments ORDER BY name")["name"].tolist())
        sql = "SELECT id,doc_no,title,category,department,project_code,owner,revision,version,issue_date,expiry_date,status,approval_stage,confidentiality,checked_out_by,filename,filepath FROM documents WHERE is_deleted=0"
        params=[]
        if q:
            sql += " AND (doc_no LIKE ? OR title LIKE ? OR owner LIKE ? OR description LIKE ?)"; like=f"%{q}%"; params += [like,like,like,like]
        if category!="All": sql += " AND category=?"; params.append(category)
        if status!="All": sql += " AND status=?"; params.append(status)
        if dept!="All": sql += " AND department=?"; params.append(dept)
        if ROLE == "Employee": sql += " AND (created_by=? OR status='Approved')"; params.append(USER)
        sql += " ORDER BY updated_at DESC"
        d = df_query(sql, params)
        st.dataframe(d.drop(columns=["filepath"], errors="ignore"), use_container_width=True, hide_index=True)
        st.caption(f"{len(d)} record(s)")

    with tabs[1]:
        with st.form("doc_upload", clear_on_submit=True):
            st.write("**Automatic document number:**", next_doc_no())
            c1,c2,c3 = st.columns(3)
            title = c1.text_input("Document Title *")
            category = c2.selectbox("Category *", ["Engineering","Drawing","MDR","Quality","HR","Accounts","Insurance","Contract","Admin","Other"])
            doc_type = c3.text_input("Document Type", placeholder="Report / Drawing / Certificate / SOP")
            c1,c2,c3 = st.columns(3)
            department = c1.selectbox("Department", df_query("SELECT name FROM departments ORDER BY name")["name"].tolist())
            project_code = c2.selectbox("Project", [""] + df_query("SELECT project_code FROM projects ORDER BY project_code")["project_code"].tolist())
            owner = c3.text_input("Owner / Responsible Person")
            c1,c2,c3 = st.columns(3)
            prepared_by = c1.text_input("Prepared By")
            checked_by = c2.text_input("Checked By")
            approved_by = c3.text_input("Approver")
            c1,c2,c3,c4 = st.columns(4)
            revision = c1.text_input("Revision", value="R0")
            issue_date = c2.date_input("Issue Date", value=date.today())
            expiry_enabled = c3.checkbox("Has Expiry")
            expiry_date = c4.date_input("Expiry Date", value=date.today()+timedelta(days=365)) if expiry_enabled else None
            c1,c2,c3 = st.columns(3)
            reminder_days = c1.selectbox("Reminder Days", [30,15,7,1], index=0)
            confidentiality = c2.selectbox("Confidentiality", ["Internal","Confidential","Restricted","Public"])
            related_to = c3.selectbox("Related To", ["General","Employee","Project","Vendor","Asset","Contract"])
            related_ref = st.text_input("Related Reference")
            description = st.text_area("Description / Remarks")
            uploaded = st.file_uploader("Upload File *", key="doc_new_file")
            send_mode = st.radio("After saving", ["Send for approval", "Save as draft only"], horizontal=True, key="doc_send_mode")
            submitted = st.form_submit_button("Create Document", use_container_width=True)
        if submitted:
            if not title or uploaded is None:
                st.error("Document title and file are required.")
            else:
                doc_no = next_doc_no()
                filename, filepath = save_uploaded_file(uploaded, UPLOAD_DIR/"documents", doc_no)
                exp = expiry_date.isoformat() if expiry_date else ""
                doc_status = "Pending Review" if send_mode == "Send for approval" else "Draft"
                stage = "Manager Review" if doc_status == "Pending Review" else "Draft"
                doc_id = execute("""INSERT INTO documents(doc_no,title,category,doc_type,department,related_to,related_ref,project_code,owner,prepared_by,checked_by,approved_by,revision,issue_date,expiry_date,reminder_days,version,confidentiality,description,filename,filepath,status,approval_stage,created_by,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (doc_no,title,category,doc_type,department,related_to,related_ref,project_code,owner,prepared_by,checked_by,approved_by,revision,issue_date.isoformat(),exp,reminder_days,1,confidentiality,description,filename,filepath,doc_status,stage,USER,now_str(),now_str()))
                if doc_status == "Pending Review":
                    execute("INSERT INTO approvals(doc_id,reviewer_role,reviewer,status,comments,action_date,created_at) VALUES(?,?,?,?,?,?,?)",
                            (doc_id,"Manager",checked_by or "Manager","Pending","","",now_str()))
                audit("CREATE", "Documents", doc_no, f"Uploaded {filename}")
                st.success(f"Document created: {doc_no}" + (" and sent for approval." if doc_status == "Pending Review" else " (saved as draft)."))

    with tabs[2]:
        if ROLE not in ["Admin", "Manager"]:
            st.info("Only Admin or Manager can delete documents.")
        else:
            dd = df_query("SELECT id,doc_no,title,category,project_code,revision,status,checked_out_by FROM documents WHERE is_deleted=0 ORDER BY updated_at DESC")
            if dd.empty:
                st.info("No documents available to delete.")
            else:
                dq = st.text_input("Search document to delete", placeholder="document no. or title...", key="del_doc_q")
                if dq:
                    dd = dd[dd.apply(lambda r: dq.lower() in f"{r['doc_no']} {r['title']}".lower(), axis=1)]
                if dd.empty:
                    st.warning("No matching documents.")
                else:
                    dlabels = [f"{r.doc_no} | {r.title}" for _, r in dd.iterrows()]
                    dsel = st.selectbox("Select document", dlabels, key="del_doc_sel")
                    drow = dd.iloc[dlabels.index(dsel)]
                    st.dataframe(dd[dd["id"] == drow["id"]].drop(columns=["id"]), use_container_width=True, hide_index=True)
                    if drow["checked_out_by"]:
                        st.warning(f"This document is checked out by {drow['checked_out_by']}. Check it in before deleting.")
                    else:
                        reason = st.text_input("Reason for deletion", key="del_doc_reason")
                        confirm = st.checkbox("I confirm I want to delete this document.", key="del_doc_confirm")
                        if st.button("Delete Document", type="primary", disabled=not confirm, key="del_doc_btn"):
                            execute("UPDATE documents SET is_deleted=1,updated_at=? WHERE id=?", (now_str(), int(drow["id"])))
                            audit("DELETE", "Documents", drow["doc_no"], reason or "Deleted by user")
                            st.success(f"{drow['doc_no']} moved to the Recycle Bin. Admin can restore it from the Recycle Bin page.")
                            st.rerun()

# ---------------------------- Approvals ----------------------------
elif page == "Approvals":
    section_title("Approvals", "Send documents and project requests for approval, review them, and track every decision in one place")
    _REQ_TYPES = ["General query", "Status change", "Budget / contract value", "Deadline extension", "Resource request", "Project closure"]
    _is_admin = ROLE == "Admin"
    _is_reviewer = ROLE in ("Admin", "Manager")

    _pending_docs = df_query("""SELECT d.id,d.doc_no,d.title,d.revision,d.version,d.status,d.approval_stage,d.owner,d.filename,d.filepath,
                         d.project_code,COALESCE(p.name,'') AS project_name,d.category,d.department,d.created_by,d.created_at,d.description
                         FROM documents d LEFT JOIN projects p ON p.project_code=d.project_code
                         WHERE d.is_deleted=0 AND d.status IN ('Pending Review','Correction Required') ORDER BY d.updated_at""") if _is_reviewer else pd.DataFrame()
    _preq = df_query("""SELECT r.*,COALESCE(p.name,'') AS pname FROM project_requests r LEFT JOIN projects p ON p.project_code=r.project_code
                        WHERE r.status='Pending' ORDER BY r.id""") if _is_admin else pd.DataFrame()

    _names = []
    if _is_reviewer: _names.append(f"Pending Documents ({len(_pending_docs)})")
    if not _is_admin: _names += ["Send for Approval", "My Requests"]
    if not _is_admin: _names.append("History")
    _tabs = dict(zip(_names, st.tabs(_names)))

    def _kv_card(title, pairs):
        return ('<div class="emp-grid"><div class="emp-card"><div class="emp-card-title">' + escape(title) + '</div>'
                + "".join(f'<div class="emp-row"><span>{escape(a)}</span><b>{escape(str(b or "-"))}</b></div>' for a, b in pairs) + '</div></div>')

    # ---------------- reviewers: pending documents ----------------
    if _is_reviewer:
        with _tabs[_names[0]]:
            if _pending_docs.empty:
                st.success("No documents are waiting for review.")
            for _, r in _pending_docs.iterrows():
                _proj = f"{r['project_code']} · {r['project_name']}" if r["project_code"] else "General (no project)"
                with st.expander(f"📁 {_proj}   |   {r['doc_no']} — {r['title']} ({r['revision']})", expanded=False):
                    st.markdown(_kv_card("Submitted from", [
                        ("Project", _proj), ("Category", r["category"]), ("Department", r["department"]),
                        ("Submitted by", r["created_by"]), ("Submitted on", str(r["created_at"] or "")[:16]),
                        ("Owner", r["owner"]), ("Remarks", r["description"])]), unsafe_allow_html=True)
                    st.write(f"Status: **{r['status']}**  |  Stage: **{r['approval_stage']}**")
                    file_download_button("Download file", r["filepath"], f"apdl_{r['id']}")
                    comments = st.text_area("Review comments", key=f"com_{r['id']}")
                    c1, c2, c3 = st.columns(3)
                    if c1.button("Approve", key=f"approve_{r['id']}"):
                        stage = r["approval_stage"]
                        if stage == "Manager Review":
                            new_status, new_stage, role = "Pending Review", "Authorized Review", "Authorized Reviewer"
                        elif stage == "Authorized Review":
                            new_status, new_stage, role = "Pending Review", "Admin Approval", "Admin"
                        else:
                            new_status, new_stage, role = "Approved", "Completed", ROLE
                        execute("UPDATE documents SET status=?,approval_stage=?,updated_at=? WHERE id=?", (new_status, new_stage, now_str(), int(r["id"])))
                        execute("INSERT INTO approvals(doc_id,reviewer_role,reviewer,status,comments,action_date,created_at) VALUES(?,?,?,?,?,?,?)",
                                (int(r["id"]), role, USER, "Approved", comments, now_str(), now_str()))
                        audit("APPROVE", "Documents", r["doc_no"], f"{stage} -> {new_stage}")
                        st.rerun()
                    if c2.button("Correction Required", key=f"corr_{r['id']}"):
                        execute("UPDATE documents SET status='Correction Required',approval_stage='Owner Correction',updated_at=? WHERE id=?", (now_str(), int(r["id"])))
                        execute("INSERT INTO approvals(doc_id,reviewer_role,reviewer,status,comments,action_date,created_at) VALUES(?,?,?,?,?,?,?)",
                                (int(r["id"]), ROLE, USER, "Correction Required", comments, now_str(), now_str()))
                        audit("CORRECTION", "Documents", r["doc_no"], comments); st.rerun()
                    if c3.button("Reject", key=f"rej_{r['id']}"):
                        execute("UPDATE documents SET status='Rejected',approval_stage='Closed',updated_at=? WHERE id=?", (now_str(), int(r["id"])))
                        execute("INSERT INTO approvals(doc_id,reviewer_role,reviewer,status,comments,action_date,created_at) VALUES(?,?,?,?,?,?,?)",
                                (int(r["id"]), ROLE, USER, "Rejected", comments, now_str(), now_str()))
                        audit("REJECT", "Documents", r["doc_no"], comments); st.rerun()

    # ---------------- admin: project requests (tab removed) ----------------
    if False:
        with _tabs[f"Project Requests ({len(_preq)})"]:
            if _preq.empty:
                st.success("No project requests are waiting.")
            for _, q in _preq.iterrows():
                with st.expander(f"📁 {q['project_code']} · {q['pname']}   |   {q['request_type']} — {q['subject']}", expanded=False):
                    st.markdown(_kv_card("Request", [
                        ("Project", f"{q['project_code']} · {q['pname']}"), ("Type", q["request_type"]), ("Subject", q["subject"]),
                        ("Details", q["details"]), ("From", f"{q['requested_by']} ({q['requested_role']})"), ("Sent", str(q["created_at"])[:16])]), unsafe_allow_html=True)
                    _reply = st.text_area("Reply / comments", key=f"preq_reply_{q['id']}")
                    b1, b2, _ = st.columns([1, 1, 3])
                    for _lab, _st, _col in (("Approve", "Approved", b1), ("Reject", "Rejected", b2)):
                        if _col.button(_lab, key=f"preq_{_st}_{q['id']}"):
                            execute("UPDATE project_requests SET status=?,admin_reply=?,decided_by=?,decided_at=? WHERE id=?", (_st, _reply, USER, now_str(), int(q["id"])))
                            audit(_st.upper(), "Projects", q["project_code"], f"{q['request_type']}: {q['subject']}"); st.rerun()

    # ---------------- everyone except Admin: send for approval ----------------
    if not _is_admin:
        with _tabs["Send for Approval"]:
            st.markdown('<div class="panel-title">📄 Send a document for approval</div>', unsafe_allow_html=True)
            _drafts = df_query("""SELECT d.id,d.doc_no,d.title,d.status,COALESCE(NULLIF(d.project_code,''),'General') AS project
                                  FROM documents d WHERE d.is_deleted=0 AND d.created_by=? AND d.status IN ('Draft','Correction Required') ORDER BY d.updated_at DESC""", (USER,))
            if _drafts.empty:
                st.caption("No drafts to send. Upload in Documents → Upload New (choose 'Save as draft only') or send it for approval directly there.")
            else:
                _lab = [f"{r.doc_no} | {r.title} · {r.project} ({r.status})" for r in _drafts.itertuples()]
                _pick = st.selectbox("Document", _lab, key="send_doc_pick")
                _to = st.radio("Send to", ["Manager (normal workflow)", "Admin (final approval directly)"], index=1 if ROLE == "Manager" else 0, horizontal=True, key="send_doc_to")
                _note = st.text_input("Note for the approver (optional)", key="send_doc_note")
                if st.button("Send document for approval", key="send_doc_btn"):
                    _row = _drafts.iloc[_lab.index(_pick)]
                    _stage, _rrole = ("Admin Approval", "Admin") if _to.startswith("Admin") else ("Manager Review", "Manager")
                    execute("UPDATE documents SET status='Pending Review',approval_stage=?,updated_at=? WHERE id=?", (_stage, now_str(), int(_row["id"])))
                    execute("INSERT INTO approvals(doc_id,reviewer_role,reviewer,status,comments,action_date,created_at) VALUES(?,?,?,?,?,?,?)",
                            (int(_row["id"]), _rrole, _rrole, "Pending", _note, "", now_str()))
                    audit("SUBMIT", "Documents", _row["doc_no"], f"Sent to {_rrole} for approval" + (f": {_note}" if _note else ""))
                    st.success(f"{_row['doc_no']} sent to {_rrole} for approval."); st.rerun()
            st.markdown('<div class="panel-title" style="margin-top:6px">📁 Send a project request / query to Admin</div>', unsafe_allow_html=True)
            _pl = df_query("SELECT project_code,name FROM projects ORDER BY project_code")
            if _pl.empty:
                st.info("No projects available.")
            else:
                _plab = [f"{r.project_code} | {r.name}" for r in _pl.itertuples()]
                with st.form("proj_req_form", clear_on_submit=True):
                    pr1, pr2 = st.columns(2)
                    _rp = pr1.selectbox("Project", _plab)
                    _rt = pr2.selectbox("Request type", _REQ_TYPES)
                    _rs = st.text_input("Subject *")
                    _rd = st.text_area("Details / query")
                    _go = st.form_submit_button("Send to Admin for approval", use_container_width=True)
                if _go:
                    if not _rs.strip():
                        st.error("Subject is required.")
                    else:
                        execute("INSERT INTO project_requests(project_code,request_type,subject,details,requested_by,requested_role,status,created_at) VALUES(?,?,?,?,?,?,?,?)",
                                (_rp.split(" | ")[0], _rt, _rs.strip(), _rd, USER, ROLE, "Pending", now_str()))
                        audit("REQUEST", "Projects", _rp.split(" | ")[0], f"{_rt}: {_rs.strip()}")
                        st.success("Request sent to Admin."); st.rerun()

        with _tabs["My Requests"]:
            st.markdown('<div class="panel-title">My documents</div>', unsafe_allow_html=True)
            _own = df_query("""SELECT d.doc_no AS Document,d.title AS Title,COALESCE(NULLIF(d.project_code,''),'General') AS Project,d.revision AS Rev,
                              d.status AS Status,d.approval_stage AS Stage,d.updated_at AS Updated
                              FROM documents d WHERE d.is_deleted=0 AND d.created_by=? AND d.status<>'Archived' ORDER BY d.updated_at DESC""", (USER,))
            if _own.empty: st.info("You have not submitted any documents yet.")
            else: st.dataframe(_own, use_container_width=True, hide_index=True)
            st.markdown('<div class="panel-title" style="margin-top:6px">My project requests</div>', unsafe_allow_html=True)
            _mine = df_query("""SELECT created_at AS Sent,project_code AS Project,request_type AS Type,subject AS Subject,status AS Status,admin_reply AS "Admin reply"
                                FROM project_requests WHERE requested_by=? ORDER BY id DESC""", (USER,))
            if _mine.empty: st.info("You have not sent any project requests yet.")
            else: st.dataframe(_mine, use_container_width=True, hide_index=True)

    # ---------------- history ----------------
    if not _is_admin:
      with _tabs["History"]:
          st.markdown('<div class="panel-title">Document decisions</div>', unsafe_allow_html=True)
          _own_only = "" if _is_reviewer else " WHERE d.created_by=?"
          hist = df_query(f"""SELECT d.doc_no AS Document,d.title AS Title,COALESCE(NULLIF(d.project_code,''),'General') AS Project,a.reviewer_role AS Role,a.reviewer AS Reviewer,
                             a.status AS Decision,a.comments AS Comments,a.action_date AS Date
                             FROM approvals a JOIN documents d ON a.doc_id=d.id{_own_only} ORDER BY a.id DESC LIMIT 200""", () if _is_reviewer else (USER,))
          st.dataframe(hist, use_container_width=True, hide_index=True)
          if _is_admin:
              st.markdown('<div class="panel-title" style="margin-top:6px">Project request decisions</div>', unsafe_allow_html=True)
              _done = df_query("""SELECT decided_at AS Decided,project_code AS Project,request_type AS Type,subject AS Subject,requested_by AS "From",status AS Status,admin_reply AS Reply
                                  FROM project_requests WHERE status<>'Pending' ORDER BY id DESC LIMIT 100""")
              st.dataframe(_done, use_container_width=True, hide_index=True)

# ---------------------------- Employees ----------------------------
elif page == "Employees":
    section_title("Employee Master", "Employee profile, department, bank, statutory and employment records")
    t1,t2,t3 = st.tabs(["Employee Register","Add Employee","Edit Employee"])
    with t1:
        e = df_query("""SELECT employee_code,name,surname,first_name,father_name,mother_name,dob,gender,marital_status,
                        department,designation,manager,joining_date,mobile,telephone,email,permanent_address,local_address,
                        pan,aadhar,employment_type,status,user_role,bank_name,bank_branch,account_number,ifsc,
                        vehicle_company,vehicle_no,license_no,software_skills,uan,pf_number,esi_number
                        FROM employees ORDER BY employee_code""")
        st.dataframe(e, use_container_width=True, hide_index=True)
        d1, d2 = st.columns([2, 1])
        if not e.empty:
            labels = [f"{r.employee_code} | {r.name}" for r in e.itertuples()]
            chosen = d1.selectbox("Select employee for filled Employee Form", labels, key="emp_form_pick")
            code = chosen.split(" | ")[0]
            full = df_query("SELECT * FROM employees WHERE employee_code=?", (code,)).iloc[0].to_dict()
            d1.download_button("Download Employee Form (PDF)", build_employee_form_pdf(full),
                               file_name=f"{full['name'].replace(' ', '_')}_Employee_Form.pdf", mime="application/pdf")
            # ---- Selected employee profile ----
            def _v(k):
                x = full.get(k)
                return "—" if x is None or (isinstance(x, float) and pd.isna(x)) or str(x).strip() == "" else str(x)
            def _dt(k):
                x = _v(k)
                try: return datetime.strptime(x[:10], "%Y-%m-%d").strftime("%d %b %Y")
                except ValueError: return x
            sections = [
                ("Personal", [("Full Name", _v("name")), ("Father Name", _v("father_name")), ("Mother Name", _v("mother_name")),
                              ("Date of Birth", _dt("dob")), ("Gender", _v("gender")), ("Marital Status", _v("marital_status"))]),
                ("Contact", [("Mobile", _v("mobile")), ("Telephone", _v("telephone")), ("Email", _v("email")),
                             ("Permanent Address", _v("permanent_address")), ("Local Address", _v("local_address"))]),
                ("Employment", [("Employee Code", _v("employee_code")), ("Department", _v("department")), ("Designation", _v("designation")),
                                ("Reporting Manager", _v("manager")), ("Employment Type", _v("employment_type")),
                                ("Joining Date", _dt("joining_date")), ("Status", _v("status")), ("System Role", _v("user_role"))]),
                ("Bank & Statutory", [("Bank Name", _v("bank_name")), ("Branch", _v("bank_branch")), ("Account No.", _v("account_number")),
                                      ("IFSC", _v("ifsc")), ("PAN", _v("pan")), ("Aadhar", _v("aadhar")),
                                      ("UAN", _v("uan")), ("PF Number", _v("pf_number")), ("ESI Number", _v("esi_number"))]),
                ("Vehicle & Skills", [("Vehicle Company", _v("vehicle_company")), ("Vehicle No.", _v("vehicle_no")),
                                      ("License No.", _v("license_no")), ("Software Skills", _v("software_skills"))]),
            ]
            cards = "".join(
                f'<div class="emp-card"><div class="emp-card-title">{escape(title)}</div>' +
                "".join(f'<div class="emp-row"><span>{escape(lab)}</span><b>{escape(val)}</b></div>' for lab, val in rows) + '</div>'
                for title, rows in sections)
            with st.expander(f"Employee Details — {_v('name')}", expanded=False):
                st.markdown(f'<div class="emp-grid">{cards}</div>', unsafe_allow_html=True)
    with t3:
        edf = df_query("SELECT * FROM employees ORDER BY employee_code")
        if edf.empty: st.info("No employees to edit.")
        else:
            if st.session_state.pop("emp_edited", None): st.success("Employee details updated.")
            elabels = [f"{r.employee_code} | {r.name}" for r in edf.itertuples()]
            esel = st.selectbox("Select employee to edit", elabels, key="emp_edit_pick")
            er = edf.iloc[elabels.index(esel)].to_dict()
            def _s(k):
                x = er.get(k)
                return "" if x is None or (isinstance(x, float) and pd.isna(x)) else str(x)
            def _pick(opts, k):
                return opts.index(_s(k)) if _s(k) in opts else None
            def _d(k):
                try: return datetime.strptime(_s(k)[:10], "%Y-%m-%d").date()
                except ValueError: return None
            with st.form(f"employee_edit_{er['employee_code']}"):
                c1,c2,c3,c4 = st.columns(4)
                e_surname = c1.text_input("Surname *", value=_s("surname"))
                e_first = c2.text_input("First Name *", value=_s("first_name"))
                e_father = c3.text_input("Father Name", value=_s("father_name"))
                e_mother = c4.text_input("Mother Name", value=_s("mother_name"))
                c1,c2,c3 = st.columns(3)
                e_dob = c1.date_input("Date of Birth", value=_d("dob"), min_value=date(1940,1,1), max_value=date.today(), format="DD/MM/YYYY")
                e_gender = c2.selectbox("Gender", ["Male","Female","Other"], index=_pick(["Male","Female","Other"], "gender"), placeholder="Select")
                e_marital = c3.selectbox("Marital Status", ["Single","Married","Divorced","Widowed"], index=_pick(["Single","Married","Divorced","Widowed"], "marital_status"), placeholder="Select")
                e_perm = st.text_area("Permanent Address", value=_s("permanent_address"), height=80)
                e_local = st.text_area("Local Address", value=_s("local_address"), height=80)
                c1,c2,c3 = st.columns(3)
                e_tel = c1.text_input("Telephone", value=_s("telephone"))
                e_mobile = c2.text_input("Mobile", value=_s("mobile"))
                e_email = c3.text_input("E-mail", value=_s("email"))
                c1,c2,c3,c4 = st.columns(4)
                e_dept = c1.text_input("Department", value=_s("department"))
                e_desig = c2.text_input("Designation", value=_s("designation"))
                e_mgr = c3.text_input("Reporting Manager", value=_s("manager"))
                e_join = c4.date_input("Joining Date", value=_d("joining_date"), format="DD/MM/YYYY")
                c1,c2,c3 = st.columns(3)
                etypes = ["Permanent","Contract","Intern","Consultant"]
                e_type = c1.selectbox("Employment Type", etypes, index=_pick(etypes, "employment_type"), placeholder="Select")
                e_status = c2.selectbox("Status", ["Active","Inactive"], index=_pick(["Active","Inactive"], "status"), placeholder="Select")
                roles = ["Admin","HR","Manager","Employee"]
                e_role = c3.selectbox("System Role", roles, index=_pick(roles, "user_role"), placeholder="Select")
                c1,c2,c3 = st.columns(3)
                e_pan = c1.text_input("PAN", value=_s("pan"))
                e_aadhar = c2.text_input("Aadhar", value=_s("aadhar"))
                e_skills = c3.text_input("Software Skills", value=_s("software_skills"))
                c1,c2,c3,c4 = st.columns(4)
                e_bank = c1.text_input("Bank Name", value=_s("bank_name"))
                e_branch = c2.text_input("Branch", value=_s("bank_branch"))
                e_acc = c3.text_input("Account No.", value=_s("account_number"))
                e_ifsc = c4.text_input("IFSC", value=_s("ifsc"))
                c1,c2,c3 = st.columns(3)
                e_vc = c1.text_input("Vehicle Company", value=_s("vehicle_company"))
                e_vn = c2.text_input("Vehicle No.", value=_s("vehicle_no"))
                e_lic = c3.text_input("License No.", value=_s("license_no"))
                c1,c2,c3 = st.columns(3)
                e_uan = c1.text_input("UAN", value=_s("uan"))
                e_pf = c2.text_input("PF Number", value=_s("pf_number"))
                e_esi = c3.text_input("ESI Number", value=_s("esi_number"))
                save_edit = st.form_submit_button("Save Changes", use_container_width=True)
            if save_edit:
                e_pan, e_ifsc = e_pan.strip().upper(), e_ifsc.strip().upper()
                e_aadhar = re.sub(r"\s", "", e_aadhar)
                errs = []
                if not e_surname.strip() or not e_first.strip(): errs.append("Surname and First Name are required.")
                if e_pan and not re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", e_pan): errs.append("PAN must look like ABCDE1234F.")
                if e_aadhar and not re.fullmatch(r"\d{12}", e_aadhar): errs.append("Aadhar must be 12 digits.")
                if e_ifsc and not re.fullmatch(r"[A-Z]{4}0[A-Z0-9]{6}", e_ifsc): errs.append("IFSC must look like SBIN0001234.")
                if errs:
                    for m in errs: st.error(m)
                else:
                    ename = " ".join(p.strip() for p in [e_first, e_surname] if p.strip())
                    execute("""UPDATE employees SET name=?,surname=?,first_name=?,father_name=?,mother_name=?,dob=?,gender=?,marital_status=?,
                               permanent_address=?,local_address=?,telephone=?,mobile=?,email=?,department=?,designation=?,manager=?,joining_date=?,
                               employment_type=?,status=?,user_role=?,pan=?,aadhar=?,software_skills=?,bank_name=?,bank_branch=?,account_number=?,ifsc=?,
                               vehicle_company=?,vehicle_no=?,license_no=?,uan=?,pf_number=?,esi_number=? WHERE employee_code=?""",
                            (ename,e_surname.strip(),e_first.strip(),e_father.strip(),e_mother.strip(),e_dob.isoformat() if e_dob else "",e_gender or "",e_marital or "",
                             e_perm.strip(),e_local.strip(),e_tel.strip(),e_mobile.strip(),e_email.strip(),e_dept.strip(),e_desig.strip(),e_mgr.strip(),
                             e_join.isoformat() if e_join else "",e_type or "",e_status or "",e_role or "",e_pan,e_aadhar,e_skills.strip(),
                             e_bank.strip(),e_branch.strip(),e_acc.strip(),e_ifsc,e_vc.strip(),e_vn.strip(),e_lic.strip(),
                             e_uan.strip(),e_pf.strip(),e_esi.strip(),er["employee_code"]))
                    audit("UPDATE","Employees",er["employee_code"],f"Edited {ename}")
                    st.session_state.emp_edited = True
                    st.rerun()
            st.markdown("#### Employee Documents")
            if st.session_state.pop("emp_doc_updated", None): st.success("Document updated. The previous file was kept in the archive.")
            doc_fields = [("Passport Photo", "photo_path", ["jpg","jpeg","png"], "Photo"),
                          ("PAN Card Copy", "pan_doc_path", ["pdf","jpg","jpeg","png"], "PAN"),
                          ("Aadhar Card Copy", "aadhar_doc_path", ["pdf","jpg","jpeg","png"], "Aadhar"),
                          ("Bank Passbook Copy", "passbook_doc_path", ["pdf","jpg","jpeg","png"], "Passbook")]
            with st.form(f"employee_docs_{er['employee_code']}"):
                new_docs = {}
                for lab, col, types, _tag in doc_fields:
                    cur = _s(col)
                    st.caption(f"{lab}: " + (Path(cur).name if cur and Path(cur).exists() else "not uploaded"))
                    new_docs[col] = st.file_uploader(f"Replace {lab}", type=types, key=f"edoc_{col}_{er['employee_code']}")
                save_docs = st.form_submit_button("Update Documents", use_container_width=True)
            for lab, col, types, _tag in doc_fields:
                cur = _s(col)
                if cur and Path(cur).exists():
                    file_download_button(f"Download current {lab}", cur, f"edl_{col}_{er['employee_code']}")
            if save_docs:
                changed = {c: u for c, u in new_docs.items() if u is not None}
                if not changed: st.warning("Choose at least one new document to upload.")
                else:
                    ecode = er["employee_code"]
                    folder = UPLOAD_DIR / "employees" / "".join(c for c in ecode if c.isalnum() or c in "-_")
                    prefix = f"{_s('first_name')}_{_s('surname')}".replace(" ", "_")
                    tags = {c: t for _l, c, _ty, t in doc_fields}
                    for col, upl in changed.items():
                        old = _s(col)
                        if old and Path(old).exists():
                            ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
                            shutil.move(old, ARCHIVE_DIR / f"EMP_{ecode}_{Path(old).name}")
                        newpath = save_uploaded_file(upl, folder, f"{prefix}_{tags[col]}")[1]
                        execute(f"UPDATE employees SET {col}=? WHERE employee_code=?", (newpath, ecode))
                    audit("UPDATE","Employees",ecode,"Documents replaced: " + ", ".join(tags[c] for c in changed))
                    st.session_state.emp_doc_updated = True
                    st.rerun()
            st.markdown("#### Delete Employee (Resigned / Left Company)")
            if st.session_state.pop("emp_deleted", None): st.success(f"Employee {st.session_state.pop('emp_deleted_name', '')} deleted.")
            with st.form(f"employee_delete_{er['employee_code']}"):
                st.warning(f"This permanently removes {er['name']} ({er['employee_code']}) from the Employee Register. "
                           "Uploaded documents are moved to the archive. Salary history is kept.")
                confirm_del = st.checkbox("I confirm this employee has left the company and should be deleted.")
                del_btn = st.form_submit_button("Delete Employee", use_container_width=True)
            if del_btn:
                if not confirm_del: st.error("Tick the confirmation box to delete.")
                else:
                    ecode = er["employee_code"]
                    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
                    for col in ["photo_path","pan_doc_path","aadhar_doc_path","passbook_doc_path"]:
                        old = _s(col)
                        if old and Path(old).exists():
                            shutil.move(old, ARCHIVE_DIR / f"EMP_{ecode}_{Path(old).name}")
                    execute("DELETE FROM employees WHERE employee_code=?", (ecode,))
                    audit("DELETE","Employees",ecode,f"Deleted {er['name']}")
                    st.session_state.emp_deleted = True
                    st.session_state.emp_deleted_name = er["name"]
                    st.rerun()
    with t2:
        if "emp_form_n" not in st.session_state:
            st.session_state.emp_form_n = 0
        if st.session_state.pop("emp_added", None):
            st.success(f"Employee {st.session_state.pop('emp_added_name', '')} added.")
        n = st.session_state.emp_form_n
        with st.form(f"employee_add_{n}"):
            head, photo_col = st.columns([3, 1])
            with head:
                logo_col, head = st.columns([1, 5], vertical_alignment="center")
                logo_col.image(str(BASE_DIR / "assets" / "logo.png"), width=90)
                head.markdown(
                    '<div style="text-align:center">'
                    '<div style="font-weight:750;font-size:1.15rem">C. V. PATIL &amp; ASSOCIATES</div>'
                    '<div class="small-note">1002, Trident Business Centre, Oppo. Audi Showroom, Mumbai-Pune Highway, Baner, Pune-411045</div>'
                    '<div style="font-weight:750;font-size:1.3rem;text-decoration:underline;margin-top:14px">EMPLOYEE FORM</div>'
                    '<div class="small-note">(* Marked are compulsory.)</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )
            photo = photo_col.file_uploader("Passport size photo (3.5cm x 4.5cm) *", type=["jpg","jpeg","png"])

            st.markdown("#### 1. Full Name")
            c1,c2,c3,c4 = st.columns(4)
            surname = c1.text_input("Surname *")
            first_name = c2.text_input("First Name *")
            father_name = c3.text_input("Father Name")
            mother_name = c4.text_input("Mother Name")
            c1,c2,c3 = st.columns(3)
            dob = c1.date_input("2. Date of Birth", value=None, min_value=date(1940,1,1), max_value=date.today(), format="DD/MM/YYYY")
            gender = c2.selectbox("3. Gender", ["Male","Female","Other"], index=None, placeholder="Select")
            marital = c3.selectbox("4. Marital Status", ["Single","Married","Divorced","Widowed"], index=None, placeholder="Select")
            perm_addr = st.text_area("5. Permanent Address *", height=80)
            local_addr = st.text_area("6. Local Address *", height=80)
            c1,c2 = st.columns(2)
            telephone = c1.text_input("7. Tel. Phone No.")
            mobile = c2.text_input("8. Cell No. *")
            c1,c2,c3 = st.columns(3)
            email = c1.text_input("9. E-mail Address")
            pan = c2.text_input("10. PAN Card No.")
            aadhar = c3.text_input("11. Aadhar Card No.")

            st.markdown("#### 12. Educational Qualification")
            edu = st.data_editor(
                pd.DataFrame({"Degree": ["Post Graduation","Graduation","HSC / Diploma"],
                              "Specialization": [""]*3, "Year of Passing": [""]*3, "% Marks / Grade": [""]*3}),
                hide_index=True, num_rows="fixed", disabled=["Degree"], use_container_width=True, key=f"emp_edu_{n}",
            )
            skills = st.text_area("13. Software Skills", height=80)

            st.markdown("#### 14. Family Details")
            family = st.data_editor(
                pd.DataFrame({"Family Member": [""]*4, "Relation with you": [""]*4, "Contact Number": [""]*4},
                             index=pd.RangeIndex(1, 5, name="Sr. No.")),
                num_rows="fixed", use_container_width=True, key=f"emp_family_{n}",
            )

            st.markdown("#### 15. Vehicle Details")
            c1,c2,c3 = st.columns(3)
            vehicle_company = c1.text_input("Vehicle Company Name")
            vehicle_no = c2.text_input("Vehicle No.")
            license_no = c3.text_input("License No.")

            st.markdown("#### 16. Bank Details *")
            c1,c2 = st.columns(2)
            bank = c1.text_input("Bank Name *")
            branch = c2.text_input("Branch Name *")
            bank_addr = st.text_input("Address of Bank *")
            c1,c2 = st.columns(2)
            account = c1.text_input("Account No. *")
            ifsc = c2.text_input("IFSC Code *")

            joining = st.date_input("17. Joining Date *", value=date.today(), format="DD/MM/YYYY")

            st.markdown("#### Compulsory Required Documents")
            st.caption("Upload in printable format (PDF / JPG / PNG).")
            c1,c2,c3 = st.columns(3)
            pan_doc = c1.file_uploader("PAN Card Copy *", type=["pdf","jpg","jpeg","png"])
            aadhar_doc = c2.file_uploader("Aadhar Card Copy *", type=["pdf","jpg","jpeg","png"])
            passbook_doc = c3.file_uploader("Bank Passbook - 1st page Copy *", type=["pdf","jpg","jpeg","png"])

            st.markdown("#### Declaration")
            declared = st.checkbox("I hereby declare the information furnished by me is correct. I bear the responsibility for all above information. *")
            go = st.form_submit_button("Add Employee", use_container_width=True)
        if go:
            pan, ifsc = pan.strip().upper(), ifsc.strip().upper()
            aadhar_digits = re.sub(r"\s", "", aadhar)
            required = {"Surname": surname, "First Name": first_name,
                        "Permanent Address": perm_addr, "Local Address": local_addr, "Cell No.": mobile,
                        "Bank Name": bank, "Address of Bank": bank_addr, "Branch Name": branch,
                        "Account No.": account, "IFSC Code": ifsc, "Photo": photo, "PAN Card Copy": pan_doc,
                        "Aadhar Card Copy": aadhar_doc, "Bank Passbook Copy": passbook_doc}
            missing = [k for k, v in required.items() if not (v.strip() if isinstance(v, str) else v)]
            errors = []
            if missing: errors.append("Required: " + ", ".join(missing) + ".")
            if pan and not re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", pan): errors.append("PAN must look like ABCDE1234F.")
            if aadhar_digits and not re.fullmatch(r"\d{12}", aadhar_digits): errors.append("Aadhar must be 12 digits.")
            if ifsc and not re.fullmatch(r"[A-Z]{4}0[A-Z0-9]{6}", ifsc): errors.append("IFSC must look like SBIN0001234.")
            if not declared: errors.append("Please accept the declaration.")
            if errors:
                for msg in errors: st.error(msg)
            else:
                name = " ".join(p.strip() for p in [first_name, surname] if p.strip())
                code = f"EMP{(scalar('SELECT COALESCE(MAX(id),0) FROM employees') or 0) + 1:04d}"
                while scalar("SELECT COUNT(*) FROM employees WHERE employee_code=?", (code,)):
                    code += "X"
                folder = UPLOAD_DIR / "employees" / "".join(c for c in code if c.isalnum() or c in "-_")
                file_prefix = f"{first_name.strip()}_{surname.strip()}".replace(" ", "_")
                photo_path = save_uploaded_file(photo, folder, f"{file_prefix}_Photo")[1]
                pan_path = save_uploaded_file(pan_doc, folder, f"{file_prefix}_PAN")[1]
                aadhar_path = save_uploaded_file(aadhar_doc, folder, f"{file_prefix}_Aadhar")[1]
                passbook_path = save_uploaded_file(passbook_doc, folder, f"{file_prefix}_Passbook")[1]
                record = dict(
                    employee_code=code.strip(), name=name, surname=surname.strip(), first_name=first_name.strip(),
                    father_name=father_name.strip(), mother_name=mother_name.strip(),
                    dob=dob.isoformat() if dob else "", gender=gender or "", marital_status=marital or "",
                    permanent_address=perm_addr.strip(), local_address=local_addr.strip(),
                    telephone=telephone.strip(), mobile=mobile.strip(), email=email.strip(), pan=pan, aadhar=aadhar_digits,
                    education=json.dumps(edu.to_dict("records")), software_skills=skills.strip(),
                    family_details=json.dumps(family.reset_index().to_dict("records")),
                    vehicle_company=vehicle_company.strip(), vehicle_no=vehicle_no.strip(), license_no=license_no.strip(),
                    bank_name=bank.strip(), bank_address=bank_addr.strip(), bank_branch=branch.strip(),
                    account_number=account.strip(), ifsc=ifsc, joining_date=joining.isoformat(),
                    employment_type="Permanent", status="Active", user_role="Employee",
                    photo_path=photo_path, pan_doc_path=pan_path, aadhar_doc_path=aadhar_path,
                    passbook_doc_path=passbook_path, declaration_at=now_str(), created_at=now_str(),
                )
                try:
                    execute(f"INSERT INTO employees({','.join(record)}) VALUES({','.join('?' for _ in record)})",
                            tuple(record.values()))
                    audit("CREATE","Employees",code,name)
                    st.session_state.emp_form_n += 1
                    st.session_state.emp_added, st.session_state.emp_added_name = True, name
                    st.rerun()
                except sqlite3.IntegrityError: st.error("Employee code already exists.")

# ---------------------------- Projects ----------------------------
elif page == "Projects":
    section_title("Projects", "Project master used for linking documents, registers, tasks and approvals")
    t_reg, t_add, t_docs = st.tabs(["Project Hub", "Add Project", "Upload Project Document"])

    def _open_project(code, name):
        st.session_state["proj_open"] = code
        st.session_state["proj_file_sel"] = f"{code} | {name}"

    def _num(v, default=0.0):
        try: return float(v)
        except (TypeError, ValueError): return default

    def _pct(v):
        return int(max(0, min(100, _num(v))))

    def _project_file(pc, k):
        pr = df_query("SELECT * FROM projects WHERE project_code=?", (pc,)).iloc[0]
        days_left = days_to(pr["end_date"]) if pr["end_date"] else None
        cards = [
            ("Project Details", [("Code", pr["project_code"]), ("Name", pr["name"]), ("Type", pr["project_type"] or "-"),
                                 ("Status", pr["status"] or "-"), ("Location", pr["location"] or "-")]),
            ("Client & Team", [("Client", pr["client"] or "-"), ("Client Contact", pr["client_contact"] or "-"),
                               ("Project Manager", pr["manager"] or "-"), ("Work Order No.", pr["work_order_no"] or "-"),
                               ("Contract Value", f"₹ {_num(pr['contract_value']):,.0f}")]),
            ("Schedule", [("Start", pr["start_date"] or "-"), ("End", pr["end_date"] or "-"),
                          ("Days Left", "-" if days_left is None else str(days_left)), ("Progress", f"{_pct(pr['progress'])}%"),
                          ("Created", str(pr["created_at"])[:10])]),
        ]
        st.markdown('<div class="emp-grid">' + "".join(
            f'<div class="emp-card"><div class="emp-card-title">{escape(t)}</div>' +
            "".join(f'<div class="emp-row"><span>{escape(a)}</span><b>{escape(str(b))}</b></div>' for a, b in rows) + '</div>'
            for t, rows in cards) + '</div>', unsafe_allow_html=True)
        st.progress(_pct(pr["progress"]) / 100, text=f"Overall progress: {_pct(pr['progress'])}%")
        if pr["description"]:
            st.markdown(f"**Scope / Description:** {pr['description']}")

        docs = df_query("SELECT id,doc_no,title,category,doc_type,revision,version,issue_date,expiry_date,status,owner,filename,filepath FROM documents WHERE project_code=? AND is_deleted=0 ORDER BY category,doc_no", (pc,))
        tasks = df_query("SELECT title,assignee,due_date,priority,status FROM tasks WHERE record_ref=? OR title LIKE ? ORDER BY due_date", (pc, f"%{pc}%"))
        regs = df_query("SELECT module,record_no,title,owner,record_date,status FROM generic_registers WHERE project_code=? ORDER BY record_date DESC", (pc,))
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Documents", len(docs))
        m2.metric("Approved", int((docs["status"] == "Approved").sum()) if not docs.empty else 0)
        m3.metric("Open Tasks", int((tasks["status"] != "Closed").sum()) if not tasks.empty else 0)
        m4.metric("Register Entries", len(regs))

        st.markdown('<div class="panel-title">Document Checklist</div>', unsafe_allow_html=True)
        counts = docs["category"].value_counts().to_dict() if not docs.empty else {}
        chk = pd.DataFrame([{"Document Set": c, "Available": counts.get(c, 0), "Status": "✔ Available" if counts.get(c, 0) else "✖ Missing"} for c in PROJECT_DOC_CHECKLIST])
        st.dataframe(chk, use_container_width=True, hide_index=True)

        st.markdown('<div class="panel-title">Project Documents</div>', unsafe_allow_html=True)
        if docs.empty:
            st.info("No documents linked to this project yet. Use the 'Upload Project Document' tab.")
        else:
            st.dataframe(docs.drop(columns=["id","filepath"]), use_container_width=True, hide_index=True)
            dsel = st.selectbox("Download a document", [f"{r.doc_no} | {r.title}" for _, r in docs.iterrows()], key=f"proj_dl_sel_{k}")
            drow = docs.iloc[[f"{r.doc_no} | {r.title}" for _, r in docs.iterrows()].index(dsel)]
            file_download_button("Download file", drow["filepath"], f"pdl_{drow['id']}_{k}")
        if not tasks.empty:
            st.markdown('<div class="panel-title">Tasks</div>', unsafe_allow_html=True)
            st.dataframe(tasks, use_container_width=True, hide_index=True)
        if not regs.empty:
            st.markdown('<div class="panel-title">Registers (Engineering / MDR / Transmittals)</div>', unsafe_allow_html=True)
            st.dataframe(regs, use_container_width=True, hide_index=True)


    def _project_edit(ec):
        er = df_query("SELECT * FROM projects WHERE project_code=?", (ec,)).iloc[0]
        def _s(k): return "" if er[k] is None else str(er[k])
        def _d(k):
            try: return date.fromisoformat(_s(k))
            except ValueError: return date.today()
        with st.form(f"project_edit_{ec}"):
            c1,c2,c3 = st.columns(3)
            e_name = c1.text_input("Project Name *", value=_s("name"))
            e_type = c2.selectbox("Project Type", PROJECT_TYPES, index=PROJECT_TYPES.index(_s("project_type")) if _s("project_type") in PROJECT_TYPES else 0)
            e_status = c3.selectbox("Status", PROJECT_STATUSES, index=PROJECT_STATUSES.index(_s("status")) if _s("status") in PROJECT_STATUSES else 0)
            c1,c2,c3 = st.columns(3)
            e_client = c1.text_input("Client", value=_s("client"))
            e_contact = c2.text_input("Client Contact", value=_s("client_contact"))
            e_wo = c3.text_input("Work Order / Contract No.", value=_s("work_order_no"))
            c1,c2,c3 = st.columns(3)
            e_mgr = c1.text_input("Project Manager", value=_s("manager"))
            e_loc = c2.text_input("Location", value=_s("location"))
            e_val = c3.number_input("Contract Value (₹)", min_value=0.0, step=10000.0, value=_num(er["contract_value"]))
            c1,c2,c3 = st.columns(3)
            e_start = c1.date_input("Start Date", value=_d("start_date"))
            e_end = c2.date_input("End Date", value=_d("end_date"))
            e_prog = c3.slider("Progress %", 0, 100, _pct(er["progress"]))
            e_desc = st.text_area("Scope / Description", value=_s("description"))
            save = st.form_submit_button("Save Changes", use_container_width=True)
        if save:
            execute("""UPDATE projects SET name=?,project_type=?,status=?,client=?,client_contact=?,work_order_no=?,manager=?,location=?,
                       contract_value=?,start_date=?,end_date=?,progress=?,description=? WHERE project_code=?""",
                    (e_name.strip(),e_type,e_status,e_client,e_contact,e_wo,e_mgr,e_loc,str(e_val),e_start.isoformat(),e_end.isoformat(),str(e_prog),e_desc,ec))
            audit("UPDATE","Projects",ec,f"Edited {e_name}"); st.success("Project updated."); st.rerun()
        if ROLE == "Admin":
            linked = scalar("SELECT COUNT(*) FROM documents WHERE project_code=? AND is_deleted=0", (ec,))
            st.markdown("**Delete Project (Admin)**")
            if True:
                if linked:
                    st.warning(f"{linked} document(s) are linked to this project, so it cannot be deleted. Close it instead.")
                elif st.checkbox("I confirm this project should be permanently deleted.", key=f"pdel_{ec}") and st.button("Delete Project", key=f"pdelbtn_{ec}"):
                    execute("DELETE FROM projects WHERE project_code=?", (ec,))
                    audit("DELETE","Projects",ec,f"Deleted {er['name']}"); st.success("Project deleted."); st.rerun()


    # ---- Register ----
    with t_reg:
        all_p = df_query("SELECT * FROM projects ORDER BY project_code")
        _po = st.session_state.get("proj_open")
        if _po and _po in set(all_p["project_code"]):
            _pr = all_p[all_p["project_code"] == _po].iloc[0]
            _idx = list(all_p["project_code"]).index(_po)
            _hero = asset_b64(f"proj_{_idx % 6 + 1}.jpg")
            if st.button("← Back to all projects", key="pj_back"):
                st.session_state.pop("proj_open", None); st.rerun()
            st.markdown(
                f'<div class="pj-detail-hero" style="background-image:url({_hero})"><div class="pj-detail-info">'
                f'<h2>{escape(str(_pr["name"]))}</h2><div>{escape(str(_pr["client"] or "-"))} · 📍 {escape(str(_pr["location"] or "-"))}</div>'
                f'<div>{escape(str(_pr["project_code"]))} · {escape(str(_pr["status"] or "-"))} · {_pct(_pr["progress"])}% complete</div></div></div>',
                unsafe_allow_html=True)
            with st.expander("✎ Edit / Update this project", expanded=False):
                _project_edit(_po)
            _project_file(_po, "card")
        else:
            f1, f2, f3 = st.columns([2, 1, 1])
            q = f1.text_input("Search", placeholder="code, name, client, manager, location...", key="proj_q")
            fstat = f2.selectbox("Status", ["All"] + PROJECT_STATUSES, key="proj_fs")
            ftype = f3.selectbox("Type", ["All"] + PROJECT_TYPES, key="proj_ft")
            view = all_p.copy()
            if q:
                ql = q.lower()
                view = view[view.apply(lambda r: ql in " ".join(str(r[c]) for c in ["project_code","name","client","manager","location"]).lower(), axis=1)]
            if fstat != "All": view = view[view["status"] == fstat]
            if ftype != "All": view = view[view["project_type"] == ftype]
            if view.empty:
                st.info("No projects found.")
            else:
                today_s = date.today().isoformat()
                _tone = {"Active": "green", "Planning": "blue", "On Hold": "red", "Completed": "teal", "Closed": "grey"}
                _imgs = [asset_b64(f"proj_{n}.jpg") for n in range(1, 7)]
                rows_ = list(view.itertuples())
                for r0 in range(0, len(rows_), 3):
                    cols = st.columns(3, gap="medium")
                    for ci, p in enumerate(rows_[r0:r0 + 3]):
                        pc = p.project_code
                        n_docs = scalar("SELECT COUNT(*) FROM documents WHERE is_deleted=0 AND project_code=?", (pc,))
                        n_dwg = scalar("SELECT COUNT(*) FROM plant_drawings WHERE is_deleted=0 AND project_code=?", (pc,))
                        n_pend = scalar("SELECT COUNT(*) FROM documents WHERE is_deleted=0 AND project_code=? AND status IN ('Pending Review','Correction Required')", (pc,))
                        n_over = scalar("SELECT COUNT(*) FROM tasks WHERE record_ref=? AND status<>'Closed' AND due_date<>'' AND due_date<?", (pc, today_s))
                        pct = _pct(p.progress)
                        img = _imgs[(r0 + ci) % 6]
                        cols[ci].markdown(
                            f'<div class="pj-card"><div class="pj-img" style="background-image:url({img})"></div><div class="pj-body">'
                            f'<div class="pj-head"><div><div class="pj-name">{escape(str(p.name))}</div><div class="pj-client">{escape(str(p.client or "-"))}</div>'
                            f'<div class="pj-loc">📍 {escape(str(p.location or "-"))}</div></div><span class="pj-pill {_tone.get(p.status, "grey")}">{escape(str(p.status or "-"))}</span></div>'
                            f'<div class="pj-bar"><i style="width:{pct}%"></i></div><div class="pj-pct">{pct}%</div>'
                            f'<div class="pj-stats"><div><span>Documents</span><b>{n_docs}</b></div><div><span>Drawings</span><b>{n_dwg}</b></div>'
                            f'<div class="pend"><span>Pending</span><b>{n_pend}</b></div><div class="over"><span>Overdue</span><b>{n_over}</b></div></div><div class="pj-open">Open Workspace →</div></div></div>',
                            unsafe_allow_html=True)
                        cols[ci].button("Open", key=f"pj_open_{pc}", use_container_width=True,
                                        on_click=_open_project, args=(pc, p.name))
                st.caption(f"{len(view)} project(s)")

    # ---- Add ----
    with t_add:
        with st.form("project_add", clear_on_submit=True):
            c1,c2,c3 = st.columns(3)
            code = c1.text_input("Project Code *")
            name = c2.text_input("Project Name *")
            ptype = c3.selectbox("Project Type", PROJECT_TYPES)
            c1,c2,c3 = st.columns(3)
            client = c1.text_input("Client")
            client_contact = c2.text_input("Client Contact (name / phone / email)")
            wo_no = c3.text_input("Work Order / Contract No.")
            c1,c2,c3 = st.columns(3)
            manager = c1.text_input("Project Manager")
            location = c2.text_input("Location")
            cvalue = c3.number_input("Contract Value (₹)", min_value=0.0, step=10000.0)
            c1,c2,c3,c4 = st.columns(4)
            status = c1.selectbox("Status", PROJECT_STATUSES)
            start = c2.date_input("Start Date", value=date.today())
            end = c3.date_input("End Date", value=date.today()+timedelta(days=180))
            progress = c4.slider("Progress %", 0, 100, 0)
            desc = st.text_area("Scope / Description")
            go = st.form_submit_button("Add Project", use_container_width=True)
        if go:
            if not code.strip() or not name.strip():
                st.error("Project code and name are required.")
            else:
                try:
                    execute("""INSERT INTO projects(project_code,name,client,manager,start_date,end_date,status,location,description,created_at,
                               project_type,client_contact,work_order_no,contract_value,progress) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (code.strip(),name.strip(),client,manager,start.isoformat(),end.isoformat(),status,location,desc,now_str(),
                             ptype,client_contact,wo_no,str(cvalue),str(progress)))
                    audit("CREATE","Projects",code.strip(),name.strip()); st.success("Project added.")
                except sqlite3.IntegrityError: st.error("Project code already exists.")

    # ---- Upload a document straight into a project ----
    with t_docs:
        plist = df_query("SELECT project_code,name FROM projects ORDER BY project_code")
        if plist.empty:
            st.info("Add a project first.")
        else:
            with st.form("proj_doc_upload", clear_on_submit=True):
                st.write("**Automatic document number:**", next_doc_no())
                c1,c2,c3 = st.columns(3)
                p_sel = c1.selectbox("Project *", [f"{r.project_code} | {r['name']}" for _, r in plist.iterrows()])
                p_cat = c2.selectbox("Document Set *", PROJECT_DOC_CHECKLIST)
                p_title = c3.text_input("Document Title *")
                c1,c2,c3 = st.columns(3)
                p_type = c1.text_input("Document Type", placeholder="Work order / Drawing / Report / Invoice")
                p_rev = c2.text_input("Revision", value="R0")
                p_issue = c3.date_input("Issue Date", value=date.today())
                c1,c2,c3 = st.columns(3)
                p_owner = c1.text_input("Owner / Responsible Person")
                p_conf = c2.selectbox("Confidentiality", ["Internal","Confidential","Restricted","Public"])
                p_exp_on = c3.checkbox("Has Expiry")
                p_exp = st.date_input("Expiry Date", value=date.today()+timedelta(days=365)) if p_exp_on else None
                p_desc = st.text_area("Remarks")
                p_file = st.file_uploader("Upload File *", key="proj_doc_file")
                p_go = st.form_submit_button("Save to Project File", use_container_width=True)
            if p_go:
                if not p_title.strip() or p_file is None:
                    st.error("Document title and file are required.")
                else:
                    p_code = p_sel.split(" | ")[0]
                    p_dept = scalar("SELECT name FROM departments ORDER BY name LIMIT 1", default="")
                    doc_no = next_doc_no()
                    fname, fpath = save_uploaded_file(p_file, UPLOAD_DIR/"documents", doc_no)
                    doc_status = "Pending Review" if ROLE in ["Employee","HR","Accounts","Manager"] else "Draft"
                    stage = "Manager Review" if doc_status == "Pending Review" else "Draft"
                    doc_id = execute("""INSERT INTO documents(doc_no,title,category,doc_type,department,related_to,related_ref,project_code,owner,revision,issue_date,expiry_date,reminder_days,version,confidentiality,description,filename,filepath,status,approval_stage,created_by,created_at,updated_at)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (doc_no,p_title.strip(),p_cat,p_type,p_dept,"Project",p_code,p_code,p_owner,p_rev,p_issue.isoformat(),p_exp.isoformat() if p_exp else "",30,1,p_conf,p_desc,fname,fpath,doc_status,stage,USER,now_str(),now_str()))
                    if doc_status == "Pending Review":
                        execute("INSERT INTO approvals(doc_id,reviewer_role,reviewer,status,comments,action_date,created_at) VALUES(?,?,?,?,?,?,?)",
                                (doc_id,"Manager","Manager","Pending","",  "", now_str()))
                    audit("CREATE","Documents",doc_no,f"Project {p_code}: {fname}")
                    st.success(f"Saved to project {p_code} as {doc_no}.")

# ---------------------------- Insurance ----------------------------
elif page == "Insurance":
    section_title("Insurance Register", "Policy documents, employee/asset linkage, expiry reminders, renewal and archive")
    t1,t2,t3 = st.tabs(["Register","Add Policy","Renew Policy"])
    with t1:
        ins = df_query("SELECT id,policy_no,policy_type,company,related_type,related_ref,start_date,expiry_date,premium,sum_insured,broker,reminder_days,status,filename,filepath FROM insurance ORDER BY expiry_date")
        if not ins.empty:
            ins["Days Left"] = ins["expiry_date"].apply(days_to)
            st.dataframe(ins.drop(columns=["filepath"]), use_container_width=True, hide_index=True)
        else: st.info("No insurance policies yet.")
    with t2:
        with st.form("ins_add", clear_on_submit=True):
            c1,c2,c3 = st.columns(3)
            policy = c1.text_input("Policy Number *")
            ptype = c2.selectbox("Policy Type", ["Employee Mediclaim","Vehicle","Asset","Professional Indemnity","Fire","Workmen Compensation","Other"])
            company = c3.text_input("Insurance Company")
            c1,c2,c3 = st.columns(3)
            related_type = c1.selectbox("Related To", ["Employee","Vehicle","Asset","Company","Project"])
            related_ref = c2.text_input("Employee / Asset / Vehicle / Project Ref")
            broker = c3.text_input("Broker / Contact")
            c1,c2,c3 = st.columns(3)
            start = c1.date_input("Start Date", value=date.today())
            expiry = c2.date_input("Expiry Date", value=date.today()+timedelta(days=365))
            reminder = c3.selectbox("Reminder Before Expiry", [30,15,7,1])
            c1,c2 = st.columns(2)
            premium = c1.number_input("Premium", min_value=0.0, step=1000.0, value=None) or 0.0
            insured = c2.number_input("Sum Insured", min_value=0.0, step=10000.0, value=None) or 0.0
            upl = st.file_uploader("Upload Policy Document")
            go=st.form_submit_button("Add Policy", use_container_width=True)
        if go:
            try:
                fname,fpath = save_uploaded_file(upl, UPLOAD_DIR/"insurance", policy) if upl else ("","")
                status = status_from_expiry(expiry.isoformat(), reminder)
                execute("""INSERT INTO insurance(policy_no,policy_type,company,related_type,related_ref,start_date,expiry_date,premium,sum_insured,broker,reminder_days,status,filename,filepath,created_at,updated_at)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (policy,ptype,company,related_type,related_ref,start.isoformat(),expiry.isoformat(),premium,insured,broker,reminder,status,fname,fpath,now_str(),now_str()))
                audit("CREATE","Insurance",policy,ptype); st.success("Insurance policy added.")
            except sqlite3.IntegrityError: st.error("Policy number already exists.")
    with t3:
        ins = df_query("SELECT * FROM insurance ORDER BY policy_no")
        if ins.empty: st.info("No policy available to renew.")
        else:
            labels=[f"{r.policy_no} | {r.policy_type}" for _,r in ins.iterrows()]
            sel=st.selectbox("Policy", labels)
            row=ins.iloc[labels.index(sel)]
            with st.form("ins_renew"):
                new_exp = st.date_input("New Expiry Date", value=date.today()+timedelta(days=365))
                _cur_prem = float(row["premium"] or 0)
                new_premium = st.number_input("New Premium", min_value=0.0, step=500.0, format="%.2f",
                                              value=_cur_prem if _cur_prem else None, placeholder="Type the new premium amount",
                                              key=f"ins_new_premium_{row['id']}")
                new_premium = new_premium or 0.0
                new_file = st.file_uploader("Renewed Policy Document")
                go=st.form_submit_button("Renew")
            if go:
                if row["filepath"] and Path(row["filepath"]).exists():
                    shutil.copy2(Path(row["filepath"]), ARCHIVE_DIR / f"INS_{row['policy_no']}_{Path(row['filepath']).name}")
                fname,fpath = save_uploaded_file(new_file, UPLOAD_DIR/"insurance", row["policy_no"]) if new_file else (row["filename"],row["filepath"])
                execute("UPDATE insurance SET expiry_date=?,premium=?,status='Renewed',filename=?,filepath=?,updated_at=? WHERE id=?",
                        (new_exp.isoformat(),new_premium,fname,fpath,now_str(),int(row["id"])))
                audit("RENEW","Insurance",row["policy_no"],f"New expiry {new_exp.isoformat()}")
                st.success("Policy renewed. Previous file retained in archive when available.")

# ---------------------------- Contracts ----------------------------
elif page == "Contracts":
    section_title("Contracts", "Contract register with expiry and renewal reminders")
    with st.expander("Add Contract"):
        with st.form("contract_add", clear_on_submit=True):
            c1,c2,c3 = st.columns(3)
            cno=c1.text_input("Contract No. *")
            title=c2.text_input("Title *")
            party=c3.text_input("Counterparty")
            c1,c2,c3 = st.columns(3)
            start=c1.date_input("Start", value=date.today())
            expiry=c2.date_input("Expiry", value=date.today()+timedelta(days=365))
            reminder=c3.selectbox("Reminder Days", [30,15,7,1])
            c1,c2=st.columns(2)
            value=c1.number_input("Contract Value", min_value=0.0, step=10000.0, value=None) or 0.0
            owner=c2.text_input("Owner")
            upl=st.file_uploader("Contract File")
            go=st.form_submit_button("Add Contract")
        if go:
            try:
                fname,fpath=save_uploaded_file(upl, UPLOAD_DIR/"contracts", cno) if upl else ("","")
                execute("INSERT INTO contracts(contract_no,title,counterparty,start_date,expiry_date,value,owner,reminder_days,status,filename,filepath,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                        (cno,title,party,start.isoformat(),expiry.isoformat(),value,owner,reminder,status_from_expiry(expiry.isoformat(),reminder),fname,fpath,now_str()))
                audit("CREATE","Contracts",cno,title); st.success("Contract added.")
            except sqlite3.IntegrityError: st.error("Contract number already exists.")
    d=df_query("SELECT id,contract_no,title,counterparty,start_date,expiry_date,value,owner,reminder_days,status,filename FROM contracts ORDER BY expiry_date")
    if not d.empty: d["Days Left"]=d["expiry_date"].apply(days_to)
    st.dataframe(d,use_container_width=True,hide_index=True)

# ---------------------------- Salary ----------------------------
elif page == "Salary":
    section_title("Salary", "Monthly salary components with automatic gross, deduction and net salary calculation")
    emps=df_query("SELECT employee_code,name FROM employees WHERE status='Active' ORDER BY employee_code")
    with st.expander("Add / Update Salary", expanded=False):
        if emps.empty: st.info("Add employees first.")
        else:
            with st.form("salary_form"):
                labels=[f"{r.employee_code} | {r.name}" for _,r in emps.iterrows()]
                sel=st.selectbox("Employee",labels)
                ecode=emps.iloc[labels.index(sel)]["employee_code"]
                month=st.text_input("Salary Month", value=date.today().strftime("%Y-%m"))
                c1,c2,c3,c4=st.columns(4)
                basic=c1.number_input("Basic",min_value=0.0,value=None) or 0.0
                hra=c2.number_input("HRA",min_value=0.0,value=None) or 0.0
                allow=c3.number_input("Allowances",min_value=0.0,value=None) or 0.0
                bonus=c4.number_input("Bonus",min_value=0.0,value=None) or 0.0
                c1,c2,c3=st.columns(3)
                pf=c1.number_input("PF",min_value=0.0,value=None) or 0.0
                tax=c2.number_input("Tax",min_value=0.0,value=None) or 0.0
                other=c3.number_input("Other Deductions",min_value=0.0,value=None) or 0.0
                gross=basic+hra+allow+bonus; deductions=pf+tax+other; net=gross-deductions
                st.info(f"Gross: {money(gross)}   |   Deductions: {money(deductions)}   |   Net: {money(net)}")
                go=st.form_submit_button("Save Salary")
            if go:
                execute("""INSERT INTO salary(employee_code,salary_month,basic,hra,allowances,bonus,pf,tax,other_deductions,gross,deductions,net,created_at)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                           ON CONFLICT(employee_code,salary_month) DO UPDATE SET basic=excluded.basic,hra=excluded.hra,allowances=excluded.allowances,bonus=excluded.bonus,pf=excluded.pf,tax=excluded.tax,other_deductions=excluded.other_deductions,gross=excluded.gross,deductions=excluded.deductions,net=excluded.net""",
                        (ecode,month,basic,hra,allow,bonus,pf,tax,other,gross,deductions,net,now_str()))
                audit("UPSERT","Salary",f"{ecode}-{month}",f"Net {net}"); st.success("Salary saved.")
    d=df_query("""SELECT s.salary_month,s.employee_code,e.name,s.basic,s.hra,s.allowances,s.bonus,s.gross,s.pf,s.tax,s.other_deductions,s.deductions,s.net
                  FROM salary s LEFT JOIN employees e ON s.employee_code=e.employee_code ORDER BY s.salary_month DESC,s.employee_code""")
    st.dataframe(d,use_container_width=True,hide_index=True)

    st.markdown('<div class="panel-title" style="margin-top:14px">Download Salary Slip</div>', unsafe_allow_html=True)
    if d.empty:
        st.info("No salary records yet. Add a salary above to generate a slip.")
    else:
        s1, s2 = st.columns(2)
        months = sorted(d["salary_month"].unique().tolist(), reverse=True)
        slip_month = s1.selectbox("Salary Month", months, key="slip_month")
        month_rows = d[d["salary_month"] == slip_month]
        slip_labels = [f"{r.employee_code} | {r['name'] if r['name'] else ''}" for _, r in month_rows.iterrows()]
        slip_sel = s2.selectbox("Employee", slip_labels, key="slip_emp")
        slip_code = slip_sel.split(" | ")[0]
        sal_row = df_query("SELECT * FROM salary WHERE employee_code=? AND salary_month=?", (slip_code, slip_month)).iloc[0].to_dict()
        emp_df = df_query("SELECT * FROM employees WHERE employee_code=?", (slip_code,))
        emp_row = emp_df.iloc[0].to_dict() if not emp_df.empty else {"employee_code": slip_code}
        slip_pdf = build_salary_slip_pdf(emp_row, sal_row)
        b1, b2 = st.columns(2)
        b1.download_button("Download Salary Slip (PDF)", slip_pdf, file_name=f"Salary_Slip_{slip_code}_{slip_month}.pdf",
                           mime="application/pdf", use_container_width=True,
                           on_click=lambda: audit("DOWNLOAD", "Salary", f"{slip_code}-{slip_month}", "Salary slip downloaded"))
        if len(month_rows) > 1:
            import zipfile as _zf
            zbuf = io.BytesIO()
            with _zf.ZipFile(zbuf, "w", _zf.ZIP_DEFLATED) as z:
                for _, mr in month_rows.iterrows():
                    code = mr["employee_code"]
                    srow = df_query("SELECT * FROM salary WHERE employee_code=? AND salary_month=?", (code, slip_month)).iloc[0].to_dict()
                    edf = df_query("SELECT * FROM employees WHERE employee_code=?", (code,))
                    z.writestr(f"Salary_Slip_{code}_{slip_month}.pdf", build_salary_slip_pdf(edf.iloc[0].to_dict() if not edf.empty else {"employee_code": code}, srow))
            b2.download_button(f"Download All Slips for {slip_month} (ZIP)", zbuf.getvalue(), file_name=f"Salary_Slips_{slip_month}.zip",
                               mime="application/zip", use_container_width=True)

# ---------------------------- Accounts ----------------------------
elif page == "Accounts":
    section_title("Accounts", "Simple company receipt/payment register and financial document references")
    with st.expander("Add Entry"):
        with st.form("acc_form", clear_on_submit=True):
            c1,c2,c3=st.columns(3)
            edate=c1.date_input("Date",value=date.today())
            etype=c2.selectbox("Entry Type",["Receipt","Payment","Journal"])
            cat=c3.selectbox("Category",["Salary","Vendor","Client","Insurance","Tax","Office","Travel","Project","Other"])
            c1,c2,c3=st.columns(3)
            amount=c1.number_input("Amount",min_value=0.0,value=None) or 0.0
            ref=c2.text_input("Reference / Voucher No.")
            party=c3.text_input("Party")
            desc=st.text_area("Description")
            go=st.form_submit_button("Add Entry")
        if go:
            rid=execute("INSERT INTO accounts(entry_date,entry_type,category,amount,reference,party,description,created_by,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                        (edate.isoformat(),etype,cat,amount,ref,party,desc,USER,now_str()))
            audit("CREATE","Accounts",rid,f"{etype} {amount}"); st.success("Account entry added.")
    if st.session_state.pop("account_deleted", False):
        st.success("Account entry deleted.")
    d=df_query("SELECT id,entry_date,entry_type,category,amount,reference,party,description,created_by FROM accounts ORDER BY entry_date DESC,id DESC")
    st.dataframe(d,use_container_width=True,hide_index=True)
    receipts=float(d.loc[d.entry_type=='Receipt','amount'].sum()) if not d.empty else 0
    payments=float(d.loc[d.entry_type=='Payment','amount'].sum()) if not d.empty else 0
    c1,c2,c3=st.columns(3); c1.metric("Receipts",money(receipts)); c2.metric("Payments",money(payments)); c3.metric("Net",money(receipts-payments))
    with st.expander("Delete Entry"):
        if d.empty:
            st.info("No account entries available to delete.")
        else:
            entries = d.set_index("id")
            entry_id = st.selectbox(
                "Select account entry", entries.index.tolist(), key="account_delete_id",
                format_func=lambda rid: f"#{rid} | {entries.loc[rid, 'entry_date']} | {entries.loc[rid, 'entry_type']} | {money(entries.loc[rid, 'amount'])} | {entries.loc[rid, 'reference']} | {entries.loc[rid, 'party']}"
            )
            confirmed = st.checkbox("Permanently delete this entry", key=f"account_delete_confirm_{entry_id}")
            if st.button("Delete Entry", key="account_delete", disabled=not confirmed):
                row = entries.loc[entry_id]
                execute("DELETE FROM accounts WHERE id=?", (int(entry_id),))
                audit("DELETE", "Accounts", int(entry_id), f"{row['entry_type']} {row['amount']} | {row['reference']} | {row['party']}")
                st.session_state["account_deleted"] = True
                st.rerun()

# ---------------------------- Tasks ----------------------------
elif page == "Tasks & Reminders":
    section_title("Tasks & Reminders", "Operational tasks, due dates, priorities and escalation tracking")
    with st.expander("Create Task"):
        with st.form("task_form", clear_on_submit=True):
            c1,c2,c3=st.columns(3)
            title=c1.text_input("Task Title *")
            module=c2.selectbox("Module",["Documents","Insurance","Contracts","Projects","HR","Accounts","Compliance","Other"])
            ref=c3.text_input("Record Reference")
            c1,c2,c3=st.columns(3)
            assignee=c1.text_input("Assignee")
            due=c2.date_input("Due Date",value=date.today()+timedelta(days=7))
            priority=c3.selectbox("Priority",["Low","Medium","High","Urgent"])
            c1,c2=st.columns(2)
            status=c1.selectbox("Status",["Open","In Progress","Waiting","Closed"])
            escalation=c2.text_input("Escalation To")
            notes=st.text_area("Notes")
            go=st.form_submit_button("Create Task")
        if go:
            rid=execute("INSERT INTO tasks(title,module,record_ref,assignee,due_date,priority,status,escalation,notes,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (title,module,ref,assignee,due.isoformat(),priority,status,escalation,notes,now_str()))
            audit("CREATE","Tasks",rid,title); st.success("Task created.")
    d=df_query("SELECT id,title,module,record_ref,assignee,due_date,priority,status,escalation,notes FROM tasks ORDER BY CASE priority WHEN 'Urgent' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END,due_date")
    if not d.empty:
        d["Days Left"]=d["due_date"].apply(days_to)
    st.dataframe(d,use_container_width=True,hide_index=True)

# ---------------------------- Plant Drawings ----------------------------
elif page == "Plant Drawings":
    section_title("Plant Drawings", "Plant layouts, P&IDs, general arrangement, civil, electrical and piping drawings with revision control")
    DWG_TYPES = ["Plant Layout", "P&ID", "General Arrangement (GA)", "Piping / Isometric", "Civil / Structural", "Electrical", "Instrumentation", "Equipment Detail", "As-Built", "Other"]
    DWG_DISCIPLINES = ["Process", "Mechanical", "Piping", "Civil", "Structural", "Electrical", "Instrumentation", "HVAC", "Architectural", "General"]
    DWG_STATUS = ["Draft", "Issued for Review", "Issued for Approval", "Approved", "Issued for Construction", "As-Built", "Superseded"]
    DWG_SIZES = ["A0", "A1", "A2", "A3", "A4"]
    DWG_FILES = ["pdf", "dwg", "dxf", "png", "jpg", "jpeg"]
    d_reg, d_new, d_rev, d_del = st.tabs(["Drawing Register", "Upload AutoCAD Drawing", "Revise Drawing", "Delete Drawing"])
    proj_codes = df_query("SELECT project_code FROM projects ORDER BY project_code")["project_code"].tolist()

    with d_reg:
        f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
        dq = f1.text_input("Search", placeholder="drawing no., title, area, prepared by...", key="dwg_q")
        dproj = f2.selectbox("Project", ["All"] + proj_codes, key="dwg_proj")
        dtype = f3.selectbox("Drawing Type", ["All"] + DWG_TYPES, key="dwg_type")
        dstat = f4.selectbox("Status", ["All"] + DWG_STATUS, key="dwg_stat")
        sql = "SELECT id,drawing_no,title,project_code,plant_area,discipline,drawing_type,revision,status,scale,sheet_size,prepared_by,checked_by,approved_by,issue_date,filename,filepath FROM plant_drawings WHERE is_deleted=0"
        prm = []
        if dq:
            like = f"%{dq}%"; sql += " AND (drawing_no LIKE ? OR title LIKE ? OR plant_area LIKE ? OR prepared_by LIKE ?)"; prm += [like] * 4
        if dproj != "All": sql += " AND project_code=?"; prm.append(dproj)
        if dtype != "All": sql += " AND drawing_type=?"; prm.append(dtype)
        if dstat != "All": sql += " AND status=?"; prm.append(dstat)
        dd = df_query(sql + " ORDER BY updated_at DESC", prm)
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Drawings", len(dd))
        k2.metric("Approved", int(dd["status"].isin(["Approved", "Issued for Construction", "As-Built"]).sum()) if not dd.empty else 0)
        k3.metric("Under Review", int(dd["status"].isin(["Issued for Review", "Issued for Approval"]).sum()) if not dd.empty else 0)
        k4.metric("Draft", int((dd["status"] == "Draft").sum()) if not dd.empty else 0)
        if dd.empty:
            st.info("No drawings found. Use 'Upload AutoCAD Drawing' to add one.")
        else:
            st.dataframe(dd.drop(columns=["id", "filepath"]), use_container_width=True, hide_index=True)
            st.markdown('<div class="panel-title" style="margin-top:14px">View / Download Drawing</div>', unsafe_allow_html=True)
            dlabels = [f"{r.drawing_no} | {r.title} | {r.revision}" for _, r in dd.iterrows()]
            dsel = st.selectbox("Select drawing", dlabels, key="dwg_view_sel")
            drow = dd.iloc[dlabels.index(dsel)]
            fp = drow["filepath"]
            if fp and Path(fp).exists():
                if Path(fp).suffix.lower() in [".png", ".jpg", ".jpeg"]:
                    st.image(fp, caption=f"{drow['drawing_no']} - {drow['title']} (Rev {drow['revision']})", use_container_width=True)
                file_download_button(f"Download {drow['filename']}", fp, f"dwgdl_{drow['id']}")
            else:
                st.warning("No file is attached to this drawing.")
            hist = df_query('SELECT revision AS Revision, filename AS File, note AS Note, changed_by AS "Changed By", changed_at AS "Changed At" FROM plant_drawing_revisions WHERE drawing_id=? ORDER BY id DESC', (int(drow["id"]),))
            if not hist.empty:
                st.markdown("**Revision history**")
                st.dataframe(hist, use_container_width=True, hide_index=True)

    with d_new:
        with st.form("dwg_new", clear_on_submit=True):
            st.write("**Automatic drawing number:**", next_record_no("DWG", "plant_drawings", "drawing_no"))
            c1, c2, c3 = st.columns(3)
            n_title = c1.text_input("Drawing Title *", placeholder="e.g. Main Plant General Layout")
            n_proj = c2.selectbox("Project", [""] + proj_codes)
            n_area = c3.text_input("Plant Area / Unit", placeholder="e.g. Unit 2 - Boiler House")
            c1, c2, c3 = st.columns(3)
            n_type = c1.selectbox("Drawing Type *", DWG_TYPES)
            n_disc = c2.selectbox("Discipline", DWG_DISCIPLINES)
            n_status = c3.selectbox("Status", DWG_STATUS)
            c1, c2, c3, c4 = st.columns(4)
            n_rev = c1.text_input("Revision", value="R0")
            n_scale = c2.text_input("Scale", placeholder="1:100")
            n_size = c3.selectbox("Sheet Size", DWG_SIZES, index=2)
            n_date = c4.date_input("Issue Date", value=date.today())
            c1, c2, c3 = st.columns(3)
            n_prep = c1.text_input("Prepared By")
            n_chk = c2.text_input("Checked By")
            n_app = c3.text_input("Approved By")
            n_rem = st.text_area("Remarks")
            st.caption("AutoCAD files (.dwg, .dxf) are stored and can be downloaded and opened in AutoCAD. PDF, PNG and JPG drawings are also accepted.")
            n_file = st.file_uploader("AutoCAD Drawing File * (DWG / DXF, or PDF / PNG / JPG)", type=DWG_FILES, key="dwg_new_file")
            n_go = st.form_submit_button("Save Drawing", use_container_width=True)
        if n_go:
            if not n_title.strip() or n_file is None:
                st.error("Drawing title and file are required.")
            else:
                dno = next_record_no("DWG", "plant_drawings", "drawing_no")
                fname, fpath = save_uploaded_file(n_file, UPLOAD_DIR / "drawings", dno)
                did = execute("""INSERT INTO plant_drawings(drawing_no,title,project_code,plant_area,discipline,drawing_type,revision,status,scale,sheet_size,prepared_by,checked_by,approved_by,issue_date,remarks,filename,filepath,created_by,created_at,updated_at)
                                 VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                              (dno, n_title.strip(), n_proj, n_area, n_disc, n_type, n_rev, n_status, n_scale, n_size, n_prep, n_chk, n_app, n_date.isoformat(), n_rem, fname, fpath, USER, now_str(), now_str()))
                execute("INSERT INTO plant_drawing_revisions(drawing_id,revision,filename,filepath,note,changed_by,changed_at) VALUES(?,?,?,?,?,?,?)",
                        (did, n_rev, fname, fpath, "Initial issue", USER, now_str()))
                audit("CREATE", "Plant Drawings", dno, f"{n_title.strip()} ({fname})")
                st.success(f"Drawing saved as {dno}.")

    with d_rev:
        rd = df_query("SELECT id,drawing_no,title,revision,status FROM plant_drawings WHERE is_deleted=0 ORDER BY updated_at DESC")
        if rd.empty:
            st.info("No drawings to revise.")
        else:
            rlabels = [f"{r.drawing_no} | {r.title} | {r.revision}" for _, r in rd.iterrows()]
            rsel = st.selectbox("Select drawing", rlabels, key="dwg_rev_sel")
            rrow = rd.iloc[rlabels.index(rsel)]
            _digits = "".join(ch for ch in str(rrow["revision"]) if ch.isdigit())
            with st.form("dwg_rev_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                r_rev = c1.text_input("New Revision", value=f"R{int(_digits or 0) + 1}")
                r_stat = c2.selectbox("Status", DWG_STATUS, index=DWG_STATUS.index(rrow["status"]) if rrow["status"] in DWG_STATUS else 0)
                r_note = st.text_input("Revision note / what changed")
                r_file = st.file_uploader("New revision file * (DWG / DXF, or PDF / PNG / JPG)", type=DWG_FILES, key="dwg_rev_file")
                r_go = st.form_submit_button("Upload Revision", use_container_width=True)
            if r_go:
                if r_file is None:
                    st.error("Please choose the new revision file.")
                else:
                    fname, fpath = save_uploaded_file(r_file, UPLOAD_DIR / "drawings", rrow["drawing_no"])
                    execute("UPDATE plant_drawings SET revision=?,status=?,filename=?,filepath=?,issue_date=?,updated_at=? WHERE id=?",
                            (r_rev, r_stat, fname, fpath, date.today().isoformat(), now_str(), int(rrow["id"])))
                    execute("INSERT INTO plant_drawing_revisions(drawing_id,revision,filename,filepath,note,changed_by,changed_at) VALUES(?,?,?,?,?,?,?)",
                            (int(rrow["id"]), r_rev, fname, fpath, r_note, USER, now_str()))
                    audit("REVISION", "Plant Drawings", rrow["drawing_no"], f"{r_rev}: {r_note}")
                    st.success(f"{rrow['drawing_no']} updated to {r_rev}. Earlier revisions are kept in the history.")

    with d_del:
        if ROLE not in ["Admin", "Manager"]:
            st.info("Only Admin or Manager can delete drawings.")
        else:
            xd = df_query("SELECT id,drawing_no,title,revision FROM plant_drawings WHERE is_deleted=0 ORDER BY updated_at DESC")
            if xd.empty:
                st.info("No drawings available to delete.")
            else:
                xlabels = [f"{r.drawing_no} | {r.title} | {r.revision}" for _, r in xd.iterrows()]
                xsel = st.selectbox("Select drawing", xlabels, key="dwg_del_sel")
                xrow = xd.iloc[xlabels.index(xsel)]
                xreason = st.text_input("Reason for deletion", key="dwg_del_reason")
                xok = st.checkbox("I confirm I want to delete this drawing.", key="dwg_del_ok")
                if st.button("Delete Drawing", type="primary", disabled=not xok, key="dwg_del_btn"):
                    execute("UPDATE plant_drawings SET is_deleted=1,updated_at=? WHERE id=?", (now_str(), int(xrow["id"])))
                    audit("DELETE", "Plant Drawings", xrow["drawing_no"], xreason or "Deleted by user")
                    st.success(f"{xrow['drawing_no']} deleted."); st.rerun()

# ---------------------------- Engineering Registers ----------------------------
elif page == "Engineering Registers":
    section_title("Engineering & Corporate Registers", "Drawing register, MDR, transmittals, correspondence, MOM, vendors and compliance")
    modules=["Drawing Register","MDR","Transmittal","Correspondence","MOM","Vendor Register","Compliance Register"]
    _dwg_label = f"{page_icons['Plant Drawings']}  Plant Drawings"
    if _dwg_label in display_to_page:
        def _open_drawings(): st.session_state["side_nav"] = _dwg_label
        st.button("⬡  Open Plant Drawings  ·  Upload AutoCAD Drawing", on_click=_open_drawings, key="open_plant_drawings")
    selected=st.selectbox("Register",modules)
    with st.expander(f"Add {selected}"):
        with st.form("genreg",clear_on_submit=True):
            c1,c2,c3=st.columns(3)
            rno=c1.text_input("Record No.")
            title=c2.text_input("Title *")
            project=c3.selectbox("Project",[""]+df_query("SELECT project_code FROM projects ORDER BY project_code")["project_code"].tolist())
            c1,c2,c3=st.columns(3)
            owner=c1.text_input("Owner")
            rdate=c2.date_input("Date",value=date.today())
            status=c3.selectbox("Status",["Open","Draft","Issued","Approved","Closed","Superseded"])
            remarks=st.text_area("Remarks")
            go=st.form_submit_button("Add Record")
        if go:
            rid=execute("INSERT INTO generic_registers(module,record_no,title,project_code,owner,record_date,status,remarks,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                        (selected,rno,title,project,owner,rdate.isoformat(),status,remarks,now_str()))
            audit("CREATE",selected,rno or rid,title); st.success("Record added.")
    st.dataframe(df_query("SELECT record_no,title,project_code,owner,record_date,status,remarks FROM generic_registers WHERE module=? ORDER BY record_date DESC,id DESC",(selected,)),use_container_width=True,hide_index=True)

# ---------------------------- Reports ----------------------------
elif page == "Reports":
    section_title("Reports & Exports", "Operational summary for management review")
    tables={
        "Documents":"SELECT * FROM documents WHERE is_deleted=0",
        "Employees":"SELECT * FROM employees",
        "Projects":"SELECT * FROM projects",
        "Insurance":"SELECT * FROM insurance",
        "Contracts":"SELECT * FROM contracts",
        "Salary":"SELECT * FROM salary",
        "Accounts":"SELECT * FROM accounts",
        "Tasks":"SELECT * FROM tasks",
        "Audit":"SELECT * FROM audit_log",
    }
    sel=st.selectbox("Report",list(tables.keys()))
    d=df_query(tables[sel])
    st.dataframe(d,use_container_width=True,hide_index=True)
    st.markdown("### Management Snapshot")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Documents",scalar("SELECT COUNT(*) FROM documents WHERE is_deleted=0"))
    c2.metric("Approved",scalar("SELECT COUNT(*) FROM documents WHERE is_deleted=0 AND status='Approved'"))
    c3.metric("Open Tasks",scalar("SELECT COUNT(*) FROM tasks WHERE status<>'Closed'"))
    c4.metric("Projects",scalar("SELECT COUNT(*) FROM projects WHERE status IN ('Planning','Active','On Hold')"))

# ---------------------------- Audit ----------------------------
elif page == "Audit Trail":
    section_title("Audit Trail", "Login, upload, approval, revision, renewal and administrative activity")
    log = df_query("SELECT id,timestamp,username,action,module,record_ref,details FROM audit_log ORDER BY id DESC")
    if log.empty:
        st.info("No activity has been recorded yet.")
    else:
        log["dt"] = pd.to_datetime(log["timestamp"], errors="coerce")
        today_s = date.today().isoformat()
        # ---- summary ----
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Total Events", len(log))
        k2.metric("Today", int((log["dt"].dt.date.astype(str) == today_s).sum()))
        k3.metric("Active Users (7 days)", int(log[log["dt"] >= pd.Timestamp.now() - pd.Timedelta(days=7)]["username"].nunique()))
        k4.metric("Logins", int((log["action"] == "LOGIN").sum()))
        k5.metric("Failed Logins", int((log["action"] == "LOGIN_FAILED").sum()))
        # ---- filters ----
        f1, f2, f3, f4 = st.columns([1.2, 1, 1, 1])
        dmin = log["dt"].min().date() if log["dt"].notna().any() else date.today()
        rng = f1.date_input("Date range", value=(dmin, date.today()), min_value=dmin, max_value=date.today(), key="aud_rng")
        fuser = f2.selectbox("User", ["All"] + sorted(log["username"].dropna().unique().tolist()), key="aud_user")
        fmod = f3.selectbox("Module", ["All"] + sorted(log["module"].dropna().unique().tolist()), key="aud_mod")
        fact = f4.selectbox("Action", ["All"] + sorted(log["action"].dropna().unique().tolist()), key="aud_act")
        q = st.text_input("Search", placeholder="reference, details, user, module...", key="aud_q")
        v = log
        if isinstance(rng, (tuple, list)) and len(rng) == 2:
            v = v[(v["dt"].dt.date >= rng[0]) & (v["dt"].dt.date <= rng[1])]
        if fuser != "All": v = v[v["username"] == fuser]
        if fmod != "All": v = v[v["module"] == fmod]
        if fact != "All": v = v[v["action"] == fact]
        if q:
            ql = q.lower()
            v = v[v.apply(lambda r: ql in " ".join(str(r[c]) for c in ["username", "action", "module", "record_ref", "details"]).lower(), axis=1)]
        # ---- activity chart ----
        c1, c2 = st.columns([2, 1], gap="large")
        with c1:
            st.markdown('<div class="panel-title">Activity per day</div>', unsafe_allow_html=True)
            if v.empty: st.caption("No events in this selection.")
            else:
                per_day = v.groupby(v["dt"].dt.date.astype(str)).size().rename("Events")
                st.bar_chart(per_day, color="#19867e", height=210)
        with c2:
            st.markdown('<div class="panel-title">By module</div>', unsafe_allow_html=True)
            if v.empty: st.caption("No events in this selection.")
            else:
                bym = v["module"].value_counts().rename_axis("Module").reset_index(name="Events")
                st.dataframe(bym, use_container_width=True, hide_index=True, height=38 + 35 * min(len(bym), 6))
        # ---- the trail ----
        st.markdown(f'<div class="panel-title" style="margin-top:8px">Activity log <span style="font-weight:500;color:#6f828b;margin-left:6px">{len(v):,} event(s)</span></div>', unsafe_allow_html=True)
        icons = {"LOGIN": "🟢 Login", "LOGOUT": "⚪ Logout", "LOGIN_FAILED": "🔴 Failed login", "CREATE": "➕ Create", "UPDATE": "✏️ Update",
                 "DELETE": "🗑️ Delete", "APPROVE": "✅ Approve", "REJECT": "❌ Reject", "RENEW": "🔄 Renew", "REVISION": "📝 Revision",
                 "DOWNLOAD": "⬇️ Download", "RESTORE": "♻️ Restore", "PURGE": "🧹 Purge", "UPSERT": "💾 Save", "CHECK_OUT": "🔒 Check out",
                 "CHECK_IN": "🔓 Check in", "LOAD_DEMO": "📦 Load sample", "LOAD_SAMPLE": "📦 Load sample", "CLEAR_DEMO": "🧹 Clear sample"}
        show = v.head(500).copy()
        show["Action"] = show["action"].map(lambda a: icons.get(a, a))
        out = show[["timestamp", "username", "Action", "module", "record_ref", "details"]]
        out.columns = ["Date & Time", "User", "Action", "Module", "Reference", "Details"]
        st.dataframe(out, use_container_width=True, hide_index=True, height=min(38 + 35 * len(out), 560),
                     column_config={"Details": st.column_config.TextColumn("Details", width="large")})

# ---------------------------- Recycle Bin ----------------------------
elif page == "Recycle Bin":
    section_title("Recycle Bin", "Restore or permanently remove soft-deleted documents")
    d=df_query("SELECT id,doc_no,title,revision,version,updated_at,filepath FROM documents WHERE is_deleted=1 ORDER BY updated_at DESC")
    if d.empty: st.info("Recycle bin is empty.")
    else:
        st.dataframe(d.drop(columns=["filepath"]),use_container_width=True,hide_index=True)
        labels=[f"{r.doc_no} | {r.title}" for _,r in d.iterrows()]
        sel=st.selectbox("Select deleted document",labels)
        row=d.iloc[labels.index(sel)]
        c1,c2=st.columns(2)
        if c1.button("Restore"):
            execute("UPDATE documents SET is_deleted=0,updated_at=? WHERE id=?",(now_str(),int(row["id"])))
            audit("RESTORE","Documents",row["doc_no"],""); st.rerun()
        if c2.button("Permanently Delete"):
            if row["filepath"] and Path(row["filepath"]).exists():
                try: Path(row["filepath"]).unlink()
                except: pass
            execute("DELETE FROM documents WHERE id=?",(int(row["id"]),))
            audit("PURGE","Documents",row["doc_no"],""); st.rerun()

# ---------------------------- Administration ----------------------------
elif page == "Administration":
    section_title("Administration", "Users, departments, security, backup and company configuration")
    t1,t2,t3,t4,t5=st.tabs(["Users","Departments","Backup","Examples","Access Control"])
    with t5:
        acc_role = st.selectbox("Role", ACCESS_ROLES, key="acc_role")
        granted = pages_for_role(acc_role)
        has_custom = scalar("SELECT COUNT(*) FROM role_page_access WHERE role=?", (acc_role,)) > 0
        st.caption("Custom access is set by Admin." if has_custom else "Using default access for this role.")
        grantable = [p for p in all_pages if p not in ("Dashboard", "Administration")]
        with st.form(f"access_form_{acc_role}"):
            new_pages = st.multiselect(f"Sections available to {acc_role}", grantable, default=[p for p in granted if p in grantable])
            c1, c2 = st.columns(2)
            save_acc = c1.form_submit_button("Save Access", use_container_width=True)
            reset_acc = c2.form_submit_button("Reset to Default", use_container_width=True)
        if save_acc:
            execute("DELETE FROM role_page_access WHERE role=?", (acc_role,))
            for p in ["Dashboard"] + new_pages:
                execute("INSERT INTO role_page_access(role,page) VALUES(?,?)", (acc_role, p))
            audit("UPDATE", "Access Control", acc_role, ", ".join(new_pages) or "Dashboard only")
            st.success(f"Access updated for {acc_role}. They will see the change on their next page load."); st.rerun()
        if reset_acc:
            execute("DELETE FROM role_page_access WHERE role=?", (acc_role,))
            audit("UPDATE", "Access Control", acc_role, "Reset to default")
            st.success("Reset to default access."); st.rerun()
        matrix = pd.DataFrame({r: ["✔" if p in pages_for_role(r) else "" for p in all_pages] for r in ["Admin"] + ACCESS_ROLES}, index=all_pages)
        st.markdown("**Current access overview**")
        st.dataframe(matrix, use_container_width=True)
    with t1:
        st.dataframe(df_query("SELECT username,full_name,role,active,created_at FROM users ORDER BY username"),use_container_width=True,hide_index=True)
        with st.form("user_add",clear_on_submit=True):
            c1,c2,c3,c4=st.columns(4)
            un=c1.text_input("Username *")
            fn=c2.text_input("Full Name *")
            role=c3.selectbox("Role",["Admin","HR","Manager","Accounts","Employee"])
            pw=c4.text_input("Password *",type="password")
            go=st.form_submit_button("Create User")
        if go:
            if not un.strip() or not fn.strip() or not pw:
                st.error("Username, full name and password are required.")
            else:
                try:
                    execute("INSERT INTO users(username,password_hash,full_name,role,active,created_at) VALUES(?,?,?,?,1,?)",(un.strip(),hash_password(pw),fn.strip(),role,now_str()))
                    audit("CREATE","Users",un.strip(),role); st.success("User created.")
                except sqlite3.IntegrityError: st.error("Username already exists.")
    with t2:
        st.dataframe(df_query("SELECT name,hod,created_at FROM departments ORDER BY name"),use_container_width=True,hide_index=True)
        with st.form("dept_add",clear_on_submit=True):
            c1,c2=st.columns(2); name=c1.text_input("Department Name *"); hod=c2.text_input("HOD")
            go=st.form_submit_button("Add Department")
        if go:
            try:
                execute("INSERT INTO departments(name,hod,created_at) VALUES(?,?,?)",(name,hod,now_str()))
                audit("CREATE","Departments",name,hod); st.success("Department added.")
            except sqlite3.IntegrityError: st.error("Department already exists.")
    with t3:
        st.write("Create a ZIP backup containing the SQLite database, uploads and archive.")
        if st.button("Create Backup"):
            out=make_backup(); audit("BACKUP","System",out.name,"")
            st.success(f"Backup created: {out.name}")
            st.download_button("Download Backup",out.read_bytes(),file_name=out.name,mime="application/zip")
        st.caption("For production use, place the application behind HTTPS, change all default passwords, and use managed database/storage backups.")

    with t4:
        st.write("Load fictional examples across the project to explore documents, approvals, employees, projects, insurance, contracts, salary, accounts, tasks and registers.")
        st.caption("Examples use DEMO references and include downloadable text documents, upcoming expiries and an overdue task. Existing records are preserved; loading again skips existing examples.")
        if st.button("Load Demo Examples", type="primary"):
            try:
                with db_conn() as con:
                    added = load_demo_data(con, UPLOAD_DIR, USER)
                if added:
                    st.success(f"Added {added} demo records. Explore the modules using the sidebar.")
                else:
                    st.info("The demo examples are already loaded.")
            except (sqlite3.Error, OSError) as exc:
                st.error(f"Could not load demo examples: {exc}")

st.markdown("---")

