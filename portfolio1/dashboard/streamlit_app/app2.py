"""
서울시 상권 분석 대시보드 (BigQuery 연동 - 실제 스키마 반영 버전)
분석: 분기별 / 업종별 / 성별 / 시간대 / 주중·주말
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from bq_client import get_bq_client

# ─────────────────────────────────────────────
# 0. 페이지 설정
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="서울시 상권 분석 대시보드",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# 0-1. 전역 CSS (다크 테마)
# ─────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #0f1117; }
[data-testid="stSidebar"]          { background-color: #161b22; }

.kpi-card {
    background: linear-gradient(135deg, #1e2330, #252c3d);
    border: 1px solid #2d3748;
    border-radius: 12px;
    padding: 18px 22px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    margin-bottom: 8px;
}
.kpi-label  { color: #a0aec0; font-size: 16px; font-weight: 600;
              letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 8px; }
.kpi-value  { color: #e2e8f0; font-size: 38px; font-weight: 700; }
.kpi-delta-up   { color: #48bb78; font-size: 17px; margin-top: 6px; }
.kpi-delta-down { color: #fc8181; font-size: 17px; margin-top: 6px; }

.section-title {
    font-size: 26px; font-weight: 700; color: #e2e8f0;
    border-left: 5px solid #667eea;
    padding-left: 14px; margin: 24px 0 16px 0;
}
[data-testid="stTabs"] button { color: #a0aec0; font-size: 16px !important; }
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #667eea; border-bottom-color: #667eea; font-size: 16px !important; }
[data-testid="metric-container"] {
    background: #1e2330; border-radius: 10px;
    padding: 18px; border: 1px solid #2d3748; }
[data-testid="stMetricValue"] { color: #e2e8f0; font-size: 32px !important; }
[data-testid="stMetricLabel"] { color: #a0aec0; font-size: 16px !important; }
[data-testid="stMetricDelta"] { font-size: 16px !important; }
/* 사이드바 네비게이션 */
[data-testid="stSidebar"] { font-size: 18px !important; }
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stRadio"] label {
    font-size: 17px !important;
    color: #e2e8f0 !important;
    font-weight: 500;
    padding: 6px 4px !important;
    transition: color 0.2s;
}
[data-testid="stRadio"] label:hover { color: #a78bfa !important; }
[data-testid="stRadio"] [data-baseweb="radio"] input:checked + div {
    background-color: #7c3aed !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #e2e8f0 !important;
}
[data-testid="stSidebar"] b { color: #e2e8f0 !important; }
[data-testid="stSidebar"] span { color: #94a3b8 !important; }
header[data-testid="stHeader"] { background: transparent; }
hr { border-color: #2d3748; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 1. BigQuery 설정
# ─────────────────────────────────────────────
PROJECT = "smart-paratext-486618-v8"
MART    = f"`{PROJECT}.mart`"
STG     = f"`{PROJECT}.stg`"

@st.cache_data(ttl=600, show_spinner=False)
def run_query(sql: str) -> pd.DataFrame:
    return get_bq_client().query(sql).to_dataframe()

# ─────────────────────────────────────────────
# 2. 공통 유틸
# ─────────────────────────────────────────────
def fmt_amt(v):
    """억 단위 숫자를 사람이 읽기 쉽게"""
    if v >= 10000:
        return f"{v/10000:.1f}조"
    return f"{v:.0f}억"

def dark_fig(fig, height=380, title=""):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0d1117", plot_bgcolor="#131720",
        height=height,
        title=dict(text=title, font=dict(size=20, color="#e2e8f0",
                   family="Inter, Pretendard, sans-serif"), x=0.01),
        margin=dict(l=10, r=10, t=52, b=10),
        legend=dict(bgcolor="rgba(13,17,23,0.7)",
                    bordercolor="#2d3748", borderwidth=1,
                    font=dict(color="#cbd5e0", size=15),
                    orientation="h", yanchor="bottom", y=-0.30,
                    xanchor="center", x=0.5),
        xaxis=dict(gridcolor="#1e2a3a", gridwidth=1,
                   color="#94a3b8", zeroline=False,
                   tickfont=dict(size=15), title_font=dict(size=16)),
        yaxis=dict(gridcolor="#1e2a3a", gridwidth=1,
                   color="#94a3b8", zeroline=False,
                   tickfont=dict(size=15), title_font=dict(size=16)),
        font=dict(size=15, color="#e2e8f0",
                  family="Inter, Pretendard, sans-serif"),
        hoverlabel=dict(bgcolor="#1e2a3a", bordercolor="#4a5568",
                        font=dict(size=14, color="#e2e8f0")),
    )
    return fig

def kpi_html(label, value, delta=None, up=True):
    d = ""
    if delta:
        cls = "kpi-delta-up" if up else "kpi-delta-down"
        d = f'<div class="{cls}">{"▲" if up else "▼"} {delta}</div>'
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {d}
    </div>"""

def section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

def yq(df):
    """year+quarter → 'YYYY Qn' 컬럼 추가"""
    df = df.copy()
    df["yq"] = df["year"].astype(str) + " Q" + df["quarter"].astype(str)
    return df

# ── 모던 비비드 팔레트 ───────────────────────────────────────────────────
PALETTE = [
    "#00d4ff", "#7c3aed", "#f97316", "#10b981", "#f43f5e",
    "#fbbf24", "#3b82f6", "#a3e635", "#e879f9", "#06b6d4",
]
# 성별 색상 (글로벌 정의 - render_gender에서 재정의하지 않도록)
GENDER_COLOR_GLOBAL = {"M": "#38bdf8", "F": "#f472b6"}

# ─────────────────────────────────────────────
# 3. 쿼리 함수 (실제 스키마 기반)
# ─────────────────────────────────────────────

# ── 메타 ─────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def get_sigungu_list():
    df = run_query(f"""
        SELECT DISTINCT sigungu_name
        FROM {MART}.mart_kpi_sigungu_quarter
        WHERE sigungu_name IS NOT NULL
        ORDER BY sigungu_name
    """)
    return df["sigungu_name"].tolist()

