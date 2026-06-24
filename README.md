# Money Football

축구 선수의 스탯, 연봉, 포지션, 리그, 팀 정보를 기반으로 감독과 스카우터의 의사결정을 돕는 Streamlit 기반 데이터 분석 서비스입니다.

## 주요 기능

### Coach Mode

- FC Barcelona 선수단 기반 포메이션별 라인업 구성
- AI 추천 라인업 생성
- 팀 종합 점수, 공격/중원/수비/골키퍼/포지션 적합도/밸런스/시너지 계산
- VS 스쿼드 비교
- Azure OpenAI 기반 전술 코멘트 생성

### Scout Mode

- 역할 기반 선수 탐색
- 25/26 시즌 스탯 기반 연봉 가치 진단
- 유사 선수 탐색
- 세밀 조건 검색
- 전체 선수 시장 대시보드

## 프로젝트 구조

```text
money-football/
├─ app.py
├─ requirements.txt
├─ requirements.azure.txt
├─ startup.azure.sh
├─ README.md
├─ AZURE_WEBAPP_TODO.md
│
├─ components/
│  ├─ cards.py
│  ├─ layout.py
│  ├─ metrics_panel.py
│  ├─ navigation.py
│  ├─ pitch.py
│  ├─ player_detail_modal.py
│  └─ scout_value_dashboard.py
│
├─ prompts/
│  └─ coach_comment_prompt.txt
│
├─ src/
│  ├─ constants.py
│  ├─ data_loader.py
│  ├─ coach/
│  │  ├─ ai_commentary.py
│  │  ├─ config.py
│  │  ├─ dashboard.py
│  │  ├─ formation_run.py
│  │  ├─ formations.py
│  │  ├─ lineup_payload.py
│  │  ├─ metrics.py
│  │  ├─ player_data.py
│  │  └─ scoring.py
│  │
│  └─ scout/
│     ├─ azure_blob_loader.py
│     ├─ salary_value.py
│     ├─ scout_features.py
│     ├─ scout_query.py
│     ├─ scout_schema.py
│     ├─ scout_state.py
│     └─ similarity.py
│
├─ services/
│  ├─ azure_blob_service.py
│  ├─ azure_config.py
│  ├─ azure_onnx_model_service.py
│  └─ azure_openai_service.py
│
├─ views/
│  ├─ home.py
│  ├─ coach/
│  │  ├─ squad.py
│  │  ├─ vs_squad.py
│  │  └─ dashboard.py
│  ├─ scouter/
│  │  ├─ search.py
│  │  ├─ result.py
│  │  └─ market_dashboard.py
│  └─ dev/
│     └─ azure_connection_test.py
│
├─ styles/
│  ├─ tokens.css
│  ├─ base.css
│  ├─ components.css
│  └─ pages/
│     ├─ home.css
│     ├─ coach_squad.css
│     ├─ coach_vs_squad.css
│     ├─ coach_dashboard.css
│     ├─ scout_search.css
│     ├─ scout_result.css
│     └─ scout_market_dashboard.css
│
└─ data/
   └─ processed/