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
import sys
import os

sys.path.append(os.path.dirname(__file__))
from src.data_loader import load_file, auto_map_columns, preprocess, get_summary

# ── 페이지 설정 ─────────────────────────────────────────────
st.set_page_config(
    page_title="내 소비 분석 AI",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 한글 폰트 ────────────────────────────────────────────────
plt.rcParams["font.family"] = "Malgun Gothic"
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
    uploaded = st.file_uploader(
        "CSV 또는 Excel 파일",
        type=["csv", "xlsx", "xls"],
        help="카카오페이, 신한카드, 직접 작성 등 어떤 형식이든 OK",
    )

    st.divider()
    st.subheader("🗂 샘플 데이터로 체험")
    use_sample = st.button("샘플 데이터 불러오기", use_container_width=True)

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
df_raw = None
col_map = {}

if uploaded:
    try:
        df_raw = load_file(uploaded)
        st.success(f"✅ 파일 로드 완료! ({len(df_raw)}행 × {len(df_raw.columns)}열)")
    except Exception as e:
        st.error(f"파일 로드 실패: {e}")
        st.info("Excel 파일은 `pip install openpyxl` 설치가 필요합니다.")

elif use_sample:
    sample_path = os.path.join(os.path.dirname(__file__), "data/raw/sample_spending.csv")
    df_raw = pd.read_csv(sample_path)
    st.info("샘플 데이터를 불러왔습니다.")

# ── 컬럼 매핑 UI ─────────────────────────────────────────────
if df_raw is not None:

    # 파일 미리보기
    with st.expander("📋 업로드된 파일 미리보기", expanded=True):
        st.dataframe(df_raw.head(5), use_container_width=True)
        st.caption(f"감지된 컬럼: {list(df_raw.columns)}")

    col_map = auto_map_columns(df_raw)

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
            df = preprocess(df_raw, col_map)
            summary = get_summary(df)
        except Exception as e:
            st.error(f"데이터 처리 오류: {e}")
            st.stop()

        # ══════════════════════════════════════════════════════
        # 탭 구성
        # ══════════════════════════════════════════════════════
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 전체 요약",
            "📅 패턴 분석",
            "🚨 충동 소비 탐지",
            "🗃 원본 데이터",
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

            col_l, col_r = st.columns(2)

            # 카테고리별 파이 차트
            with col_l:
                st.markdown("**카테고리별 지출 비율**")
                cat_sum = df.groupby("category")["amount"].sum().sort_values(ascending=False)
                fig, ax = plt.subplots(figsize=(6, 5))
                wedges, texts, autotexts = ax.pie(
                    cat_sum.values,
                    labels=None,          # 라벨 겹침 방지 → legend로 대체
                    autopct="%1.1f%%",
                    startangle=90,
                    pctdistance=0.75,
                )
                for t in autotexts:
                    t.set_fontsize(9)
                ax.legend(
                    wedges,
                    cat_sum.index,
                    loc="upper left",
                    bbox_to_anchor=(-0.3, 1.1),
                    fontsize=9,
                    frameon=False,
                )
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()

            # 카테고리별 막대
            with col_r:
                st.markdown("**카테고리별 지출 금액**")
                fig, ax = plt.subplots(figsize=(6, 5))
                ax.barh(
                    cat_sum.index[::-1],
                    cat_sum.values[::-1],
                    color="#4ECDC4",
                    edgecolor="white",
                )
                ax.set_xlabel("금액 (원)")
                ax.tick_params(axis="y", labelsize=9)
                # 금액 레이블은 막대 끝에만 표시
                max_val = cat_sum.values.max()
                for i, v in enumerate(cat_sum.values[::-1]):
                    ax.text(v + max_val * 0.01, i, f"{v:,.0f}", va="center", fontsize=8)
                ax.set_xlim(0, max_val * 1.25)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()

            # 일별 추이
            st.markdown("**일별 지출 추이**")
            daily = df.groupby("date")["amount"].sum().reset_index()
            daily["rolling_7"] = daily["amount"].rolling(7, min_periods=1).mean()
            fig, ax = plt.subplots(figsize=(12, 3))
            ax.bar(daily["date"], daily["amount"], alpha=0.5, color="#5B8CFF", label="일별 지출")
            ax.plot(daily["date"], daily["rolling_7"], color="red", linewidth=2, label="7일 평균")
            ax.set_ylabel("금액 (원)")
            ax.legend()
            plt.xticks(rotation=30)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        # ┌─────────────────────────────────────────────────────
        # │ TAB 2 – 패턴 분석
        # └─────────────────────────────────────────────────────
        with tab2:
            col_l, col_r = st.columns(2)

            # 요일별
            with col_l:
                st.markdown("**요일별 지출**")
                weekday_order = ["월", "화", "수", "목", "금", "토", "일"]
                weekday_sum = df.groupby("weekday_name")["amount"].sum().reindex(weekday_order).fillna(0)
                colors = ["#FF6B6B" if w in ["토", "일"] else "#4ECDC4" for w in weekday_order]
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.bar(weekday_order, weekday_sum.values, color=colors, edgecolor="white")
                ax.set_ylabel("금액 (원)")
                ax.set_title("요일별 총 지출")
                for i, v in enumerate(weekday_sum.values):
                    ax.text(i, v + 100, f"{v:,.0f}", ha="center", fontsize=8)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()

            # 시간대별
            with col_r:
                st.markdown("**시간대별 지출** (데이터 있는 경우)")
                if df["hour"].notna().sum() > 0:
                    hour_sum = df.groupby("hour")["amount"].sum()
                    colors_h = ["#FF4444" if h >= 22 else "#5B8CFF" for h in hour_sum.index]
                    fig, ax = plt.subplots(figsize=(6, 4))
                    ax.bar(hour_sum.index, hour_sum.values, color=colors_h, edgecolor="white")
                    ax.set_xlabel("시간 (24h)")
                    ax.set_ylabel("금액 (원)")
                    ax.set_title("시간대별 지출 (빨강=심야)")
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
                else:
                    st.info("시간 데이터가 없어 시간대 분석을 건너뜁니다.")

            # 카테고리 × 요일 히트맵
            st.markdown("**카테고리 × 요일 히트맵**")
            pivot = df.pivot_table(
                values="amount", index="category", columns="weekday_name",
                aggfunc="sum", fill_value=0
            ).reindex(columns=[w for w in weekday_order if w in df["weekday_name"].unique()])
            fig, ax = plt.subplots(figsize=(10, max(3, len(pivot) * 0.6)))
            sns.heatmap(
                pivot, annot=True, fmt=",", cmap="YlOrRd",
                linewidths=0.5, ax=ax, cbar_kws={"label": "금액(원)"}
            )
            ax.set_title("카테고리 × 요일 지출 히트맵")
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
                st.markdown("""
| 기준 | 설명 |
|------|------|
| 카테고리 평균 2배 초과 | 평소 그 카테고리에서 쓰는 금액의 2배 이상 |
| 21시 이후 결제 | 저녁 9시 이후 발생한 모든 결제 |
| 같은 날 동일 카테고리 3건 이상 | 하루에 같은 곳에서 3번 이상 결제 |
| 하루 지출 평균 1.5배 초과 | 그날 총 지출이 내 일평균의 1.5배 넘을 때 |
| 주말 야간 결제 | 토·일 21시 이후 결제 |
                """)

            st.divider()

            # 충동 소비 거래 목록 + 이유 표시
            st.markdown("**충동 소비 의심 거래 목록**")

            if len(impulse_df) > 0:
                show_cols = ["date", "category", "amount", "impulse_reason"]
                if "memo" in impulse_df.columns:
                    show_cols = ["date", "category", "amount", "memo", "impulse_reason"]
                show_cols = [c for c in show_cols if c in impulse_df.columns]
                st.dataframe(
                    impulse_df[show_cols].sort_values("amount", ascending=False).rename(
                        columns={"impulse_reason": "탐지 이유", "date": "날짜",
                                 "category": "카테고리", "amount": "금액", "memo": "메모"}
                    ),
                    use_container_width=True,
                    height=320,
                )

                # 탐지 이유별 건수 통계
                st.markdown("**탐지 이유별 건수**")
                reason_counts = {
                    "카테고리 평균 2배 초과": int(df["flag_over_cat_avg"].sum()),
                    "21시 이후 결제":         int(df["flag_night"].sum()),
                    "동일 카테고리 3건+":      int(df["flag_freq_impulse"].sum()),
                    "하루 평균 1.5배 초과":    int(df["flag_over_daily_avg"].sum()),
                    "주말 야간":               int(df["flag_weekend_night"].sum()),
                }
                rc_df = pd.DataFrame(reason_counts.items(), columns=["이유", "건수"])
                rc_df = rc_df[rc_df["건수"] > 0].sort_values("건수", ascending=False)

                fig, ax = plt.subplots(figsize=(8, 3))
                ax.barh(rc_df["이유"][::-1], rc_df["건수"][::-1], color="#FF6B6B", edgecolor="white")
                ax.set_xlabel("건수")
                for i, v in enumerate(rc_df["건수"][::-1]):
                    ax.text(v + 0.1, i, str(v), va="center", fontsize=10)
                ax.set_xlim(0, rc_df["건수"].max() * 1.3)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()

            else:
                st.success("충동 소비 의심 거래가 없습니다!")

            # 충동 소비 카테고리 분포
            if len(impulse_df) > 0:
                st.markdown("**충동 소비 카테고리별 금액**")
                imp_cat = impulse_df.groupby("category")["amount"].sum().sort_values(ascending=False)
                fig, ax = plt.subplots(figsize=(9, 3))
                ax.bar(imp_cat.index, imp_cat.values, color="#FF6B6B", edgecolor="white")
                ax.set_ylabel("금액 (원)")
                ax.tick_params(axis="x", rotation=30)
                max_v = imp_cat.values.max()
                for i, v in enumerate(imp_cat.values):
                    ax.text(i, v + max_v * 0.01, f"{v:,.0f}", ha="center", fontsize=8)
                ax.set_ylim(0, max_v * 1.2)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()

            # 소비 진단 코멘트
            st.divider()
            st.markdown("**소비 진단**")

            if impulse_ratio > 20:
                st.error(f"충동 소비 비율 **{impulse_ratio:.1f}%** — 꽤 높아요. 특히 야간이나 배달 지출을 줄여보세요.")
            elif impulse_ratio > 10:
                st.warning(f"충동 소비 비율 **{impulse_ratio:.1f}%** — 보통 수준이에요. 조금만 더 줄이면 됩니다.")
            else:
                st.success(f"충동 소비 비율 **{impulse_ratio:.1f}%** — 소비 패턴이 안정적이에요!")

            if night_ratio > 15:
                st.warning(f"21시 이후 지출 비율 **{night_ratio:.1f}%** — 저녁 이후 충동 구매 패턴이 있어요.")

            top_cat = df.groupby("category")["amount"].sum().idxmax()
            top_amount = df.groupby("category")["amount"].sum().max()
            st.info(f"가장 많이 쓴 카테고리: **{top_cat}** ({top_amount:,}원) — 이 항목 예산을 먼저 관리해보세요.")

        # ┌─────────────────────────────────────────────────────
        # │ TAB 4 – 원본 데이터
        # └─────────────────────────────────────────────────────
        with tab4:
            st.markdown("**원본 데이터 미리보기**")

            # 필터
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                cats = ["전체"] + sorted([str(c) for c in df["category"].dropna().unique().tolist()])
                selected_cat = st.selectbox("카테고리 필터", cats)
            with col_f2:
                min_amt = int(df["amount"].min())
                max_amt = int(df["amount"].max())
                amt_range = st.slider("금액 범위", min_amt, max_amt, (min_amt, max_amt), step=1000)

            filtered = df.copy()
            if selected_cat != "전체":
                filtered = filtered[filtered["category"] == selected_cat]
            filtered = filtered[(filtered["amount"] >= amt_range[0]) & (filtered["amount"] <= amt_range[1])]

            st.caption(f"{len(filtered)}건 표시 중")
            show_cols = ["date", "category", "subcategory", "amount", "memo", "is_impulse", "is_night"]
            show_cols = [c for c in show_cols if c in filtered.columns]
            st.dataframe(filtered[show_cols].sort_values("date", ascending=False), use_container_width=True)

            # 다운로드
            csv = filtered[show_cols].to_csv(index=False, encoding="utf-8-sig")
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