@st.cache_data(ttl=3600, show_spinner=False)
def get_industry_list():
    df = run_query(f"""
        SELECT DISTINCT service_industry_name
        FROM {MART}.mart_sales_sigungu_quarter_industry
        WHERE service_industry_name IS NOT NULL
        ORDER BY service_industry_name
    """)
    return df["service_industry_name"].tolist()

# ── 분기별 ───────────────────────────────────

def q_quarterly_seoul():
    """서울 전체 분기별 매출"""
    return yq(run_query(f"""
        SELECT year, quarter,
            ROUND(SUM(total_sales_amount)/1e8, 1) AS sales_100m
        FROM {MART}.mart_kpi_sigungu_quarter
        GROUP BY year, quarter ORDER BY year, quarter
    """))

def q_seoul_qoq():
    """서울 전체 QoQ"""
    return run_query(f"""
        WITH base AS (
            SELECT year, quarter,
                CONCAT(CAST(year AS STRING),' Q',CAST(quarter AS STRING)) AS yq,
                ROUND(SUM(total_sales_amount)/1e8,1) AS sales_100m
            FROM {MART}.mart_kpi_sigungu_quarter
            GROUP BY year, quarter
        )
        SELECT *,
            ROUND((sales_100m
                - LAG(sales_100m) OVER (ORDER BY year, quarter))
                / NULLIF(LAG(sales_100m) OVER (ORDER BY year, quarter),0)*100, 2) AS qoq_pct
        FROM base ORDER BY year, quarter
    """)

def q_seoul_pop_trend():
    """서울 전체 유동인구 트렌드"""
    return yq(run_query(f"""
        SELECT year, quarter,
            ROUND(AVG(avg_quarter_population),1) AS avg_pop
        FROM {MART}.mart_livingpop_seoul_quarter
        GROUP BY year, quarter ORDER BY year, quarter
    """))

def q_top10_efficiency():
    """상권 효율 TOP10 (인당 매출 평균)"""
    return run_query(f"""
        SELECT sigungu_name,
            ROUND(AVG(sales_per_capita),0)         AS avg_per_capita,
            ROUND(SUM(total_sales_amount)/1e8,1)   AS total_sales_100m
        FROM {MART}.mart_kpi_sigungu_quarter
        WHERE sigungu_name IS NOT NULL
        GROUP BY sigungu_name
        ORDER BY avg_per_capita DESC LIMIT 10
    """)

def q_top10_long_growth():
    """장기 성장 상권 TOP10 (전체 기간 첫분기→마지막분기 누적 성장률)"""
    return run_query(f"""
        WITH first_last AS (
            SELECT
                sigungu_name,
                FIRST_VALUE(total_sales_amount)
                    OVER (PARTITION BY sigungu_name
                          ORDER BY year, quarter) AS first_sales,
                LAST_VALUE(total_sales_amount)
                    OVER (PARTITION BY sigungu_name
                          ORDER BY year, quarter
                          ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                    ) AS last_sales
            FROM {MART}.mart_kpi_sigungu_quarter
            WHERE sigungu_name IS NOT NULL
        )
        SELECT DISTINCT
            sigungu_name,
            ROUND(SAFE_DIVIDE(last_sales - first_sales, first_sales) * 100, 2) AS growth_pct
        FROM first_last
        ORDER BY growth_pct DESC
        LIMIT 10
    """)

def q_top5_recent_hot():
    """최근 뜨는 상권 TOP5 (2025년 Q1~Q3 평균 QoQ 성장률 — 노트북 기준)"""
    return run_query(f"""
        WITH base AS (
            SELECT sigungu_name, year, quarter, total_sales_amount
            FROM {MART}.mart_kpi_sigungu_quarter
            WHERE year = 2025
              AND quarter IN (1, 2, 3)
              AND sigungu_name IS NOT NULL
        ),
        lagged AS (
            SELECT
                sigungu_name, year, quarter, total_sales_amount,
                LAG(total_sales_amount)
                    OVER (PARTITION BY sigungu_name ORDER BY year, quarter) AS prev_sales
            FROM base
        ),
        growth AS (
            SELECT
                sigungu_name, year, quarter,
                SAFE_DIVIDE(total_sales_amount - prev_sales, prev_sales) AS qoq_growth
            FROM lagged
            WHERE prev_sales IS NOT NULL
              AND prev_sales > 0
        )
        SELECT
            sigungu_name,
            ROUND(AVG(qoq_growth) * 100, 2) AS avg_recent_qoq
        FROM growth
        GROUP BY sigungu_name
        ORDER BY avg_recent_qoq DESC
        LIMIT 5
    """)

# ── 업종별 ───────────────────────────────────

def q_industry_seoul():
    """서울 전체 업종별 분기 매출"""
    return yq(run_query(f"""
        SELECT year, quarter, service_industry_name,
            ROUND(SUM(sales_amount)/1e8,1) AS sales_100m
        FROM {MART}.mart_sales_seoul_quarter_industry
        WHERE service_industry_name IS NOT NULL
        GROUP BY year, quarter, service_industry_name
        ORDER BY year, quarter
    """))

def q_industry_sigungu(sigungu: str):
    """특정 구 업종별 분기 매출"""
    return yq(run_query(f"""
        SELECT year, quarter, service_industry_name,
            ROUND(SUM(sales_amount)/1e8,1) AS sales_100m
        FROM {MART}.mart_sales_sigungu_quarter_industry
        WHERE sigungu_name = '{sigungu}' AND service_industry_name IS NOT NULL
        GROUP BY year, quarter, service_industry_name
        ORDER BY year, quarter
    """))

