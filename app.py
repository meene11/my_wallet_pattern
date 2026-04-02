"""
개인 소비 분석 + 무의식 지출 탐지 AI
Streamlit 웹 앱 메인
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import plotly.graph_objects as go
import streamlit.components.v1 as components
import sys
import os

sys.path.append(os.path.dirname(__file__))
from src.data_loader import (
    load_file, auto_map_columns, preprocess, get_summary,
    IMPULSE_CAT_MULTIPLIER, IMPULSE_NIGHT_HOUR, IMPULSE_FREQ_COUNT, IMPULSE_DAILY_MULTIPLIER,
    DIAG_HIGH_THRESHOLD, DIAG_MED_THRESHOLD,
)
from src.gemini_analyzer import analyze_impulse

# ── 페이지 설정 ─────────────────────────────────────────────
st.set_page_config(
    page_title="내 소비 분석 AI",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 한글 폰트 (Windows: Malgun Gothic / Linux: NanumGothic) ──
import matplotlib.font_manager as _fm
_available = [f.name for f in _fm.fontManager.ttflist]
if "Malgun Gothic" in _available:
    plt.rcParams["font.family"] = "Malgun Gothic"
elif "NanumGothic" in _available:
    plt.rcParams["font.family"] = "NanumGothic"
else:
    plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False

# ── 스타일 ───────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 16px 20px;
        border-left: 4px solid #4ECDC4;
        margin-bottom: 8px;
    }
    .impulse-card {
        background: #fff5f5;
        border-radius: 12px;
        padding: 16px 20px;
        border-left: 4px solid #FF6B6B;
        margin-bottom: 8px;
    }
    .section-title {
        font-size: 1.2rem;
        font-weight: 700;
        margin: 20px 0 10px 0;
        color: #333;
    }
.ai-result-cause {
        background: #fff5f5;
        border-radius: 12px;
        padding: 18px 22px;
        border-left: 5px solid #FF6B6B;
        margin-bottom: 10px;
        font-size: 1rem;
        line-height: 1.6;
    }
    .ai-result-coach {
        background: #f0f7ff;
        border-radius: 12px;
        padding: 18px 22px;
        border-left: 5px solid #4A90E2;
        margin-bottom: 10px;
        font-size: 1rem;
        line-height: 1.6;
    }
    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #FF6B6B, #ff4757) !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 14px 0 !important;
        letter-spacing: 0.03em !important;
        box-shadow: 0 4px 14px rgba(255, 107, 107, 0.45) !important;
        transition: all 0.2s !important;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #ff4757, #FF6B6B) !important;
        box-shadow: 0 6px 20px rgba(255, 107, 107, 0.6) !important;
        transform: translateY(-1px) !important;
    }
    [data-testid="stFileUploaderDropzone"] button {
        background-color: #FF6B6B !important;
        color: white !important;
        border: 2px solid #FF6B6B !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: background-color 0.2s, color 0.2s !important;
    }
    [data-testid="stFileUploaderDropzone"] button:hover {
        background-color: white !important;
        color: #FF6B6B !important;
        border: 2px solid #FF6B6B !important;
    }
    .threshold-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #f0faf4;
        border-left: 3px solid #2ecc71;
        border-radius: 6px;
        padding: 6px 10px;
        margin-bottom: 6px;
        font-size: 0.82rem;
    }
    .threshold-label {
        color: #2c7a4b;
        font-weight: 600;
    }
    .threshold-val {
        background: #2ecc71;
        color: white;
        border-radius: 10px;
        padding: 2px 9px;
        font-size: 0.78rem;
        font-weight: 700;
        white-space: nowrap;
    }
    /* 사이드바 충동소비 탐지 기준 expander 헤더 */
    section[data-testid="stSidebar"] [data-testid="stExpander"] summary {
        background: #fff5f5 !important;
        border: 1.5px solid #FF6B6B !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        color: #FF6B6B !important;
    }
    section[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
        background: #ffe8e8 !important;
    }
    /* 탭 가독성 강화 */
    button[data-baseweb="tab"] {
        font-size: 0.92rem !important;
        font-weight: 600 !important;
        padding: 10px 18px !important;
        color: #555 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #FF6B6B !important;
        border-bottom: 3px solid #FF6B6B !important;
        font-weight: 700 !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #FF6B6B !important;
        background: #fff5f5 !important;
    }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# 사이드바
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("💸 내 소비 분석 AI")
    st.caption("카드/지출 내역을 올리면\n소비 심리까지 분석해드려요")
    st.divider()

    st.subheader("📂 파일 업로드")

    card_preset = st.selectbox(
        "카드사 / 형식 선택",
        ["자동 감지", "카카오페이", "신한카드", "국민카드", "하나카드", "직접 입력"],
        help="선택하면 컬럼이 자동 세팅됩니다",
    )
    st.session_state["card_preset"] = card_preset

    uploaded = st.file_uploader(
        "CSV 또는 Excel 파일",
        type=["csv", "xlsx", "xls"],
        help="카카오페이, 신한카드, 직접 작성 등 어떤 형식이든 OK",
    )

    st.divider()
    st.subheader("🗂 샘플 데이터로 체험")
    use_sample = st.button("샘플 데이터 불러오기", use_container_width=True)

    st.divider()
    with st.expander("⚙️ 충동소비 탐지 기준", expanded=False):
        st.markdown(
            '<p style="color:#2c7a4b;font-size:0.8rem;margin-bottom:10px;">'
            '슬라이더 조정 후 <b>기준 적용</b> 버튼을 눌러야 반영됩니다.</p>',
            unsafe_allow_html=True,
        )

        # 현재 적용된 값 배지 표시
        _cm  = float(st.session_state.get("applied_cat_mult",   IMPULSE_CAT_MULTIPLIER))
        _nh  = int(st.session_state.get("applied_night_hour",   IMPULSE_NIGHT_HOUR))
        _fc  = int(st.session_state.get("applied_freq_count",   IMPULSE_FREQ_COUNT))
        _dm  = float(st.session_state.get("applied_daily_mult", IMPULSE_DAILY_MULTIPLIER))
        st.markdown(f"""
