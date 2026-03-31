"""
소비 데이터 로드 및 전처리 모듈
- CSV / Excel 파일 모두 지원
- 컬럼명 자동 매핑 (카카오페이, 신한카드, 직접입력 등)
"""
import pandas as pd
import numpy as np


# 지원하는 컬럼명 매핑 (여러 카드사/앱 형식)
COLUMN_MAP = {
    "date": ["date", "날짜", "거래일", "결제일", "이용일자", "승인일자", "거래일자"],
    "time": ["time", "시간", "거래시간", "결제시간"],
    "amount": ["amount", "금액", "거래금액", "결제금액", "이용금액", "출금액", "지출"],
    "category": ["category", "카테고리", "분류", "업종", "가맹점업종"],
    "subcategory": ["subcategory", "소분류", "세부분류"],
    "memo": ["memo", "메모", "적요", "내용", "가맹점명", "상호명"],
    "payment_method": ["payment_method", "결제수단", "카드종류"],
}

# 충동 소비 가능성 높은 카테고리 키워드
IMPULSE_CATEGORIES = [
    "배달", "편의점", "온라인", "쇼핑", "간식", "카페", "커피",
    "delivery", "convenience", "online", "shopping",
]


def load_file(uploaded_file) -> pd.DataFrame:
    """업로드된 파일을 DataFrame으로 변환"""
    filename = uploaded_file.name.lower()
    if filename.endswith(".csv"):
        try:
            df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding="cp949")
    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    else:
        raise ValueError("CSV 또는 Excel 파일만 지원합니다.")
    return df


def auto_map_columns(df: pd.DataFrame) -> dict:
    """DataFrame 컬럼을 표준 컬럼명으로 자동 매핑"""
    mapping = {}
    df_cols_lower = {col.lower().strip(): col for col in df.columns}

    for standard_col, candidates in COLUMN_MAP.items():
        for candidate in candidates:
            if candidate.lower() in df_cols_lower:
                mapping[standard_col] = df_cols_lower[candidate.lower()]
                break
    return mapping


def preprocess(df: pd.DataFrame, col_map: dict) -> pd.DataFrame:
    """매핑된 컬럼 기준으로 전처리"""
    result = pd.DataFrame()

    # 날짜
    if "date" in col_map:
        result["date"] = pd.to_datetime(df[col_map["date"]], errors="coerce")

    # 시간
    if "time" in col_map:
        try:
            result["hour"] = pd.to_datetime(
                df[col_map["time"]], format="%H:%M", errors="coerce"
            ).dt.hour
        except Exception:
            result["hour"] = np.nan
    else:
        result["hour"] = np.nan

    # 금액 (쉼표 제거 후 숫자 변환)
    if "amount" in col_map:
        amt = df[col_map["amount"]].astype(str).str.replace(",", "").str.replace("원", "")
        result["amount"] = pd.to_numeric(amt, errors="coerce").abs()

    # 카테고리
    result["category"] = df[col_map["category"]].fillna("기타").astype(str) if "category" in col_map else "기타"
    result["subcategory"] = df[col_map["subcategory"]] if "subcategory" in col_map else ""
    result["memo"] = df[col_map["memo"]] if "memo" in col_map else ""
    result["payment_method"] = df[col_map["payment_method"]] if "payment_method" in col_map else "카드"

    # 파생 컬럼
    if "date" in result.columns:
        result["weekday"] = result["date"].dt.dayofweek
        weekday_map = {0: "월", 1: "화", 2: "수", 3: "목", 4: "금", 5: "토", 6: "일"}
        result["weekday_name"] = result["weekday"].map(weekday_map)
        result["month"] = result["date"].dt.month
        result["week"] = result["date"].dt.isocalendar().week.astype(int)

    # 결측값 제거
    result = result.dropna(subset=["amount"])
    result = result[result["amount"] > 0]
    result = result.reset_index(drop=True)

    # ── 충동 소비 탐지 (데이터 기반) ──────────────────────────

    # 기준 1: 해당 카테고리 평균의 2배 이상 지출
    cat_mean = result.groupby("category")["amount"].transform("mean")
    result["flag_over_cat_avg"] = result["amount"] > cat_mean * 2

    # 기준 2: 21시 이후 결제
    result["flag_night"] = result["hour"].apply(
        lambda h: h >= 21 if not pd.isna(h) else False
    )

    # 기준 3: 충동성 카테고리에서 하루 3건 이상
    def is_impulse_cat(cat):
        return any(kw in str(cat).lower() for kw in IMPULSE_CATEGORIES)

    result["_is_impulse_cat"] = result["category"].apply(is_impulse_cat)
    daily_impulse_cnt = result[result["_is_impulse_cat"]].groupby(
        result["date"].dt.date
    )["amount"].transform("count")
    result["flag_freq_impulse"] = False
    impulse_idx = result[result["_is_impulse_cat"]].index
    result.loc[impulse_idx, "flag_freq_impulse"] = daily_impulse_cnt >= 3

    # 기준 4: 하루 총 지출이 개인 일평균의 1.5배 초과
    daily_total = result.groupby(result["date"].dt.date)["amount"].transform("sum")
    personal_daily_avg = result.groupby(result["date"].dt.date)["amount"].sum().mean()
    result["flag_over_daily_avg"] = daily_total > personal_daily_avg * 1.5

    # 기준 5: 주말 야간 (토·일 + 21시 이후)
    result["flag_weekend_night"] = (
        (result["weekday"] >= 5) & result["flag_night"]
    )

    # 최종 충동 소비 플래그 + 이유 생성
    result["is_impulse"] = (
        result["flag_over_cat_avg"] |
        result["flag_night"] |
        result["flag_freq_impulse"] |
        result["flag_over_daily_avg"] |
        result["flag_weekend_night"]
    )

    def impulse_reason(row):
        reasons = []
        if row["flag_over_cat_avg"]:
            reasons.append("카테고리 평균 2배 초과")
        if row["flag_night"]:
            reasons.append("21시 이후 결제")
        if row["flag_freq_impulse"]:
            reasons.append("같은 날 동일 카테고리 3건 이상")
        if row["flag_over_daily_avg"]:
            reasons.append("하루 지출 평균 1.5배 초과")
        if row["flag_weekend_night"]:
            reasons.append("주말 야간 결제")
        return " / ".join(reasons) if reasons else ""

    result["impulse_reason"] = result.apply(impulse_reason, axis=1)

    # 내부용 컬럼 정리
    result = result.drop(columns=["_is_impulse_cat"])

    # 이전 호환용 (야간 여부)
    result["is_night"] = result["flag_night"]

    return result


def get_summary(df: pd.DataFrame) -> dict:
    """주요 요약 통계"""
    return {
        "total": int(df["amount"].sum()),
        "count": len(df),
        "avg_per_day": int(df.groupby("date")["amount"].sum().mean()),
        "avg_per_tx": int(df["amount"].mean()),
        "max_tx": int(df["amount"].max()),
        "max_category": df.groupby("category")["amount"].sum().idxmax(),
        "impulse_total": int(df[df["is_impulse"]]["amount"].sum()),
        "impulse_count": int(df["is_impulse"].sum()),
        "night_total": int(df[df["is_night"]]["amount"].sum()),
    }
