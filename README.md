# 💸 MyWallet — 개인 소비 분석 + AI 소비 코치

> 카드/지출 내역을 올리면 **소비 심리 분석 + 충동소비 탐지 + AI 맞춤 코칭**까지 한 번에

---

## 프로젝트 소개

단순 가계부가 아닙니다.
지출 데이터와 감정 메모를 함께 분석해서 **충동소비 패턴, 무의식 지출 원인, 행동 개선 조언**을 제공하는 AI 소비 코치입니다.

CSV 또는 Excel 파일 하나만 올리면 바로 분석이 시작됩니다.
카카오페이, 신한카드, 국민카드, 하나카드 등 주요 카드사 형식을 자동 인식합니다.

---

## 주요 기능

| 탭 | 기능 |
|----|------|
| 📊 **전체 요약** | 총 지출 / 카테고리별 비율 (파이차트) / 일별 추이 (7일 이동평균) |
| 📅 **패턴 분석** | 요일별·시간대별 소비 패턴 / 카테고리×요일 히트맵 |
| 🚨 **충동소비 탐지** | 5가지 규칙 기반 충동소비 자동 플래그 + AI 소비 코치 |
| 🗃 **원본 데이터** | 필터링 / CSV 다운로드 |
| 💰 **예산 관리** | 카테고리별 월 예산 설정 / 초과 알림 / 진행률 시각화 |

---

## 기술 스택

| 분류 | 기술 | 선택 이유 |
|------|------|-----------|
| **언어** | Python 3.x | 데이터 분석 생태계 최강 |
| **웹 프레임워크** | Streamlit | Python만으로 대화형 웹앱 구현 가능 |
| **데이터 처리** | Pandas, NumPy | 표 형태 소비 데이터 처리의 표준 |
| **시각화** | Matplotlib, Seaborn, Plotly | 정적 차트(Matplotlib/Seaborn) + 인터랙티브(Plotly) 혼용 |
| **AI 코칭 (LLM)** | OpenAI GPT-4o mini | 한국어 품질 우수, 비용 매우 낮음 (1회당 $0.0002 이하) |
| **벡터 DB (RAG)** | ChromaDB | 로컬 설치, 완전 무료, Python 친화적 |
| **임베딩** | OpenAI text-embedding-3-small | 고성능 벡터 변환, 저렴한 비용 |
| **환경 변수** | python-dotenv | API 키 안전하게 관리 |

---

## 데이터 파이프라인

```
[CSV / Excel 업로드]
        │
        ▼
[인코딩 자동 감지]  UTF-8 / EUC-KR / Excel
        │
        ▼
[카드사 프리셋 적용]  카카오페이 / 신한 / 국민 / 하나 / 자동감지
        │
        ▼
[컬럼 자동 매핑]  키워드 매칭 → 데이터 타입 추론
        │
        ▼
[전처리]
 ├── 날짜/시간 파싱
 ├── 금액 정제 (쉼표·원 제거)
 ├── 가맹점명 → 카테고리 자동 분류 (80+ 키워드)
 └── 파생 컬럼 생성 (요일, 시간대, 주차)
        │
        ▼
[충동소비 탐지]  5가지 규칙 기반 플래그 (사이드바 슬라이더로 조정 가능)
        │
        ├── [시각화] 탭1~4 렌더링
        │
        └── [AI 코칭 파이프라인]
              │
              ├── 소비 요약 + 메모 감정 추출
              ├── RAG: ChromaDB에서 유사 코칭 문서 검색
              └── GPT-4o mini: 데이터 + RAG 결과 → 원인/코칭 출력
```

---

## 충동소비 탐지 기준 (사용자 조정 가능)

| 기준 | 기본값 | 설명 |
|------|--------|------|
| 카테고리 평균 배수 | 2.0배 | 평소 그 카테고리 평균의 N배 초과 |
| 야간 기준 시간 | 21시 | 이 시간 이후 결제 |
| 동일 카테고리 건수 | 3건 | 하루 동일 카테고리 N건 이상 |
| 하루 지출 배수 | 1.5배 | 그날 총 지출이 일평균의 N배 초과 |
| 주말 야간 | 자동 | 토·일 + 야간 기준 시간 이후 |

> 사이드바 슬라이더로 직접 조정하면 분석 결과에 즉시 반영됩니다.

---

## RAG 코칭 구조

```
유저 소비 패턴 (충동카테고리 + 메모감정 + 야간비율)
        │
        ▼
[ChromaDB 유사도 검색]
 data/knowledge/
 ├── stress_spending.md    스트레스성 충동소비
 ├── night_shopping.md     야간 충동소비
 ├── delivery_food.md      배달 과소비
 ├── online_shopping.md    온라인 쇼핑 충동
 ├── weekend_spending.md   주말 과소비
 └── cafe_repeat.md        카페 반복 지출
        │
        ▼
[관련 코칭 문서 2개 검색]
        │
        ▼
[GPT-4o mini]
 소비 데이터 + 메모 + RAG 문서 → 원인/코칭 출력
```

---

## 프로젝트 구조

```
mywallet/
├── app.py                     # Streamlit 메인 앱 (탭 5개)
├── src/
│   ├── data_loader.py         # 로드 / 전처리 / 충동소비 탐지
│   ├── gemini_analyzer.py     # OpenAI 연동 + 메모 감정 + RAG 주입
│   └── rag_engine.py          # ChromaDB 인덱싱 + 유사도 검색
├── data/
│   ├── raw/
│   │   └── sample_spending.csv
│   └── knowledge/             # RAG 코칭 문서 (6개)
├── notebooks/                 # EDA, 감정분석, 이상탐지, 예측
├── requirements.txt
├── .env                       # API 키 (gitignore)
└── .gitignore
```

---

## 개발 환경 설정

```bash
# 1. 클론
git clone https://github.com/meene11/my_wallet_pattern.git
cd my_wallet_pattern

# 2. 가상환경
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. 패키지 설치
pip install -r requirements.txt

# 4. API 키 설정
# .env 파일 생성 후 아래 내용 입력:
# OPENAI_API_KEY=sk-...

# 5. 실행
streamlit run app.py
```

---

## 브랜치 구조

| 브랜치 | 내용 |
|--------|------|
| `main` | 초기 구조 |
| `feature/gemini-analyzer` | OpenAI AI 코칭 기본 연동 |
| `feature/sidebar-thresholds` | 충동소비 임계값 사이드바 슬라이더 |
| `feature/card-preset` | 카드사별 컬럼 자동 매핑 프리셋 |
| `feature/memo-emotion` | 메모 감정 텍스트 AI 분석 반영 |
| `feature/budget-alert` | 카테고리별 예산 설정 + 초과 알림 탭 |
| `feature/rag-coaching` | RAG 소비 코칭 (ChromaDB + 임베딩) |

---

## 배포 (Streamlit Cloud)

1. [share.streamlit.io](https://share.streamlit.io) → GitHub 연동
2. Repository: `meene11/my_wallet_pattern` / Branch: `main` / Main file: `app.py`
3. Secrets에 `OPENAI_API_KEY` 등록
4. Deploy

> 무료 플랜으로 충분합니다.