<div class="threshold-row"><span class="threshold-label">카테고리 평균 초과</span><span class="threshold-val">{_cm:.1f}배</span></div>
<div class="threshold-row"><span class="threshold-label">야간 기준 시간</span><span class="threshold-val">{_nh}시 이후</span></div>
<div class="threshold-row"><span class="threshold-label">동일 카테고리 건수</span><span class="threshold-val">일 {_fc}건+</span></div>
<div class="threshold-row"><span class="threshold-label">하루 지출 초과</span><span class="threshold-val">평균 {_dm:.1f}배</span></div>
""", unsafe_allow_html=True)

        st.markdown("---")
        thr_cat_mult = st.slider(
            "카테고리 평균 배수 초과",
            min_value=1.5, max_value=5.0,
            value=_cm, step=0.5,
            help="평소 그 카테고리 평균의 N배 넘으면 충동소비로 분류",
        )
        thr_night_hour = st.slider(
            "야간 기준 시간",
            min_value=18, max_value=23,
            value=_nh, step=1,
            help="이 시간 이후 결제를 야간 충동소비로 분류",
            format="%d시",
        )
        thr_freq_count = st.slider(
            "동일 카테고리 일일 건수",
            min_value=2, max_value=10,
            value=_fc, step=1,
            help="하루에 같은 카테고리에서 N건 이상이면 충동소비로 분류",
        )
        thr_daily_mult = st.slider(
            "하루 지출 평균 배수 초과",
            min_value=1.2, max_value=3.0,
            value=_dm, step=0.1,
            help="그날 총 지출이 내 일평균의 N배 넘으면 충동소비로 분류",
            format="%.1fx",
        )

        if st.button("✅ 기준 적용하기", use_container_width=True):
            st.session_state["applied_cat_mult"] = thr_cat_mult
            st.session_state["applied_night_hour"] = thr_night_hour
            st.session_state["applied_freq_count"] = thr_freq_count
            st.session_state["applied_daily_mult"] = thr_daily_mult
            st.success("탐지 기준이 반영됐습니다!")

    # 실제 분석에 사용할 값 (버튼 누른 값 기준)
    thr_cat_mult   = float(st.session_state.get("applied_cat_mult",   IMPULSE_CAT_MULTIPLIER))
    thr_night_hour = int(st.session_state.get("applied_night_hour",   IMPULSE_NIGHT_HOUR))
    thr_freq_count = int(st.session_state.get("applied_freq_count",   IMPULSE_FREQ_COUNT))
    thr_daily_mult = float(st.session_state.get("applied_daily_mult", IMPULSE_DAILY_MULTIPLIER))

    st.divider()
    st.caption("""
**지원 형식**
- CSV (UTF-8, EUC-KR 모두 OK)
- Excel (.xlsx, .xls)

**필수 컬럼**
- 날짜, 금액, 카테고리