def q_top5_industry_latest(hot_list: list):
    """뜨는 상권 TOP5 × 2025 Q1~Q3 누적 업종별 매출
    (노트북 Cell 123 기준: 최근 3분기 누적 — 기간을 뜨는상권 쿼리와 통일)"""
    hot_str = "','".join(hot_list)
    return run_query(f"""
        SELECT
            s.sigungu_name,
            s.service_industry_name,
            ROUND(SUM(s.sales_amount) / 1e8, 1) AS sales_100m
        FROM {MART}.mart_sales_sigungu_quarter_industry s
        WHERE s.sigungu_name IN ('{hot_str}')
          AND s.year = 2025
          AND s.quarter IN (1, 2, 3)
          AND s.service_industry_name IS NOT NULL
        GROUP BY s.sigungu_name, s.service_industry_name
        ORDER BY s.sigungu_name, sales_100m DESC
    """)

# ── 성별 ─────────────────────────────────────

def q_gender_seoul():
    """서울 전체 성별 분기 매출 (dong→sigungu 집계)"""
    return yq(run_query(f"""
        SELECT g.year, g.quarter, g.gender,
            ROUND(SUM(g.sales_amount)/1e8,1) AS sales_100m
        FROM {MART}.mart_sales_dong_quarter_gender g
        GROUP BY g.year, g.quarter, g.gender
        ORDER BY g.year, g.quarter, g.gender
    """))

def q_gender_sigungu(sigungu: str):
    """특정 구 성별 분기 매출"""
    return yq(run_query(f"""
        SELECT g.year, g.quarter, g.gender,
            ROUND(SUM(g.sales_amount)/1e8,1) AS sales_100m
        FROM {MART}.mart_sales_dong_quarter_gender g
        JOIN {MART}.dim_admin_dong d USING (admin_dong_code)
        WHERE d.sigungu_name = '{sigungu}'
        GROUP BY g.year, g.quarter, g.gender
        ORDER BY g.year, g.quarter, g.gender
    """))

def q_gender_timeslot_sigungu(sigungu: str):
    """특정 구 성별 × 시간대 매출 + 유동인구 (최근 연도)"""
    return run_query(f"""
        WITH latest AS (
            SELECT MAX(year) y FROM {MART}.mart_sales_dong_quarter_time
        ),
        sales AS (
            SELECT t.time_bucket,
                g.gender,
                ROUND(SUM(g.sales_amount)/1e8,1) AS sales_100m
            FROM {MART}.mart_sales_dong_quarter_gender g
            JOIN {MART}.dim_admin_dong d USING (admin_dong_code)
            JOIN {MART}.mart_sales_dong_quarter_time t
              ON g.admin_dong_code=t.admin_dong_code
             AND g.year=t.year AND g.quarter=t.quarter,
            latest
            WHERE d.sigungu_name='{sigungu}' AND g.year=latest.y
            GROUP BY t.time_bucket, g.gender
        )
        SELECT time_bucket, gender, sales_100m
        FROM sales ORDER BY time_bucket, gender
    """)

def q_gender_pop_sigungu(sigungu: str):
    """특정 구 성별 유동인구 (최근 연도)"""
    return run_query(f"""
        WITH latest AS (
            SELECT MAX(year) y FROM {MART}.mart_livingpop_dong_quarter_gender
        )
        SELECT g.gender,
            ROUND(SUM(g.avg_population),1) AS avg_pop
        FROM {MART}.mart_livingpop_dong_quarter_gender g
        JOIN {MART}.dim_admin_dong d USING (admin_dong_code),
        latest
        WHERE d.sigungu_name='{sigungu}' AND g.year=latest.y
        GROUP BY g.gender ORDER BY g.gender
    """)

# ── 시간대 ───────────────────────────────────

def q_timeslot_sigungu(sigungu: str):
    """특정 구 시간대별 매출 + 유동인구 (전체 기간 평균)"""
    return run_query(f"""
        WITH s AS (
            SELECT time_bucket, bucket_id,
                ROUND(AVG(sales_amount)/1e8,1) AS sales_100m
            FROM {MART}.mart_sales_sigungu_quarter_time
            WHERE sigungu_name='{sigungu}'
            GROUP BY time_bucket, bucket_id
        ),
        p AS (
            SELECT time_bucket, bucket_id,
                ROUND(AVG(avg_population_sum),1) AS avg_pop
            FROM {MART}.mart_livingpop_sigungu_quarter_time
            WHERE sigungu_name='{sigungu}'
            GROUP BY time_bucket, bucket_id
        )
        SELECT s.time_bucket, s.bucket_id,
               s.sales_100m, p.avg_pop
        FROM s LEFT JOIN p USING (time_bucket, bucket_id)
        ORDER BY s.bucket_id
    """)

def q_timeslot_top5(hot_list: list):
    """뜨는 상권 TOP5 × 시간대 매출"""
    hot_str = "','".join(hot_list)
    return run_query(f"""
        SELECT sigungu_name, time_bucket, bucket_id,
            ROUND(AVG(sales_amount)/1e8,1) AS sales_100m
        FROM {MART}.mart_sales_sigungu_quarter_time
        WHERE sigungu_name IN ('{hot_str}')
        GROUP BY sigungu_name, time_bucket, bucket_id
        ORDER BY sigungu_name, bucket_id
    """)

# ── 주중/주말 & 요일 ─────────────────────────

def q_weektype_sigungu(sigungu: str):
    """특정 구 주중/주말 분기별 매출"""
    return yq(run_query(f"""
        SELECT w.year, w.quarter, w.week_type,
            ROUND(SUM(w.total_sales)/1e8,1) AS sales_100m  -- ✅ mart_sales_dong_quarter_weektype 실제 컬럼명
        FROM {MART}.mart_sales_dong_quarter_weektype w
        JOIN {MART}.dim_admin_dong d USING (admin_dong_code)
        WHERE d.sigungu_name='{sigungu}'
        GROUP BY w.year, w.quarter, w.week_type
        ORDER BY w.year, w.quarter, w.week_type
    """))

def q_weekday_sales_sigungu(sigungu: str):
    """특정 구 요일별 매출 vs 유동인구 (weekday_quarter 테이블)"""
    return run_query(f"""
        SELECT w.year, w.quarter,
            ROUND(AVG(w.weekday_sales)/1e8,2)              AS weekday_sales_100m,
            ROUND(AVG(w.avg_weekday_population),1)          AS avg_weekday_pop,
            ROUND(AVG(w.sales_per_person),0)                AS sales_per_person
        FROM {MART}.mart_sales_vs_livingpop_weekday_quarter w
        JOIN {MART}.dim_admin_dong d USING (admin_dong_code)
        WHERE d.sigungu_name='{sigungu}'
        GROUP BY w.year, w.quarter
        ORDER BY w.year, w.quarter
    """)

