"""
서울시 상권 분석 대시보드
디자인: Warm Red Dark Theme (예제 코드 스타일)
데이터: BigQuery 실시간 연동
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
from bq_client import get_bq_client
import io

# ─────────────────────────────────────────────
# 0. 페이지 설정
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="서울시 상권 분석",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# 0-1. 전역 CSS — Warm Red Dark Theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ════════════════════════════════════════════
   BASE — Warm Red Dark Theme (PPT Edition)
════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #2B2626 !important;
    color: #F3EAEA;
    font-family: 'Inter', 'Noto Sans KR', sans-serif;
}
[data-testid="stHeader"]         { background-color: #2B2626 !important; }
[data-testid="stSidebar"]        {
    background: linear-gradient(180deg, #1A1515 0%, #1E1A1A 100%) !important;
    border-right: 1px solid #3A3030 !important;
}
[data-testid="block-container"]  { padding: 1.2rem 2rem 2rem; }
[data-testid="stAppViewContainer"] > div { background-color: #2B2626; }

/* ── 탭 ── */
div[data-testid="stTabs"] button {
    color: #C9B9B9 !important;
    font-size: 0.92rem !important;
    font-weight: 500 !important;
    padding: 0.5rem 1rem !important;
    border-radius: 6px 6px 0 0 !important;
    transition: all 0.2s ease;
}
div[data-testid="stTabs"] button:hover {
    color: #F3EAEA !important;
    background: rgba(255,122,122,0.08) !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #FF7A7A !important;
    border-bottom: 2.5px solid #FF7A7A !important;
    font-weight: 700 !important;
    background: rgba(255,122,122,0.07) !important;
}

/* ── 라디오 / 선택박스 ── */
div[data-testid="stRadio"] label {
    color: #F3EAEA !important;
    font-size: 0.92rem !important;
}
div[data-testid="stSelectbox"] label  { color: #C9B9B9 !important; font-size:0.88rem; }
div[data-testid="stMultiSelect"] label { color: #C9B9B9 !important; font-size:0.88rem; }

/* ── 사이드바 전용 ── */
[data-testid="stSidebar"] * { color: #F3EAEA !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    font-size: 16px !important;
    font-weight: 500 !important;
    padding: 0.35rem 0.5rem !important;
    border-radius: 8px !important;
    transition: background 0.2s;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(255,122,122,0.12) !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-selected="true"] {
    background: rgba(255,122,122,0.18) !important;
    color: #FF7A7A !important;
}

/* ── 버튼 ── */
div[data-testid="stButton"] button {
    background: #3A3333 !important; color: #FF7A7A !important;
    border: 1.5px solid #FF7A7A !important; border-radius: 8px !important;
    font-size: 0.85rem !important; padding: 0.35rem 1rem !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stButton"] button:hover {
    background: #FF7A7A !important; color: #1E1A1A !important;
    box-shadow: 0 4px 14px rgba(255,122,122,0.3) !important;
}
div[data-testid="stDownloadButton"] button {
    background: #3A3333 !important; color: #FF7A7A !important;
    border: 1.5px solid #FF7A7A !important; border-radius: 8px !important;
}

/* ── 메트릭 ── */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #342F2F, #3A3333) !important;
    border: 1px solid #4A3F3F !important;
    border-top: 3px solid #FF7A7A !important;
    border-radius: 12px !important; padding: 16px !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.35) !important;
    transition: transform 0.2s ease !important;
}
[data-testid="metric-container"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(255,122,122,0.15) !important;
}
[data-testid="stMetricValue"]  {
    color: #FF7A7A !important; font-size: 30px !important;
    font-weight: 800 !important;
}
[data-testid="stMetricLabel"]  { color: #C9B9B9 !important; font-size: 13px !important; }
[data-testid="stMetricDelta"]  { font-size: 14px !important; }

/* ── 인풋 / 셀렉트박스 ── */
[data-testid="stSelectbox"] > div > div {
    background: #342F2F !important; border-color: #4A3F3F !important;
    color: #F3EAEA !important; border-radius: 8px !important;
}
[data-baseweb="select"] { background: #342F2F !important; }
[data-baseweb="popover"] { background: #2B2626 !important; }

/* ── 구분선 ── */
hr { border-color: #3A3030 !important; margin: 0.8rem 0 !important; }
div[data-testid="stMarkdownContainer"] h4 { color: #FF7A7A; }

/* ── Spinner ── */
[data-testid="stSpinner"] { color: #FF7A7A !important; }

/* ════════════════════════════════════════════
   커스텀 컴포넌트
════════════════════════════════════════════ */

/* 페이지 헤더 */
.page-header {
    background: linear-gradient(135deg, #1E1A1A 0%, #2B2626 60%, #342F2F 100%);
    border-radius: 16px;
    padding: 1.6rem 2rem 1.4rem;
    margin-bottom: 1.2rem;
    border: 1px solid #3A3030;
    position: relative;
    overflow: hidden;
}
.page-header::before {
    content: '';
    position: absolute; left: 0; top: 0; bottom: 0;
    width: 5px;
    background: linear-gradient(180deg, #FF7A7A, #FFA07A);
    border-radius: 16px 0 0 16px;
}
.page-title {
    font-size: 2rem; font-weight: 900; color: #FF7A7A;
    margin: 0 0 0.2rem 0; line-height: 1.2;
    letter-spacing: -0.02em;
}
.page-sub {
    font-size: 0.88rem; color: #C9B9B9; margin: 0;
}

/* 섹션 타이틀 */
.section-wrap {
    display: flex; align-items: center; gap: 0.7rem;
    margin: 1.4rem 0 0.75rem;
}
.section-bar {
    width: 5px; height: 1.5rem; border-radius: 3px;
    background: linear-gradient(180deg, #FF7A7A, #FFA07A);
    flex-shrink: 0;
}
.section-title {
    font-size: 1rem; font-weight: 700; color: #F3EAEA;
    letter-spacing: 0.01em; margin: 0;
}

/* KPI 카드 */
.kpi-card {
    background: linear-gradient(135deg, #342F2F 0%, #3A3333 100%);
    border: 1px solid #4A3F3F;
    border-top: 3px solid #FF7A7A;
    border-radius: 14px;
    padding: 18px 20px 16px;
    text-align: center;
    box-shadow: 0 6px 20px rgba(0,0,0,0.4);
    margin-bottom: 8px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    position: relative;
    overflow: hidden;
}
.kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 28px rgba(255,122,122,0.18);
}
.kpi-card::after {
    content: '';
    position: absolute; right: -20px; top: -20px;
    width: 80px; height: 80px;
    background: radial-gradient(circle, rgba(255,122,122,0.08) 0%, transparent 70%);
    border-radius: 50%;
}
.kpi-label {
    color: #C9B9B9; font-size: 11px; font-weight: 700;
    letter-spacing: 0.1em; text-transform: uppercase;
    margin-bottom: 8px;
}
.kpi-value {
    color: #FF7A7A; font-size: 34px; font-weight: 900;
    line-height: 1.1;
}
.kpi-delta-up   { color: #4ade80; font-size: 13px; margin-top: 6px; font-weight: 600; }
.kpi-delta-down { color: #f87171; font-size: 13px; margin-top: 6px; font-weight: 600; }

/* 패널 */
.panel {
    background: #342F2F;
    border: 1px solid #4A3F3F;
    border-radius: 12px;
    padding: 0.9rem 1.2rem;
    margin-bottom: 0.6rem;
}
.panel-sub { color: #C9B9B9; font-size: 0.78rem; margin: 0.2rem 0 0.3rem; }

/* 상세 카드 */
.detail-card {
    background: #342F2F; border: 1px solid #4A3F3F;
    border-left: 5px solid #FF7A7A; border-radius: 12px;
    padding: 1.1rem 1.3rem;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
}
.detail-card h2 { color: #FF7A7A; margin: 0 0 0.3rem; font-size: 1.25rem; font-weight: 800; }
.detail-card .meta { color: #C9B9B9; font-size: 0.8rem; margin-bottom: 0.9rem; }
.stat-row { display:flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 0.6rem; }
.stat-box {
    background: #3A3333; border: 1px solid #4A3F3F;
    border-radius: 10px; padding: 0.65rem 1rem; min-width: 130px; flex: 1;
    transition: border-color 0.2s;
}
.stat-box:hover { border-color: #FF7A7A; }
.stat-box .label { font-size: 0.7rem; color: #C9B9B9; margin-bottom: 0.25rem; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; }
.stat-box .value { font-size: 1.2rem; font-weight: 900; color: #FF7A7A; }

/* 인사이트 박스 */
.insight-box {
    background: #342F2F; border: 1px solid #4A3F3F;
    border-left: 4px solid #FF7A7A;
    border-radius: 10px; padding: 0.85rem 1.1rem;
    margin-bottom: 0.5rem;
    font-size: 0.88rem; color: #F3EAEA;
    line-height: 1.5;
}
.insight-box b { color: #FF7A7A; }

/* 랭킹 아이템 */
.rank-item {
    background: #3A3333; border-radius: 10px;
    padding: 0.45rem 0.9rem; margin-bottom: 5px;
    font-size: 0.87rem; color: #F3EAEA;
    display: flex; align-items: center; gap: 0.5rem;
    border: 1px solid transparent; transition: border-color 0.2s;
}
.rank-item:hover { border-color: #FF7A7A; }
.rank-num { color: #FF7A7A; font-weight: 800; min-width: 1.2rem; }
.rank-pct { color: #4ade80; font-weight: 700; margin-left: auto; }

/* 데이터 테이블 */
[data-testid="stDataFrame"] { border-radius: 10px !important; overflow: hidden !important; }

/* 힌트 */
.hint { font-size: 0.76rem; color: #BDAAAA; margin-top: 0.35rem; }

/* Plotly 차트 테두리 */
[data-testid="stPlotlyChart"] > div {
    border-radius: 12px !important; overflow: hidden !important;
}

/* Folium 지도 */
[data-testid="stCustomComponentV1"] > iframe {
    border-radius: 12px !important;
    border: 1px solid #4A3F3F !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 1. 색상 상수
# ─────────────────────────────────────────────
CHART_BG  = "#342F2F"
GRID_CLR  = "#4A3F3F"
TEXT_CLR  = "#F3EAEA"
SUB_CLR   = "#C9B9B9"
MAIN_CLR  = "#FF7A7A"
SEC_CLR   = "#FFA07A"
LINE_CLR  = "#7EC8E3"   # 바+라인 혼합 차트 전용 라인 색 (하늘색 계열, 코랄 바와 대비)
MALE_CLR  = "#6FA8DC"
FEM_CLR   = "#FF7A7A"
PALETTE   = [
    "#FF7A7A","#6FA8DC","#FFA07A","#82C882",
    "#C9A0FF","#FFD700","#87CEEB","#DDA0DD",
    "#98FB98","#F0E68C",
]
GENDER_COLOR = {"M": MALE_CLR, "F": FEM_CLR}

# 서울 25개 구 좌표
SIGUNGU_COORDS = {
    "강남구":  (37.5172, 127.0473), "강동구":  (37.5301, 127.1238),
    "강북구":  (37.6396, 127.0257), "강서구":  (37.5510, 126.8495),
    "관악구":  (37.4784, 126.9516), "광진구":  (37.5385, 127.0823),
    "구로구":  (37.4954, 126.8874), "금천구":  (37.4562, 126.8956),
    "노원구":  (37.6541, 127.0568), "도봉구":  (37.6688, 127.0470),
    "동대문구":(37.5744, 127.0396), "동작구":  (37.5124, 126.9393),
    "마포구":  (37.5663, 126.9014), "서대문구":(37.5791, 126.9368),
    "서초구":  (37.4837, 127.0324), "성동구":  (37.5633, 127.0369),
    "성북구":  (37.5894, 127.0167), "송파구":  (37.5145, 127.1059),
    "양천구":  (37.5270, 126.8561), "영등포구":(37.5264, 126.8963),
    "용산구":  (37.5326, 126.9906), "은평구":  (37.6176, 126.9227),
    "종로구":  (37.5730, 126.9794), "중구":    (37.5640, 126.9975),
    "중랑구":  (37.6063, 127.0927),
}

# ─────────────────────────────────────────────
# 2. BigQuery 설정
# ─────────────────────────────────────────────
PROJECT = "smart-paratext-486618-v8"
MART    = f"`{PROJECT}.mart`"

@st.cache_data(ttl=600, show_spinner=False)
def run_query(sql: str) -> pd.DataFrame:
    return get_bq_client().query(sql).to_dataframe()

# ─────────────────────────────────────────────
# 3. 공통 헬퍼
# ─────────────────────────────────────────────
def fmt_amt(v: float) -> str:
    if v >= 10000: return f"{v/10000:.1f}조"
    return f"{v:.0f}억"

def yq(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["yq"] = df["year"].astype(str) + " Q" + df["quarter"].astype(str)
    return df

def base_layout(h=240, **kw):
    return dict(
        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
        font=dict(color=TEXT_CLR, size=12),
        margin=dict(l=10, r=10, t=44, b=10),
        height=h, **kw,
    )

def warm_fig(fig, height=300, title=""):
    """PPT Edition — Warm Red 다크 테마 레이아웃"""
    fig.update_layout(
        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
        height=height,
        title=dict(
            text=title,
            font=dict(size=16, color=TEXT_CLR, family="Inter, Noto Sans KR, sans-serif"),
            x=0.01, xanchor="left",
            pad=dict(l=4, t=4),
        ),
        margin=dict(l=14, r=14, t=52, b=14),
        legend=dict(
            bgcolor="rgba(42,38,38,0.85)",
            bordercolor=GRID_CLR, borderwidth=1,
            font=dict(color=SUB_CLR, size=13),
            orientation="h", yanchor="bottom", y=-0.28,
            xanchor="center", x=0.5,
        ),
        xaxis=dict(
            gridcolor=GRID_CLR, color=SUB_CLR, linecolor=GRID_CLR,
            tickfont=dict(size=13, color=SUB_CLR),
            title_font=dict(size=14, color=SUB_CLR),
            zeroline=False,
        ),
        yaxis=dict(
            gridcolor=GRID_CLR, color=SUB_CLR, linecolor=GRID_CLR,
            tickfont=dict(size=13, color=SUB_CLR),
            title_font=dict(size=14, color=SUB_CLR),
            zeroline=False,
        ),
        font=dict(size=13, color=TEXT_CLR, family="Inter, Noto Sans KR, sans-serif"),
        hoverlabel=dict(
            bgcolor="#3A3333", bordercolor=MAIN_CLR,
            font=dict(size=13, color=TEXT_CLR),
        ),
    )
    return fig

def section(title: str):
    st.markdown(
        f'''<div class="section-wrap">
            <div class="section-bar"></div>
            <div class="section-title">{title}</div>
        </div>''',
        unsafe_allow_html=True,
    )

def kpi_html(label, value, delta=None, up=True):
    d = ""
    if delta:
        arrow = "▲" if up else "▼"
        cls   = "kpi-delta-up" if up else "kpi-delta-down"
        d = f'<div class="{cls}">{arrow} {delta}</div>'
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {d}
    </div>"""