**있으면 좋은 컬럼**
- 시간, 메모, 소분류
    """)


# ══════════════════════════════════════════════════════════════
# 메인
# ══════════════════════════════════════════════════════════════
st.title("💸 개인 소비 분석 + 무의식 지출 탐지 AI")
st.caption("단순 가계부가 아닙니다. 소비 심리와 충동 패턴을 분석해드려요.")


# ── 데이터 로드 ───────────────────────────────────────────────
col_map = {}

if uploaded:
    try:
        df_raw = load_file(uploaded)
        st.session_state["df_raw"] = df_raw
        st.session_state["data_source"] = "upload"
        st.session_state["gemini_result"] = None
        st.session_state["gemini_error"] = None
        st.success(f"✅ 파일 로드 완료! ({len(df_raw)}행 × {len(df_raw.columns)}열)")
    except Exception as e:
        st.error(f"파일 로드 실패: {e}")
        st.info("Excel 파일은 `pip install openpyxl` 설치가 필요합니다.")

elif use_sample:
    sample_path = os.path.join(os.path.dirname(__file__), "data/raw/sample_spending.csv")
    st.session_state["df_raw"] = pd.read_csv(sample_path)
    st.session_state["data_source"] = "sample"
    st.session_state["gemini_result"] = None
    st.session_state["gemini_error"] = None
    st.info("샘플 데이터를 불러왔습니다.")

df_raw = st.session_state.get("df_raw", None)

# ── 컬럼 매핑 UI ─────────────────────────────────────────────
if df_raw is not None:

    # 파일 미리보기
    with st.expander("📋 업로드된 파일 미리보기", expanded=True):
        st.dataframe(df_raw.head(5), use_container_width=True)
        st.caption(f"감지된 컬럼: {list(df_raw.columns)}")

    # 카드사 프리셋 정의 (컬럼명 → 표준키 매핑)
    CARD_PRESETS = {
        "카카오페이": {"date": "거래일시", "amount": "금액", "category": "분류", "memo": "내용"},
        "신한카드":   {"date": "이용일자", "amount": "이용금액", "category": "가맹점업종", "memo": "가맹점명"},
        "국민카드":   {"date": "이용일", "amount": "이용금액", "category": "업종", "memo": "가맹점"},
        "하나카드":   {"date": "승인일자", "amount": "승인금액", "category": "업종명", "memo": "가맹점명"},
    }

    preset = st.session_state.get("card_preset", "자동 감지")
    col_map = auto_map_columns(df_raw)

    if preset in CARD_PRESETS:
        for std_key, col_name in CARD_PRESETS[preset].items():
            if col_name in df_raw.columns:
                col_map[std_key] = col_name


    # 자동 매핑 결과 표시
    missing = [k for k in ["date", "amount", "category"] if k not in col_map]
    label_map = {"date": "날짜", "amount": "금액", "category": "카테고리"}

    if not missing:
        st.success(f"✅ 컬럼 자동 매핑 완료 → 날짜: `{col_map['date']}` / 금액: `{col_map['amount']}` / 카테고리: `{col_map['category']}`")
    else:
        st.warning(f"⚠️ 아래 컬럼을 직접 지정해주세요 (자동 인식 실패: {[label_map[k] for k in missing]})")

    # 수동 매핑 (항상 표시 — 자동 매핑 결과 수정 가능)
    with st.expander("🔧 컬럼 매핑 설정" + ("  ← 여기서 직접 지정하세요!" if missing else ""), expanded=bool(missing)):
        cols_options = ["(없음)"] + list(df_raw.columns)
        full_label = {"date": "날짜 컬럼", "amount": "금액 컬럼", "category": "카테고리 컬럼",
                      "time": "시간 컬럼 (선택)", "memo": "메모 컬럼 (선택)"}
        for key in ["date", "amount", "category", "time", "memo"]:
            default = col_map.get(key, "(없음)")
            default_idx = cols_options.index(default) if default in cols_options else 0
            selected = st.selectbox(full_label[key], cols_options, index=default_idx, key=f"map_{key}")
            if selected != "(없음)":
                col_map[key] = selected
            elif key in col_map:
                del col_map[key]

    # 처리 버튼
    can_process = all(k in col_map for k in ["date", "amount", "category"])

    if can_process:
        try:
            df = preprocess(df_raw, col_map,
                            cat_multiplier=thr_cat_mult,
                            night_hour=thr_night_hour,
                            freq_count=thr_freq_count,
                            daily_multiplier=thr_daily_mult)
            summary = get_summary(df)
        except Exception as e:
            st.error(f"데이터 처리 오류: {e}")
            st.stop()

        # ══════════════════════════════════════════════════════
        # 탭 구성
        # ══════════════════════════════════════════════════════
        _impulse_n = summary["impulse_count"]
        _total_n   = len(df)
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 전체 요약",
            "📅 패턴 분석",
            f"🚨 충동 소비 탐지  {_impulse_n}건",
            f"🗃 내역 조회  {_total_n}건",
            "💰 소비 목표",
        ])

        # ┌─────────────────────────────────────────────────────
        # │ TAB 1 – 전체 요약
        # └─────────────────────────────────────────────────────
        with tab1:
            st.markdown('<div class="section-title">💰 이번 달 한눈에 보기</div>', unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("총 지출", f"{summary['total']:,}원")
            c2.metric("총 거래 건수", f"{summary['count']}건")
            c3.metric("일 평균 지출", f"{summary['avg_per_day']:,}원")
            c4.metric("건당 평균", f"{summary['avg_per_tx']:,}원")

            st.divider()

            cat_sum = df.groupby("category")["amount"].sum().sort_values(ascending=False)
            total_amt = cat_sum.sum()
            n_cats = len(cat_sum)

            # 표용 번호 (항상 숫자)
            labels_num = [str(i + 1) for i in range(n_cats)]
            # 파이차트용 번호 (26번째부터 · 으로 대체)
            labels_pie = [str(i + 1) if i < 25 else "·" for i in range(n_cats)]

            col_chart, col_table = st.columns([1, 1])

            # ── 파이 차트 ──
            with col_chart:
                PIE_OUTER_THRESHOLD = 8  # 이 수 초과 시 숫자를 원 밖으로
                many = n_cats > PIE_OUTER_THRESHOLD
                label_dist  = 1.18 if many else 0.84
                label_fs    = max(5, 8 - max(0, n_cats - PIE_OUTER_THRESHOLD) // 2)
                pct_dist    = 0.70 if many else 0.62
                pct_fs      = max(5, label_fs - 1)

                # 작은 슬라이스(3% 미만)는 % 숨김
                total_amt_pie = cat_sum.sum()
                def _autopct(pct):
                    return f"{pct:.0f}%" if pct >= 3 else ""

                fig, ax = plt.subplots(figsize=(2.8, 2.8))
                colors = plt.cm.Set3.colors[:n_cats]
                wedges, texts, autotexts = ax.pie(
                    cat_sum.values,
                    labels=labels_pie,
                    autopct=_autopct,
                    startangle=90,
                    pctdistance=pct_dist,
                    labeldistance=label_dist,
                    colors=colors,
                )
                for t in texts:
                    t.set_fontsize(label_fs)
                    t.set_fontweight("bold")
                for a in autotexts:
                    a.set_fontsize(pct_fs)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()

            # ── 범례 테이블 ──
            with col_table:
                legend_data = pd.DataFrame({
                    "No": labels_num,
                    "카테고리": cat_sum.index,
                    "금액": [f"{v:,.0f}원" for v in cat_sum.values],
                    "비율": [f"{v/total_amt*100:.1f}%" for v in cat_sum.values],
                })
                st.dataframe(
                    legend_data,
                    use_container_width=True,
                    hide_index=True,
                    height=min(38 * n_cats + 38, 350),
                )

            # ── 일별 추이 ──
            st.markdown("**일별 지출 추이**")
            daily = df.groupby("date")["amount"].sum().reset_index()
            daily["rolling_7"] = daily["amount"].rolling(7, min_periods=1).mean()
            fig, ax = plt.subplots(figsize=(6, 2.0))
            ax.bar(daily["date"], daily["amount"], alpha=0.5, color="#5B8CFF", label="일별 지출")
            ax.plot(daily["date"], daily["rolling_7"], color="red", linewidth=1.5, label="7일 평균")
            ax.set_ylabel("금액 (원)", fontsize=9)
            ax.legend(fontsize=8)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            plt.xticks(rotation=30, fontsize=7)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        # ┌─────────────────────────────────────────────────────
        # │ TAB 2 – 패턴 분석
        # └─────────────────────────────────────────────────────
        with tab2:
            col_l, col_r = st.columns(2)

            weekday_order = ["월", "화", "수", "목", "금", "토", "일"]

            # 요일별
            with col_l:
                st.markdown("**요일별 지출**")
                weekday_sum = df.groupby("weekday_name")["amount"].sum().reindex(weekday_order).fillna(0)
                colors = ["#FF6B6B" if w in ["토", "일"] else "#4ECDC4" for w in weekday_order]
                fig, ax = plt.subplots(figsize=(3.5, 2.2))
                ax.bar(weekday_order, weekday_sum.values, color=colors, edgecolor="white")
                ax.set_ylabel("금액 (원)", fontsize=9)
                ax.tick_params(labelsize=8)
                max_w = weekday_sum.values.max()
                for i, v in enumerate(weekday_sum.values):
                    if v > 0:
                        ax.text(i, v + max_w * 0.02, f"{v/1000:.0f}k", ha="center", fontsize=7)
                ax.set_ylim(0, max_w * 1.2)
                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
                st.markdown(
                    "<p style='font-size:0.72rem;color:#aaa;margin-top:-6px;'>"
                    "※ k = 1,000 &nbsp;|&nbsp; 예) 500k = 500,000원 (50만원)</p>",
                    unsafe_allow_html=True,
                )

            # 시간대별
            with col_r:
                st.markdown("**시간대별 지출**")
                if df["hour"].notna().sum() > 0:
                    hour_sum = df.groupby("hour")["amount"].sum()
                    colors_h = ["#FF4444" if h >= 21 else "#5B8CFF" for h in hour_sum.index]
                    fig, ax = plt.subplots(figsize=(3.5, 2.2))
                    ax.bar(hour_sum.index, hour_sum.values, color=colors_h, edgecolor="white")
                    ax.set_xlabel("시간", fontsize=9)
                    ax.set_ylabel("금액 (원)", fontsize=9)
                    ax.tick_params(labelsize=7)
                    ax.spines["top"].set_visible(False)
                    ax.spines["right"].set_visible(False)
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
                else:
                    st.info("파일에 시간 데이터가 없습니다.")

            # 카테고리 × 요일 히트맵
            st.markdown("**카테고리 × 요일 히트맵**")
            pivot = df.pivot_table(
                values="amount", index="category", columns="weekday_name",
                aggfunc="sum", fill_value=0
            ).reindex(columns=[w for w in weekday_order if w in df["weekday_name"].unique()])
            pivot.columns.name = None
            hmap_h = max(2.0, len(pivot) * 0.32)
            fig, ax = plt.subplots(figsize=(5.5, hmap_h))
            sns.heatmap(
                pivot, annot=True, fmt=",", cmap="YlOrRd",
                linewidths=0.4, ax=ax, annot_kws={"size": 7},
                cbar_kws={"label": "금액(원)", "shrink": 0.8}
            )
            ax.tick_params(labelsize=8)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        # ┌─────────────────────────────────────────────────────
        # │ TAB 3 – 충동 소비 탐지
        # └─────────────────────────────────────────────────────
        with tab3:
            impulse_df = df[df["is_impulse"]].copy()

            impulse_ratio = summary["impulse_total"] / summary["total"] * 100 if summary["total"] > 0 else 0
            night_ratio = summary["night_total"] / summary["total"] * 100 if summary["total"] > 0 else 0

            c1, c2, c3 = st.columns(3)
            c1.metric(
                "충동 소비 의심 금액",
                f"{summary['impulse_total']:,}원",
                delta=f"전체의 {impulse_ratio:.1f}%",
                delta_color="inverse",
            )
            c2.metric("충동 소비 의심 건수", f"{summary['impulse_count']}건")
            c3.metric(
                "21시 이후 지출",
                f"{summary['night_total']:,}원",
                delta=f"전체의 {night_ratio:.1f}%",
                delta_color="inverse",
            )

            # 탐지 기준 안내
            with st.expander("탐지 기준 보기"):
                st.markdown(f"""
