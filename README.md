# 💸 MyWallet — 개인 소비 분석 + AI 소비 코치

> 카드/지출 내역을 올리면 **소비 패턴 분석 + 충동소비 탐지 + AI 맞춤 코칭**까지 한 번에

---

## 프로젝트 소개

단순 가계부가 아닙니다.  
지출 데이터를 분석해서 **충동소비 패턴 자동 탐지, 원인 분석, 행동 개선 조언**을 제공하는 AI 소비 코치입니다.

CSV 또는 Excel 파일 하나만 올리면 바로 분석이 시작됩니다.  
카카오페이, 신한카드, 국민카드, 하나카드 등 주요 카드사 형식을 자동 인식합니다.

---

## 주요 기능

| 탭 | 기능 |
|----|------|
| 📊 **전체 요약** | 총 지출 / 카테고리별 비율 (파이차트) / 일별 추이 (7일 이동평균) |
| 📅 **패턴 분석** | 요일별·시간대별 소비 패턴 / 카테고리×요일 히트맵 |
| 🚨 **충동소비 탐지** | 5가지 규칙 기반 자동 플래그 + 탐지 기준 필터 + AI 소비 코치 |
| 🗃 **내역 조회** | 소비왕·충동소비·야간소비 필터 / 충동소비 행 핑크 하이라이트 / CSV 다운로드 |
| 💰 **소비 목표** | 카테고리별 목표 금액 설정 / 실제 지출 비교 / 초과 알림 |

---

## AI 기술 스택

| 기술 | 역할 |
|------|------|
| **OpenAI GPT-4o mini** | 충동소비 원인 분석 + 맞춤 코칭 문장 생성 |
| **OpenAI text-embedding-3-small** | 코칭 문서를 벡터로 변환 (RAG 임베딩) |
| **ChromaDB** | 벡터 유사도 검색 (로컬 벡터 DB) |
| **RAG** | 전문 코칭 문서 검색 → GPT 프롬프트 주입으로 정밀 답변 |

> AI 기술 상세 설명 → [AI_TECH_GUIDE.md](./AI_TECH_GUIDE.md)

---

## 전체 기술 스택

| 분류 | 기술 | 선택 이유 |
|------|------|-----------|
| **언어** | Python 3.x | 데이터 분석 생태계 최강 |
| **웹 프레임워크** | Streamlit | Python만으로 대화형 웹앱 구현 |
| **데이터 처리** | Pandas, NumPy | 소비 데이터 처리 표준 |
| **시각화** | Matplotlib, Seaborn, Plotly | 정적 + 인터랙티브 차트 혼용 |
| **AI 코칭** | OpenAI GPT-4o mini | 한국어 품질 우수, 비용 매우 낮음 |
| **벡터 DB** | ChromaDB | 로컬 설치, 완전 무료 |
| **임베딩** | OpenAI text-embedding-3-small | 고성능 벡터 변환 |
| **환경 변수** | python-dotenv | API 키 안전 관리 |

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
        ├── [시각화] 탭 1~4 렌더링
        │
        └── [AI 코칭 파이프라인]
              │
              ├── 소비 요약 생성
              ├── RAG: ChromaDB에서 유사 코칭 문서 검색
              └── GPT-4o mini: 소비 데이터 + RAG 결과 → 원인/코칭 출력
```

---

## RAG 코칭 구조

```
유저 소비 패턴 (충동카테고리 + 야간비율)
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
 소비 데이터 + RAG 문서 → 원인/코칭 출력
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

> 사이드바 슬라이더로 직접 조정하면 적용 버튼 클릭 시 반영됩니다.

---

## 프로젝트 구조

```
mywallet/
├── app.py                     # Streamlit 메인 앱 (탭 5개)
├── src/
│   ├── data_loader.py         # 로드 / 전처리 / 충동소비 탐지
│   ├── gemini_analyzer.py     # OpenAI 연동 + RAG 주입
│   └── rag_engine.py          # ChromaDB 인덱싱 + 유사도 검색
├── data/
│   ├── raw/
│   │   └── sample_spending.csv
│   └── knowledge/             # RAG 코칭 문서 (6개)
├── AI_TECH_GUIDE.md           # AI 기술 상세 설명
├── PROJECT_STRUCTURE.md       # 프로젝트 구조 문서
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

## 배포 (Streamlit Cloud)

1. [share.streamlit.io](https://share.streamlit.io) → GitHub 연동
2. Repository: `meene11/my_wallet_pattern` / Branch: `main` / Main file: `app.py`
3. Secrets에 `OPENAI_API_KEY` 등록
4. Deploy → 인터넷 접근 가능한 URL 자동 생성

> 무료 플랜으로 충분합니다.

---

## 브랜치 구조

| 브랜치 | 내용 |
|--------|------|
| `main` | 배포 기준 브랜치 |
| `feature/gemini-analyzer` | OpenAI AI 코칭 기본 연동 |
| `feature/sidebar-thresholds` | 충동소비 임계값 사이드바 슬라이더 |
| `feature/card-preset` | 카드사별 컬럼 자동 매핑 프리셋 |
| `feature/memo-emotion` | 메모 감정 텍스트 AI 분석 반영 |
| `feature/budget-alert` | 소비 목표 설정 + 초과 알림 탭 |
| `feature/rag-coaching` | RAG 소비 코칭 (ChromaDB + 임베딩) |
