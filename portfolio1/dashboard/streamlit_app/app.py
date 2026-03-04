import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ─────────────────────────────
# 페이지 설정
# ─────────────────────────────
st.set_page_config(
    page_title="서울시 상권 분석",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────
# 스타일 (핑크톤 다크)
# ─────────────────────────────
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background-color: #2B2626;
    color: #F3EAEA;
}
[data-testid="stHeader"] { background-color: #2B2626; }
[data-testid="block-container"] { padding: 1.3rem 1.8rem; }

/* 라디오 버튼 */
div[data-testid="stRadio"] label {
    color: #F3EAEA !important;
    font-size: 0.9rem;
}

/* 타이틀 */
.page-title {
    font-size: 1.7rem;
    font-weight: 900;
    color: #FF7A7A;
    margin-bottom: 0.15rem;
}
.page-sub {
    font-size: 0.86rem;
    color: #C9B9B9;
    margin-bottom: 1.1rem;
}

/* 섹션 제목 */
.section-title {
    font-size: 0.8rem;
    font-weight: 700;
    color: #FF7A7A;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.55rem;
}

/* 패널 */
.panel {
    background: #342F2F;
    border: 1px solid #4A3F3F;
    border-radius: 12px;
    padding: 1rem 1.1rem;
}
.panel-sub {
    color: #C9B9B9;
    font-size: 0.78rem;
    margin-top: -0.15rem;
    margin-bottom: 0.75rem;
}

/* 상세 카드 */
.detail-card {
    background: #342F2F;
    border: 1px solid #4A3F3F;
    border-left: 4px solid #FF7A7A;
    border-radius: 12px;
    padding: 1.2rem 1.25rem;
}
.detail-card h2 {
    color: #FF7A7A;
    margin: 0 0 0.35rem 0;
    font-size: 1.25rem;
}
.detail-card .meta {
    color: #C9B9B9;
    font-size: 0.78rem;
    margin-bottom: 0.85rem;
}
.stat-row {
    display: flex;
    gap: 0.9rem;
    flex-wrap: wrap;
}
.stat-box {
    background: #3A3333;
    border: 1px solid #4A3F3F;
    border-radius: 10px;
    padding: 0.7rem 0.9rem;
    min-width: 140px;
    flex: 1;
}
.stat-box .label {
    font-size: 0.72rem;
    color: #C9B9B9;
    margin-bottom: 0.25rem;
}
.stat-box .value {
    font-size: 1.15rem;
    font-weight: 800;
    color: #FF7A7A;
}

/* 안내 */
.hint {
    font-size: 0.75rem;
    color: #BDAAAA;
    margin-top: 0.35rem;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────
# 샘플 데이터 (mock)
# ─────────────────────────────
data = {
    "강남구":    {"매출": 12000, "유동인구": 230, "1인당매출": 5200, "폐업률": 3.2, "lat": 37.5172, "lon": 127.0473},
    "서초구":    {"매출": 9800,  "유동인구": 190, "1인당매출": 5158, "폐업률": 3.8, "lat": 37.4837, "lon": 127.0324},
    "마포구":    {"매출": 7600,  "유동인구": 175, "1인당매출": 4343, "폐업률": 4.5, "lat": 37.5663, "lon": 126.9014},
    "송파구":    {"매출": 8900,  "유동인구": 210, "1인당매출": 4238, "폐업률": 3.6, "lat": 37.5145, "lon": 127.1059},
    "영등포구":  {"매출": 6800,  "유동인구": 185, "1인당매출": 3676, "폐업률": 6.8, "lat": 37.5264, "lon": 126.8963},
    "종로구":    {"매출": 5400,  "유동인구": 160, "1인당매출": 3375, "폐업률": 5.1, "lat": 37.5730, "lon": 126.9794},
    "중구":      {"매출": 5100,  "유동인구": 155, "1인당매출": 3290, "폐업률": 5.5, "lat": 37.5640, "lon": 126.9975},
    "용산구":    {"매출": 5800,  "유동인구": 140, "1인당매출": 4143, "폐업률": 4.2, "lat": 37.5326, "lon": 126.9906},
    "성동구":    {"매출": 4900,  "유동인구": 130, "1인당매출": 3769, "폐업률": 5.0, "lat": 37.5633, "lon": 127.0369},
    "광진구":    {"매출": 4300,  "유동인구": 120, "1인당매출": 3583, "폐업률": 5.3, "lat": 37.5385, "lon": 127.0823},
    "노원구":    {"매출": 3800,  "유동인구": 200, "1인당매출": 1900, "폐업률": 6.0, "lat": 37.6541, "lon": 127.0568},
    "은평구":    {"매출": 3500,  "유동인구": 170, "1인당매출": 2059, "폐업률": 6.5, "lat": 37.6176, "lon": 126.9227},
    "관악구":    {"매출": 3200,  "유동인구": 190, "1인당매출": 1684, "폐업률": 7.2, "lat": 37.4784, "lon": 126.9516},
}

df = pd.DataFrame(data).T.reset_index()
df.columns = ["구이름", "매출", "유동인구", "1인당매출", "폐업률", "lat", "lon"]
df = df.astype({"매출": float, "유동인구": float, "1인당매출": float, "폐업률": float, "lat": float, "lon": float})

# ─────────────────────────────
# 세션 상태
# ─────────────────────────────
if "selected_gu" not in st.session_state:
    st.session_state.selected_gu = None

# 상단(요약 지도)에서 클릭 시 expander 펼침
if "show_top_detail" not in st.session_state:
    st.session_state.show_top_detail = False

if "top_selected_gu" not in st.session_state:
    st.session_state.top_selected_gu = None

# ─────────────────────────────
# Helper: 색상 스케일
# ─────────────────────────────
def make_color_scale(series: pd.Series):
    vmin, vmax = float(series.min()), float(series.max())
    def get_color(value):
        ratio = (value - vmin) / (vmax - vmin + 1e-9)
        r = int(80 + ratio * 175)
        g = int(45 + ratio * 70)
        b = int(55 + ratio * 55)
        return f"#{r:02X}{g:02X}{b:02X}"
    return get_color, vmin, vmax

# 뜨는 상권 점수(mock)
rng = np.random.default_rng(7)
df["뜨는점수"] = (df["매출"].rank(pct=True) * 60
                 + df["유동인구"].rank(pct=True) * 30
                 - df["폐업률"].rank(pct=True) * 40
                 + rng.normal(0, 3, len(df))).round(1)

# ─────────────────────────────
# 타이틀
# ─────────────────────────────
st.markdown('<div class="page-title">🏙️ 서울 상권 분석 대시보드</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">랜딩 · TOP 요약 지도(클릭 시 펼침 상세) · 메인 지도(클릭 시 오른쪽 상세)</div>', unsafe_allow_html=True)

# ─────────────────────────────
# [1] 랜딩 상단: 요약 지도 2개
# ─────────────────────────────
st.markdown('<div class="section-title">Landing · 요약 지도</div>', unsafe_allow_html=True)
top_row = st.columns([1, 1, 0.9], gap="large")

# ── TOP10 지도 ─────────────────
with top_row[0]:
    st.markdown('<div class="panel"><div class="section-title">최근 분기 매출 TOP10</div>'
                '<div class="panel-sub">클릭하면 아래에 상세가 펼쳐지고, 오른쪽 상세도 동기화</div></div>', unsafe_allow_html=True)

    top10 = df.sort_values("매출", ascending=False).head(10).copy()
    get_color, vmin, vmax = make_color_scale(top10["매출"])
    m1 = folium.Map(location=[37.5665, 126.9780], zoom_start=11, tiles="CartoDB Voyager", prefer_canvas=True)

    for _, row in top10.iterrows():
        color = get_color(row["매출"])
        tooltip_html = f"""
        <div style="background:#342F2F;color:#F3EAEA;padding:10px 12px;border-radius:10px;
                    border-left:4px solid #FF7A7A;font-family:sans-serif;font-size:12px;min-width:160px;">
            <b style="color:#FF7A7A;font-size:13px;">📍 {row['구이름']}</b><br>
            <hr style="border-color:#4A3F3F;margin:6px 0;">
            💰 매출: <b>{row['매출']/100:.1f}조</b><br>
            👣 유동인구: <b>{int(row['유동인구'])}만</b><br>
            💵 1인당 매출: <b>{int(row['1인당매출']):,}원</b>
        </div>
        """
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9 + (row["매출"] - vmin) / (vmax - vmin + 1e-9) * 7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.78,
            weight=2,
            tooltip=folium.Tooltip(tooltip_html, sticky=False),
            popup=folium.Popup(row["구이름"], max_width=120),
        ).add_to(m1)

    r1 = st_folium(m1, height=240, width=None, returned_objects=["last_object_clicked_popup"], key="mini_top10")
    if r1 and r1.get("last_object_clicked_popup"):
        clicked = r1["last_object_clicked_popup"]
        if clicked in data:
            # ✅ 상단 상세 + 메인 상세 동기화
            st.session_state.top_selected_gu = clicked
            st.session_state.show_top_detail = True
            st.session_state.selected_gu = clicked

# ── 뜨는 상권 TOP5 지도 ─────────
with top_row[1]:
    st.markdown('<div class="panel"><div class="section-title">뜨는 상권 TOP5</div>'
                '<div class="panel-sub">목업 점수(나중에 실제 지표로 교체)</div></div>', unsafe_allow_html=True)

    top5 = df.sort_values("뜨는점수", ascending=False).head(5).copy()
    get_color2, vmin2, vmax2 = make_color_scale(top5["뜨는점수"])
    m2 = folium.Map(location=[37.5665, 126.9780], zoom_start=11, tiles="CartoDB Voyager", prefer_canvas=True)

    for _, row in top5.iterrows():
        color = get_color2(row["뜨는점수"])
        tooltip_html = f"""
        <div style="background:#342F2F;color:#F3EAEA;padding:10px 12px;border-radius:10px;
                    border-left:4px solid #FF7A7A;font-family:sans-serif;font-size:12px;min-width:170px;">
            <b style="color:#FF7A7A;font-size:13px;">🔥 {row['구이름']}</b><br>
            <hr style="border-color:#4A3F3F;margin:6px 0;">
            ⭐ 뜨는점수: <b>{row['뜨는점수']}</b><br>
            💰 매출: <b>{row['매출']/100:.1f}조</b><br>
            👣 유동인구: <b>{int(row['유동인구'])}만</b>
        </div>
        """
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=10 + (row["뜨는점수"] - vmin2) / (vmax2 - vmin2 + 1e-9) * 10,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.80,
            weight=2,
            tooltip=folium.Tooltip(tooltip_html, sticky=False),
            popup=folium.Popup(row["구이름"], max_width=120),
        ).add_to(m2)

    r2 = st_folium(m2, height=240, width=None, returned_objects=["last_object_clicked_popup"], key="mini_hot5")
    if r2 and r2.get("last_object_clicked_popup"):
        clicked = r2["last_object_clicked_popup"]
        if clicked in data:
            # ✅ 상단 상세 + 메인 상세 동기화
            st.session_state.top_selected_gu = clicked
            st.session_state.show_top_detail = True
            st.session_state.selected_gu = clicked