| 기준 | 현재 적용값 |
|------|------------|
| 카테고리 평균 배수 초과 | 평균의 **{thr_cat_mult:.1f}배** 이상 |
| 야간 기준 시간 | **{thr_night_hour}시** 이후 결제 |
| 동일 카테고리 일일 건수 | 하루 **{thr_freq_count}건** 이상 |
| 하루 지출 평균 배수 초과 | 일평균의 **{thr_daily_mult:.1f}배** 초과 |
| 주말 야간 결제 | 토·일 **{thr_night_hour}시** 이후 결제 |
                """)

            st.divider()

            # 충동 소비 거래 목록 + 이유 표시
            st.markdown("**충동 소비 의심 거래 목록**")

            if len(impulse_df) > 0:
                # 탐지 기준 필터
                FLAG_MAP = {
                    f"카테고리 평균 {thr_cat_mult:.1f}배 초과": "flag_over_cat_avg",
                    f"{thr_night_hour}시 이후 결제":            "flag_night",
                    f"동일 카테고리 {thr_freq_count}건+":        "flag_freq_impulse",
                    "하루 지출 평균 초과":                        "flag_over_daily_avg",
                    "주말 야간 결제":                             "flag_weekend_night",
                }
                avail_flags = {k: v for k, v in FLAG_MAP.items()
                               if v in impulse_df.columns and impulse_df[v].any()}
                selected_flags = st.multiselect(
                    "탐지 기준 필터 (복수 선택 시 OR 조건)",
                    list(avail_flags.keys()),
                    key="impulse_filter",
                )
                if selected_flags:
                    mask = pd.Series(False, index=impulse_df.index)
                    for label in selected_flags:
                        mask = mask | impulse_df[avail_flags[label]]
                    view_df = impulse_df[mask]
                else:
                    view_df = impulse_df

                show_cols = ["date", "category", "amount", "impulse_reason"]
                show_cols = [c for c in show_cols if c in view_df.columns]
                display_df = (
                    view_df[show_cols]
                    .sort_values("amount", ascending=False)
                    .rename(columns={"impulse_reason": "탐지 이유", "date": "날짜",
                                     "category": "카테고리", "amount": "금액"})
                    .reset_index(drop=True)
                )
                display_df["금액"] = display_df["금액"].apply(lambda x: f"{int(x):,}")
                display_df.index = range(1, len(display_df) + 1)
                st.dataframe(display_df, use_container_width=True, height=480)

                # 탐지 이유별 건수 통계
                st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
                st.markdown("**탐지 이유별 건수**")
                reason_counts = {
                    f"카테고리 평균 {thr_cat_mult:.1f}배 초과": int(df["flag_over_cat_avg"].sum()),
                    f"{thr_night_hour}시 이후 결제":            int(df["flag_night"].sum()),
                    f"동일 카테고리 {thr_freq_count}건+":        int(df["flag_freq_impulse"].sum()),
                    f"하루 평균 {thr_daily_mult:.1f}배 초과":    int(df["flag_over_daily_avg"].sum()),
                    "주말 야간":                                 int(df["flag_weekend_night"].sum()),
                }
                rc_df = pd.DataFrame(reason_counts.items(), columns=["이유", "건수"])
                rc_df = rc_df[rc_df["건수"] > 0].sort_values("건수", ascending=False)

                fig, ax = plt.subplots(figsize=(5, max(1.2, len(rc_df) * 0.38)))
                ax.barh(rc_df["이유"][::-1], rc_df["건수"][::-1], color="#FF6B6B", edgecolor="white", height=0.5)
                ax.set_xlabel("건수", fontsize=9)
                ax.tick_params(labelsize=9)
                for i, v in enumerate(rc_df["건수"][::-1]):
                    ax.text(v + 0.1, i, str(v), va="center", fontsize=9)
                ax.set_xlim(0, rc_df["건수"].max() * 1.3)
                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()

            else:
                st.success("충동 소비 의심 거래가 없습니다!")

            # 충동 소비 카테고리 분포
            SCROLL_CAT_THRESHOLD = 8  # 이 수 초과하면 가로 스크롤 활성화
            if len(impulse_df) > 0:
                st.markdown("**충동 소비 카테고리별 금액**")
                imp_cat = impulse_df.groupby("category")["amount"].sum().sort_values(ascending=False)
                n_imp = len(imp_cat)

                pfig = go.Figure(go.Bar(
                    x=imp_cat.index.tolist(),
                    y=imp_cat.values.tolist(),
                    marker_color="#FF6B6B",
                    text=[f"{v:,.0f}원" for v in imp_cat.values],
                    textposition="outside",
                ))
                pfig.update_layout(
                    height=260,
                    margin=dict(l=40, r=20, t=10, b=70),
                    yaxis_title="금액 (원)",
                    showlegend=False,
                    font=dict(size=11),
                    xaxis=dict(tickangle=-35),
                )

                if n_imp > SCROLL_CAT_THRESHOLD:
                    pfig.update_layout(width=max(500, n_imp * 70))
                    html_str = pfig.to_html(
                        include_plotlyjs="cdn", full_html=False,
                        config={"displayModeBar": False},
                    )
                    components.html(
                        f'<div style="overflow-x:auto;width:100%;">{html_str}</div>',
                        height=300,
                    )
                else:
                    st.plotly_chart(pfig, use_container_width=True)

            # 소비 진단 — 실제 데이터 기반
            st.divider()
            st.markdown("**소비 진단**")

            # 어떤 기준이 가장 많이 트리거됐는지 파악
            reason_counts = {
                f"카테고리 평균 {thr_cat_mult:.1f}배 초과": int(df["flag_over_cat_avg"].sum()),
                f"{thr_night_hour}시 이후 결제":            int(df["flag_night"].sum()),
                f"동일 카테고리 {thr_freq_count}건+":        int(df["flag_freq_impulse"].sum()),
                f"하루 평균 {thr_daily_mult:.1f}배 초과":    int(df["flag_over_daily_avg"].sum()),
                "주말 야간":                                 int(df["flag_weekend_night"].sum()),
            }
            top_reason = max(reason_counts, key=reason_counts.get)
            top_cat = df.groupby("category")["amount"].sum().idxmax()
            top_amount = df.groupby("category")["amount"].sum().max()

            if impulse_ratio > DIAG_HIGH_THRESHOLD:
                st.error(f"충동 소비 비율 **{impulse_ratio:.1f}%** (기준 {DIAG_HIGH_THRESHOLD}% 초과) — 주요 원인: **{top_reason}**")
            elif impulse_ratio > DIAG_MED_THRESHOLD:
                st.warning(f"충동 소비 비율 **{impulse_ratio:.1f}%** (기준 {DIAG_MED_THRESHOLD}% 초과) — 주요 원인: **{top_reason}**")
            else:
                st.success(f"충동 소비 비율 **{impulse_ratio:.1f}%** (기준 {DIAG_MED_THRESHOLD}% 이하) — 소비 패턴이 안정적이에요!")

            night_key = f"{thr_night_hour}시 이후 결제"
            if reason_counts.get(night_key, 0) > 0 and night_ratio > 15:
                st.warning(f"{thr_night_hour}시 이후 지출 비율 **{night_ratio:.1f}%** — 저녁 이후 충동 구매 패턴이 있어요.")

            st.info(f"가장 많이 쓴 카테고리: **{top_cat}** ({top_amount:,}원) — 이 항목 예산을 먼저 관리해보세요.")

            # ── AI 소비 코칭 ──────────────────────────────────────
            st.divider()

            # 현재 데이터 식별용 해시 (총지출 + 건수 + 충동건수)
            data_hash = f"{summary['total']}_{summary['count']}_{summary['impulse_count']}"

            # 데이터가 바뀌면 이전 결과 자동 무효화
            if st.session_state.get("gemini_data_hash") != data_hash:
                st.session_state["gemini_result"] = None
                st.session_state["gemini_error"] = None
                st.session_state["gemini_data_hash"] = data_hash

            @st.fragment
            def ai_coaching(summary, df):
                st.markdown('<div class="section-title"><span style="font-size:1.8rem; filter: sepia(1) saturate(5) hue-rotate(5deg) brightness(1.3);">🤖</span> AI 소비 코치</div>', unsafe_allow_html=True)

                if st.button("✨ AI 분석 받기", key="gemini_btn",
                             use_container_width=True, type="primary"):
                    with st.spinner("AI가 소비 패턴을 분석 중이에요..."):
                        try:
                            result = analyze_impulse(summary, df)
                            st.session_state["gemini_result"] = result
                            st.session_state["gemini_error"] = None
                        except Exception as e:
                            st.session_state["gemini_result"] = None
                            st.session_state["gemini_error"] = str(e)

                if st.session_state.get("gemini_result"):
                    lines = st.session_state["gemini_result"].splitlines()
                    for line in lines:
                        line = line.strip()
                        if line.startswith("원인:"):
                            st.markdown(
                                f'<div class="ai-result-cause">🔍 <strong>충동소비 원인</strong><br>{line[3:].strip()}</div>',
                                unsafe_allow_html=True,
                            )
                        elif line.startswith("코칭:"):
                            st.markdown(
                                f'<div class="ai-result-coach">💡 <strong>맞춤 코칭</strong><br>{line[3:].strip()}</div>',
                                unsafe_allow_html=True,
                            )

                if st.session_state.get("gemini_error"):
                    st.error(f"AI 분석 실패: {st.session_state['gemini_error']}")

            ai_coaching(summary, df)


        # ┌─────────────────────────────────────────────────────
        # │ TAB 5 – 소비 목표
        # └─────────────────────────────────────────────────────
        with tab5:
            st.markdown('<div class="section-title">💰 카테고리별 소비 목표</div>', unsafe_allow_html=True)
            st.caption("이번 달 목표 금액을 입력하면 실제 지출과 바로 비교할 수 있어요.")

            BUDGET_CATEGORIES = ["식비", "쇼핑", "마트", "카페"]
            cat_actual = df.groupby("category")["amount"].sum()

            if "budgets" not in st.session_state:
                st.session_state["budgets"] = {}

            st.markdown("**소비 목표 입력**")
            cols = st.columns(4)
            for i, cat in enumerate(BUDGET_CATEGORIES):
                with cols[i]:
                    default_val = int(st.session_state["budgets"].get(cat, 0))
                    val = st.number_input(
                        cat, min_value=0, step=10000, value=default_val,
                        key=f"budget_{cat}", format="%d"
                    )
                    st.session_state["budgets"][cat] = val

            st.divider()
            st.markdown("**소비 목표 vs 실제 지출**")

            has_budget = any(st.session_state["budgets"].get(c, 0) > 0 for c in BUDGET_CATEGORIES)
            if not has_budget:
                st.info("위에서 소비 목표를 입력하면 여기에 결과가 표시됩니다.")
            else:
                for cat in BUDGET_CATEGORIES:
                    budget = st.session_state["budgets"].get(cat, 0)
                    if budget == 0:
                        continue
                    actual = int(cat_actual.get(cat, 0))
                    ratio = actual / budget if budget > 0 else 0
                    over = actual > budget

                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        bar_color = "🔴" if over else "🟢"
                        st.markdown(f"**{bar_color} {cat}**")
                        st.progress(min(ratio, 1.0))
                    with col_b:
                        st.metric(
                            label="사용 / 예산",
                            value=f"{actual:,}원",
                            delta=f"{actual - budget:+,}원",
                            delta_color="inverse",
                        )

                st.divider()
                total_budget = sum(st.session_state["budgets"].get(c, 0) for c in BUDGET_CATEGORIES)
                total_actual = int(sum(cat_actual.get(c, 0) for c in BUDGET_CATEGORIES))
                over_cats = [
                    c for c in BUDGET_CATEGORIES
                    if st.session_state["budgets"].get(c, 0) > 0
                    and cat_actual.get(c, 0) > st.session_state["budgets"].get(c, 0)
                ]

                c1, c2, c3 = st.columns(3)
                c1.metric("총 예산", f"{total_budget:,}원")
                c2.metric("총 지출", f"{total_actual:,}원",
                          delta=f"{total_actual - total_budget:+,}원",
                          delta_color="inverse")
                c3.metric("초과 카테고리", f"{len(over_cats)}개",
                          delta="주의 필요" if over_cats else "양호",
                          delta_color="inverse" if over_cats else "normal")

                if over_cats:
                    st.error(f"예산 초과 항목: **{', '.join(over_cats)}**")
                else:
                    st.success("모든 카테고리가 예산 범위 내에 있습니다!")

        # ┌─────────────────────────────────────────────────────
        # │ TAB 4 – 내역 조회
        # └─────────────────────────────────────────────────────
        with tab4:
            # 먼저 전체 df로 소비왕 rank 계산 (필터 전 전체 기준)
            full_rank = df["amount"].rank(method="first", ascending=False).astype(int)
            KING_EMOJI = {1: "🤬", 2: "😡", 3: "😤"}

            base_cols = ["date", "category", "amount", "is_impulse", "is_night"]
            base_cols = [c for c in base_cols if c in df.columns]
            raw_display = df[base_cols].copy()
            raw_display.insert(0, "소비왕", full_rank.map(KING_EMOJI).fillna(""))
            raw_display = raw_display.rename(columns={
                "date": "날짜", "category": "카테고리",
                "amount": "금액", "is_impulse": "충동소비", "is_night": "야간소비",
            })
            raw_display["금액"] = raw_display["금액"].apply(lambda x: f"{int(x):,}")
            raw_display = raw_display.sort_values("날짜", ascending=False)

            # 필터 selectbox (단일 선택)
            filter_option = st.selectbox(
                "조회 필터",
                ["전체", "🤬 소비왕 (상위 3건)", "⚡ 충동소비", "🌙 야간소비"],
                key="raw_filter",
            )

            filtered = raw_display.copy()
            if filter_option == "🤬 소비왕 (상위 3건)":
                filtered = filtered[filtered["소비왕"] != ""]
            elif filter_option == "⚡ 충동소비":
                filtered = filtered[filtered["충동소비"] == True]
            elif filter_option == "🌙 야간소비" and "야간소비" in filtered.columns:
                filtered = filtered[filtered["야간소비"] == True]

            st.caption(f"{len(filtered)}건 표시 중")

            # 충동소비 행 흐린 핑크 하이라이트 + 소비왕 이모티콘 크게/중앙
            def _highlight_impulse(row):
                if row.get("충동소비", False):
                    return ["background-color: #ffe4e8"] * len(row)
                return [""] * len(row)

            styled = (
                filtered.style
                .apply(_highlight_impulse, axis=1)
                .set_properties(subset=["소비왕"], **{
                    "font-size": "2.2rem",
                    "text-align": "center",
                    "vertical-align": "middle",
                })
                .set_properties(subset=["금액"], **{
                    "text-align": "right",
                })
            )
            st.dataframe(styled, use_container_width=True)

            # 다운로드 (스타일 제외한 원본)
            csv = raw_display.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                "분석 결과 CSV 다운로드",
                data=csv,
                file_name="spending_analysis.csv",
                mime="text/csv",
            )

    else:
        st.warning("필수 컬럼(날짜, 금액, 카테고리)을 모두 매핑해야 분석이 시작됩니다.")

else:
    # 랜딩 화면
    st.markdown("""
    ### 👈 왼쪽에서 파일을 업로드하거나 샘플 데이터를 불러오세요

    ---

    #### 이 앱이 분석해주는 것

    | 기능 | 내용 |
    |------|------|
    | 📊 **전체 요약** | 총 지출, 카테고리별 비율, 일별 추이 |
    | 📅 **패턴 분석** | 요일별/시간대별 소비 패턴 히트맵 |
    | 🚨 **충동 소비 탐지** | 감정 키워드 + 심야 결제 기반 분석 |
    | 🤖 **AI 소비 진단** | 패턴 기반 맞춤 코멘트 |

    ---

    #### 파일 형식 안내

    ```
    날짜, 금액, 카테고리 컬럼이 있으면 어떤 형식이든 OK
    카카오페이 내역서, 신한카드 내역, 직접 작성 CSV 모두 지원
    ```
    """)
