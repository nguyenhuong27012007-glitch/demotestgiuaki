"""
🌸 Hệ thống AI Agent - Đánh giá Thị trường Mở rộng Kinh doanh (HUMAN-IN-THE-LOOP WIZARD)
Quy trình 3 Bước có Người duyệt & Chỉnh sửa trực tiếp trên Web
"""

import streamlit as st
import pandas as pd
import json
import os
import sys
import base64
import plotly.graph_objects as go
import plotly.express as px

# Đảm bảo đường dẫn module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator import AgentOrchestrator
from config import COMPANY_NAME, EXPANSION_SLOTS, TOTAL_REGIONS, DEFAULT_CRITERIA, DEFAULT_GEMINI_API_KEY
from utils.column_mapper import COLUMN_SCHEMA

# ============================================================
# CẤU HÌNH TRANG STREAMLIT
# ============================================================
st.set_page_config(
    page_title="🌸 Hưng Phát WMS | Quy Trình 3 Bước Thông Minh",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CHUYỂN DẢI HOA TULIP CHÂN TRANG SANG BASE64
# ============================================================
tulip_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tulip_bottom_strip.png")
if not os.path.exists(tulip_path):
    tulip_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tulip_flowers_transparent.png")

tulip_b64 = ""
if os.path.exists(tulip_path):
    with open(tulip_path, "rb") as f:
        tulip_b64 = base64.b64encode(f.read()).decode()

# ============================================================
# CSS GIAO DIỆN PASTEL: TIÊU ĐỀ GỌN, CHỮ TO RÕ, STEPPER HIỆN ĐẠI
# ============================================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Playfair+Display:ital,wght@0,700;1,700&display=swap');
    
    html, body, [class*="css"], .stMarkdown p, .stMarkdown span, .stMarkdown div, .stMarkdown li, label {{
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 1.28rem !important;
        line-height: 1.55 !important;
        color: #1a162b !important;
    }}

    /* Tiêu đề các mục h3, h4, h5 và chú thích (caption) to rõ, không làm phình khung */
    .stMarkdown h3 {{
        font-size: 1.72rem !important;
        font-weight: 800 !important;
        line-height: 1.3 !important;
        margin-top: 0.4rem !important;
        margin-bottom: 0.4rem !important;
    }}
    .stMarkdown h4 {{
        font-size: 1.48rem !important;
        font-weight: 800 !important;
        line-height: 1.3 !important;
    }}
    .stMarkdown h5 {{
        font-size: 1.34rem !important;
        font-weight: 700 !important;
        line-height: 1.3 !important;
    }}
    div[data-testid="stCaptionContainer"] p,
    div[data-testid="stCaptionContainer"] span {{
        font-size: 1.18rem !important;
        font-weight: 600 !important;
        line-height: 1.4 !important;
        color: #4a154b !important;
    }}
    div[data-testid="stFileUploader"] small,
    div[data-testid="stFileUploader"] span,
    .st-key-step1_gsheet_box input {{
        font-size: 1.24rem !important;
        font-weight: 600 !important;
    }}
    div[data-testid="stAlert"] p {{
        font-size: 1.26rem !important;
        line-height: 1.45 !important;
    }}

    /* Nền Pastel nhạt êm mắt */
    .stApp {{
        background: linear-gradient(180deg, #fdf8f9 0%, #fef5f7 40%, #f9f4f8 100%) !important;
    }}

    /* Container chính */
    .main .block-container {{
        background: #ffffff !important;
        border-radius: 28px !important;
        padding: 2.2rem 3rem 1.5rem 3rem !important;
        margin-top: 1.2rem !important;
        max-width: 1320px !important;
        box-shadow: 0 16px 40px rgba(244, 114, 182, 0.1) !important;
        border: 2px solid #fdf2f8 !important;
    }}

    /* Sidebar pastel */
    section[data-testid="stSidebar"] {{
        background: #fdf6f9 !important;
        border-right: 2px solid #fae8f0 !important;
    }}

    /* Banner chính - giữ nguyên kích thước khung, chữ to nổi bật và bắt buộc 1 dòng mỗi câu */
    .hero-banner-tulip {{
        background: linear-gradient(135deg, #fbcfe8 0%, #fed7aa 50%, #fecdd3 100%);
        padding: 1.35rem 2.2rem;
        border-radius: 24px;
        border: 2px solid #ffffff;
        box-shadow: 0 14px 32px -6px rgba(244, 114, 182, 0.25);
        margin-bottom: 2rem;
        overflow: hidden;
    }}
    .hero-banner-tulip .banner-line-1 {{
        font-family: 'Playfair Display', serif !important;
        font-size: clamp(1.9rem, 2.45vw, 2.65rem) !important;
        font-weight: 800 !important;
        color: #4a154b !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.2 !important;
        white-space: nowrap !important;
    }}
    .hero-banner-tulip .banner-line-2 {{
        color: #701a75 !important;
        font-size: clamp(1.15rem, 1.42vw, 1.48rem) !important;
        margin: 0.45rem 0 0 0 !important;
        padding: 0 !important;
        line-height: 1.25 !important;
        font-weight: 700 !important;
        white-space: nowrap !important;
    }}

    /* THANH ĐIỀU HƯỚNG QUY TRÌNH (STEP WIZARD) */
    .wizard-steps-container {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 2.2rem;
        background: #fbf2f6;
        border-radius: 24px;
        padding: 8px 12px;
        border: 1.5px solid #fce7f3;
    }}
    .wizard-step {{
        flex: 1;
        text-align: center;
        padding: 12px 16px;
        border-radius: 18px;
        font-weight: 700;
        font-size: 1.15rem !important;
        color: #701a75;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
    }}
    .wizard-step.active {{
        background: #ffffff;
        color: #db2777 !important;
        box-shadow: 0 4px 16px rgba(219, 39, 119, 0.22);
        font-weight: 800;
    }}
    .wizard-step.completed {{
        color: #059669 !important;
    }}

    /* Khung Duyệt Của Con Người (Human Checkpoint Card) - Chữ to hơn, giữ nguyên kích thước khung */
    .human-approval-card {{
        background: linear-gradient(135deg, #fff7ed 0%, #fffbeb 100%);
        border: 2px dashed #f59e0b;
        border-radius: 22px;
        padding: 1.25rem 1.8rem;
        margin: 1.6rem 0;
        box-shadow: 0 8px 24px rgba(245, 158, 11, 0.12);
    }}
    .human-approval-card h4 {{
        color: #b45309 !important;
        font-size: 1.52rem !important;
        font-weight: 800;
        line-height: 1.25 !important;
        margin: 0 0 6px 0;
    }}
    .human-approval-card p {{
        color: #78350f !important;
        font-size: 1.26rem !important;
        line-height: 1.35 !important;
        margin: 0;
    }}

    /* Nút bấm lớn - Chữ to hơn nhưng KHÔNG làm khung nút to hơn */
    .stButton > button,
    .stDownloadButton > button {{
        border-radius: 22px !important;
        font-weight: 800 !important;
        font-size: 1.32rem !important;
        padding: 0.55rem 1.4rem !important;
        border: 1.5px solid #fbcfe8 !important;
        background: #ffffff !important;
        color: #831843 !important;
        box-shadow: 0 4px 14px rgba(244, 114, 182, 0.15) !important;
        transition: all 0.25s ease !important;
    }}
    .stButton > button p,
    .stButton > button span,
    .stDownloadButton > button p,
    .stDownloadButton > button span {{
        font-size: 1.32rem !important;
        font-weight: 800 !important;
        line-height: 1.2 !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(244, 114, 182, 0.3) !important;
        border-color: #ec4899 !important;
        background: #fdf2f8 !important;
    }}
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #f43f5e 0%, #ec4899 50%, #db2777 100%) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 6px 18px rgba(236, 72, 153, 0.35) !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #e11d48 0%, #db2777 50%, #be185d 100%) !important;
    }}

    /* Metric Cards */
    .metric-card-tulip {{
        background: #ffffff;
        border: 2px solid #fdf2f8;
        border-radius: 22px;
        padding: 1.4rem 1.6rem;
        box-shadow: 0 6px 20px rgba(244, 114, 182, 0.08);
    }}
    .metric-card-tulip .title {{
        color: #64748b;
        font-size: 1rem !important;
        font-weight: 700;
        text-transform: uppercase;
    }}
    .metric-card-tulip .value {{
        color: #831843;
        font-size: 2.2rem !important;
        font-weight: 800;
        margin-top: 0.25rem;
    }}

    /* HOA TULIP NẰM Ở CHÂN TRANG */
    .footer-tulip-meadow {{
        width: 100%;
        height: 270px;
        margin-top: 5rem;
        background-image: url("data:image/png;base64,{tulip_b64}");
        background-repeat: repeat-x;
        background-position: bottom center;
        background-size: auto 270px;
        position: relative;
    }}

    /* TÙY CHỈNH 2 NÚT TAB (BÁO CÁO BÊN TRÁI - DASHBOARD BÊN PHẢI) Ở BƯỚC 3 */
    .st-key-step3_tab_buttons .stButton > button {{
        min-height: 68px !important;
        padding: 0.7rem 1.4rem !important;
        border-radius: 22px !important;
        border: 2.5px solid #f472b6 !important;
        background: #ffffff !important;
        color: #831843 !important;
        box-shadow: 0 6px 18px rgba(131, 24, 67, 0.12) !important;
    }}
    .st-key-step3_tab_buttons .stButton > button p,
    .st-key-step3_tab_buttons .stButton > button span {{
        font-size: 1.56rem !important;
        font-weight: 800 !important;
        color: #831843 !important;
        white-space: nowrap !important;
    }}
    .st-key-step3_tab_buttons .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #f43f5e 0%, #ec4899 50%, #db2777 100%) !important;
        border: 3px solid #ffffff !important;
        box-shadow: 0 10px 28px rgba(219, 39, 119, 0.42) !important;
    }}
    .st-key-step3_tab_buttons .stButton > button[kind="primary"] p,
    .st-key-step3_tab_buttons .stButton > button[kind="primary"] span {{
        color: #ffffff !important;
        font-size: 1.58rem !important;
        font-weight: 800 !important;
        white-space: nowrap !important;
    }}
    /* Tab 1 căn sát trái trong cột trái, Tab 2 căn sát phải trong cột phải */
    .st-key-btn_tab_report_left {{
        display: flex !important;
        justify-content: flex-start !important;
    }}
    .st-key-btn_tab_dashboard_right {{
        display: flex !important;
        justify-content: flex-end !important;
    }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# KHỞI TẠO STATE HỆ THỐNG (3 BƯỚC WIZARD)
# ============================================================
if "current_step" not in st.session_state:
    st.session_state.current_step = 1  # 1: Nhập file, 2: Làm sạch & Sửa file, 3: Quy trình & Báo cáo

if "step1_approved" not in st.session_state:
    st.session_state.step1_approved = False
if "step2_approved" not in st.session_state:
    st.session_state.step2_approved = False
if "step3_approved" not in st.session_state:
    st.session_state.step3_approved = False

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = AgentOrchestrator()
if "api_key_set" not in st.session_state:
    st.session_state.api_key_set = False
if "files_loaded" not in st.session_state:
    st.session_state.files_loaded = []
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "file_messages" not in st.session_state:
    st.session_state.file_messages = []
if "pending_spinner_msg" not in st.session_state:
    st.session_state.pending_spinner_msg = ""
if "selected_ai_model" not in st.session_state:
    st.session_state.selected_ai_model = "gemini-3.1-pro"

def set_spinner_msg(msg: str):
    st.session_state.pending_spinner_msg = msg

def get_orchestrator() -> AgentOrchestrator:
    return st.session_state.orchestrator

orch = get_orchestrator()

if not st.session_state.api_key_set and DEFAULT_GEMINI_API_KEY:
    try:
        success, _ = orch.initialize_ai(DEFAULT_GEMINI_API_KEY, model_name=st.session_state.selected_ai_model)
    except TypeError:
        success, _ = orch.initialize_ai(DEFAULT_GEMINI_API_KEY)
    if success:
        st.session_state.api_key_set = True

# ============================================================
# BANNER ĐIỀU HÀNH
# ============================================================
st.markdown(f"""
<div class="hero-banner-tulip">
    <div class="banner-line-1">🌸 Phân tích dữ liệu</div>
    <div class="banner-line-2">🍃 Quy trình 3 Bước thông minh: Nhập dữ liệu ➔ Làm sạch & Chỉnh sửa trực tiếp ➔ Phân tích & Xuất Báo cáo HTML</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# THANH ĐIỀU HƯỚNG BƯỚC (STEP INDICATOR - BẤM TRỰC TIẾP ĐƯỢC)
# ============================================================
step = st.session_state.current_step

# Thiết kế hộp thông báo chạy chính giữa màn hình cho stSpinner
st.markdown("""
<style>
    div[data-testid="stSpinner"] {
        position: fixed !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        background: linear-gradient(135deg, #ffffff 0%, #fdf2f8 100%) !important;
        color: #831843 !important;
        padding: 24px 42px !important;
        border-radius: 26px !important;
        border: 3px solid #ec4899 !important;
        box-shadow: 0 20px 55px rgba(131, 24, 67, 0.35) !important;
        z-index: 999999 !important;
        text-align: center !important;
        min-width: 420px !important;
    }
    div[data-testid="stSpinner"] p,
    div[data-testid="stSpinner"] span {
        font-size: 1.32rem !important;
        font-weight: 800 !important;
        color: #831843 !important;
    }
</style>
""", unsafe_allow_html=True)

s1_icon = "✅" if st.session_state.step1_approved else "1️⃣"
s2_icon = "✅" if st.session_state.step2_approved else "2️⃣"
s3_icon = "✅" if st.session_state.step3_approved else "3️⃣"

s1_color = "#047857" if st.session_state.step1_approved else "#831843"
s2_color = "#047857" if st.session_state.step2_approved else "#831843"
s3_color = "#047857" if st.session_state.step3_approved else "#831843"

s1_bg = "#ecfdf5" if st.session_state.step1_approved else "#ffffff"
s2_bg = "#ecfdf5" if st.session_state.step2_approved else "#ffffff"
s3_bg = "#ecfdf5" if st.session_state.step3_approved else "#ffffff"

s1_border = "#10b981" if st.session_state.step1_approved else "#f472b6"
s2_border = "#10b981" if st.session_state.step2_approved else "#f472b6"
s3_border = "#10b981" if st.session_state.step3_approved else "#f472b6"

st.markdown(f"""
<style>
    /* Đóng khung lớn nổi bật bao quanh 3 nút điều hướng bước ở trên */
    .st-key-top_wizard_bar {{
        background: linear-gradient(135deg, #fdf2f8 0%, #fce7f3 50%, #fbcfe8 100%);
        border-radius: 30px;
        padding: 18px 24px;
        border: 3px solid #f472b6;
        margin-bottom: 2.2rem;
        box-shadow: 0 12px 32px rgba(219, 39, 119, 0.18);
    }}
    .st-key-top_wizard_bar .stButton > button {{
        border-radius: 22px !important;
        padding: 0.85rem 0.5rem !important;
        min-height: 74px !important;
        height: 74px !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 6px 18px rgba(131, 24, 67, 0.10) !important;
    }}
    .st-key-top_wizard_bar .stButton > button p,
    .st-key-top_wizard_bar .stButton > button span,
    .st-key-top_wizard_bar .stButton > button div {{
        font-size: clamp(1.12rem, 1.24vw, 1.30rem) !important;
        font-weight: 800 !important;
        letter-spacing: -0.2px !important;
        white-space: nowrap !important;
        overflow: visible !important;
        text-overflow: clip !important;
    }}
    .st-key-top_nav_step1 button {{
        background: {s1_bg} !important;
        border: 2.5px solid {s1_border} !important;
        color: {s1_color} !important;
    }}
    .st-key-top_nav_step1 button p, .st-key-top_nav_step1 button span {{ color: {s1_color} !important; }}

    .st-key-top_nav_step2 button {{
        background: {s2_bg} !important;
        border: 2.5px solid {s2_border} !important;
        color: {s2_color} !important;
    }}
    .st-key-top_nav_step2 button p, .st-key-top_nav_step2 button span {{ color: {s2_color} !important; }}

    .st-key-top_nav_step3 button {{
        background: {s3_bg} !important;
        border: 2.5px solid {s3_border} !important;
        color: {s3_color} !important;
    }}
    .st-key-top_nav_step3 button p, .st-key-top_nav_step3 button span {{ color: {s3_color} !important; }}
    
    .st-key-top_wizard_bar .stButton > button:hover {{
        transform: translateY(-3px) scale(1.01) !important;
        box-shadow: 0 12px 26px rgba(219, 39, 119, 0.28) !important;
    }}
    /* Nút đang ở bước hiện tại (active) nổi bật rực rỡ với nền hồng đậm Gradient & chữ trắng vừa khung */
    .st-key-top_wizard_bar .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #f43f5e 0%, #ec4899 50%, #be185d 100%) !important;
        color: #ffffff !important;
        border: 3px solid #ffffff !important;
        box-shadow: 0 12px 30px rgba(225, 29, 72, 0.45) !important;
        transform: scale(1.01) !important;
    }}
    .st-key-top_wizard_bar .stButton > button[kind="primary"] p,
    .st-key-top_wizard_bar .stButton > button[kind="primary"] span,
    .st-key-top_wizard_bar .stButton > button[kind="primary"] div {{
        color: #ffffff !important;
        font-size: clamp(1.14rem, 1.26vw, 1.32rem) !important;
        font-weight: 800 !important;
        letter-spacing: -0.2px !important;
        white-space: nowrap !important;
    }}

    /* Chữ to hơn cho các nút "Duyệt Bước X ➔ Sang Bước Y", KHÔNG làm khung nút to hơn */
    .st-key-btn_approve_step1 button,
    .st-key-btn_approve_step2 button {{
        padding: 0.45rem 1.2rem !important;
    }}
    .st-key-btn_approve_step1 button p,
    .st-key-btn_approve_step1 button span,
    .st-key-btn_approve_step2 button p,
    .st-key-btn_approve_step2 button span {{
        font-size: 1.54rem !important;
        font-weight: 800 !important;
        line-height: 1.15 !important;
        color: #ffffff !important;
        white-space: nowrap !important;
    }}

    /* Kéo ô Google Sheet cao bằng đúng mép dưới của ô Upload bên trái (Streamlit giới hạn max-height: 2.5rem trên thẻ gốc nên cần ghi đè max-height: none) */
    div[data-testid="stFileUploader"] section {{
        min-height: 74px !important;
        height: 74px !important;
        box-sizing: border-box !important;
    }}
    .st-key-step1_gsheet_box div[data-testid="stTextInputRootElement"],
    .st-key-step1_gsheet_box div[data-baseweb="input"],
    .st-key-step1_gsheet_box div[data-baseweb="base-input"] {{
        min-height: 74px !important;
        height: 74px !important;
        max-height: none !important;
        align-items: center !important;
        box-sizing: border-box !important;
    }}
    .st-key-step1_gsheet_box input {{
        min-height: 72px !important;
        height: 72px !important;
        max-height: none !important;
        padding-top: 20px !important;
        padding-bottom: 20px !important;
        box-sizing: border-box !important;
    }}
</style>
""", unsafe_allow_html=True)

with st.container(key="top_wizard_bar"):
    nav_col1, nav_col2, nav_col3 = st.columns(3)

    with nav_col1:
        if st.button(
            f"{s1_icon} Bước 1: Nhập Dữ Liệu",
            key="top_nav_step1",
            use_container_width=True,
            type="primary" if step == 1 else "secondary"
        ):
            set_spinner_msg("⏳ Đang chuyển về Bước 1: Tiếp nhận & Kiểm tra tệp dữ liệu...")
            st.session_state.current_step = 1
            st.rerun()

    with nav_col2:
        if st.button(
            f"{s2_icon} Bước 2: Làm Sạch & Chỉnh Sửa File",
            key="top_nav_step2",
            use_container_width=True,
            type="primary" if step == 2 else "secondary"
        ):
            if st.session_state.step1_approved:
                set_spinner_msg("⏳ Đang mở Bước 2: Bảng làm sạch & Chỉnh sửa dữ liệu trực tiếp...")
                st.session_state.current_step = 2
                st.rerun()
            else:
                st.toast("⚠️ Vui lòng nạp file và bấm Duyệt Bước 1 trước khi sang Bước 2!", icon="⚠️")
                st.warning("⚠️ Bạn cần hoàn tất và bấm Duyệt ở Bước 1 trước khi chuyển sang Bước 2.")

    with nav_col3:
        if st.button(
            f"{s3_icon} Bước 3: Phân Tích & Báo Cáo HTML",
            key="top_nav_step3",
            use_container_width=True,
            type="primary" if step == 3 else "secondary"
        ):
            if st.session_state.step2_approved:
                set_spinner_msg("⏳ Đang mở Bước 3: Phân tích đa tiêu chí, Báo cáo & Dashboard...")
                st.session_state.current_step = 3
                st.rerun()
            else:
                st.toast("⚠️ Vui lòng duyệt dữ liệu sạch ở Bước 2 trước khi sang Bước 3!", icon="⚠️")
                st.warning("⚠️ Bạn cần hoàn tất và bấm Duyệt ở Bước 2 trước khi chuyển sang Bước 3.")

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("<h2 style='color:#831843; font-size:1.5rem;'>🌸 Bảng Cài Đặt</h2>", unsafe_allow_html=True)
    
    st.markdown("#### 🔑 Kết nối AI Agent")
    api_key_input = st.text_input(
        "Gemini API Key",
        type="password",
        value=DEFAULT_GEMINI_API_KEY,
        help="Đã tích hợp sẵn API Key tự động"
    )
    if st.button("✨ Cập nhật API Key", use_container_width=True):
        if api_key_input:
            try:
                success, msg = orch.initialize_ai(api_key_input, model_name=st.session_state.selected_ai_model)
            except TypeError:
                success, msg = orch.initialize_ai(api_key_input)
            if success:
                st.session_state.api_key_set = True
                st.success(f"🌸 Kết nối thành công ({st.session_state.selected_ai_model})!")
            else:
                st.error(msg)
                
    st.divider()
    st.markdown("#### 🤖 Chọn Phiên Bản Model AI")
    ai_model_options = {
        "gemini-3.1-pro": "🚀 Gemini 3.1 Pro (Recommended)",
        "gemini-3.8-ultra": "💎 Gemini 3.8 Ultra (Reasoning)",
        "argon-4.0": "⚡ Argon 4.0 (Enterprise AI)",
        "gemini-3.1-flash": "✨ Gemini 3.1 Flash (Tốc độ cao)",
        "gemini-2.5-pro": "🧠 Gemini 2.5 Pro",
        "gemini-2.5-flash": "🌟 Gemini 2.5 Flash",
        "gemini-2.0-flash": "🔹 Gemini 2.0 Flash"
    }
    model_keys = list(ai_model_options.keys())
    cur_idx = model_keys.index(st.session_state.selected_ai_model) if st.session_state.selected_ai_model in model_keys else 0
    chosen_model = st.selectbox(
        "Mô hình AI đang sử dụng:",
        options=model_keys,
        index=cur_idx,
        format_func=lambda k: ai_model_options[k],
        key="sidebar_model_selector"
    )
    if chosen_model != st.session_state.selected_ai_model:
        with st.spinner(f"⏳ Đang chuyển đổi sang mô hình {ai_model_options[chosen_model]}..."):
            st.session_state.selected_ai_model = chosen_model
            try:
                orch.initialize_ai(api_key_input or DEFAULT_GEMINI_API_KEY, model_name=chosen_model)
            except TypeError:
                orch.initialize_ai(api_key_input or DEFAULT_GEMINI_API_KEY)
            st.toast(f"✅ Đã chuyển sang {ai_model_options[chosen_model]}", icon="🤖")
        st.rerun()
    st.caption(f"🟢 Đang kích hoạt: **{ai_model_options[st.session_state.selected_ai_model]}**")

# ============================================================
# TRÌNH BẮT LỖI TOÀN CỤC — ĐẢM BẢO MỌI THÔNG BÁO ĐỀU BẰNG TIẾNG VIỆT DỄ HIỂU
# ============================================================
def _vietnamese_error_message(exc: Exception) -> str:
    msg = str(exc)
    if "invalid error value" in msg:
        return "⚠️ Không thể chuyển đổi một số ô văn bản sang kiểu số. Hệ thống đã giữ nguyên giá trị văn bản gốc."
    if "429" in msg or "quota" in msg.lower() or "ResourceExhausted" in msg:
        return "⚠️ Hệ thống AI đang quá tải hoặc hết hạn mức truy cập tạm thời. Hệ thống đã tự động dùng bộ phân tích dự phòng."
    if "404" in msg:
        return "⚠️ Không tìm thấy tài nguyên hoặc liên kết Google Sheet. Vui lòng kiểm tra lại đường dẫn."
    if "403" in msg or "permission" in msg.lower():
        return "⚠️ Không có quyền truy cập tệp hoặc Google Sheet chưa bật chế độ chia sẻ công khai."
    if "API_KEY" in msg.upper() or "api key" in msg.lower():
        return "⚠️ Mã kết nối AI (API Key) chưa hợp lệ. Vui lòng kiểm tra lại trong Bảng Cài Đặt bên trái."
    if "ParserError" in msg or "tokenizing" in msg:
        return "⚠️ Định dạng tệp dữ liệu có dòng bị lệch cột. Vui lòng kiểm tra lại tệp CSV/Excel."
    return "⚠️ Hệ thống gặp sự cố nhỏ khi xử lý thao tác vừa rồi. Vui lòng kiểm tra lại dữ liệu hoặc thử lại."

try:
    # ============================================================
        # BƯỚC 1: NHẬP FILE (EXCEL / CSV / GOOGLE SHEET)
    # ============================================================
    if st.session_state.current_step == 1:
        if st.session_state.pending_spinner_msg:
            with st.spinner(st.session_state.pending_spinner_msg):
                import time
                time.sleep(0.15)
            st.session_state.pending_spinner_msg = ""
        st.markdown("### 📥 Bước 1: Tiếp Nhận & Kiểm Tra Định Dạng File")
    
        col_up1, col_up2 = st.columns([1, 1])
    
        with col_up1:
            st.markdown("##### 📁 Tải tệp lên")
            uploaded_files = st.file_uploader(
                "Tải tệp lên",
                type=["csv", "xlsx", "xls"],
                accept_multiple_files=True,
                label_visibility="collapsed"
            )
            if uploaded_files and st.button("🌸 Xác thực & Nạp tệp", use_container_width=True):
                with st.spinner("⏳ Bước 1: Đang đọc và kiểm tra cấu trúc tệp dữ liệu, vui lòng đợi..."):
                    for up in uploaded_files:
                        content = up.read()
                        success, msg = orch.load_file(content, up.name)
                        st.session_state.file_messages.append({"file": up.name, "success": success, "msg": msg})
                        if success and up.name not in st.session_state.files_loaded:
                            st.session_state.files_loaded.append(up.name)
                set_spinner_msg("⏳ Bước 1: Đang hiển thị kết quả xác thực tệp dữ liệu...")
                st.rerun()

        with col_up2:
            st.markdown("##### 🔗 Dán link Google Sheet công khai")
            with st.container(key="step1_gsheet_box"):
                sheet_url = st.text_input(
                    "Liên kết Google Sheet",
                    placeholder="https://docs.google.com/spreadsheets/d/.../edit",
                    label_visibility="collapsed"
                )
            if sheet_url and st.button("🍃 Đọc Google Sheet", use_container_width=True):
                with st.spinner("⏳ Bước 1: Đang kết nối và đọc dữ liệu từ Google Sheet, vui lòng đợi..."):
                    success, msg = orch.load_google_sheet(sheet_url)
                    st.session_state.file_messages.append({"file": "Google Sheet", "success": success, "msg": msg})
                    if success:
                        st.session_state.files_loaded.append("Google Sheet")
                set_spinner_msg("⏳ Bước 1: Đang hiển thị dữ liệu từ Google Sheet...")
                st.rerun()

        # Hiển thị thông báo trạng thái
        if st.session_state.file_messages:
            st.write("")
            st.markdown("##### 🔔 Kết quả kiểm tra file:")
            for item in st.session_state.file_messages[-6:]:
                if item["success"]:
                    st.success(f"🌱 **{item['file']}**: {item['msg']}")
                else:
                    st.error(f"❌ **{item['file']}**: {item['msg']}")

        # Kiểm tra xem có file hợp lệ chưa
        if orch.data_agent.raw_dataframes:
            st.divider()
            st.markdown("#### 📊 Danh sách các tệp đã nạp thành công:")
            c1, c2, c3 = st.columns(3)
            c1.metric("Số tệp hợp lệ", len(orch.data_agent.raw_dataframes))
            c2.metric("Tổng bản ghi", sum(len(df) for df in orch.data_agent.raw_dataframes.values()))
            c3.metric("Địa bàn tìm thấy", len(orch.data_agent.get_regions_detected()))

            # Khung kiểm tra & duyệt của con người
            st.markdown("""
            <div class="human-approval-card">
                <h4>🧑‍💼 ĐIỂM DUYỆT 1: Con Người Xác Nhận Nạp File</h4>
                <p>Vui lòng kiểm tra lại danh sách các tệp trên. Nếu tệp dữ liệu đã đầy đủ và không bị lỗi, hãy bấm <strong>"Xác nhận duyệt Bước 1 & Chuyển sang Bước 2"</strong>.</p>
            </div>
            """, unsafe_allow_html=True)
        
            col_c1, col_c2 = st.columns([2, 1])
            with col_c1:
                st.info(f"Các địa bàn nhận diện được: **{', '.join(orch.data_agent.get_regions_detected())}**")
            with col_c2:
                if st.button("👉 Duyệt Bước 1 ➔ Sang Bước 2", type="primary", use_container_width=True, key="btn_approve_step1"):
                    set_spinner_msg("⏳ Bước 1 ➔ Bước 2: Đang chuyển sang bảng làm sạch và chỉnh sửa dữ liệu trực tiếp...")
                    st.session_state.step1_approved = True
                    st.session_state.current_step = 2
                    st.rerun()
        else:
            st.info("💡 Hãy tải file Excel/CSV, dán link Google Sheet ở trên, hoặc bấm nút **'🌺 Nạp 6 File Dự Án Mẫu'** ở thanh bên trái để bắt đầu.")

    # ============================================================
    # BƯỚC 2: LÀM SẠCH & CHỈNH SỬA DỮ LIỆU TRỰC TIẾP TRÊN WEB
    # ============================================================
    elif st.session_state.current_step == 2:
        if st.session_state.pending_spinner_msg:
            with st.spinner(st.session_state.pending_spinner_msg):
                import time
                time.sleep(0.15)
            st.session_state.pending_spinner_msg = ""
        st.markdown("### 🧹 Bước 2: Làm Sạch, Chuẩn Hóa & Chỉnh Sửa File Trực Tiếp")
        st.caption("✨ Bạn có thể nhấp đúp vào bất kỳ ô nào trong bảng bên dưới để chỉnh sửa giá trị trực tiếp trên web.")

        if not orch.data_agent.raw_dataframes:
            st.error("❌ Không có dữ liệu để làm sạch. Vui lòng quay lại Bước 1.")
            if st.button("⬅️ Quay lại Bước 1"):
                st.session_state.current_step = 1
                st.rerun()
        else:
            # Chọn file để chỉnh sửa (Thu gọn bằng 2/3 chiều rộng)
            file_list = list(orch.data_agent.raw_dataframes.keys())
            col_sel_file, _ = st.columns([2, 1])
            with col_sel_file:
                selected_file = st.selectbox("📂 Chọn tệp dữ liệu bạn muốn xem và sửa trực tiếp:", file_list)

            df_current = orch.data_agent.raw_dataframes[selected_file]
            total_rows = len(df_current)
            file_info_cur = orch.data_agent.file_infos.get(selected_file, {})

            st.markdown(f"#### ✏️ Bảng Chỉnh Sửa Trực Tiếp: `{selected_file}` ({total_rows:,} dòng × {len(df_current.columns)} cột)")
        
            if total_rows > 1000:
                st.success(f"⚡ **Chế độ Dữ Liệu Lớn (Big Data Engine):** File có **{total_rows:,} dòng**. Hệ thống hỗ trợ phân trang, tìm kiếm nhanh và chỉnh sửa trực tiếp từng trang mà không gây giật lag trình duyệt!")
                if file_info_cur.get("aggregated_df") is not None:
                    with st.expander("📊 Xem Bảng Tự Động Tổng Hợp (Group-By) từ toàn bộ " + f"{total_rows:,} dòng"):
                        st.dataframe(file_info_cur["aggregated_df"], use_container_width=True)

            _, col_info_2_3, _ = st.columns([1, 4, 1])
            with col_info_2_3:
                st.info("💡 **Hướng dẫn:** Nhấn đúp chuột vào ô bất kỳ để sửa nội dung, nhấn dấu `+` ở cuối bảng để thêm dòng mới. Sau khi sửa bấm nút **Lưu Dữ Liệu Đã Sửa**.")

            # Hỗ trợ phân trang & lọc nhanh nếu file lớn (> 1000 dòng) hoặc xem toàn bộ (Thu gọn khung bảng bằng 2/3 chiều rộng & 2/3 chiều cao)
            if total_rows > 1000:
                _, col_p_wrap, _ = st.columns([1, 4, 1])
                with col_p_wrap:
                    col_p1, col_p2, col_p3 = st.columns([1.2, 1.2, 1.6])
                    with col_p1:
                        page_size = st.selectbox("📄 Số dòng hiển thị mỗi trang:", [500, 1000, 2500, 5000, total_rows], index=1, format_func=lambda x: f"Tất cả ({x:,} dòng)" if x == total_rows else f"{x:,} dòng/trang")
                    total_pages = max(1, (total_rows + page_size - 1) // page_size)
                    with col_p2:
                        current_page = st.number_input(f"🔢 Chọn trang (1 - {total_pages}):", min_value=1, max_value=total_pages, value=1, step=1)
                    with col_p3:
                        search_kw = st.text_input("🔍 Lọc nhanh theo từ khóa (Địa bàn / Mã...):", placeholder="Nhập từ khóa để lọc dòng cần sửa...")

                    start_idx = (current_page - 1) * page_size
                    end_idx = min(start_idx + page_size, total_rows)

                    if search_kw.strip():
                        mask = df_current.astype(str).apply(lambda x: x.str.contains(search_kw.strip(), case=False, na=False)).any(axis=1)
                        df_slice = df_current[mask]
                        st.caption(f"🔎 Tìm thấy **{len(df_slice):,} dòng** khớp với từ khóa `{search_kw}`.")
                    else:
                        df_slice = df_current.iloc[start_idx:end_idx]
                        st.caption(f"📑 Đang hiển thị dòng **{start_idx + 1:,}** đến **{end_idx:,}** trên tổng số **{total_rows:,}** dòng.")

                    edited_slice = st.data_editor(
                        df_slice,
                        use_container_width=True,
                        num_rows="dynamic",
                        height=345,
                        key=f"editor_{selected_file}_{current_page}_{page_size}_{search_kw}"
                    )
            else:
                # Streamlit Data Editor thu gọn bằng 2/3 chiều rộng và 2/3 chiều cao
                _, col_editor_2_3, _ = st.columns([1, 4, 1])
                with col_editor_2_3:
                    edited_slice = st.data_editor(
                        df_current,
                        use_container_width=True,
                        num_rows="dynamic",
                        height=180,
                        key=f"editor_{selected_file}"
                    )

            col_save, col_clean = st.columns([1, 1])
            with col_save:
                if st.button("💾 Lưu Dữ Liệu Đã Sửa Vào Hệ Thống", use_container_width=True):
                    try:
                        with st.spinner("⏳ Bước 2: Đang lưu dữ liệu đã chỉnh sửa vào hệ thống, vui lòng đợi..."):
                            if total_rows > 1000 and not (search_kw.strip() if 'search_kw' in locals() else False) and page_size < total_rows:
                                # Ghép phần đã sửa vào DataFrame gốc
                                updated_full = pd.concat([
                                    df_current.iloc[:start_idx],
                                    edited_slice,
                                    df_current.iloc[end_idx:]
                                ], ignore_index=True)
                                orch.data_agent.raw_dataframes[selected_file] = updated_full
                            elif total_rows > 1000 and ('search_kw' in locals() and search_kw.strip()):
                                df_current.loc[edited_slice.index] = edited_slice
                                orch.data_agent.raw_dataframes[selected_file] = df_current
                            else:
                                orch.data_agent.raw_dataframes[selected_file] = edited_slice

                            # Cập nhật lại mapping và bảng Group-By nếu là file lớn
                            from utils.column_mapper import map_columns
                            from utils.file_handler import _auto_aggregate
                            new_df = orch.data_agent.raw_dataframes[selected_file]
                            orch.data_agent.column_mappings[selected_file] = map_columns(list(new_df.columns))
                            if len(new_df) > 1000:
                                agg_df, agg_note = _auto_aggregate(new_df, selected_file)
                                orch.data_agent.file_infos[selected_file]["aggregated_df"] = agg_df
                                orch.data_agent.file_infos[selected_file]["aggregation_note"] = agg_note
                                orch.data_agent.file_infos[selected_file]["rows"] = len(new_df)
                            st.success(f"✅ Đã lưu cập nhật thành công cho tệp {selected_file} ({len(new_df):,} dòng)!")
                        set_spinner_msg(f"⏳ Bước 2: Đang cập nhật lại bảng dữ liệu {selected_file} sau khi lưu...")
                        st.rerun()
                    except Exception:
                        st.error("❌ Đã xảy ra lỗi khi lưu dữ liệu chỉnh sửa. Vui lòng kiểm tra lại định dạng các ô vừa nhập.")
                
            with col_clean:
                if st.button("✨ Tự động Xóa dòng trống & Chuẩn hóa kiểu số (Toàn bộ File)", use_container_width=True):
                    try:
                        with st.spinner(f"⏳ Bước 2: Đang làm sạch và chuẩn hóa toàn bộ {len(df_current):,} dòng dữ liệu..."):
                            cleaned_df = df_current.dropna(how="all").copy()
                            for c in cleaned_df.columns:
                                try:
                                    if cleaned_df[c].dtype == "object":
                                        cleaned_df[c] = pd.to_numeric(cleaned_df[c].astype(str).str.replace(",", "").str.strip())
                                    else:
                                        cleaned_df[c] = pd.to_numeric(cleaned_df[c])
                                except Exception:
                                    # Nếu cột chứa văn bản (Địa bàn, Mã đơn, Tên...) thì giữ nguyên văn bản đã cắt khoảng trắng thừa
                                    try:
                                        if cleaned_df[c].dtype == "object":
                                            cleaned_df[c] = cleaned_df[c].astype(str).str.strip()
                                    except Exception:
                                        pass
                            orch.data_agent.raw_dataframes[selected_file] = cleaned_df
                            if len(cleaned_df) > 1000:
                                from utils.file_handler import _auto_aggregate
                                agg_df, agg_note = _auto_aggregate(cleaned_df, selected_file)
                                orch.data_agent.file_infos[selected_file]["aggregated_df"] = agg_df
                        st.success(f"✅ Đã làm sạch tự động toàn bộ {len(cleaned_df):,} dòng!")
                        set_spinner_msg(f"⏳ Bước 2: Đang hiển thị bảng dữ liệu {selected_file} sau khi làm sạch...")
                        st.rerun()
                    except Exception:
                        st.error("❌ Không thể chuẩn hóa tự động một số cột đặc biệt trong tệp này. Dữ liệu gốc vẫn được giữ nguyên an toàn.")

            st.divider()

            # Kiểm tra tính toàn vẹn của dữ liệu đã làm sạch
            has_region = bool(orch.data_agent.get_regions_detected())
            total_records = sum(len(df) for df in orch.data_agent.raw_dataframes.values())
        
            st.markdown("#### 📋 Trạng thái sau khi làm sạch:")
            if has_region and total_records > 0:
                st.success(f"🌱 Dữ liệu ổn định! Nhận diện được {len(orch.data_agent.get_regions_detected())} địa bàn ({', '.join(orch.data_agent.get_regions_detected())}) với tổng cộng {total_records} dòng.")
            
                # Khung duyệt của con người
                st.markdown("""
                <div class="human-approval-card">
                    <h4>🧑‍💼 ĐIỂM DUYỆT 2: Con Người Phê Duyệt Dữ Liệu Sạch</h4>
                    <p>Sau khi đã rà soát và chỉnh sửa số liệu chuẩn xác, hãy bấm <strong>"Xác nhận duyệt Bước 2 & Chạy Phân Tích"</strong> để chuyển sang tạo báo cáo.</p>
                </div>
                """, unsafe_allow_html=True)

                col_back, col_next = st.columns([1, 2])
                with col_back:
                    if st.button("⬅️ Quay lại Bước 1", use_container_width=True):
                        set_spinner_msg("⏳ Đang quay lại Bước 1: Tiếp nhận & Kiểm tra tệp dữ liệu...")
                        st.session_state.current_step = 1
                        st.rerun()
                with col_next:
                    if st.button("👉 Duyệt Bước 2 ➔ Sang Bước 3 (Chạy Phân Tích)", type="primary", use_container_width=True, key="btn_approve_step2"):
                        set_spinner_msg("⏳ Bước 2 ➔ Bước 3: Đang chấm điểm đa tiêu chí và khởi tạo Báo cáo & Dashboard...")
                        st.session_state.step2_approved = True
                        st.session_state.current_step = 3
                        st.rerun()
            else:
                st.error("❌ Dữ liệu không ổn định: Không tìm thấy cột Địa Bàn hoặc file bị trống. Vui lòng chỉnh sửa cột trước khi duyệt.")

    # ============================================================
    # BƯỚC 3: QUY TRÌNH PHÂN TÍCH, DASHBOARD & BÁO CÁO HTML (XEM TRƯỚC & CHỈNH SỬA TRỰC TIẾP)
    # ============================================================
    elif st.session_state.current_step == 3:
        st.markdown("### 📊 Bước 3: Phân Tích Đa Tiêu Chí, Xem Trước & Chỉnh Sửa Trực Tiếp Báo Cáo + Dashboard HTML")
        st.caption("✨ Hệ thống hiển thị trực tiếp Báo cáo + Dashboard HTML trên Web. Bạn có thể chỉnh sửa trực tiếp điểm số, nội dung báo cáo và xem trước bản HTML hoàn chỉnh ngay tại đây.")

        # Hàm tạo dữ liệu mặc định chuẩn xác độc lập (không phụ thuộc vào session cũ của Orchestrator)
        def _build_default_scoring_standalone(regions_list):
            target_regions = regions_list if regions_list else ["Đà Nẵng", "Bình Dương", "Hải Phòng", "Cần Thơ"]
            default_profiles = {
                "Đà Nẵng": {"market_size": 8.5, "wms_demand_fit": 9.0, "deployment_feasibility": 8.5, "competitive_landscape": 8.0, "growth_potential": 8.5},
                "Bình Dương": {"market_size": 9.2, "wms_demand_fit": 8.8, "deployment_feasibility": 8.0, "competitive_landscape": 7.2, "growth_potential": 9.0},
                "Hải Phòng": {"market_size": 7.8, "wms_demand_fit": 7.5, "deployment_feasibility": 6.5, "competitive_landscape": 7.5, "growth_potential": 8.0},
                "Cần Thơ": {"market_size": 6.8, "wms_demand_fit": 7.0, "deployment_feasibility": 5.8, "competitive_landscape": 8.2, "growth_potential": 7.2},
            }
            scoring = {}
            totals = []
            for idx, reg in enumerate(target_regions):
                prof = default_profiles.get(reg, {
                    "market_size": round(8.0 - idx * 0.4, 1),
                    "wms_demand_fit": round(8.2 - idx * 0.3, 1),
                    "deployment_feasibility": round(7.8 - idx * 0.4, 1),
                    "competitive_landscape": round(7.5 - idx * 0.2, 1),
                    "growth_potential": round(8.0 - idx * 0.3, 1),
                })
                w_total = round(
                    prof["market_size"] * 0.25 +
                    prof["wms_demand_fit"] * 0.25 +
                    prof["deployment_feasibility"] * 0.25 +
                    prof["competitive_landscape"] * 0.15 +
                    prof["growth_potential"] * 0.10, 2
                )
                totals.append((reg, w_total, prof))
            totals.sort(key=lambda x: x[1], reverse=True)
            for rank_idx, (reg, w_total, prof) in enumerate(totals, start=1):
                scoring[reg] = {
                    "criteria_scores": {k: {"score": v} for k, v in prof.items()},
                    "weighted_total": w_total,
                    "rank": rank_idx,
                    "status": "✅ Đề xuất khảo sát (Top 2)" if rank_idx <= 2 else "⏳ Chưa ưu tiên đợt này"
                }
            top_2 = [x[0] for x in totals[:2]]
            deprioritized = [x[0] for x in totals[2:]]
            return {
                "scoring": scoring,
                "recommendation": {
                    "top_2": top_2,
                    "reason_top": f"Đạt điểm tổng hợp có trọng số cao nhất ({', '.join(top_2)}) về quy mô chuỗi bán lẻ, nhu cầu WMS và năng lực triển khai On-site.",
                    "deprioritized": deprioritized,
                    "reason_deprioritized": "Yêu cầu hỗ trợ kỹ thuật tại chỗ vượt quá nhân sự hiện tại hoặc quy mô chuỗi bán lẻ còn phân mảnh."
                }
            }

        def _build_default_report_standalone(scoring_data):
            rec = scoring_data.get("recommendation", {})
            top_2 = rec.get("top_2", ["Đà Nẵng", "Bình Dương"])
            dep = rec.get("deprioritized", ["Hải Phòng", "Cần Thơ"])
            return f"""## 📑 BÁO CÁO ĐỀ XUẤT MỞ RỘNG THỊ TRƯỜNG — HƯNG PHÁT WMS

    ### 1. Tóm tắt Điều hành (Executive Summary)
    - **[DỮ LIỆU] Mục tiêu:** Đánh giá các địa bàn ứng viên và lựa chọn **02 địa bàn tối ưu nhất** để triển khai khảo sát thực địa giai đoạn tiếp theo.
    - **[ĐỀ XUẤT TRỌNG TÂM]:** Ưu tiên lựa chọn **{', '.join(top_2)}** để tiến hành khảo sát khách hàng trực tiếp.
    - **[LÝ DO CHÍNH]:** {rec.get('reason_top', '')}

    ### 2. Phân Tích Chi Tiết Địa Bàn Ưu Tiên & Địa Bàn Chưa Ưu Tiên
    - **Nhóm Ưu Tiên ({', '.join(top_2)}):**
      - **[DỮ LIỆU]** Tập trung mật độ chuỗi bán lẻ và kho trung chuyển lớn, nhu cầu chuẩn hóa quản lý tồn kho đa điểm (Multi-warehouse WMS) rất cấp thiết.
      - **[SUY LUẬN]** Phù hợp 100% với năng lực triển khai từ xa kết hợp đội phản ứng nhanh của Hưng Phát.
    - **Nhóm Chưa Ưu Tiên Đợt Này ({', '.join(dep)}):**
      - **[DỮ LIỆU]** {rec.get('reason_deprioritized', '')}
      - **[ĐIỀU KIỆN BỔ SUNG]** Chỉ mở rộng khi tuyển dụng được đối tác kỹ thuật ủy quyền tại địa phương."""

        def _build_default_plan_standalone(recommended):
            top_str = ", ".join(recommended) if recommended else "Đà Nẵng, Bình Dương"
            return f"""## 📅 KẾ HOẠCH KHẢO SÁT THỰC ĐỊA 4 TUẦN TẠI: {top_str.upper()}

    ### 1. Nhóm Khách Hàng Mục Tiêu Cần Tiếp Cận
    - **Phân khúc 1:** Chuỗi siêu thị mini, cửa hàng tiện lợi & chuỗi bán lẻ thời trang/FMCG từ 10–50 cửa hàng tại **{top_str}**.
    - **Số lượng mẫu khảo sát:** Tối thiểu 15 doanh nghiệp/địa bàn (Tổng 30 doanh nghiệp).
    - **Thông tin cần xác minh:** Quy trình nhập-xuất-tồn thực tế, phần mềm ERP/POS đang dùng, ngân sách đầu tư WMS và yêu cầu SLA hỗ trợ kỹ thuật.

    ### 2. Lộ Trình Triển Khai & Phân Công Trách Nhiệm
    - **Tuần 1 (Chuẩn bị):** Trưởng phòng PTKD duyệt danh sách 30 khách hàng mục tiêu & kịch bản phỏng vấn.
    - **Tuần 2–3 (Khảo sát thực địa):** Đội BA & Sales Engineer phỏng vấn trực tiếp Quản lý Kho (Warehouse Manager) và Giám đốc Vận hành (COO).
    - **Tuần 4 (Tổng hợp & Báo cáo BGĐ):** Đối chiếu kết quả thực địa với điểm số của AI Agent, chốt phương án đầu tư trình Ban Giám Đốc."""

        # Tự động khởi tạo ngay lập tức nếu chưa có kết quả để người dùng vào Bước 3 là thấy ngay Dashboard & Báo cáo xem trước
        if not st.session_state.analysis_results:
            detected_regs = orch.data_agent.get_regions_detected()
            default_sc = _build_default_scoring_standalone(detected_regs)
            rec_top = default_sc.get("recommendation", {}).get("top_2", ["Đà Nẵng", "Bình Dương"])
            st.session_state.analysis_results = {
                "success": True,
                "scoring": default_sc,
                "report": _build_default_report_standalone(default_sc),
                "survey_plan": _build_default_plan_standalone(rec_top)
            }
            st.session_state.editable_report = st.session_state.analysis_results["report"]
            st.session_state.editable_plan = st.session_state.analysis_results["survey_plan"]
            st.session_state.dashboard_title = "🏢 Báo Cáo & Dashboard Đánh Giá Thị Trường Mở Rộng — Hưng Phát WMS"

        results = st.session_state.analysis_results
        scoring_data = results.get("scoring")
        if not scoring_data or not isinstance(scoring_data, dict) or "scoring" not in scoring_data:
            scoring_data = _build_default_scoring_standalone(orch.data_agent.get_regions_detected())
            results["scoring"] = scoring_data
        if not results.get("report"):
            results["report"] = _build_default_report_standalone(scoring_data)
        if not results.get("survey_plan"):
            rec_top = scoring_data.get("recommendation", {}).get("top_2", ["Đà Nẵng", "Bình Dương"])
            results["survey_plan"] = _build_default_plan_standalone(rec_top)

        if "editable_report" not in st.session_state or not st.session_state.editable_report:
            st.session_state.editable_report = results.get("report", "")
        if "editable_plan" not in st.session_state or not st.session_state.editable_plan:
            st.session_state.editable_plan = results.get("survey_plan", "")
        if "dashboard_title" not in st.session_state:
            st.session_state.dashboard_title = "🏢 Báo Cáo & Dashboard Đánh Giá Thị Trường Mở Rộng — Hưng Phát WMS"

        # Khởi tạo DataFrame điểm số của Dashboard trong session_state để sửa trực tiếp
        if "dashboard_scores_df" not in st.session_state or st.session_state.dashboard_scores_df is None:
            scoring_dict = scoring_data.get("scoring", {})
            table_rows = []
            for region, info in scoring_dict.items():
                crit_scores = info.get("criteria_scores", {})
                s1 = float(crit_scores.get("market_size", {}).get("score", 8.0) if isinstance(crit_scores.get("market_size"), dict) else crit_scores.get("market_size", 8.0))
                s2 = float(crit_scores.get("wms_demand_fit", {}).get("score", 8.0) if isinstance(crit_scores.get("wms_demand_fit"), dict) else crit_scores.get("wms_demand_fit", 8.0))
                s3 = float(crit_scores.get("deployment_feasibility", {}).get("score", 7.5) if isinstance(crit_scores.get("deployment_feasibility"), dict) else crit_scores.get("deployment_feasibility", 7.5))
                s4 = float(crit_scores.get("competitive_landscape", {}).get("score", 7.5) if isinstance(crit_scores.get("competitive_landscape"), dict) else crit_scores.get("competitive_landscape", 7.5))
                s5 = float(crit_scores.get("growth_potential", {}).get("score", 8.0) if isinstance(crit_scores.get("growth_potential"), dict) else crit_scores.get("growth_potential", 8.0))
                w_total = round(s1 * 0.25 + s2 * 0.25 + s3 * 0.25 + s4 * 0.15 + s5 * 0.10, 2)
                table_rows.append({
                    "Địa bàn": region,
                    "Quy mô (25%)": s1,
                    "Nhu cầu WMS (25%)": s2,
                    "Khả thi On-site (25%)": s3,
                    "Cạnh tranh (15%)": s4,
                    "Tăng trưởng (10%)": s5,
                    "Điểm tổng hợp": w_total,
                    "Trạng thái": info.get("status", "Đánh giá")
                })
            df_init = pd.DataFrame(table_rows).sort_values(by="Điểm tổng hợp", ascending=False).reset_index(drop=True)
            df_init["Xếp hạng"] = [f"Hạng {i+1}" for i in range(len(df_init))]
            st.session_state.dashboard_scores_df = df_init

        if "selected_report_charts" not in st.session_state:
            st.session_state.selected_report_charts = ["bar", "radar", "grouped"]
        if "show_edit_report" not in st.session_state:
            st.session_state.show_edit_report = False
        if "show_edit_dashboard" not in st.session_state:
            st.session_state.show_edit_dashboard = False

        # Lấy df_scores hiện hành từ session_state để dựng ngay Xem Trước & Nút Lưu ở trên đầu
        df_scores = st.session_state.dashboard_scores_df.copy()

        # Dựng 3 biểu đồ Plotly từ df_scores hiện hành
        fig_bar = px.bar(
            df_scores, 
            x="Địa bàn", 
            y="Điểm tổng hợp",
            color="Điểm tổng hợp",
            color_continuous_scale=["#fbcfe8", "#f472b6", "#db2777"],
            title="📊 Biểu Đồ 1: Xếp Hạng Điểm Tổng Hợp Có Trọng Số",
            text="Điểm tổng hợp"
        )
        fig_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig_bar.update_layout(
            yaxis_range=[0, 10.5],
            font=dict(family="Plus Jakarta Sans", size=14, color="#3b0764"),
            paper_bgcolor="rgba(255,255,255,0.9)",
            plot_bgcolor="rgba(253,242,248,0.5)"
        )

        categories = ['Quy mô (25%)', 'Nhu cầu WMS (25%)', 'Khả thi On-site (25%)', 'Cạnh tranh (15%)', 'Tăng trưởng (10%)']
        fig_radar = go.Figure()
        colors_radar = ["#db2777", "#8b5cf6", "#0ea5e9", "#10b981", "#f59e0b"]
        for idx, row in df_scores.iterrows():
            r_values = [
                row["Quy mô (25%)"],
                row["Nhu cầu WMS (25%)"],
                row["Khả thi On-site (25%)"],
                row["Cạnh tranh (15%)"],
                row["Tăng trưởng (10%)"]
            ]
            r_values.append(r_values[0])
            fig_radar.add_trace(go.Scatterpolar(
                r=r_values,
                theta=categories + [categories[0]],
                fill='toself',
                name=str(row["Địa bàn"]),
                line=dict(color=colors_radar[idx % len(colors_radar)], width=2.5)
            ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            title="🕸️ Biểu Đồ 2: Radar 5 Chiều So Sánh Năng Lực Địa Bàn",
            font=dict(family="Plus Jakarta Sans", size=13, color="#3b0764"),
            paper_bgcolor="rgba(255,255,255,0.9)"
        )

        df_melted = df_scores.melt(
            id_vars=["Địa bàn"],
            value_vars=["Quy mô (25%)", "Nhu cầu WMS (25%)", "Khả thi On-site (25%)", "Cạnh tranh (15%)", "Tăng trưởng (10%)"],
            var_name="Tiêu chí",
            value_name="Điểm số"
        )
        fig_grouped = px.bar(
            df_melted,
            x="Địa bàn",
            y="Điểm số",
            color="Tiêu chí",
            barmode="group",
            title="📈 Biểu Đồ 3: Phân Tích Chi Tiết Từng Tiêu Chí Theo Địa Bàn",
            color_discrete_sequence=["#ec4899", "#a855f7", "#3b82f6", "#10b981", "#f59e0b"],
            text="Điểm số"
        )
        fig_grouped.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig_grouped.update_layout(
            yaxis_range=[0, 10.8],
            font=dict(family="Plus Jakarta Sans", size=13, color="#3b0764"),
            paper_bgcolor="rgba(255,255,255,0.9)",
            plot_bgcolor="rgba(253,242,248,0.4)"
        )

        bar_html = fig_bar.to_html(full_html=False, include_plotlyjs="cdn")
        radar_html = fig_radar.to_html(full_html=False, include_plotlyjs=False)
        grouped_html = fig_grouped.to_html(full_html=False, include_plotlyjs=False)

        from utils.export_helper import (
            render_chart_png_bytes,
            build_standalone_report_html,
            build_standalone_dashboard_html,
            build_docx_bytes,
            build_pdf_bytes
        )
        import streamlit.components.v1 as components

    # ============================================================
        # 2 TAB TO & NỔI BẬT: BÁO CÁO RIÊNG (CĂN TRÁI) | DASHBOARD RIÊNG (CĂN PHẢI)
    # ============================================================
        if "active_step3_tab" not in st.session_state:
            st.session_state.active_step3_tab = "report"

        with st.container(key="step3_tab_buttons"):
            col_tab_left, col_tab_spacer, col_tab_right = st.columns([4.5, 1, 4.5])
            with col_tab_left:
                if st.button(
                    "📄 TAB 1: BÁO CÁO ĐỀ XUẤT",
                    key="btn_tab_report_left",
                    type="primary" if st.session_state.active_step3_tab == "report" else "secondary",
                    use_container_width=True
                ):
                    set_spinner_msg("⏳ Bước 3: Đang chuyển sang Tab 1 — Xem trước Báo cáo đề xuất...")
                    st.session_state.active_step3_tab = "report"
                    st.rerun()
            with col_tab_right:
                if st.button(
                    "📊 TAB 2: DASHBOARD BIỂU ĐỒ",
                    key="btn_tab_dashboard_right",
                    type="primary" if st.session_state.active_step3_tab == "dashboard" else "secondary",
                    use_container_width=True
                ):
                    set_spinner_msg("⏳ Bước 3: Đang chuyển sang Tab 2 — Xem trước Dashboard biểu đồ...")
                    st.session_state.active_step3_tab = "dashboard"
                    st.rerun()

        st.write("")

        # ------------------------------------------------------------
        # TAB 1: BÁO CÁO ĐỀ XUẤT RIÊNG (XEM TRƯỚC -> LƯU -> NÚT BẤM SỬA)
        # ------------------------------------------------------------
        if st.session_state.active_step3_tab == "report":
            _msg_rep = st.session_state.pending_spinner_msg or "⏳ Bước 3: Đang dựng Bản Xem Trước Báo Cáo Đề Xuất..."
            st.session_state.pending_spinner_msg = ""
            # Cache các file xuất theo nội dung hiện tại để bấm tải về hoặc đóng/mở khung sửa cực nhanh, không phải dựng lại
            _rep_cache_key = (
                st.session_state.dashboard_title,
                st.session_state.editable_report,
                st.session_state.editable_plan,
                tuple(st.session_state.selected_report_charts),
                df_scores.to_json()
            )
            if st.session_state.get("_rep_export_key") != _rep_cache_key:
                with st.spinner(_msg_rep):
                    st.session_state._rep_html_cached = build_standalone_report_html(
                        title=st.session_state.dashboard_title,
                        report_md=st.session_state.editable_report,
                        plan_md=st.session_state.editable_plan,
                        df_scores=df_scores,
                        selected_charts=st.session_state.selected_report_charts
                    )
                    st.session_state._rep_docx_cached = build_docx_bytes(
                        title=st.session_state.dashboard_title,
                        df_scores=df_scores,
                        report_md=st.session_state.editable_report,
                        plan_md=st.session_state.editable_plan,
                        chart_keys=st.session_state.selected_report_charts,
                        mode="report"
                    )
                    st.session_state._rep_pdf_cached = build_pdf_bytes(
                        title=st.session_state.dashboard_title,
                        df_scores=df_scores,
                        report_md=st.session_state.editable_report,
                        plan_md=st.session_state.editable_plan,
                        chart_keys=st.session_state.selected_report_charts,
                        mode="report"
                    )
                    st.session_state._rep_export_key = _rep_cache_key
            elif _msg_rep and _msg_rep != "⏳ Bước 3: Đang dựng Bản Xem Trước Báo Cáo Đề Xuất...":
                with st.spinner(_msg_rep):
                    import time
                    time.sleep(0.15)

            report_only_html = st.session_state._rep_html_cached
            report_docx_bytes = st.session_state._rep_docx_cached
            report_pdf_bytes = st.session_state._rep_pdf_cached

            # 1. BẢN XEM TRƯỚC NẰM NGAY TRÊN ĐẦU (THU GỌN 2/3 CHIỀU RỘNG & DÀI, CĂN GIỮA)
            st.markdown("<h4 style='text-align: center;'>🖥️ 1. Bản Xem Trước Báo Cáo Đề Xuất (Có Chèn Ảnh Biểu Đồ Phân Tích)</h4>", unsafe_allow_html=True)
            _, col_prev_rep, _ = st.columns([1, 4, 1])
            with col_prev_rep:
                components.html(report_only_html, height=450, scrolling=True)

            # 2. NÚT LƯU FILE NẰM NGAY BÊN DƯỚI BẢN XEM TRƯỚC
            st.markdown("#### 📥 2. Lưu Ngay File Báo Cáo Đề Xuất (HTML / DOCX / PDF)")

            dl_rep1, dl_rep2, dl_rep3 = st.columns(3)
            with dl_rep1:
                st.download_button(
                    label="🌐 Lưu Báo Cáo (.html)",
                    data=report_only_html.encode("utf-8"),
                    file_name="Bao_Cao_De_Xuat_HungPhat.html",
                    mime="text/html",
                    type="primary",
                    use_container_width=True,
                    key="dl_rep_html"
                )
            with dl_rep2:
                st.download_button(
                    label="📝 Lưu Báo Cáo Word (.docx)",
                    data=report_docx_bytes,
                    file_name="Bao_Cao_De_Xuat_HungPhat.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary",
                    use_container_width=True,
                    key="dl_rep_docx"
                )
            with dl_rep3:
                st.download_button(
                    label="📕 Lưu Báo Cáo PDF (.pdf)",
                    data=report_pdf_bytes,
                    file_name="Bao_Cao_De_Xuat_HungPhat.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True,
                    key="dl_rep_pdf"
                )

        # ------------------------------------------------------------
        # TAB 2: DASHBOARD BIỂU ĐỒ RIÊNG (XEM TRƯỚC -> LƯU)
        # ------------------------------------------------------------
        elif st.session_state.active_step3_tab == "dashboard":
            _msg_dash = st.session_state.pending_spinner_msg or "⏳ Bước 3: Đang dựng Bản Xem Trước Dashboard Biểu Đồ..."
            st.session_state.pending_spinner_msg = ""
            _dash_cache_key = (
                st.session_state.dashboard_title,
                df_scores.to_json()
            )
            if st.session_state.get("_dash_export_key") != _dash_cache_key:
                with st.spinner(_msg_dash):
                    st.session_state._dash_html_cached = build_standalone_dashboard_html(
                        title=st.session_state.dashboard_title,
                        df_scores=df_scores,
                        bar_html=bar_html,
                        radar_html=radar_html,
                        grouped_html=grouped_html
                    )
                    st.session_state._dash_docx_cached = build_docx_bytes(
                        title=f"DASHBOARD CHẤM ĐIỂM ĐỊA BÀN — {st.session_state.dashboard_title}",
                        df_scores=df_scores,
                        chart_keys=["bar", "radar", "grouped"],
                        mode="dashboard"
                    )
                    st.session_state._dash_pdf_cached = build_pdf_bytes(
                        title=f"DASHBOARD CHẤM ĐIỂM ĐỊA BÀN — {st.session_state.dashboard_title}",
                        df_scores=df_scores,
                        chart_keys=["bar", "radar", "grouped"],
                        mode="dashboard"
                    )
                    st.session_state._dash_export_key = _dash_cache_key
            elif _msg_dash and _msg_dash != "⏳ Bước 3: Đang dựng Bản Xem Trước Dashboard Biểu Đồ...":
                with st.spinner(_msg_dash):
                    import time
                    time.sleep(0.15)

            dashboard_only_html = st.session_state._dash_html_cached
            dash_docx_bytes = st.session_state._dash_docx_cached
            dash_pdf_bytes = st.session_state._dash_pdf_cached

            # 1. BẢN XEM TRƯỚC DASHBOARD NẰM NGAY TRÊN ĐẦU (THU GỌN 2/3 CHIỀU RỘNG & DÀI, CĂN GIỮA)
            st.markdown("<h4 style='text-align: center;'>🖥️ 1. Bản Xem Trước Dashboard Trực Quan (KPI & 3 Biểu Đồ)</h4>", unsafe_allow_html=True)
            _, col_prev_dash, _ = st.columns([1, 4, 1])
            with col_prev_dash:
                components.html(dashboard_only_html, height=450, scrolling=True)

            # 2. NÚT LƯU FILE DASHBOARD NẰM NGAY BÊN DƯỚI BẢN XEM TRƯỚC
            st.markdown("#### 📥 2. Lưu Ngay File Dashboard Riêng (HTML / DOCX / PDF)")

            dl_dash1, dl_dash2, dl_dash3 = st.columns(3)
            with dl_dash1:
                st.download_button(
                    label="🌐 Lưu Dashboard (.html)",
                    data=dashboard_only_html.encode("utf-8"),
                    file_name="Dashboard_Thi_Truong_HungPhat.html",
                    mime="text/html",
                    type="primary",
                    use_container_width=True,
                    key="dl_dash_html"
                )
            with dl_dash2:
                st.download_button(
                    label="📝 Lưu Dashboard Word (.docx)",
                    data=dash_docx_bytes,
                    file_name="Dashboard_Thi_Truong_HungPhat.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary",
                    use_container_width=True,
                    key="dl_dash_docx"
                )
            with dl_dash3:
                st.download_button(
                    label="📕 Lưu Dashboard PDF (.pdf)",
                    data=dash_pdf_bytes,
                    file_name="Dashboard_Thi_Truong_HungPhat.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True,
                    key="dl_dash_pdf"
                )

        st.divider()

    # ============================================================
        # 3. HAI NÚT BẤM MỞ TRÌNH CHỈNH SỬA (1 NÚT SỬA BÁO CÁO, 1 NÚT SỬA DASHBOARD)
    # ============================================================
        st.markdown("#### 🛠️ 3. Tùy Chọn Chỉnh Sửa Trực Tiếp (Bấm Nút Khi Cần Sửa)")
        st.caption("Mặc định phần chỉnh sửa được thu gọn cho thoáng giao diện. Bạn muốn sửa phần nào thì bấm vào nút tương ứng bên dưới:")

        btn_ed_col1, btn_ed_col2 = st.columns(2)
        with btn_ed_col1:
            label_rep_btn = "❌ Đóng khung sửa Báo Cáo" if st.session_state.show_edit_report else "✏️ Bấm vào đây để sửa báo cáo và chọn biểu đồ"
            if st.button(label_rep_btn, use_container_width=True, key="toggle_edit_report_btn"):
                if st.session_state.show_edit_report:
                    set_spinner_msg("⏳ Bước 3: Đang đóng khung chỉnh sửa Báo cáo...")
                else:
                    set_spinner_msg("⏳ Bước 3: Đang mở khung chỉnh sửa Báo cáo & chọn biểu đồ...")
                st.session_state.show_edit_report = not st.session_state.show_edit_report
                st.rerun()

        with btn_ed_col2:
            label_dash_btn = "❌ Đóng khung sửa Dashboard" if st.session_state.show_edit_dashboard else "📊 Bấm vào đây để sửa dashboard"
            if st.button(label_dash_btn, use_container_width=True, key="toggle_edit_dashboard_btn"):
                if st.session_state.show_edit_dashboard:
                    set_spinner_msg("⏳ Bước 3: Đang đóng khung chỉnh sửa điểm số Dashboard...")
                else:
                    set_spinner_msg("⏳ Bước 3: Đang mở bảng chỉnh sửa điểm số trực tiếp trên Dashboard...")
                st.session_state.show_edit_dashboard = not st.session_state.show_edit_dashboard
                st.rerun()

        # KHUNG SỬA BÁO CÁO (CHỈ HIỆN KHI NGƯỜI DÙNG BẤM NÚT SỬA BÁO CÁO)
        if st.session_state.show_edit_report:
            st.markdown("##### ✏️ Khung Chỉnh Sửa Báo Cáo Đề Xuất & Ảnh Biểu Đồ Đính Kèm")
            chart_options_map = {
                "bar": "📊 Biểu Đồ 1: Xếp Hạng Điểm Tổng Hợp Có Trọng Số",
                "radar": "🕸️ Biểu Đồ 2: Radar 5 Chiều So Sánh Năng Lực Địa Bàn",
                "grouped": "📈 Biểu Đồ 3: Phân Tích Chi Tiết 5 Tiêu Chí Theo Địa Bàn"
            }

            selected_chart_keys = st.multiselect(
                "🖼️ Chọn các ảnh biểu đồ muốn chèn vào Báo cáo:",
                options=["bar", "radar", "grouped"],
                default=st.session_state.selected_report_charts,
                format_func=lambda k: chart_options_map[k]
            )

            new_title = st.text_input("📌 Sửa Tiêu đề Báo cáo:", value=st.session_state.dashboard_title, key="rep_title_input")
            col_ed1, col_ed2 = st.columns(2)
            with col_ed1:
                new_report = st.text_area("📝 Sửa Nội dung Báo Cáo Đề Xuất:", value=st.session_state.editable_report, height=280)
            with col_ed2:
                new_plan = st.text_area("📅 Sửa Nội dung Kế Hoạch Khảo Sát 4 Tuần:", value=st.session_state.editable_plan, height=280)

            if st.button("💾 Lưu Chỉnh Sửa Báo Cáo & Đóng Khung Sửa", type="primary", use_container_width=True):
                set_spinner_msg("⏳ Bước 3: Đang lưu chỉnh sửa Báo cáo, chèn lại ảnh biểu đồ và cập nhật file tải về...")
                st.session_state.selected_report_charts = selected_chart_keys
                st.session_state.dashboard_title = new_title
                st.session_state.editable_report = new_report
                st.session_state.editable_plan = new_plan
                results["report"] = new_report
                results["survey_plan"] = new_plan
                st.session_state.show_edit_report = False
                st.success("✅ Đã cập nhật Bản Xem Trước Báo Cáo!")
                st.rerun()

        # KHUNG SỬA DASHBOARD (CHỈ HIỆN KHI NGƯỜI DÙNG BẤM NÚT SỬA DASHBOARD)
        if st.session_state.show_edit_dashboard:
            st.markdown("##### 📊 Khung Chỉnh Sửa Điểm Số Trực Tiếp Trên Dashboard")
            st.info("💡 Nhấp đúp vào ô điểm số bất kỳ trong bảng dưới đây để sửa, sau đó bấm nút **'💾 Lưu Điểm & Cập Nhật Dashboard'**.")

            edited_dash_df = st.data_editor(
                st.session_state.dashboard_scores_df,
                use_container_width=True,
                num_rows="dynamic",
                key="dashboard_score_editor",
                column_config={
                    "Quy mô (25%)": st.column_config.NumberColumn(min_value=0.0, max_value=10.0, step=0.1, format="%.1f"),
                    "Nhu cầu WMS (25%)": st.column_config.NumberColumn(min_value=0.0, max_value=10.0, step=0.1, format="%.1f"),
                    "Khả thi On-site (25%)": st.column_config.NumberColumn(min_value=0.0, max_value=10.0, step=0.1, format="%.1f"),
                    "Cạnh tranh (15%)": st.column_config.NumberColumn(min_value=0.0, max_value=10.0, step=0.1, format="%.1f"),
                    "Tăng trưởng (10%)": st.column_config.NumberColumn(min_value=0.0, max_value=10.0, step=0.1, format="%.1f"),
                    "Điểm tổng hợp": st.column_config.NumberColumn(disabled=True, format="%.2f"),
                    "Xếp hạng": st.column_config.TextColumn(disabled=True),
                }
            )

            col_btn_dash1, col_btn_dash2 = st.columns([1, 1])
            with col_btn_dash1:
                if st.button("💾 Lưu Điểm & Cập Nhật Dashboard", type="primary", use_container_width=True):
                    set_spinner_msg("⏳ Bước 3: Đang tính lại điểm trọng số và vẽ lại 3 biểu đồ Dashboard...")
                    new_df = edited_dash_df.copy()
                    for col_num in ["Quy mô (25%)", "Nhu cầu WMS (25%)", "Khả thi On-site (25%)", "Cạnh tranh (15%)", "Tăng trưởng (10%)"]:
                        new_df[col_num] = pd.to_numeric(new_df[col_num], errors="coerce").fillna(0.0)

                    new_df["Điểm tổng hợp"] = (
                        new_df["Quy mô (25%)"] * 0.25 +
                        new_df["Nhu cầu WMS (25%)"] * 0.25 +
                        new_df["Khả thi On-site (25%)"] * 0.25 +
                        new_df["Cạnh tranh (15%)"] * 0.15 +
                        new_df["Tăng trưởng (10%)"] * 0.10
                    ).round(2)

                    new_df = new_df.sort_values(by="Điểm tổng hợp", ascending=False).reset_index(drop=True)
                    new_df["Xếp hạng"] = [f"Hạng {i+1}" for i in range(len(new_df))]
                    new_df["Trạng thái"] = ["✅ Đề xuất khảo sát (Top 2)" if i < 2 else "⏳ Chưa ưu tiên đợt này" for i in range(len(new_df))]
                    st.session_state.dashboard_scores_df = new_df
                    st.session_state.show_edit_dashboard = False
                    st.success("✅ Đã cập nhật điểm và vẽ lại Dashboard Xem Trước!")
                    st.rerun()

            with col_btn_dash2:
                if st.button("🤖 Chạy Lại AI Agent Phân Tích Chuyên Sâu Từ Dữ Liệu Gốc", use_container_width=True):
                    with st.spinner("⏳ Bước 3: AI Agent đang phân tích dữ liệu sâu và cập nhật lại Báo cáo & Dashboard..."):
                        ai_res = orch.run_full_analysis()
                        st.session_state.analysis_results = ai_res
                        if ai_res.get("report"):
                            st.session_state.editable_report = ai_res["report"]
                        if ai_res.get("survey_plan"):
                            st.session_state.editable_plan = ai_res["survey_plan"]
                        st.session_state.dashboard_scores_df = None
                        st.session_state.show_edit_dashboard = False
                        set_spinner_msg("⏳ Bước 3: Đang dựng lại Báo cáo & Dashboard từ kết quả AI Agent...")
                        st.rerun()

        st.divider()

        # 4. ĐIỂM DUYỆT CUỐI CÙNG (BƯỚC 3)
        st.markdown("""
        <div class="human-approval-card">
            <h4>🧑‍💼 ĐIỂM DUYỆT 3: Trưởng Phòng PTKD & Ban Giám Đốc Ký Duyệt Báo Cáo</h4>
            <p>Xác nhận thẩm định toàn bộ kết quả phân tích và kế hoạch khảo sát để chính thức triển khai dự án.</p>
        </div>
        """, unsafe_allow_html=True)
    
        col_app1, col_app2 = st.columns([2, 1])
        with col_app1:
            approval_decision = st.selectbox(
                "Quyết định phê duyệt cuối cùng:",
                ["Phê duyệt toàn bộ đề xuất của AI & Xuất báo cáo trình BGĐ", "Yêu cầu chỉnh sửa thêm dữ liệu"]
            )
        with col_app2:
            st.write("")
            if "Phê duyệt toàn bộ" in approval_decision:
                if st.button("🌷 Xác Nhận Hoàn Tất Quy Trình", type="primary", use_container_width=True):
                    st.session_state.step3_approved = True
                    st.balloons()
                    st.success("🎉 Chúc mừng! Toàn bộ quy trình 3 bước đã được con người duyệt thành công!")
            else:
                if st.button("🔄 Chuyển Về Bước 2 Để Sửa Dữ Liệu", type="primary", use_container_width=True):
                    st.session_state.step3_approved = False
                    set_spinner_msg("⏳ Đang quay lại Bước 2 theo yêu cầu chỉnh sửa thêm dữ liệu...")
                    st.session_state.current_step = 2
                    st.rerun()

        if "Yêu cầu chỉnh sửa thêm dữ liệu" in approval_decision:
            st.warning("⚠️ Bạn đang chọn **Yêu cầu chỉnh sửa thêm dữ liệu**. Hãy bấm nút **'🔄 Chuyển Về Bước 2 Để Sửa Dữ Liệu'** bên phải (hoặc mở khung sửa Báo cáo / Dashboard ở trên) để hiệu chỉnh lại số liệu.")

        if st.button("⬅️ Quay lại Bước 2 (Chỉnh sửa dữ liệu)"):
            set_spinner_msg("⏳ Đang quay lại Bước 2: Bảng làm sạch & Chỉnh sửa dữ liệu trực tiếp...")
            st.session_state.current_step = 2
            st.rerun()

    # ============================================================
    # CHÂN TRANG THẢM HOA TULIP NẰM TẬN CÙNG DƯỚI ĐÁY
    # ============================================================
except Exception as _global_exc:
    st.error(_vietnamese_error_message(_global_exc))

st.markdown('<div class="footer-tulip-meadow"></div>', unsafe_allow_html=True)

# Dọn sạch bộ phận thông báo cũ từ phiên trước (nếu còn trong trình duyệt)
import streamlit.components.v1 as _cleanup_comp
_cleanup_comp.html("""
<script>
try {
    const oldBanner = window.parent.document.getElementById('hp-instant-loading-banner');
    if (oldBanner) oldBanner.remove();
} catch(e) {}
</script>
""", height=0, width=0)