# ── 요약 패널 ───────────────────
with top_row[2]:
    st.markdown('<div class="panel"><div class="section-title">요약</div>'
                '<div class="panel-sub">상단 지도 클릭 → 아래 펼침 상세 + 오른쪽 상세 동기화</div></div>', unsafe_allow_html=True)
    st.write("")
    if st.session_state.selected_gu:
        st.success(f"현재 선택: {st.session_state.selected_gu}")
    else:
        st.info("아직 선택 없음")
    st.write("")
    st.write("• 상단 지도: 빠른 비교")
    st.write("• 메인 지도: 전체 선택")
    st.write("• 현재 데이터: mock(13개 구)")

# ─────────────────────────────
# ✅ 상단 지도 클릭 시 펼쳐지는 상세 (닫기 가능)
# ─────────────────────────────
top_gu = st.session_state.get("top_selected_gu")
if top_gu:
    with st.expander(f"📌 (상단 지도 선택) {top_gu} 상세 분석", expanded=st.session_state.show_top_detail):
        colA, colB = st.columns([1, 6])
        with colA:
            if st.button("닫기", key="close_top_detail"):
                st.session_state.show_top_detail = False
                st.rerun()
        with colB:
            st.caption("상단 TOP 지도에서 선택한 구의 상세입니다. (메인 상세도 같은 구로 동기화됨)")

        d = data[top_gu]
        st.markdown(f"""
        <div class="detail-card">
            <h2>📍 {top_gu} 상세 분석</h2>
            <div class="meta">2023년 기준 · (mock) 분기 평균 데이터</div>
            <div class="stat-row">
                <div class="stat-box">
                    <div class="label">💰 매출 규모</div>
                    <div class="value">{d['매출']/100:.1f}조</div>
                </div>
                <div class="stat-box">
                    <div class="label">👣 유동인구</div>
                    <div class="value">{int(d['유동인구'])}만</div>
                </div>
                <div class="stat-box">
                    <div class="label">💵 1인당 매출</div>
                    <div class="value">{int(d['1인당매출']):,}원</div>
                </div>
                <div class="stat-box">
                    <div class="label" style="color:#FF7A7A;">🚪 폐업률</div>
                    <div class="value" style="color:{'#FF4444' if d['폐업률'] > 5 else '#FF7A7A'};">{d['폐업률']}%</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        quarters = ["Q1", "Q2", "Q3", "Q4"]
        base = d["매출"]
        sales = [round(base * 0.92), round(base * 0.96), round(base * 1.01), round(base * 1.05)]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=quarters, y=sales,
            mode="lines+markers",
            line=dict(color="#FF7A7A", width=3),
            marker=dict(color="#FF7A7A", size=8),
            fill="tozeroy",
            fillcolor="rgba(255,122,122,0.12)",
            name="매출"
        ))
        fig.update_layout(
            title=dict(text="📈 분기별 매출 트렌드 (mock)", font=dict(color="#FF7A7A", size=13)),
            paper_bgcolor="#342F2F",
            plot_bgcolor="#342F2F",
            font=dict(color="#F3EAEA", size=11),
            xaxis=dict(showgrid=False, color="#C9B9B9"),
            yaxis=dict(showgrid=True, gridcolor="#4A3F3F", color="#C9B9B9"),
            margin=dict(l=10, r=10, t=40, b=10),
            height=220,
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# ─────────────────────────────
# [2] 메인 섹션: 왼쪽(메인 지도) | 오른쪽(상세)
# ─────────────────────────────
left_col, right_col = st.columns([1.1, 0.9], gap="large")

# ══════════════════════════════
# 왼쪽: 메인 지도
# ══════════════════════════════
with left_col:
    st.markdown('<div class="section-title">📍 서울 전체 구 선택 (메인)</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-sub">Hover: 요약 · Click: 오른쪽 상세 고정</div>', unsafe_allow_html=True)

    color_mode = st.radio(
        label="color_select",
        options=["매출 규모", "1인당 매출", "유동인구"],
        horizontal=True,
        label_visibility="collapsed",
        key="color_mode_main",
    )

    value_col = "매출" if color_mode == "매출 규모" else ("1인당매출" if color_mode == "1인당 매출" else "유동인구")
    get_color_main, vmin_main, vmax_main = make_color_scale(df[value_col])

    m = folium.Map(
        location=[37.5665, 126.9780],
        zoom_start=11,
        tiles="CartoDB Voyager",
        prefer_canvas=True,
    )

    for _, row in df.iterrows():
        color = get_color_main(row[value_col])
        tooltip_html = f"""
        <div style="background:#342F2F;color:#F3EAEA;padding:10px 12px;border-radius:10px;
                    border-left:4px solid #FF7A7A;font-family:sans-serif;font-size:12px;min-width:180px;">
            <b style="color:#FF7A7A;font-size:13px;">📍 {row['구이름']}</b><br>
            <hr style="border-color:#4A3F3F;margin:6px 0;">
            💰 매출: <b>{row['매출']/100:.1f}조</b><br>
            👣 유동인구: <b>{int(row['유동인구'])}만</b><br>
            💵 1인당 매출: <b>{int(row['1인당매출']):,}원</b>
        </div>
        """
        radius = 12 + (row[value_col] - vmin_main) / (vmax_main - vmin_main + 1e-9) * 16

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.78,
            weight=2,
            tooltip=folium.Tooltip(tooltip_html, sticky=False),
            popup=folium.Popup(row["구이름"], max_width=120),
        ).add_to(m)

        folium.Marker(
            location=[row["lat"], row["lon"]],
            icon=folium.DivIcon(
                html=f'<div style="color:#F3EAEA;font-size:10px;font-weight:800;'
                     f'text-shadow:1px 1px 2px #000;white-space:nowrap;">'
                     f'{row["구이름"]}</div>',
                icon_size=(90, 18),
                icon_anchor=(45, -6),
            ),
        ).add_to(m)

    map_result = st_folium(
        m,
        width=None,
        height=480,
        returned_objects=["last_object_clicked_popup"],
        key="seoul_map_main"
    )

    if map_result and map_result.get("last_object_clicked_popup"):
        clicked = map_result["last_object_clicked_popup"]
        if clicked in data:
            st.session_state.selected_gu = clicked

    st.markdown('<div class="hint">💡 Hover: 상세 툴팁 · Click: 오른쪽 상세 갱신</div>', unsafe_allow_html=True)

# ══════════════════════════════
# 오른쪽: 상세 분석 패널
# ══════════════════════════════
with right_col:
    st.markdown('<div class="section-title">📊 상세 분석 (메인)</div>', unsafe_allow_html=True)

    selected = st.session_state.selected_gu
    if selected is None:
        st.markdown("""
        <div class="detail-card" style="border-left-color:#4A3F3F;">
            <h2>🗺️ 구를 선택해줘</h2>
            <div class="meta">메인 지도 또는 상단 요약 지도에서 구를 클릭하면 표시됩니다.</div>
            <div style="color:#C9B9B9;font-size:0.9rem;">
                • 상단 지도 클릭: 아래 펼침 상세 + 오른쪽 상세 동기화<br>
                • 메인 지도 클릭: 오른쪽 상세 고정
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        d = data[selected]

        st.markdown(f"""
        <div class="detail-card">
            <h2>📍 {selected} 상세 분석</h2>
            <div class="meta">2023년 기준 · (mock) 분기 평균 데이터</div>
            <div class="stat-row">
                <div class="stat-box">
                    <div class="label">💰 매출 규모</div>
                    <div class="value">{d['매출']/100:.1f}조</div>
                </div>
                <div class="stat-box">
                    <div class="label">👣 유동인구</div>
                    <div class="value">{int(d['유동인구'])}만</div>
                </div>
                <div class="stat-box">
                    <div class="label">💵 1인당 매출</div>
                    <div class="value">{int(d['1인당매출']):,}원</div>
                </div>
                <div class="stat-box">
                    <div class="label" style="color:#FF7A7A;">🚪 폐업률</div>
                    <div class="value" style="color:{'#FF4444' if d['폐업률'] > 5 else '#FF7A7A'};">{d['폐업률']}%</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        quarters = ["Q1", "Q2", "Q3", "Q4"]
        base = d["매출"]
        sales = [round(base * 0.92), round(base * 0.96), round(base * 1.01), round(base * 1.05)]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=quarters, y=sales,
            mode="lines+markers",
            line=dict(color="#FF7A7A", width=3),
            marker=dict(color="#FF7A7A", size=9),
            fill="tozeroy",
            fillcolor="rgba(255,122,122,0.12)",
            name="매출"
        ))
        fig.update_layout(
            title=dict(text="📈 분기별 매출 트렌드 (mock)", font=dict(color="#FF7A7A", size=13)),
            paper_bgcolor="#342F2F",
            plot_bgcolor="#342F2F",
            font=dict(color="#F3EAEA", size=11),
            xaxis=dict(showgrid=False, color="#C9B9B9"),
            yaxis=dict(showgrid=True, gridcolor="#4A3F3F", color="#C9B9B9"),
            margin=dict(l=10, r=10, t=40, b=10),
            height=220,
        )
        st.plotly_chart(fig, use_container_width=True)

        sorted_df = df.sort_values("매출", ascending=True)
        colors = ["#FF7A7A" if g == selected else "#6A6060" for g in sorted_df["구이름"]]

        fig2 = go.Figure(go.Bar(
            x=sorted_df["매출"],
            y=sorted_df["구이름"],
            orientation="h",
            marker_color=colors,
        ))
        fig2.update_layout(
            title=dict(text="📊 타 구 매출 비교 (mock)", font=dict(color="#FF7A7A", size=13)),
            paper_bgcolor="#342F2F",
            plot_bgcolor="#342F2F",
            font=dict(color="#F3EAEA", size=10),
            xaxis=dict(showgrid=True, gridcolor="#4A3F3F", color="#C9B9B9"),
            yaxis=dict(showgrid=False, color="#F3EAEA"),
            margin=dict(l=10, r=10, t=40, b=10),
            height=300,
        )
        st.plotly_chart(fig2, use_container_width=True)