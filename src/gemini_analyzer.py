"""
OpenAI API 기반 소비 패턴 분석 및 코칭
- RAG: 유사한 소비 코칭 문서를 검색하여 GPT 프롬프트에 주입
"""
import os
from dotenv import load_dotenv
from openai import OpenAI
from src.rag_engine import retrieve_coaching_context

load_dotenv()

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY가 .env에 없습니다.")
        _client = OpenAI(api_key=api_key)
    return _client


def analyze_impulse(summary: dict, df) -> str:
    """
    소비 요약 + 충동소비 데이터를 OpenAI에 전송하고
    원인 분석 + 코칭 한 줄을 반환합니다.
    """
    client = _get_client()

    total = summary["total"]
    impulse_total = summary["impulse_total"]
    impulse_count = summary["impulse_count"]
    impulse_ratio = impulse_total / total * 100 if total > 0 else 0
    night_total = summary["night_total"]
    night_ratio = night_total / total * 100 if total > 0 else 0

    # 카테고리별 지출 상위 5개
    cat_sum = df.groupby("category")["amount"].sum().sort_values(ascending=False).head(5)
    cat_str = ", ".join(f"{cat}({amt:,}원)" for cat, amt in cat_sum.items())

    # 충동소비 카테고리 상위 3개
    if impulse_count > 0:
        imp_cat = (
            df[df["is_impulse"]]
            .groupby("category")["amount"]
            .sum()
            .sort_values(ascending=False)
            .head(3)
        )
        imp_cat_str = ", ".join(f"{cat}({amt:,}원)" for cat, amt in imp_cat.items())
    else:
        imp_cat_str = "없음"

    # RAG: 유저 패턴과 유사한 코칭 문서 검색
    rag_query = f"충동소비 카테고리: {imp_cat_str}, 야간지출비율: {night_ratio:.1f}%"
    rag_context = retrieve_coaching_context(rag_query, n_results=2)

    rag_section = ""
    if rag_context:
        rag_section = f"""
[참고 코칭 자료 — 아래 내용을 참고하여 더 구체적인 조언을 작성하세요]
{rag_context}
"""

    prompt = f"""당신은 친근하고 솔직한 재무 코치입니다. 아래 소비 데이터를 보고 짧고 실용적인 코멘트를 한국어로 작성해주세요.

[소비 데이터]
- 총 지출: {total:,}원
- 충동소비 의심 금액: {impulse_total:,}원 (전체의 {impulse_ratio:.1f}%)
- 충동소비 의심 건수: {impulse_count}건
- 21시 이후 지출: {night_total:,}원 (전체의 {night_ratio:.1f}%)
- 지출 많은 카테고리: {cat_str}
- 충동소비 주요 카테고리: {imp_cat_str}
{rag_section}
규칙:
- 위 데이터에 없는 카테고리, 상품, 서비스명은 절대 언급하지 마세요.
- 실제 데이터에 나온 카테고리명만 근거로 사용하세요.
- 참고 코칭 자료가 있다면 코칭 조언에 자연스럽게 녹여내세요.
- 추측이나 가정 없이 데이터 그대로 분석하세요.

아래 형식으로 각각 한 문장씩 작성하세요. 다른 말은 쓰지 마세요.

원인: (이 소비 패턴의 주요 충동소비 원인 한 문장)
코칭: (이 사람에게 맞는 구체적이고 실용적인 개선 조언 한 문장)"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=250,
    )
    return response.choices[0].message.content.strip()