def q_weekday_pop_sigungu(sigungu: str):
    """특정 구 일별 유동인구 (주중/주말 추정)"""
    return run_query(f"""
        SELECT p.base_date,
            EXTRACT(DAYOFWEEK FROM p.base_date) AS dow,
            ROUND(SUM(p.avg_daily_population),1) AS total_pop
        FROM {MART}.mart_livingpop_sigungu_day p
        WHERE p.sigungu_name='{sigungu}'
        GROUP BY p.base_date, dow
        ORDER BY p.base_date
    """)

# ─────────────────────────────────────────────
# 4. 섹션 렌더링
# ─────────────────────────────────────────────

# ── KPI 헤더 ─────────────────────────────────


def render_kpi():
    with st.spinner("KPI 로딩 중…"):
        df = q_seoul_qoq()
    if df.empty:
        return
    latest = df.iloc[-1]
    prev   = df.iloc[-2] if len(df) > 1 else latest
    qoq    = float(latest["qoq_pct"]) if pd.notna(latest.get("qoq_pct")) else 0.0
    avg_qoq = float(df["qoq_pct"].dropna().mean())

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi_html("최근 분기 서울 매출",
            fmt_amt(latest["sales_100m"]),
            f"{qoq:+.1f}% (QoQ)", qoq >= 0), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_html("직전 분기 매출",
            fmt_amt(prev["sales_100m"])), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_html("평균 QoQ 성장률",
            f"{avg_qoq:+.1f}%"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_html("분석 기간",
            f"{len(df)}분기"), unsafe_allow_html=True)


# ── 분기별 ───────────────────────────────────

def render_quarterly():
    section("📈 분기별 매출 분석")
    t1, t2, t3, t4, t5 = st.tabs([
        "서울 매출 트렌드", "QoQ 증감률",
        "매출 vs 유동인구", "상권 효율 TOP10", "성장 상권"
    ])

    # ── 탭1
    with t1:
        with st.spinner("로딩 중…"):
            df = q_quarterly_seoul()
        if df.empty: st.info("데이터 없음"); return
        fig = go.Figure()
        fig.add_bar(x=df["yq"], y=df["sales_100m"],
                    name="매출(억)", marker_color="#7c3aed",
                    text=[fmt_amt(v) for v in df["sales_100m"]],
                    textposition="outside", textfont=dict(size=15, color="#e2e8f0"))
        fig.add_scatter(x=df["yq"], y=df["sales_100m"],
                        mode="lines+markers",
                        line=dict(color="#fbbf24", width=2),
                        marker=dict(size=6), name="추세선")
        dark_fig(fig, title="서울시 전체 분기별 매출 (억원)")
        st.plotly_chart(fig, width="stretch")

    # ── 탭2
    with t2:
        with st.spinner("로딩 중…"):
            df = q_seoul_qoq()
        if df.empty: st.info("데이터 없음"); return
        colors = ["#48bb78" if v >= 0 else "#fc8181"
                  for v in df["qoq_pct"].fillna(0)]
        fig = go.Figure()
        fig.add_bar(x=df["yq"], y=df["qoq_pct"],
                    marker_color=colors,
                    text=[f"{v:+.1f}%" if pd.notna(v) else "N/A"
                          for v in df["qoq_pct"]],
                    textposition="outside",
                    textfont=dict(size=15, color="#e2e8f0"))
        fig.add_hline(y=0, line_dash="dot", line_color="#4a5568", line_width=1)
        dark_fig(fig, title="서울시 분기별 QoQ 증감률 (%)")
        st.plotly_chart(fig, width="stretch")

    # ── 탭3
    with t3:
        with st.spinner("로딩 중…"):
            df_s = q_quarterly_seoul()
            df_p = q_seoul_pop_trend()
        if df_s.empty: st.info("데이터 없음"); return
        df_m = df_s.merge(df_p, on=["year","quarter","yq"], how="left")
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_bar(x=df_m["yq"], y=df_m["sales_100m"],
                    name="매출(억)", marker_color="#7c3aed",
                    opacity=0.8, secondary_y=False)
        fig.add_scatter(x=df_m["yq"], y=df_m["avg_pop"],
                        mode="lines+markers", name="평균 유동인구",
                        line=dict(color="#fbbf24", width=2),
                        marker=dict(size=7), secondary_y=True)
        dark_fig(fig, title="서울 매출 vs 유동인구 트렌드")
        fig.update_yaxes(title_text="매출(억)", secondary_y=False,
                         gridcolor="#2d3748", color="#a0aec0")
        fig.update_yaxes(title_text="평균 유동인구", secondary_y=True,
                         gridcolor="rgba(0,0,0,0)", color="#a0aec0")
        st.plotly_chart(fig, width="stretch")

    # ── 탭4
    with t4:
        with st.spinner("로딩 중…"):
            df = q_top10_efficiency()
        if df.empty: st.info("데이터 없음"); return
        fig = px.bar(df.sort_values("avg_per_capita"),
                     x="avg_per_capita", y="sigungu_name",
                     orientation="h", text="avg_per_capita",
                     color="avg_per_capita", color_continuous_scale="Plasma")
        fig.update_traces(texttemplate="%{text:,.0f}원", textposition="outside")
        dark_fig(fig, height=420, title="상권 효율 TOP10 (인당 평균 매출)")
        fig.update_coloraxes(showscale=False)
        st.plotly_chart(fig, width="stretch")

    # ── 탭5
    with t5:
        c1, c2 = st.columns(2)
        with c1:
            with st.spinner("로딩 중…"):
                df = q_top10_long_growth()
            if not df.empty:
                df_s = df.sort_values("growth_pct")
                n = len(df_s)
                # Teal→Cyan→Lime 그라데이션 (값 순서 기준)
                import colorsys
                bar_colors = [
                    f"hsl({int(160 + 60*(i/(max(n-1,1))))},{int(80+15*(i/(max(n-1,1))))}%,{int(40+25*(i/(max(n-1,1))))}%)"
                    for i in range(n)
                ]
                fig = go.Figure(go.Bar(
                    x=df_s["growth_pct"], y=df_s["sigungu_name"],
                    orientation="h",
                    text=[f"{v:+.1f}%" for v in df_s["growth_pct"]],
                    textposition="outside",
                    textfont=dict(size=14, color="#e2e8f0"),
                    marker=dict(
                        color=bar_colors,
                        line=dict(color="rgba(255,255,255,0.1)", width=1),
                    ),
                    hovertemplate="<b>%{y}</b><br>누적 성장률: %{x:+.1f}%<extra></extra>",
                ))
                dark_fig(fig, height=420, title="📈 장기 성장 상권 TOP10 (3년 누적)")
                st.plotly_chart(fig, width="stretch")
        with c2:
            with st.spinner("로딩 중…"):
                df = q_top5_recent_hot()
            if not df.empty:
                df_s2 = df.sort_values("avg_recent_qoq")
                n2 = len(df_s2)
                # Orange→Pink→Magenta 그라데이션
                bar_colors2 = [
                    f"hsl({int(20 + 40*(i/(max(n2-1,1))))},{int(90+8*(i/(max(n2-1,1))))}%,{int(50+15*(i/(max(n2-1,1))))}%)"
                    for i in range(n2)
                ]
                fig = go.Figure(go.Bar(
                    x=df_s2["avg_recent_qoq"], y=df_s2["sigungu_name"],
                    orientation="h",
                    text=[f"{v:+.1f}%" for v in df_s2["avg_recent_qoq"]],
                    textposition="outside",
                    textfont=dict(size=14, color="#e2e8f0"),
                    marker=dict(
                        color=bar_colors2,
                        line=dict(color="rgba(255,255,255,0.1)", width=1),
                    ),
                    hovertemplate="<b>%{y}</b><br>평균 QoQ: %{x:+.1f}%<extra></extra>",
                ))
                dark_fig(fig, height=420, title="🔥 최근 뜨는 상권 TOP5 (2025 Q1~Q3 평균 QoQ)")
                st.plotly_chart(fig, width="stretch")


