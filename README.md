# 개인 소비 분석 + 무의식 지출 탐지 AI

> 카드/지출 데이터를 넣으면 **"왜 돈이 새는지 + 소비 심리까지 분석해주는 AI"**

---

## 프로젝트 소개

단순 가계부가 아닙니다.
지출 데이터 + 감정 메모를 분석해서 **충동 소비 패턴, 무의식 지출 원인, 행동 개선 루틴**을 제안하는 AI 개인 소비 코치입니다.

---

## 주요 기능

### 1. 감정 기반 소비 분석 (NLP)
- 지출할 때 짧은 메모 입력 ("오늘 답답해서 마라탕 시킴")
- AI가 감정 키워드 자동 추출 → [스트레스, 보상심리, 충동]
- 감정 × 지출 패턴 시각화

### 2. 이상 소비 탐지 (Anomaly Detection)
- 나의 평소 소비 패턴(시간대, 금액, 카테고리)을 학습
- 평소와 다른 이상 패턴 감지 시 알림
- "새벽 결제 급증 → 스트레스 지출 가능성 높음"

### 3. 초개인화 소비 코칭 (RAG + LLM)
- 과거 소비 데이터 + 감정 기록 기반 대화형 피드백
- "지난달 비 오는 날 평균 4만원 배달비 지출 → 오늘도 비 오는데 미리 알림"
- 행동경제학 지식베이스를 RAG로 연결

### 4. 다음 달 지출 예측 (Time-series Forecasting)
- 과거 패턴 기반 다음 달 지출 예측
- "시험 기간 → 스트레스성 지출 15% 증가 예상"
- 예산 미리 조정 제안

---

## 기술 스택

| 분류 | 기술 | 이유 |
|------|------|------|
| **언어** | Python 3.10+ | 데이터 분석 생태계 최강 |
| **데이터 처리** | pandas, numpy | 표 형태 소비 데이터 처리 |
| **시각화** | matplotlib, seaborn, plotly | 소비 패턴 그래프 |
| **NLP / 감정 분석** | Hugging Face Transformers (한국어 감정 모델) | 무료, 오픈소스 |
| **이상 탐지** | scikit-learn (Isolation Forest) | 간단하고 성능 좋음 |
| **클러스터링** | scikit-learn (K-Means) | 소비 유형 분류 |
| **시계열 예측** | Prophet (Meta, 무료) | 설치 쉽고 직관적 |
| **LLM 연결** | Google Gemini API (무료 티어) | 무료 할당량 있음 |
| **벡터 DB (RAG)** | ChromaDB (로컬) | 설치 간단, 완전 무료 |
| **웹 UI** | Streamlit | 파이썬만으로 웹앱 완성 |
| **노트북** | Jupyter Notebook | 분석 과정 시각화 |
| **데이터** | Kaggle 공개 금융 데이터셋 | 무료 |

---

## 프로젝트 구조 (예정)

```
my_wallet_pattern/
├── data/               # 소비 데이터 (CSV)
│   ├── raw/            # 원본 데이터
│   └── processed/      # 전처리된 데이터
├── notebooks/          # Jupyter 분석 노트북
│   ├── 01_eda.ipynb           # 탐색적 데이터 분석
│   ├── 02_emotion_analysis.ipynb  # 감정 분석
│   ├── 03_anomaly_detection.ipynb # 이상 탐지
│   └── 04_forecasting.ipynb   # 시계열 예측
├── src/                # 핵심 모듈
│   ├── emotion.py      # NLP 감정 추출
│   ├── anomaly.py      # 이상 탐지
│   ├── forecast.py     # 지출 예측
│   └── rag.py          # RAG 코칭
├── app.py              # Streamlit 웹앱
├── requirements.txt
└── README.md
```

---

## 개발 순서 (단계별)

1. **1단계**: 데이터 준비 + EDA (Kaggle 데이터 분석)
2. **2단계**: 소비 카테고리 클러스터링 + 패턴 시각화
3. **3단계**: 감정 메모 NLP 분석
4. **4단계**: 이상 탐지 모델 구현
5. **5단계**: Prophet 시계열 예측
6. **6단계**: Gemini API + ChromaDB로 RAG 코칭 구현
7. **7단계**: Streamlit으로 UI 통합

---

## 데이터 출처

- [Kaggle - Personal Finance Dataset](https://www.kaggle.com/datasets)
- 소비 패턴 공개 데이터 (금융감독원, 통계청)

---

## 개발 환경

```bash
pip install -r requirements.txt
```

> 혼자 만드는 무료 프로젝트입니다. 모든 기술 스택은 오픈소스 또는 무료 티어 기반입니다.