# ─────────────────────────────────────────────
# 4. Folium 지도 헬퍼
# ─────────────────────────────────────────────
def make_map_tooltip(gu, sales_100m, per_capita, pop=None):
    pop_line = f"👣 유동인구: <b>{pop:.0f}</b><br>" if pop else ""
    return f"""
    <div style="background:#342F2F;color:#F3EAEA;padding:10px 12px;border-radius:10px;
         border-left:4px solid #FF7A7A;font-family:sans-serif;font-size:12px;min-width:180px;">
        <b style="color:#FF7A7A;font-size:13px;">📍 {gu}</b>
        <hr style="border-color:#4A3F3F;margin:6px 0;">
        💰 매출: <b>{fmt_amt(sales_100m)}</b><br>
        {pop_line}
        💵 인당 매출: <b>{per_capita:,.0f}원</b>
    </div>"""

def get_circle_color(val, vmin, vmax):
    ratio = (val - vmin) / (vmax - vmin + 1e-9)
    r = int(80  + ratio * 175)
    g = int(45  + ratio * 70)
    b = int(55  + ratio * 55)
    return f"#{r:02X}{g:02X}{b:02X}"

# ─────────────────────────────────────────────
# 5. 세션 상태 초기화
# ─────────────────────────────────────────────
# "__closed__" = sentinel: st_folium이 이전 클릭값을 계속 반환할 때 재발동 방지용
_CLOSED = "__closed__"