# ── 업종별 ───────────────────────────────────

def render_industry():
    section("🏪 업종별 분석")
    t1, t2, t3 = st.tabs([
        "서울 전체 업종 트렌드", "구별 업종 분석", "뜨는 상권 TOP5 × 업종"
    ])

    with t1:
        with st.spinner("로딩 중…"):
            df = q_industry_seoul()
        if df.empty: st.info("데이터 없음"); return
        inds = df["service_industry_name"].unique().tolist()
        top5 = (df.groupby("service_industry_name")["sales_100m"]
                  .sum().nlargest(5).index.tolist())
        sel = st.multiselect("업종 선택", inds, default=top5, key="ind_s")
        if sel:
            df_f = df[df["service_industry_name"].isin(sel)]
            fig = px.line(df_f, x="yq", y="sales_100m",
                          color="service_industry_name", markers=True,
                          labels={"sales_100m":"매출(억)","yq":"분기",
                                  "service_industry_name":"업종"})
            dark_fig(fig, height=420, title="서울 전체 업종별 매출 추이")
            st.plotly_chart(fig, width="stretch")

            # 최근 분기 파이
            st.markdown('<div class="section-title" style="font-size:20px;margin:16px 0 10px;">최근 분기 업종 비중</div>', unsafe_allow_html=True)
            df_pie = (df_f[df_f["yq"]==df_f["yq"].max()]
                      .groupby("service_industry_name")["sales_100m"]
                      .sum().reset_index())
            DONUT_COLORS = [
                "#00d4ff","#7c3aed","#f97316","#10b981","#f43f5e",
                "#fbbf24","#3b82f6","#a3e635","#e879f9","#06b6d4",
            ]
            fig2 = go.Figure(go.Pie(
                labels=df_pie["service_industry_name"],
                values=df_pie["sales_100m"],
                hole=0.52,
                marker=dict(
                    colors=DONUT_COLORS[:len(df_pie)],
                    line=dict(color="#0d1117", width=2),
                ),
                textinfo="percent+label",
                textfont=dict(size=13, color="#e2e8f0"),
                hovertemplate="<b>%{label}</b><br>매출: %{value:.0f}억<br>비율: %{percent}<extra></extra>",
                pull=[0.03]*len(df_pie),
            ))
            dark_fig(fig2, height=380)
            fig2.update_layout(
                legend=dict(font=dict(size=13, color="#cbd5e0"),
                            bgcolor="rgba(13,17,23,0.7)",
                            bordercolor="#2d3748", borderwidth=1),
                annotations=[dict(
                    text="업종<br>비중", x=0.5, y=0.5,
                    font_size=15, font_color="#e2e8f0",
                    showarrow=False,
                )],
            )
            st.plotly_chart(fig2, width="stretch")

    with t2:
        sel_gu = st.selectbox("구 선택", get_sigungu_list(), key="ind_gu")
        with st.spinner("로딩 중…"):
            df = q_industry_sigungu(sel_gu)
        if df.empty: st.info("데이터 없음"); return
        inds = df["service_industry_name"].unique().tolist()
        top5 = (df.groupby("service_industry_name")["sales_100m"]
                  .sum().nlargest(5).index.tolist())
        sel = st.multiselect("업종 선택", inds, default=top5, key="ind_gu_m")
        if sel:
            df_f = df[df["service_industry_name"].isin(sel)]
            fig = px.line(df_f, x="yq", y="sales_100m",
                          color="service_industry_name", markers=True,
                          labels={"sales_100m":"매출(억)","yq":"분기",
                                  "service_industry_name":"업종"})
            dark_fig(fig, height=400, title=f"{sel_gu} 업종별 매출 추이")
            st.plotly_chart(fig, width="stretch")

    with t3:
        with st.spinner("뜨는 상권 로딩 중…"):
            df_hot = q_top5_recent_hot()
        if df_hot.empty: st.info("데이터 없음"); return
        hot_list = df_hot["sigungu_name"].tolist()
        with st.spinner("업종 로딩 중…"):
            df_ind = q_top5_industry_latest(hot_list)
        if df_ind.empty: st.info("데이터 없음"); return

        pivot = df_ind.pivot_table(
            index="sigungu_name", columns="service_industry_name",
            values="sales_100m", aggfunc="sum", fill_value=0)

        # ── px.imshow 히트맵 (선명한 색상 대비) ───────────────────────
        fig = px.imshow(
            pivot,
            labels=dict(x="업종", y="구", color="매출(억)"),
            color_continuous_scale=[
                [0.00, "#0f0728"],   # 거의 0 → 딥 다크 퍼플
                [0.10, "#3b0764"],   # 낮음 → 진한 보라
                [0.30, "#6d28d9"],   # 중하 → 비비드 퍼플
                [0.55, "#ec4899"],   # 중상 → 핑크
                [0.78, "#f97316"],   # 높음 → 오렌지
                [1.00, "#facc15"],   # 최고 → 선명한 옐로
            ],
            aspect="auto",
            text_auto=False,
        )
        dark_fig(fig, height=420,
                 title="🔥 뜨는 상권 TOP5 × 최근 분기 업종 히트맵")
        fig.update_layout(
            xaxis=dict(side="bottom", tickangle=-35,
                       tickfont=dict(size=13), title_font=dict(size=15)),
            yaxis=dict(tickfont=dict(size=15)),
            margin=dict(l=10, r=20, t=60, b=100),
            coloraxis_colorbar=dict(
                title=dict(text="매출(억)",
                           font=dict(color="#e2e8f0", size=14)),
                tickfont=dict(color="#a0aec0", size=13),
                thickness=14, len=0.85,
            ),
        )
        st.plotly_chart(fig, width="stretch")

        fig2 = px.bar(df_ind, x="service_industry_name", y="sales_100m",
                      color="sigungu_name", barmode="group",
                      labels={"sales_100m":"매출(억)",
                              "service_industry_name":"업종","sigungu_name":"구"})
        dark_fig(fig2, height=400, title="뜨는 상권 TOP5 업종별 매출 비교")
        st.plotly_chart(fig2, width="stretch")


# ── 성별 ─────────────────────────────────────

def render_gender():
    section("👥 성별 분석")
    t1, t2, t3 = st.tabs([
        "서울 전체 성별 트렌드", "구별 성별 분석", "성별 유동인구 현황"
    ])

    # 성별 레이블 색상
    GENDER_COLOR = GENDER_COLOR_GLOBAL

    with t1:
        with st.spinner("로딩 중…"):
            df = q_gender_seoul()
        if df.empty: st.info("데이터 없음"); return

        fig = px.bar(df, x="yq", y="sales_100m",
                     color="gender", barmode="group",
                     color_discrete_map=GENDER_COLOR,
                     labels={"sales_100m":"매출(억)","yq":"분기","gender":"성별"})
        dark_fig(fig, title="서울 전체 분기별 성별 매출")
        st.plotly_chart(fig, width="stretch")

        # 비율 추이
        df_wide = df.pivot_table(
            index=["year","quarter","yq"],
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
                             line=dict(color="#38bdf8", width=2))
            fig2.add_scatter(x=df_wide["yq"], y=df_wide["F_pct"],
                             mode="lines+markers", name="여성(%)",
                             line=dict(color="#f472b6", width=2))
            fig2.add_hline(y=50, line_dash="dot",
                           line_color="#4a5568", line_width=1)
            dark_fig(fig2, title="성별 매출 비율 추이 (%)")
            st.plotly_chart(fig2, width="stretch")

    with t2:
        sel_gu = st.selectbox("구 선택", get_sigungu_list(), key="gen_gu")
        with st.spinner("로딩 중…"):
            df = q_gender_sigungu(sel_gu)
        if df.empty: st.info("데이터 없음"); return
        c1, c2 = st.columns(2)
        with c1:
            fig = px.bar(df, x="yq", y="sales_100m",
                         color="gender", barmode="group",
                         color_discrete_map=GENDER_COLOR,
                         labels={"sales_100m":"매출(억)","yq":"분기","gender":"성별"})
            dark_fig(fig, title=f"{sel_gu} 분기별 성별 매출(억)")
            st.plotly_chart(fig, width="stretch")
        with c2:
            latest_yq = df["yq"].max()
            df_d = df[df["yq"]==latest_yq]
            fig2 = go.Figure(go.Pie(
                labels=df_d["gender"],
                values=df_d["sales_100m"],
                hole=0.55,
                marker_colors=["#38bdf8","#f472b6"]))
            dark_fig(fig2, height=340,
                     title=f"{sel_gu} 최근 분기 성별 매출 비율")
            fig2.update_traces(textinfo="percent+label")
            st.plotly_chart(fig2, width="stretch")

    with t3:
        sel_gu2 = st.selectbox("구 선택", get_sigungu_list(), key="gen_pop_gu")
        with st.spinner("로딩 중…"):
            df_pop = q_gender_pop_sigungu(sel_gu2)
        if not df_pop.empty:
            fig = px.bar(df_pop, x="gender", y="avg_pop",
                         color="gender",
                         color_discrete_map=GENDER_COLOR,
                         text="avg_pop",
                         labels={"avg_pop":"평균 유동인구","gender":"성별"})
            fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
            dark_fig(fig, height=340,
                     title=f"{sel_gu2} 성별 평균 유동인구 (최근 연도)")
            st.plotly_chart(fig, width="stretch")


# ── 시간대 ───────────────────────────────────