_defaults = {
    # 상단 순위표 선택 상태
    "top_selected_gu":  None,  "show_top_detail":  False,
    # 메인 지도 선택 상태
    "main_selected_gu": None,  "show_main_detail": False,
    # 메인 지도 클릭 중복 방지
    "last_key_main":    None,
    "skip_main_once":   False,
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ─────────────────────────────────────────────
# 6. 쿼리 함수 (실제 BigQuery 스키마)
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def get_sigungu_list():
    df = run_query(f"""
        SELECT DISTINCT sigungu_name FROM {MART}.mart_kpi_sigungu_quarter
        WHERE sigungu_name IS NOT NULL ORDER BY sigungu_name
    """)
    return df["sigungu_name"].tolist()

@st.cache_data(ttl=3600, show_spinner=False)
def q_map_all_sigungu():
    """전체 구 지도용 데이터 (2025년 기준)"""
    return run_query(f"""
        SELECT sigungu_name,
               ROUND(SUM(total_sales_amount)/1e8, 1) AS sales_100m,
               ROUND(AVG(sales_per_capita), 0)        AS per_capita,
               ROUND(AVG(total_avg_quarter_population), 1) AS avg_pop
        FROM {MART}.mart_kpi_sigungu_quarter
        WHERE year = 2025
        GROUP BY sigungu_name ORDER BY sales_100m DESC
    """)

def q_quarterly_seoul():
    return yq(run_query(f"""
        SELECT year, quarter,
            ROUND(SUM(total_sales_amount)/1e8, 1) AS sales_100m
        FROM {MART}.mart_kpi_sigungu_quarter
        GROUP BY year, quarter ORDER BY year, quarter
    """))

def q_seoul_qoq():
    return run_query(f"""
        WITH base AS (
            SELECT year, quarter,
                CONCAT(CAST(year AS STRING),' Q',CAST(quarter AS STRING)) AS yq,
                ROUND(SUM(total_sales_amount)/1e8,1) AS sales_100m
            FROM {MART}.mart_kpi_sigungu_quarter
            GROUP BY year, quarter
        )
        SELECT *,
            ROUND((sales_100m - LAG(sales_100m) OVER (ORDER BY year, quarter))
                / NULLIF(LAG(sales_100m) OVER (ORDER BY year, quarter),0)*100, 2) AS qoq_pct
        FROM base ORDER BY year, quarter
    """)

def q_seoul_pop_trend():
    return yq(run_query(f"""
        SELECT year, quarter,
            ROUND(AVG(avg_quarter_population),1) AS avg_pop
        FROM {MART}.mart_livingpop_seoul_quarter
        GROUP BY year, quarter ORDER BY year, quarter
    """))

def q_top10_efficiency():
    return run_query(f"""
        SELECT sigungu_name,
            ROUND(AVG(sales_per_capita),0)       AS avg_per_capita,
            ROUND(SUM(total_sales_amount)/1e8,1) AS total_sales_100m
        FROM {MART}.mart_kpi_sigungu_quarter
        WHERE sigungu_name IS NOT NULL
        GROUP BY sigungu_name ORDER BY avg_per_capita DESC LIMIT 10
    """)

def q_top10_long_growth():
    return run_query(f"""
        WITH first_last AS (
            SELECT sigungu_name,
                FIRST_VALUE(total_sales_amount)
                    OVER (PARTITION BY sigungu_name ORDER BY year, quarter) AS first_s,
                LAST_VALUE(total_sales_amount)
                    OVER (PARTITION BY sigungu_name ORDER BY year, quarter
                          ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS last_s
            FROM {MART}.mart_kpi_sigungu_quarter WHERE sigungu_name IS NOT NULL
        )
        SELECT DISTINCT sigungu_name,
            ROUND(SAFE_DIVIDE(last_s - first_s, first_s)*100, 2) AS growth_pct
        FROM first_last ORDER BY growth_pct DESC LIMIT 10
    """)

def q_top5_recent_hot():
    return run_query(f"""
        WITH base AS (
            SELECT sigungu_name, year, quarter, total_sales_amount
            FROM {MART}.mart_kpi_sigungu_quarter
            WHERE year=2025 AND quarter IN (1,2,3) AND sigungu_name IS NOT NULL
        ), lagged AS (
            SELECT sigungu_name, year, quarter, total_sales_amount,
                LAG(total_sales_amount) OVER (PARTITION BY sigungu_name ORDER BY year,quarter) AS prev_sales
            FROM base
        ), growth AS (
            SELECT sigungu_name,
                SAFE_DIVIDE(total_sales_amount-prev_sales, prev_sales) AS qoq_growth
            FROM lagged WHERE prev_sales IS NOT NULL AND prev_sales > 0
        )
        SELECT sigungu_name,
            ROUND(AVG(qoq_growth)*100, 2) AS avg_recent_qoq
        FROM growth GROUP BY sigungu_name ORDER BY avg_recent_qoq DESC LIMIT 5
    """)

def q_industry_seoul():
    return yq(run_query(f"""
        SELECT year, quarter, service_industry_name,
            ROUND(SUM(sales_amount)/1e8,1) AS sales_100m
        FROM {MART}.mart_sales_seoul_quarter_industry
        WHERE service_industry_name IS NOT NULL
        GROUP BY year, quarter, service_industry_name ORDER BY year, quarter
    """))

def q_industry_sigungu(sigungu: str):
    return yq(run_query(f"""
        SELECT year, quarter, service_industry_name,
            ROUND(SUM(sales_amount)/1e8,1) AS sales_100m
        FROM {MART}.mart_sales_sigungu_quarter_industry
        WHERE sigungu_name='{sigungu}' AND service_industry_name IS NOT NULL
        GROUP BY year, quarter, service_industry_name ORDER BY year, quarter
    """))

def q_top5_industry_latest(hot_list: list):
    hot_str = "','".join(hot_list)
    return run_query(f"""
        SELECT s.sigungu_name, s.service_industry_name,
            ROUND(SUM(s.sales_amount)/1e8,1) AS sales_100m
        FROM {MART}.mart_sales_sigungu_quarter_industry s
        WHERE s.sigungu_name IN ('{hot_str}') AND s.year=2025
          AND s.quarter IN (1,2,3) AND s.service_industry_name IS NOT NULL
        GROUP BY s.sigungu_name, s.service_industry_name
        ORDER BY s.sigungu_name, sales_100m DESC
    """)

def q_gender_seoul():
    return yq(run_query(f"""
        SELECT g.year, g.quarter, g.gender,
            ROUND(SUM(g.sales_amount)/1e8,1) AS sales_100m
        FROM {MART}.mart_sales_dong_quarter_gender g
        GROUP BY g.year, g.quarter, g.gender ORDER BY g.year, g.quarter, g.gender
    """))

def q_gender_sigungu(sigungu: str):
    return yq(run_query(f"""
        SELECT g.year, g.quarter, g.gender,
            ROUND(SUM(g.sales_amount)/1e8,1) AS sales_100m
        FROM {MART}.mart_sales_dong_quarter_gender g
        JOIN {MART}.dim_admin_dong d USING (admin_dong_code)
        WHERE d.sigungu_name='{sigungu}'
        GROUP BY g.year, g.quarter, g.gender ORDER BY g.year, g.quarter, g.gender
    """))

def q_gender_pop_sigungu(sigungu: str):
    return run_query(f"""
        WITH latest AS (SELECT MAX(year) y FROM {MART}.mart_livingpop_dong_quarter_gender)
        SELECT g.gender, ROUND(SUM(g.avg_population),1) AS avg_pop
        FROM {MART}.mart_livingpop_dong_quarter_gender g
        JOIN {MART}.dim_admin_dong d USING (admin_dong_code), latest
        WHERE d.sigungu_name='{sigungu}' AND g.year=latest.y
        GROUP BY g.gender ORDER BY g.gender
    """)

def q_timeslot_sigungu(sigungu: str):
    return run_query(f"""
        WITH s AS (
            SELECT time_bucket, bucket_id,
                ROUND(AVG(sales_amount)/1e8,1) AS sales_100m
            FROM {MART}.mart_sales_sigungu_quarter_time WHERE sigungu_name='{sigungu}'
            GROUP BY time_bucket, bucket_id
        ), p AS (
            SELECT time_bucket, bucket_id,
                ROUND(AVG(avg_population_sum),1) AS avg_pop
            FROM {MART}.mart_livingpop_sigungu_quarter_time WHERE sigungu_name='{sigungu}'
            GROUP BY time_bucket, bucket_id
        )
        SELECT s.time_bucket, s.bucket_id, s.sales_100m, p.avg_pop
        FROM s LEFT JOIN p USING (time_bucket, bucket_id) ORDER BY s.bucket_id
    """)

def q_timeslot_top5(hot_list: list):
    hot_str = "','".join(hot_list)
    return run_query(f"""
        SELECT sigungu_name, time_bucket, bucket_id,
            ROUND(AVG(sales_amount)/1e8,1) AS sales_100m
        FROM {MART}.mart_sales_sigungu_quarter_time
        WHERE sigungu_name IN ('{hot_str}')
        GROUP BY sigungu_name, time_bucket, bucket_id ORDER BY sigungu_name, bucket_id
    """)

def q_weektype_sigungu(sigungu: str):
    return yq(run_query(f"""
        SELECT w.year, w.quarter, w.week_type,
            ROUND(SUM(w.total_sales)/1e8,1) AS sales_100m
        FROM {MART}.mart_sales_dong_quarter_weektype w
        JOIN {MART}.dim_admin_dong d USING (admin_dong_code)
        WHERE d.sigungu_name='{sigungu}'
        GROUP BY w.year, w.quarter, w.week_type ORDER BY w.year, w.quarter, w.week_type
    """))

def q_weekday_sales_sigungu(sigungu: str):
    return run_query(f"""
        SELECT w.year, w.quarter,
            ROUND(AVG(w.weekday_sales)/1e8,2)         AS weekday_sales_100m,
            ROUND(AVG(w.avg_weekday_population),1)     AS avg_weekday_pop,
            ROUND(AVG(w.sales_per_person),0)           AS sales_per_person
        FROM {MART}.mart_sales_vs_livingpop_weekday_quarter w
        JOIN {MART}.dim_admin_dong d USING (admin_dong_code)
        WHERE d.sigungu_name='{sigungu}'
        GROUP BY w.year, w.quarter ORDER BY w.year, w.quarter
    """)

def q_weekday_pop_sigungu(sigungu: str):
    return run_query(f"""
        SELECT p.base_date,
            EXTRACT(DAYOFWEEK FROM p.base_date) AS dow,
            ROUND(SUM(p.avg_daily_population),1) AS total_pop
        FROM {MART}.mart_livingpop_sigungu_day p WHERE p.sigungu_name='{sigungu}'
        GROUP BY p.base_date, dow ORDER BY p.base_date
    """)

def q_sigungu_detail(sigungu: str):
    """단일 구 KPI + 최근 분기별 추이"""
    return run_query(f"""
        WITH latest AS (
            SELECT MAX(year) AS y, MAX(quarter) AS q
            FROM {MART}.mart_kpi_sigungu_quarter
            WHERE year=2025
        )
        SELECT k.year, k.quarter,
            ROUND(k.total_sales_amount/1e8,1)     AS sales_100m,
            ROUND(k.sales_per_capita,0)            AS per_capita,
            ROUND(k.total_avg_quarter_population,1) AS avg_pop
        FROM {MART}.mart_kpi_sigungu_quarter k
        WHERE k.sigungu_name='{sigungu}'
        ORDER BY k.year, k.quarter
    """)

# ─────────────────────────────────────────────
# 7. KPI 렌더
# ─────────────────────────────────────────────
def render_kpi():
    with st.spinner("KPI 로딩 중…"):
        df = q_seoul_qoq()
    if df.empty: return
    latest = df.iloc[-1]
    prev   = df.iloc[-2] if len(df) > 1 else latest
    qoq    = float(latest["qoq_pct"]) if pd.notna(latest.get("qoq_pct")) else 0.0
    avg_qoq = float(df["qoq_pct"].dropna().mean())
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        st.markdown(kpi_html("최근 분기 서울 매출",
            fmt_amt(latest["sales_100m"]),
            f"{qoq:+.1f}% (QoQ)", qoq>=0), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_html("직전 분기 매출",
            fmt_amt(prev["sales_100m"])), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_html("평균 QoQ 성장률",
            f"{avg_qoq:+.1f}%"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_html("분석 기간",
            f"{len(df)}분기"), unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 8. 구 상세 패널 (지도 클릭 시 공통 렌더)
# ─────────────────────────────────────────────
def render_detail_panel(gu_name: str, pk: str):
    with st.spinner(f"{gu_name} 데이터 로딩…"):
        df_kpi   = q_sigungu_detail(gu_name)
        df_gen   = q_gender_sigungu(gu_name)
        df_ts    = q_timeslot_sigungu(gu_name)
        df_wt    = q_weektype_sigungu(gu_name)
        df_wpop  = q_weekday_pop_sigungu(gu_name)

    # ── 최근 수치 추출
    latest_row = df_kpi.iloc[-1] if not df_kpi.empty else {}
    sales_v    = float(latest_row.get("sales_100m",0)) if latest_row is not None else 0
    pc_v       = float(latest_row.get("per_capita",0)) if latest_row is not None else 0
    pop_v      = float(latest_row.get("avg_pop",0))    if latest_row is not None else 0

    st.markdown(f"""
    <div class="detail-card">
        <h2>📍 {gu_name} 상세 분석</h2>
        <div class="meta">2025년 기준 · BigQuery 실시간 연동</div>
        <div class="stat-row">
            <div class="stat-box">
                <div class="label">💰 최근 분기 매출</div>
                <div class="value">{fmt_amt(sales_v)}</div>
            </div>
            <div class="stat-box">
                <div class="label">👣 평균 유동인구</div>
                <div class="value">{pop_v:.1f}</div>
            </div>
            <div class="stat-box">
                <div class="label">💵 인당 매출</div>
                <div class="value">{pc_v:,.0f}원</div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)
    st.write("")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📈 분기별", "⚥ 성별", "🕐 시간대", "📅 주중/주말", "📆 요일"]
    )

    # ── 탭1: 분기별
    with tab1:
        if not df_kpi.empty:
            df_kpi2 = yq(df_kpi)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_kpi2["yq"], y=df_kpi2["sales_100m"],
                mode="lines+markers", name="매출(억)",
                line=dict(color=MAIN_CLR, width=3),
                marker=dict(color=MAIN_CLR, size=8),
                fill="tozeroy", fillcolor="rgba(255,122,122,0.10)",
            ))
            warm_fig(fig, 240, f"{gu_name} 분기별 매출 추이")
            fig.update_xaxes(showgrid=False)
            st.plotly_chart(fig, use_container_width=True, key=f"t1_{pk}")

            # 타 구 비교 바
            try:
                df_all = q_map_all_sigungu()
                df_s   = df_all.sort_values("sales_100m", ascending=True)
                bc     = [MAIN_CLR if g==gu_name else "#6A6060" for g in df_s["sigungu_name"]]
                fig2   = go.Figure(go.Bar(
                    x=df_s["sales_100m"], y=df_s["sigungu_name"],
                    orientation="h", marker_color=bc,
                    hovertemplate="<b>%{y}</b><br>매출: %{x:.0f}억<extra></extra>",
                ))
                warm_fig(fig2, 340, "서울 전체 구 매출 비교")
                fig2.update_xaxes(showgrid=True, gridcolor=GRID_CLR)
                fig2.update_yaxes(showgrid=False, tickfont=dict(size=11))
                st.plotly_chart(fig2, use_container_width=True, key=f"t1b_{pk}")
            except Exception: pass

    # ── 탭2: 성별
    with tab2:
        if not df_gen.empty:
            ca, cb = st.columns(2)
            with ca:
                latest_yq = df_gen["yq"].max()
                df_pie = df_gen[df_gen["yq"]==latest_yq]
                # ★ 데이터 순서에 맞게 색상 동적 매핑 (M→파랑, F→빨강)
                pie3_colors = [MALE_CLR if g=="M" else FEM_CLR for g in df_pie["gender"]]
                fig3 = go.Figure(go.Pie(
                    labels=df_pie["gender"], values=df_pie["sales_100m"],
                    marker_colors=pie3_colors, hole=0.5,
                    textinfo="label+percent",
                    textfont=dict(color=TEXT_CLR),
                ))
                warm_fig(fig3, 220, "성별 매출 비율 (최근 분기)")
                fig3.update_layout(showlegend=False)
                st.plotly_chart(fig3, use_container_width=True, key=f"t2a_{pk}")
            with cb:
                for g, clr in [("M", MALE_CLR), ("F", FEM_CLR)]:
                    gdf = df_gen[df_gen["gender"]==g]
                    if not gdf.empty:
                        pass
                fig4 = go.Figure()
                for g, clr, lbl in [("M", MALE_CLR,"남성"), ("F", FEM_CLR,"여성")]:
                    gdf = df_gen[df_gen["gender"]==g]
                    if not gdf.empty:
                        fig4.add_trace(go.Scatter(
                            x=gdf["yq"], y=gdf["sales_100m"],
                            mode="lines+markers", name=lbl,
                            line=dict(color=clr, width=2), marker=dict(size=6),
                        ))
                warm_fig(fig4, 220, "성별 분기별 추이")
                fig4.update_layout(legend=dict(bgcolor=CHART_BG, bordercolor=GRID_CLR))
                st.plotly_chart(fig4, use_container_width=True, key=f"t2b_{pk}")

    # ── 탭3: 시간대
    with tab3:
        if not df_ts.empty:
            tcolors = [MAIN_CLR if v==df_ts["sales_100m"].max() else "#6A6060"
                       for v in df_ts["sales_100m"]]
            fig5 = go.Figure(go.Bar(
                x=df_ts["time_bucket"], y=df_ts["sales_100m"],
                marker_color=tcolors,
                text=[f"{v:.0f}억" for v in df_ts["sales_100m"]],
                textposition="outside", textfont=dict(color=TEXT_CLR, size=12),
            ))
            warm_fig(fig5, 240, f"{gu_name} 시간대별 매출")
            fig5.update_xaxes(showgrid=False)
            st.plotly_chart(fig5, use_container_width=True, key=f"t3a_{pk}")

            if "avg_pop" in df_ts.columns and df_ts["avg_pop"].notna().any():
                fig6 = go.Figure(go.Scatter(
                    x=df_ts["time_bucket"], y=df_ts["avg_pop"],
                    mode="lines+markers+text", name="유동인구",
                    line=dict(color=SEC_CLR, width=2, dash="dot"),
                    marker=dict(size=8, color=SEC_CLR),
                    text=[f"{v:.1f}" for v in df_ts["avg_pop"]],
                    textposition="top center",
                    textfont=dict(color=TEXT_CLR, size=10),
                ))
                warm_fig(fig6, 220, f"{gu_name} 시간대별 유동인구")
                st.plotly_chart(fig6, use_container_width=True, key=f"t3b_{pk}")

    # ── 탭4: 주중/주말
    with tab4:
        if not df_wt.empty:
            latest_yq2 = df_wt["yq"].max()
            df_d = df_wt[df_wt["yq"]==latest_yq2]
            wday = float(df_d[df_d["week_type"]=="weekday"]["sales_100m"].sum())
            wend = float(df_d[df_d["week_type"]=="weekend"]["sales_100m"].sum())
            total_w = wday + wend if wday + wend > 0 else 1
            cc, cd = st.columns(2)
            with cc:
                fig7 = go.Figure(go.Pie(
                    labels=["주중(월~금)","주말(토~일)"],
                    values=[wday, wend],
                    marker_colors=[MALE_CLR, FEM_CLR], hole=0.5,
                    textinfo="label+percent", textfont=dict(color=TEXT_CLR),
                ))
                warm_fig(fig7, 220, "주중/주말 비율")
                fig7.update_layout(showlegend=False)
                st.plotly_chart(fig7, use_container_width=True, key=f"t4a_{pk}")
            with cd:
                fig8 = go.Figure()
                for wt, clr, nm in [("weekday", MALE_CLR,"주중"),("weekend", FEM_CLR,"주말")]:
                    sub = df_wt[df_wt["week_type"]==wt]
                    fig8.add_trace(go.Bar(
                        x=sub["yq"], y=sub["sales_100m"],
                        name=nm, marker_color=clr,
                    ))
                warm_fig(fig8, 220, "주중/주말 분기별 추이")
                fig8.update_layout(barmode="group",
                    legend=dict(bgcolor=CHART_BG, bordercolor=GRID_CLR, font=dict(color=TEXT_CLR)))
                st.plotly_chart(fig8, use_container_width=True, key=f"t4b_{pk}")

            st.markdown(f"""
            <div style="background:#3A3333;border-radius:10px;padding:0.7rem 1rem;
                 display:flex;gap:1.5rem;flex-wrap:wrap;margin-top:0.3rem;">
                <div><div style="color:#C9B9B9;font-size:0.72rem;">주중 매출</div>
                     <div style="color:{MALE_CLR};font-weight:800;font-size:1.05rem;">{fmt_amt(wday)}</div></div>
                <div><div style="color:#C9B9B9;font-size:0.72rem;">주말 매출</div>
                     <div style="color:{FEM_CLR};font-weight:800;font-size:1.05rem;">{fmt_amt(wend)}</div></div>
                <div><div style="color:#C9B9B9;font-size:0.72rem;">주말 비율</div>
                     <div style="color:{SEC_CLR};font-weight:800;font-size:1.05rem;">{wend/total_w*100:.1f}%</div></div>
            </div>""", unsafe_allow_html=True)

    # ── 탭5: 요일
    with tab5:
        if not df_wpop.empty:
            dow_map = {1:"일",2:"월",3:"화",4:"수",5:"목",6:"금",7:"토"}
            df_wpop["요일"] = df_wpop["dow"].map(dow_map)
            order = ["월","화","수","목","금","토","일"]
            df_avg = (df_wpop.groupby("요일")["total_pop"].mean()
                             .reset_index().rename(columns={"total_pop":"avg_pop"}))
            df_avg["요일"] = pd.Categorical(df_avg["요일"], categories=order, ordered=True)
            df_avg = df_avg.sort_values("요일")
            max_day = df_avg.loc[df_avg["avg_pop"].idxmax(), "요일"]
            dc = [MAIN_CLR if d==max_day else "#6A6060" for d in df_avg["요일"]]
            fig9 = go.Figure(go.Bar(
                x=df_avg["요일"], y=df_avg["avg_pop"],
                marker_color=dc,
                text=[f"{v:.1f}" for v in df_avg["avg_pop"]],
                textposition="outside", textfont=dict(color=TEXT_CLR, size=12),
            ))
            warm_fig(fig9, 240, f"{gu_name} 요일별 평균 유동인구 (최고: {max_day}요일)")
            fig9.update_xaxes(showgrid=False)
            st.plotly_chart(fig9, use_container_width=True, key=f"t5a_{pk}")

# ─────────────────────────────────────────────
# 9. 종합 대시보드 (Folium 지도 + 클릭 상세)
# ─────────────────────────────────────────────
def render_overview():
    with st.spinner("지도 데이터 로딩 중…"):
        df_map = q_map_all_sigungu()

    if df_map.empty:
        st.warning("지도 데이터를 불러올 수 없습니다.")
        return

    # 좌표 병합
    df_map["lat"] = df_map["sigungu_name"].map(lambda x: SIGUNGU_COORDS.get(x,(37.5665,126.978))[0])
    df_map["lon"] = df_map["sigungu_name"].map(lambda x: SIGUNGU_COORDS.get(x,(37.5665,126.978))[1])
    df_map["per_capita"] = df_map["per_capita"].fillna(0)
    df_map["avg_pop"]    = df_map["avg_pop"].fillna(0)

    top10 = df_map.sort_values("sales_100m", ascending=False).head(10).reset_index(drop=True)
    hot5  = q_top5_recent_hot()

    # ── 상단: 순위표 2개 ──────────────────────────────────────────────────────
    section("📊 상권 순위")
    col_rank1, col_rank2 = st.columns(2, gap="large")

    # ── 왼쪽: 매출 TOP10 ──
    with col_rank1:
        st.markdown(
            '<div class="panel">'
            '<div class="section-title">🏆 최근 분기 매출 TOP 10</div>'
            '<div class="panel-sub">행을 클릭하면 상세 분석이 펼쳐집니다</div>'
            '</div>',
            unsafe_allow_html=True)
        st.write("")

        max_sales = float(top10["sales_100m"].max()) if not top10.empty else 1

        for i, row in top10.iterrows():
            gu    = row["sigungu_name"]
            sales = float(row["sales_100m"])
            pct   = sales / max_sales * 100
            rank_num    = i + 1
            medal_color = {0:"#FFD700", 1:"#C0C0C0", 2:"#CD7F32"}.get(i, "#6A6060")

            is_selected = (st.session_state.top_selected_gu == gu
                           and st.session_state.show_top_detail)
            bg_color = "#3A2F2F" if is_selected else "#2F2929"
            border   = "#FF7A7A" if is_selected else "#4A3F3F"
            bar_clr  = "#FF7A7A" if is_selected else "#8B6060"

            c1, c2, c3 = st.columns([0.4, 2.5, 1.8])
            with c1:
                st.markdown(
                    f'<div style="text-align:center;padding-top:6px;'
                    f'color:{medal_color};font-weight:800;font-size:1rem;">#{rank_num}</div>',
                    unsafe_allow_html=True)
            with c2:
                st.markdown(
                    f'<div style="background:{bg_color};border:1px solid {border};'
                    f'border-radius:8px;padding:0.38rem 0.75rem;margin-bottom:4px;">'
                    f'<span style="color:#F3EAEA;font-weight:600;">{gu}</span>'
                    f'<span style="color:#FF7A7A;float:right;font-size:0.85rem;'
                    f'font-weight:700;">{sales:.1f}억</span>'
                    f'<div style="background:#4A3F3F;border-radius:3px;'
                    f'width:100%;height:5px;margin-top:5px;overflow:hidden;">'
                    f'<div style="background:{bar_clr};width:{pct:.0f}%;height:100%;'
                    f'border-radius:3px;"></div></div>'
                    f'</div>',
                    unsafe_allow_html=True)
            with c3:
                btn_label = "✓ 닫기" if is_selected else "상세보기"
                if st.button(btn_label, key=f"t10_{gu}", use_container_width=True):
                    if is_selected:
                        st.session_state.show_top_detail = False
                        st.session_state.top_selected_gu = None
                    else:
                        st.session_state.top_selected_gu  = gu
                        st.session_state.show_top_detail  = True
                        st.session_state.show_main_detail = False
                    st.rerun()

    # ── 오른쪽: 뜨는 상권 TOP5 ──
    with col_rank2:
        st.markdown(
            '<div class="panel">'
            '<div class="section-title">🔥 뜨는 상권 TOP 5</div>'
            '<div class="panel-sub">최근 분기 QoQ 성장률 기준 · 행을 클릭하면 상세 분석이 펼쳐집니다</div>'
            '</div>',
            unsafe_allow_html=True)
        st.write("")

        if hot5.empty:
            st.info("데이터를 불러올 수 없습니다.")
        else:
            max_qoq = float(hot5["avg_recent_qoq"].abs().max()) if not hot5.empty else 1
            hot5_r  = hot5.reset_index(drop=True)
            fire_icons = ["🔥","⚡","📈","📊","✨"]

            for i, row in hot5_r.iterrows():
                gu      = row["sigungu_name"]
                qoq     = float(row["avg_recent_qoq"])
                bar_pct = abs(qoq) / max_qoq * 100
                rank_num  = i + 1
                fire_icon = fire_icons[i] if i < len(fire_icons) else "📈"

                is_selected = (st.session_state.top_selected_gu == gu
                               and st.session_state.show_top_detail)
                bg_color = "#3A2F2F" if is_selected else "#2F2929"
                border   = "#FF7A7A" if is_selected else "#4A3F3F"
                bar_clr  = "#FF7A7A" if is_selected else "#A05050"

                c1, c2, c3 = st.columns([0.4, 2.5, 1.8])
                with c1:
                    st.markdown(
                        f'<div style="text-align:center;padding-top:6px;'
                        f'font-size:1.1rem;">{fire_icon}</div>',
                        unsafe_allow_html=True)
                with c2:
                    st.markdown(
                        f'<div style="background:{bg_color};border:1px solid {border};'
                        f'border-radius:8px;padding:0.38rem 0.75rem;margin-bottom:4px;">'
                        f'<span style="color:#F3EAEA;font-weight:600;">{gu}</span>'
                        f'<span style="color:#FF7A7A;float:right;font-size:0.85rem;'
                        f'font-weight:700;">{qoq:+.1f}%</span>'
                        f'<div style="background:#4A3F3F;border-radius:3px;'
                        f'width:100%;height:5px;margin-top:5px;overflow:hidden;">'
                        f'<div style="background:{bar_clr};width:{bar_pct:.0f}%;height:100%;'
                        f'border-radius:3px;"></div></div>'
                        f'</div>',
                        unsafe_allow_html=True)
                with c3:
                    btn_label = "✓ 닫기" if is_selected else "상세보기"
                    if st.button(btn_label, key=f"h5_{gu}", use_container_width=True):
                        if is_selected:
                            st.session_state.show_top_detail = False
                            st.session_state.top_selected_gu = None
                        else:
                            st.session_state.top_selected_gu  = gu
                            st.session_state.show_top_detail  = True
                            st.session_state.show_main_detail = False
                        st.rerun()

    # ── 상단 상세 패널 (순위표 클릭 시 펼침) ────────────────────────────────
    top_gu = st.session_state.top_selected_gu
    if top_gu and st.session_state.show_top_detail:
        st.write("")
        hdr_col, btn_col = st.columns([5, 1])
        with hdr_col:
            st.markdown(
                f'<div style="background:#2F2929;border:1px solid #FF7A7A;border-radius:10px;'
                f'padding:0.6rem 1rem;">'
                f'<span style="color:#FF7A7A;font-weight:700;font-size:1.05rem;">'
                f'📌 상세 분석 — {top_gu}</span></div>',
                unsafe_allow_html=True)
        with btn_col:
            if st.button("✕ 닫기", key="close_top_rank"):
                st.session_state.show_top_detail = False
                st.session_state.top_selected_gu = None
                st.rerun()
        render_detail_panel(top_gu, pk="top")
        st.divider()

    # ── 메인 지도 ──────────────────────────────────────────────────────────
    st.divider()
    section("📍 서울 전체 구 선택 (메인)")
    left_col, right_col = st.columns([1.1, 0.9], gap="large")

    with left_col:
        st.markdown('<div class="panel-sub">Hover: 요약 툴팁 · Click: 오른쪽 상세 갱신</div>',
                    unsafe_allow_html=True)
        color_mode = st.radio(
            "color_select",
            ["매출 규모", "인당 매출", "유동인구"],
            horizontal=True, label_visibility="collapsed", key="color_mode_main",
        )
        vcol   = {"매출 규모":"sales_100m","인당 매출":"per_capita","유동인구":"avg_pop"}[color_mode]
        vmin_m = float(df_map[vcol].min())
        vmax_m = float(df_map[vcol].max())

        m = folium.Map(location=[37.5665,126.978], zoom_start=11,
                       tiles="CartoDB DarkMatter", prefer_canvas=True)
        for _, row in df_map.iterrows():
            c      = get_circle_color(row[vcol], vmin_m, vmax_m)
            radius = 12 + (row[vcol]-vmin_m)/(vmax_m-vmin_m+1e-9)*16
            folium.CircleMarker(
                location=[row["lat"], row["lon"]], radius=radius,
                color=c, fill=True, fill_color=c, fill_opacity=0.78, weight=2,
                tooltip=folium.Tooltip(make_map_tooltip(
                    row["sigungu_name"], row["sales_100m"],
                    row["per_capita"], row["avg_pop"]), sticky=False),
                popup=folium.Popup(row["sigungu_name"], max_width=120),
            ).add_to(m)
            folium.Marker(
                location=[row["lat"], row["lon"]],
                icon=folium.DivIcon(
                    html=f'<div style="color:#F3EAEA;font-size:10px;font-weight:800;'
                         f'text-shadow:1px 1px 2px #000;white-space:nowrap;">{row["sigungu_name"]}</div>',
                    icon_size=(90,18), icon_anchor=(45,-6)),
            ).add_to(m)

        r_main = st_folium(m, width=None, height=480,
                           returned_objects=["last_object_clicked_popup"],
                           key="seoul_map_main")
        st.markdown('<div class="hint">💡 Hover: 상세 툴팁 · Click: 오른쪽 상세 갱신</div>',
                    unsafe_allow_html=True)

    with right_col:
        section("📊 상세 분석 (메인)")
        clicked_main = r_main.get("last_object_clicked_popup") if r_main else None

        if st.session_state.skip_main_once:
            st.session_state.skip_main_once = False
        elif (clicked_main and clicked_main in SIGUNGU_COORDS
                and clicked_main != st.session_state.last_key_main):
            st.session_state.last_key_main    = clicked_main
            st.session_state.main_selected_gu = clicked_main
            st.session_state.show_main_detail = True
            # 상단 순위표 상세는 자동 닫기
            st.session_state.show_top_detail  = False
            st.session_state.top_selected_gu  = None
            st.rerun()

        main_gu = st.session_state.main_selected_gu
        if not main_gu or not st.session_state.show_main_detail:
            st.markdown("""
            <div class="detail-card" style="border-left-color:#4A3F3F;">
                <h2>🗺️ 구를 선택해주세요</h2>
                <div class="meta">왼쪽 메인 지도에서 구를 클릭하면 표시됩니다.</div>
                <div style="color:#C9B9B9;font-size:0.9rem;">
                    • 상단 순위표 클릭 → 순위표 아래 상세 펼침<br>
                    • 메인 지도 클릭 → 이 패널에 상세 표시
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            close_col, _ = st.columns([1, 4])
            with close_col:
                if st.button("✕ 상세 닫기", key="close_main"):
                    st.session_state.show_main_detail = False
                    st.session_state.skip_main_once   = True
                    st.session_state.last_key_main    = _CLOSED
                    st.rerun()
            render_detail_panel(main_gu, pk="main")

# ─────────────────────────────────────────────
# 10. 분기별 분석
# ─────────────────────────────────────────────
def render_quarterly():
    section("📈 분기별 매출 분석")
    t1,t2,t3,t4,t5 = st.tabs(["서울 매출 트렌드","QoQ 증감률","매출 vs 유동인구","상권 효율 TOP10","성장 상권"])

    with t1:
        df = q_quarterly_seoul()
        if df.empty: st.info("데이터 없음"); return
        fig = go.Figure()
        n_q = len(df)
        q_colors = [f"rgba(255,{int(122+80*(i/max(n_q-1,1)))},{int(122+40*(i/max(n_q-1,1)))},0.88)"
                    for i in range(n_q)]
        fig.add_bar(x=df["yq"], y=df["sales_100m"], name="매출(억)",
                    marker=dict(color=q_colors, line=dict(color="rgba(255,255,255,0.05)", width=0.5)),
                    text=[fmt_amt(v) for v in df["sales_100m"]],
                    textposition="outside", textfont=dict(size=13, color=TEXT_CLR))
        fig.add_scatter(x=df["yq"], y=df["sales_100m"], mode="lines+markers",
                        line=dict(color=LINE_CLR, width=2.5),
                        marker=dict(size=7, color=LINE_CLR, line=dict(color=TEXT_CLR, width=1)),
                        name="추세선")
        warm_fig(fig, 400, "서울시 전체 분기별 매출 (억원)")
        st.plotly_chart(fig, use_container_width=True)

    with t2:
        df = q_seoul_qoq()
        if df.empty: st.info("데이터 없음"); return
        colors = ["#4ade80" if v>=0 else "#f87171" for v in df["qoq_pct"].fillna(0)]
        fig = go.Figure()
        fig.add_bar(x=df["yq"], y=df["qoq_pct"], marker_color=colors,
                    text=[f"{v:+.1f}%" if pd.notna(v) else "N/A" for v in df["qoq_pct"]],
                    textposition="outside", textfont=dict(size=13, color=TEXT_CLR))
        fig.add_hline(y=0, line_dash="dot", line_color=SUB_CLR, line_width=1)
        warm_fig(fig, 380, "서울시 분기별 QoQ 증감률 (%)")
        st.plotly_chart(fig, use_container_width=True)

    with t3:
        df_s = q_quarterly_seoul(); df_p = q_seoul_pop_trend()
        if df_s.empty: st.info("데이터 없음"); return
        df_m = df_s.merge(df_p, on=["year","quarter","yq"], how="left")
        fig = make_subplots(specs=[[{"secondary_y":True}]])
        fig.add_bar(x=df_m["yq"], y=df_m["sales_100m"],
                    name="매출(억)", marker_color=MAIN_CLR, opacity=0.82, secondary_y=False)
        fig.add_scatter(x=df_m["yq"], y=df_m["avg_pop"],
                        mode="lines+markers", name="평균 유동인구",
                        line=dict(color=LINE_CLR, width=2.5), marker=dict(size=7, color=LINE_CLR), secondary_y=True)
        warm_fig(fig, 380, "서울 매출 vs 유동인구 트렌드")
        fig.update_yaxes(title_text="매출(억)", secondary_y=False, gridcolor=GRID_CLR, color=SUB_CLR)
        fig.update_yaxes(title_text="평균 유동인구", secondary_y=True, gridcolor="rgba(0,0,0,0)", color=SUB_CLR)
        st.plotly_chart(fig, use_container_width=True)

    with t4:
        df = q_top10_efficiency()
        if df.empty: st.info("데이터 없음"); return
        df_s = df.sort_values("avg_per_capita")
        n = len(df_s)
        bar_colors = [f"hsl({int(0+15*(i/max(n-1,1)))},{int(70+20*(i/max(n-1,1)))}%,{int(55+15*(i/max(n-1,1)))}%)" for i in range(n)]
        fig = go.Figure(go.Bar(
            x=df_s["avg_per_capita"], y=df_s["sigungu_name"], orientation="h",
            text=[f"{v:,.0f}원" for v in df_s["avg_per_capita"]],
            textposition="outside", textfont=dict(size=12, color=TEXT_CLR),
            marker=dict(color=bar_colors),
        ))
        warm_fig(fig, 420, "상권 효율 TOP10 (인당 평균 매출)")
        st.plotly_chart(fig, use_container_width=True)

    with t5:
        c1, c2 = st.columns(2)
        with c1:
            df = q_top10_long_growth()
            if not df.empty:
                df_s = df.sort_values("growth_pct"); n = len(df_s)
                bc = [f"hsl({int(160+60*(i/max(n-1,1)))},{int(70)}%,{int(40+20*(i/max(n-1,1)))}%)" for i in range(n)]
                fig = go.Figure(go.Bar(
                    x=df_s["growth_pct"], y=df_s["sigungu_name"], orientation="h",
                    text=[f"{v:+.1f}%" for v in df_s["growth_pct"]],
                    textposition="outside", textfont=dict(size=12, color=TEXT_CLR),
                    marker=dict(color=bc),
                ))
                warm_fig(fig, 420, "📈 장기 성장 상권 TOP10 (3년 누적)")
                st.plotly_chart(fig, use_container_width=True)
        with c2:
            df = q_top5_recent_hot()
            if not df.empty:
                df_s = df.sort_values("avg_recent_qoq"); n = len(df_s)
                bc2 = [f"hsl({int(0+10*(i/max(n-1,1)))},{int(80)}%,{int(50+15*(i/max(n-1,1)))}%)" for i in range(n)]
                fig = go.Figure(go.Bar(
                    x=df_s["avg_recent_qoq"], y=df_s["sigungu_name"], orientation="h",
                    text=[f"{v:+.1f}%" for v in df_s["avg_recent_qoq"]],
                    textposition="outside", textfont=dict(size=12, color=TEXT_CLR),
                    marker=dict(color=bc2),
                ))
                warm_fig(fig, 420, "🔥 최근 뜨는 상권 TOP5 (2025 Q1~Q3)")
                st.plotly_chart(fig, use_container_width=True)
        # 인사이트 패널
        st.markdown('''
        <div class="insight-box">
            <b>📌 장기 성장 TOP10</b> — 외곽 주거 밀집 지역(관악·도봉·강북)이
            3년 누적 두 자릿수 성장률을 기록. 강남 3구 포화 대비 틈새 성장세 뚜렷.
        </div>
        <div class="insight-box">
            <b>🔥 최근 뜨는 TOP5</b> — 성수동(성동구)·홍대(마포구)·흑석(동작구) 등
            MZ 소비 밀집 상권이 QoQ 두 자릿수 성장 지속. 소셜 미디어 유입 효과 반영.
        </div>''', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 11. 업종별 분석
# ─────────────────────────────────────────────
def render_industry():
    section("🏪 업종별 분석")
    t1, t2, t3 = st.tabs(["서울 전체 업종 트렌드","구별 업종 분석","뜨는 상권 TOP5 × 업종"])

    with t1:
        df = q_industry_seoul()
        if df.empty: st.info("데이터 없음"); return
        inds = df["service_industry_name"].unique().tolist()
        top5 = (df.groupby("service_industry_name")["sales_100m"].sum().nlargest(5).index.tolist())
        sel  = st.multiselect("업종 선택", inds, default=top5, key="ind_s")
        if sel:
            df_f = df[df["service_industry_name"].isin(sel)]
            fig = px.line(df_f, x="yq", y="sales_100m", color="service_industry_name",
                          markers=True, color_discrete_sequence=PALETTE,
                          labels={"sales_100m":"매출(억)","yq":"분기","service_industry_name":"업종"})
            warm_fig(fig, 420, "서울 전체 업종별 매출 추이")
            st.plotly_chart(fig, use_container_width=True)

            st.markdown('<div class="section-title" style="font-size:0.85rem;margin:16px 0 10px;">최근 분기 업종 비중</div>', unsafe_allow_html=True)
            df_pie = (df_f[df_f["yq"]==df_f["yq"].max()]
                      .groupby("service_industry_name")["sales_100m"].sum().reset_index())
            fig2 = go.Figure(go.Pie(
                labels=df_pie["service_industry_name"], values=df_pie["sales_100m"], hole=0.55,
                marker=dict(
                    colors=PALETTE[:len(df_pie)],
                    line=dict(color="#2B2626", width=2.5),
                ),
                textinfo="percent+label",
                textfont=dict(size=13, color=TEXT_CLR, family="Inter, sans-serif"),
                pull=[0.035]*len(df_pie),
                hovertemplate="<b>%{label}</b><br>매출: %{value:.0f}억<br>비중: %{percent}<extra></extra>",
            ))
            warm_fig(fig2, 380)
            fig2.update_layout(
                annotations=[dict(
                    text="업종<br>비중", x=0.5, y=0.5,
                    font=dict(size=15, color=TEXT_CLR, family="Inter, sans-serif"),
                    showarrow=False,
                )],
                showlegend=True,
                legend=dict(
                    orientation="v", x=1.02, y=0.5,
                    bgcolor="rgba(0,0,0,0)",
                    font=dict(color=SUB_CLR, size=12),
                ),
            )
            st.plotly_chart(fig2, use_container_width=True)

    with t2:
        sel_gu = st.selectbox("구 선택", get_sigungu_list(), key="ind_gu")
        df = q_industry_sigungu(sel_gu)
        if df.empty: st.info("데이터 없음"); return
        inds = df["service_industry_name"].unique().tolist()
        top5 = (df.groupby("service_industry_name")["sales_100m"].sum().nlargest(5).index.tolist())
        sel  = st.multiselect("업종 선택", inds, default=top5, key="ind_gu_m")
        if sel:
            df_f = df[df["service_industry_name"].isin(sel)]
            fig = px.line(df_f, x="yq", y="sales_100m", color="service_industry_name",
                          markers=True, color_discrete_sequence=PALETTE,
                          labels={"sales_100m":"매출(억)","yq":"분기","service_industry_name":"업종"})
            warm_fig(fig, 400, f"{sel_gu} 업종별 매출 추이")
            st.plotly_chart(fig, use_container_width=True)

    with t3:
        df_hot = q_top5_recent_hot()
        if df_hot.empty: st.info("데이터 없음"); return
        hot_list = df_hot["sigungu_name"].tolist()
        df_ind   = q_top5_industry_latest(hot_list)
        if df_ind.empty: st.info("데이터 없음"); return
        pivot = df_ind.pivot_table(index="sigungu_name", columns="service_industry_name",
                                   values="sales_100m", aggfunc="sum", fill_value=0)
        fig = px.imshow(pivot, labels=dict(x="업종",y="구",color="매출(억)"),
                        color_continuous_scale=[
                            [0.00,"#0f0728"],[0.10,"#3b0764"],[0.30,"#6d28d9"],
                            [0.55,"#ec4899"],[0.78,"#f97316"],[1.00,"#facc15"],
                        ], aspect="auto", text_auto=False)
        warm_fig(fig, 420, "🔥 뜨는 상권 TOP5 × 최근 분기 업종 히트맵")
        fig.update_layout(xaxis=dict(tickangle=-35,tickfont=dict(size=12)),
                          yaxis=dict(tickfont=dict(size=14)),
                          margin=dict(l=10,r=20,t=60,b=100))
        st.plotly_chart(fig, use_container_width=True)

        fig2 = px.bar(df_ind, x="service_industry_name", y="sales_100m",
                      color="sigungu_name", barmode="group",
                      color_discrete_sequence=PALETTE,
                      labels={"sales_100m":"매출(억)","service_industry_name":"업종","sigungu_name":"구"})
        warm_fig(fig2, 400, "뜨는 상권 TOP5 업종별 매출 비교")
        st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────
# 12. 성별 분석
# ─────────────────────────────────────────────
def render_gender():
    section("👥 성별 분석")
    t1, t2, t3 = st.tabs(["서울 전체 성별 트렌드","구별 성별 분석","성별 유동인구 현황"])

    with t1:
        df = q_gender_seoul()
        if df.empty: st.info("데이터 없음"); return
        fig = px.bar(df, x="yq", y="sales_100m", color="gender", barmode="group",
                     color_discrete_map=GENDER_COLOR,
                     labels={"sales_100m":"매출(억)","yq":"분기","gender":"성별"})
        warm_fig(fig, 360, "서울 전체 분기별 성별 매출")
        st.plotly_chart(fig, use_container_width=True)

        df_wide = df.pivot_table(index=["year","quarter","yq"],
                                  columns="gender", values="sales_100m",
                                  aggfunc="sum").reset_index()
        df_wide.columns.name = None
        if "M" in df_wide.columns and "F" in df_wide.columns:
            df_wide["total"] = df_wide["M"] + df_wide["F"]
            df_wide["M_pct"] = df_wide["M"] / df_wide["total"] * 100
            df_wide["F_pct"] = df_wide["F"] / df_wide["total"] * 100
            fig2 = go.Figure()
            fig2.add_scatter(x=df_wide["yq"], y=df_wide["M_pct"],
                             mode="lines+markers", name="남성(%)",
                             line=dict(color=MALE_CLR, width=2))
            fig2.add_scatter(x=df_wide["yq"], y=df_wide["F_pct"],
                             mode="lines+markers", name="여성(%)",
                             line=dict(color=FEM_CLR, width=2))
            fig2.add_hline(y=50, line_dash="dot", line_color=SUB_CLR, line_width=1)
            warm_fig(fig2, 320, "성별 매출 비율 추이 (%)")
            st.plotly_chart(fig2, use_container_width=True)

    with t2:
        sel_gu = st.selectbox("구 선택", get_sigungu_list(), key="gen_gu")
        df = q_gender_sigungu(sel_gu)
        if df.empty: st.info("데이터 없음"); return
        c1, c2 = st.columns(2)
        with c1:
            fig = px.bar(df, x="yq", y="sales_100m", color="gender", barmode="group",
                         color_discrete_map=GENDER_COLOR,
                         labels={"sales_100m":"매출(억)","yq":"분기","gender":"성별"})
            warm_fig(fig, 300, f"{sel_gu} 분기별 성별 매출")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            latest_yq = df["yq"].max()
            df_d = df[df["yq"]==latest_yq]
            # ★ 데이터 순서에 맞게 색상 동적 매핑 (M→파랑, F→빨강)
            pie2_colors = [MALE_CLR if g=="M" else FEM_CLR for g in df_d["gender"]]
            fig2 = go.Figure(go.Pie(
                labels=df_d["gender"], values=df_d["sales_100m"], hole=0.55,
                marker_colors=pie2_colors,
                textinfo="percent+label", textfont=dict(color=TEXT_CLR),
            ))
            warm_fig(fig2, 300, f"{sel_gu} 최근 분기 성별 비율")
            fig2.update_layout(showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

    with t3:
        sel_gu2 = st.selectbox("구 선택", get_sigungu_list(), key="gen_pop_gu")
        df_pop  = q_gender_pop_sigungu(sel_gu2)
        if not df_pop.empty:
            gc = [MALE_CLR if g=="M" else FEM_CLR for g in df_pop["gender"]]
            fig = go.Figure(go.Bar(
                x=df_pop["gender"], y=df_pop["avg_pop"],
                marker_color=gc, text=[f"{v:.1f}" for v in df_pop["avg_pop"]],
                textposition="outside", textfont=dict(color=TEXT_CLR, size=14),
            ))
            warm_fig(fig, 300, f"{sel_gu2} 성별 평균 유동인구 (최근 연도)")
            st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────
# 13. 시간대 분석
# ─────────────────────────────────────────────
def render_timeslot():
    section("🕐 시간대 분석")
    t1, t2 = st.tabs(["구별 시간대 매출 vs 유동인구","뜨는 상권 TOP5 시간대 비교"])

    with t1:
        sel_gu = st.selectbox("구 선택", get_sigungu_list(), key="ts_gu")
        df = q_timeslot_sigungu(sel_gu)
        if df.empty: st.info("데이터 없음"); return
        fig = make_subplots(specs=[[{"secondary_y":True}]])
        fig.add_bar(x=df["time_bucket"], y=df["sales_100m"],
                    name="매출(억)", marker_color=MAIN_CLR, opacity=0.85, secondary_y=False)
        fig.add_scatter(x=df["time_bucket"], y=df["avg_pop"],
                        mode="lines+markers", name="평균 유동인구",
                        line=dict(color=LINE_CLR, width=2.5), marker=dict(size=8, color=LINE_CLR), secondary_y=True)
        warm_fig(fig, 420, f"{sel_gu} 시간대별 매출 vs 유동인구")
        fig.update_yaxes(title_text="매출(억)", secondary_y=False, gridcolor=GRID_CLR, color=SUB_CLR)
        fig.update_yaxes(title_text="평균 유동인구", secondary_y=True, gridcolor="rgba(0,0,0,0)", color=SUB_CLR)
        st.plotly_chart(fig, use_container_width=True)

        if "avg_pop" in df.columns and df["avg_pop"].notna().any():
            df["per_person"] = df["sales_100m"] / df["avg_pop"].replace(0, float("nan"))
            tcolors = [MAIN_CLR if v==df["per_person"].max() else "#6A6060"
                       for v in df["per_person"]]
            fig2 = go.Figure(go.Bar(
                x=df["time_bucket"], y=df["per_person"],
                marker_color=tcolors,
                text=[f"{v:.2f}" for v in df["per_person"]],
                textposition="outside", textfont=dict(size=12, color=TEXT_CLR),
            ))
            warm_fig(fig2, 300, f"{sel_gu} 시간대별 인당 매출 효율")
            st.plotly_chart(fig2, use_container_width=True)

    with t2:
        df_hot = q_top5_recent_hot()
        if df_hot.empty: st.info("데이터 없음"); return
        hot_list = df_hot["sigungu_name"].tolist()
        df = q_timeslot_top5(hot_list)
        if df.empty: st.info("데이터 없음"); return
        VIVID5 = ["#FF7A7A","#6FA8DC","#FFA07A","#82C882","#C9A0FF"]
        fig = px.bar(df, x="time_bucket", y="sales_100m",
                     color="sigungu_name", barmode="group",
                     color_discrete_sequence=VIVID5,
                     labels={"sales_100m":"매출(억)","time_bucket":"시간대","sigungu_name":"구"})
        fig.update_traces(marker_line_color="rgba(255,255,255,0.08)",
                          marker_line_width=1, opacity=0.92)
        warm_fig(fig, 420, "🕐 뜨는 상권 TOP5 시간대별 매출 비교")
        st.plotly_chart(fig, use_container_width=True)

        buckets = sorted(df["time_bucket"].unique())
        fig2 = go.Figure()
        for gu, clr in zip(hot_list, VIVID5):
            r = (df[df["sigungu_name"]==gu].sort_values("bucket_id")["sales_100m"].tolist())
            if r:
                fig2.add_trace(go.Scatterpolar(
                    r=r+[r[0]], theta=buckets+[buckets[0]],
                    fill="toself", name=gu, opacity=0.7,
                    line=dict(color=clr),
                ))
        warm_fig(fig2, 420, "뜨는 상권 TOP5 시간대 패턴 (레이더)")
        fig2.update_layout(polar=dict(
            bgcolor=CHART_BG,
            radialaxis=dict(gridcolor=GRID_CLR, color=SUB_CLR),
            angularaxis=dict(gridcolor=GRID_CLR, color=SUB_CLR)))
        st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────
# 14. 주중/주말 분석
# ─────────────────────────────────────────────
def render_weekday():
    section("📅 주중 / 주말 분석")
    sel_gu = st.selectbox("구 선택", get_sigungu_list(), key="wd_gu")
    t1, t2, t3 = st.tabs(["주중/주말 분기별 추이","요일별 패턴","주중 매출 vs 유동인구"])

    with t1:
        df = q_weektype_sigungu(sel_gu)
        if df.empty: st.info("데이터 없음"); return
        fig = px.line(df, x="yq", y="sales_100m", color="week_type", markers=True,
                      color_discrete_map={"weekday": MALE_CLR,"weekend": FEM_CLR},
                      labels={"sales_100m":"매출(억)","yq":"분기","week_type":"구분"})
        warm_fig(fig, 360, f"{sel_gu} 주중/주말 분기별 매출")
        st.plotly_chart(fig, use_container_width=True)

        latest_yq = df["yq"].max()
        df_d = df[df["yq"]==latest_yq]
        fig2 = go.Figure(go.Pie(
            labels=df_d["week_type"], values=df_d["sales_100m"], hole=0.55,
            marker_colors=[MALE_CLR, FEM_CLR],
            textinfo="percent+label", textfont=dict(color=TEXT_CLR),
        ))
        warm_fig(fig2, 280, f"{sel_gu} 최근 분기 주중/주말 비율")
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    with t2:
        df = q_weekday_pop_sigungu(sel_gu)
        if df.empty: st.info("데이터 없음"); return
        dow_map = {1:"일",2:"월",3:"화",4:"수",5:"목",6:"금",7:"토"}
        df["요일"] = df["dow"].map(dow_map)
        df_avg = (df.groupby("요일")["total_pop"].mean()
                    .reset_index().rename(columns={"total_pop":"avg_pop"}))
        order = ["월","화","수","목","금","토","일"]
        df_avg["요일"] = pd.Categorical(df_avg["요일"], categories=order, ordered=True)
        df_avg = df_avg.sort_values("요일")
        colors = [MALE_CLR if d not in ["토","일"] else FEM_CLR for d in df_avg["요일"]]
        fig = go.Figure(go.Bar(
            x=df_avg["요일"], y=df_avg["avg_pop"],
            marker_color=colors,
            text=[f"{v:.1f}" for v in df_avg["avg_pop"]],
            textposition="outside", textfont=dict(size=14, color=TEXT_CLR),
        ))
        warm_fig(fig, 340, f"{sel_gu} 요일별 평균 유동인구")
        st.plotly_chart(fig, use_container_width=True)

    with t3:
        df = q_weekday_sales_sigungu(sel_gu)
        if df.empty: st.info("데이터 없음"); return
        df = yq(df)
        fig = make_subplots(specs=[[{"secondary_y":True}]])
        fig.add_bar(x=df["yq"], y=df["weekday_sales_100m"],
                    name="주중 매출(억)", marker_color=MAIN_CLR, opacity=0.85, secondary_y=False)
        fig.add_scatter(x=df["yq"], y=df["avg_weekday_pop"],
                        mode="lines+markers", name="주중 평균 유동인구",
                        line=dict(color=LINE_CLR, width=2.5), marker=dict(size=7, color=LINE_CLR), secondary_y=True)
        warm_fig(fig, 380, f"{sel_gu} 주중 매출 vs 유동인구 추이")
        fig.update_yaxes(title_text="매출(억)", secondary_y=False, gridcolor=GRID_CLR, color=SUB_CLR)
        fig.update_yaxes(title_text="평균 유동인구", secondary_y=True, gridcolor="rgba(0,0,0,0)", color=SUB_CLR)
        st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────
# 15. 메인
# ─────────────────────────────────────────────
def main():
    # ── 사이드바
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:20px 0 22px;">
            <div style="font-size:42px;line-height:1;">🏙️</div>
            <div style="font-size:18px;font-weight:900;color:#FF7A7A;
                        margin-top:12px;letter-spacing:-0.02em;">
                서울시 상권 분석</div>
            <div style="font-size:11px;color:#C9B9B9;margin-top:5px;
                        letter-spacing:0.04em;text-transform:uppercase;">
                BigQuery Realtime</div>
            <div style="margin:12px auto 0;width:40px;height:3px;
                        background:linear-gradient(90deg,#FF7A7A,#FFA07A);
                        border-radius:2px;"></div>
        </div>""", unsafe_allow_html=True)
        st.divider()

        page = st.radio("메뉴", [
            "📊 종합 대시보드",
            "📈 분기별 분석",
            "🏪 업종별 분석",
            "👥 성별 분석",
            "🕐 시간대 분석",
            "📅 주중/주말 분석",
        ], label_visibility="collapsed")

        st.divider()
        st.markdown("""
        <div style="background:#2A2424;border:1px solid #3A3030;border-radius:10px;
                    padding:12px 14px;font-size:12px;color:#C9B9B9;line-height:1.7;">
            <div style="color:#FF7A7A;font-weight:700;margin-bottom:6px;font-size:13px;">
                📌 데이터 출처</div>
            <div>• 서울시 상권 매출 통계</div>
            <div>• 서울 생활 유동인구</div>
            <div style="color:#6A6060;font-size:11px;margin-top:6px;
                        border-top:1px solid #3A3030;padding-top:6px;">
                smart-paratext-486618-v8</div>
        </div>""", unsafe_allow_html=True)

    # ── 헤더
    st.markdown('''
    <div class="page-header">
        <div class="page-title">🏙️ 서울 상권 분석 대시보드</div>
        <div class="page-sub">BigQuery 실시간 연동 &nbsp;·&nbsp; 분기별 · 업종별 · 성별 · 시간대 · 주중/주말</div>
    </div>''', unsafe_allow_html=True)

    try:
        render_kpi()
    except Exception as e:
        st.warning(f"KPI 로딩 실패: {e}")
    st.divider()

    if   page == "📊 종합 대시보드":  render_overview()
    elif page == "📈 분기별 분석":    render_quarterly()
    elif page == "🏪 업종별 분석":    render_industry()
    elif page == "👥 성별 분석":      render_gender()
    elif page == "🕐 시간대 분석":    render_timeslot()
    elif page == "📅 주중/주말 분석":  render_weekday()


if __name__ == "__main__":
    main()