def render_timeslot():
    section("🕐 시간대 분석")
    t1, t2 = st.tabs([
        "구별 시간대 매출 vs 유동인구", "뜨는 상권 TOP5 시간대 비교"
    ])

    with t1:
        sel_gu = st.selectbox("구 선택", get_sigungu_list(), key="ts_gu")
        with st.spinner("로딩 중…"):
            df = q_timeslot_sigungu(sel_gu)
        if df.empty: st.info("데이터 없음"); return

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_bar(x=df["time_bucket"], y=df["sales_100m"],
                    name="매출(억)", marker_color="#7c3aed",
                    opacity=0.85, secondary_y=False)
        fig.add_scatter(x=df["time_bucket"], y=df["avg_pop"],
                        mode="lines+markers", name="평균 유동인구",
                        line=dict(color="#fbbf24", width=2),
                        marker=dict(size=8), secondary_y=True)
        dark_fig(fig, height=420,
                 title=f"{sel_gu} 시간대별 매출 vs 유동인구")
        fig.update_yaxes(title_text="매출(억)", secondary_y=False,
                         gridcolor="#2d3748", color="#a0aec0")
        fig.update_yaxes(title_text="평균 유동인구", secondary_y=True,
                         gridcolor="rgba(0,0,0,0)", color="#a0aec0")
        st.plotly_chart(fig, width="stretch")

        # 시간대별 인당 매출 (효율)
        if "avg_pop" in df.columns:
            df["per_person"] = df["sales_100m"] / df["avg_pop"].replace(0, float("nan"))
            fig2 = px.bar(df, x="time_bucket", y="per_person",
                          color="per_person",
                          color_continuous_scale="Magenta",
                          text="per_person",
                          labels={"per_person":"인당 매출(억)","time_bucket":"시간대"})
            fig2.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            dark_fig(fig2, height=320,
                     title=f"{sel_gu} 시간대별 인당 매출 효율")
            fig2.update_coloraxes(showscale=False)
            st.plotly_chart(fig2, width="stretch")

    with t2:
        with st.spinner("뜨는 상권 로딩 중…"):
            df_hot = q_top5_recent_hot()
        if df_hot.empty: st.info("데이터 없음"); return
        hot_list = df_hot["sigungu_name"].tolist()
        with st.spinner("시간대 로딩 중…"):
            df = q_timeslot_top5(hot_list)
        if df.empty: st.info("데이터 없음"); return

        VIVID5 = ["#00d4ff", "#7c3aed", "#f97316", "#10b981", "#f43f5e"]
        fig = px.bar(df, x="time_bucket", y="sales_100m",
                     color="sigungu_name", barmode="group",
                     color_discrete_sequence=VIVID5,
                     labels={"sales_100m":"매출(억)",
                             "time_bucket":"시간대","sigungu_name":"구"})
        fig.update_traces(marker_line_color="rgba(255,255,255,0.08)",
                          marker_line_width=1, opacity=0.92)
        dark_fig(fig, height=420,
                 title="🕐 뜨는 상권 TOP5 시간대별 매출 비교")
        st.plotly_chart(fig, width="stretch")

        # 레이더 차트
        buckets = sorted(df["time_bucket"].unique())
        fig2 = go.Figure()
        for gu in hot_list:
            r = (df[df["sigungu_name"]==gu]
                 .sort_values("bucket_id")["sales_100m"].tolist())
            if r:
                fig2.add_trace(go.Scatterpolar(
                    r=r+[r[0]], theta=buckets+[buckets[0]],
                    fill="toself", name=gu, opacity=0.7))
        dark_fig(fig2, height=420,
                 title="뜨는 상권 TOP5 시간대 패턴 (레이더)")
        fig2.update_layout(polar=dict(
            bgcolor="#161b22",
            radialaxis=dict(gridcolor="#2d3748", color="#a0aec0"),
            angularaxis=dict(gridcolor="#2d3748", color="#a0aec0")))
        st.plotly_chart(fig2, width="stretch")


# ── 주중/주말 ────────────────────────────────

def render_weekday():
    section("📅 주중 / 주말 분석")
    sel_gu = st.selectbox("구 선택", get_sigungu_list(), key="wd_gu")
    t1, t2, t3 = st.tabs([
        "주중/주말 분기별 추이", "요일별 패턴 (일별)", "주중 매출 vs 유동인구"
    ])

    with t1:
        with st.spinner("로딩 중…"):
            df = q_weektype_sigungu(sel_gu)
        if df.empty: st.info("데이터 없음"); return

        fig = px.line(df, x="yq", y="sales_100m",
                      color="week_type", markers=True,
                      color_discrete_map={
                          "weekday":"#7c3aed","weekend":"#fbbf24"},
                      labels={"sales_100m":"매출(억)",
                              "yq":"분기","week_type":"구분"})
        dark_fig(fig, title=f"{sel_gu} 주중/주말 분기별 매출")
        st.plotly_chart(fig, width="stretch")

        latest_yq = df["yq"].max()
        df_d = df[df["yq"]==latest_yq]
        fig2 = go.Figure(go.Pie(
            labels=df_d["week_type"], values=df_d["sales_100m"],
            hole=0.55,
            marker_colors=["#7c3aed","#fbbf24"]))
        dark_fig(fig2, height=300,
                 title=f"{sel_gu} 최근 분기 주중/주말 비율")
        fig2.update_traces(textinfo="percent+label")
        st.plotly_chart(fig2, width="stretch")

    with t2:
        with st.spinner("일별 유동인구 로딩 중…"):
            df = q_weekday_pop_sigungu(sel_gu)
        if df.empty: st.info("데이터 없음"); return

        # 요일 레이블
        dow_map = {1:"일",2:"월",3:"화",4:"수",5:"목",6:"금",7:"토"}
        df["요일"] = df["dow"].map(dow_map)
        df_avg = (df.groupby("요일")["total_pop"].mean()
                    .reset_index().rename(columns={"total_pop":"avg_pop"}))
        order = ["월","화","수","목","금","토","일"]
        df_avg["요일"] = pd.Categorical(df_avg["요일"], categories=order, ordered=True)
        df_avg = df_avg.sort_values("요일")

        colors = ["#38bdf8" if d not in ["토","일"] else "#f472b6"
                  for d in df_avg["요일"]]
        fig = go.Figure(go.Bar(
            x=df_avg["요일"], y=df_avg["avg_pop"],
            marker_color=colors,
            text=[f"{v:.1f}" for v in df_avg["avg_pop"]],
            textposition="outside", textfont=dict(size=15, color="#e2e8f0")))
        dark_fig(fig, title=f"{sel_gu} 요일별 평균 유동인구")
        st.plotly_chart(fig, width="stretch")

    with t3:
        with st.spinner("로딩 중…"):
            df = q_weekday_sales_sigungu(sel_gu)
        if df.empty: st.info("데이터 없음"); return
        df = yq(df)
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_bar(x=df["yq"], y=df["weekday_sales_100m"],
                    name="주중 매출(억)", marker_color="#7c3aed",
                    opacity=0.85, secondary_y=False)
        fig.add_scatter(x=df["yq"], y=df["avg_weekday_pop"],
                        mode="lines+markers", name="주중 평균 유동인구",
                        line=dict(color="#fbbf24", width=2),
                        marker=dict(size=7), secondary_y=True)
        dark_fig(fig, height=380,
                 title=f"{sel_gu} 주중 매출 vs 유동인구 추이")
        fig.update_yaxes(title_text="매출(억)", secondary_y=False,
                         gridcolor="#2d3748", color="#a0aec0")
        fig.update_yaxes(title_text="평균 유동인구", secondary_y=True,
                         gridcolor="rgba(0,0,0,0)", color="#a0aec0")
        st.plotly_chart(fig, width="stretch")


# ─────────────────────────────────────────────
# 5. 사이드바 + 라우팅
# ─────────────────────────────────────────────

def main():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:16px 0 20px;">
            <div style="font-size:40px;">🏙️</div>
            <div style="font-size:22px;font-weight:700;color:#e2e8f0;margin-top:10px;">
                서울시 상권 분석</div>
            <div style="font-size:15px;color:#718096;margin-top:4px;">
                BigQuery 실시간 연동</div>
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
        <div style="font-size:15px;color:#718096;padding:6px;">
            <b style="color:#a0aec0;">📌 데이터 출처</b><br>
            서울시 상권 매출 통계<br>
            서울 생활 유동인구<br>
            <span style="color:#4a5568;">smart-paratext-486618-v8</span>
        </div>""", unsafe_allow_html=True)

    # ── 헤더
    st.markdown("""
    <h1 style="font-size:34px;font-weight:800;color:#e2e8f0;margin:0 0 6px;">
        🏙️ 서울시 상권 분석 대시보드</h1>
    <p style="color:#718096;font-size:17px;margin:0 0 20px;">
        BigQuery 실시간 연동 | 분기별·업종별·성별·시간대·주중주말</p>
    """, unsafe_allow_html=True)

    try:
        render_kpi()
    except Exception as e:
        st.warning(f"KPI 로딩 실패: {e}")
    st.divider()

    # ── 종합 대시보드
    if page == "📊 종합 대시보드":
        c1, c2 = st.columns(2)
        with c1:
            section("📈 서울 분기별 매출")
            try:
                df = q_quarterly_seoul()
                if not df.empty:
                    fig = go.Figure()
                    fig.add_bar(x=df["yq"], y=df["sales_100m"],
                                marker_color="#7c3aed", name="매출(억)")
                    fig.add_scatter(x=df["yq"], y=df["sales_100m"],
                                    mode="lines+markers",
                                    line=dict(color="#fbbf24",width=2),
                                    marker=dict(size=5), name="추세")
                    dark_fig(fig, height=280)
                    st.plotly_chart(fig, width="stretch")
            except Exception as e:
                st.warning(f"로딩 실패: {e}")

        with c2:
            section("🏆 상권 효율 TOP10")
            try:
                df = q_top10_efficiency()
                if not df.empty:
                    fig = px.bar(df.sort_values("avg_per_capita"),
                                 x="avg_per_capita", y="sigungu_name",
                                 orientation="h",
                                 color="avg_per_capita",
                                 color_continuous_scale="Plasma")
                    fig.update_traces(texttemplate="%{x:,.0f}원",
                                      textposition="outside")
                    dark_fig(fig, height=350)
                    fig.update_coloraxes(showscale=False)
                    st.plotly_chart(fig, width="stretch")
            except Exception as e:
                st.warning(f"로딩 실패: {e}")

        c3, c4 = st.columns(2)
        with c3:
            section("🔥 최근 뜨는 상권 TOP5")
            try:
                df = q_top5_recent_hot()
                if not df.empty:
                    fig = px.bar(df, x="avg_recent_qoq", y="sigungu_name",
                                 orientation="h",
                                 color="avg_recent_qoq",
                                 color_continuous_scale="Hot",
                                 text="avg_recent_qoq")
                    fig.update_traces(texttemplate="%{text:+.1f}%",
                                      textposition="outside")
                    dark_fig(fig, height=280)
                    fig.update_coloraxes(showscale=False)
                    st.plotly_chart(fig, width="stretch")
            except Exception as e:
                st.warning(f"로딩 실패: {e}")

        with c4:
            section("👥 최근 분기 성별 매출")
            try:
                df = q_gender_seoul()
                if not df.empty:
                    latest_yq = df["yq"].max()
                    df_d = df[df["yq"]==latest_yq]
                    fig = go.Figure(go.Pie(
                        labels=df_d["gender"],
                        values=df_d["sales_100m"],
                        hole=0.55,
                        marker_colors=["#38bdf8","#f472b6"]))
                    dark_fig(fig, height=280,
                             title="최근 분기 성별 매출 비율")
                    fig.update_traces(textinfo="percent+label")
                    st.plotly_chart(fig, width="stretch")
            except Exception as e:
                st.warning(f"로딩 실패: {e}")

    elif page == "📈 분기별 분석":   render_quarterly()
    elif page == "🏪 업종별 분석":   render_industry()
    elif page == "👥 성별 분석":     render_gender()
    elif page == "🕐 시간대 분석":   render_timeslot()
    elif page == "📅 주중/주말 분석": render_weekday()


if __name__ == "__main__":
    main()
