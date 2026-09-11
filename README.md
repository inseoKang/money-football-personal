# Money Football

팀 프로젝트 **Money Football**을 개인적으로 디벨롭한 저장소입니다.

Money Football은 축구 선수의 경기 기록, 연봉, 포지션, 리그, 팀 데이터를 활용해 **감독과 스카우터의 의사결정을 지원하는 Streamlit 기반 데이터 분석 서비스**입니다.

저는 프로젝트에서 **Frontend를 중심으로 서비스 기획과 UI/UX 설계, 일부 백엔드 구조 설계, Frontend-Backend 연동, Azure 배포, 문서화**를 담당했습니다. 단순히 화면을 구현하는 데 그치지 않고, 사용자가 Coach Mode와 Scout Mode의 분석 결과를 자연스럽게 이해하고 사용할 수 있도록 전체 사용자 흐름과 화면 구조를 설계하고 실제 데이터/서비스 로직과 연결하는 역할을 맡았습니다.

> 현재 공개 포트폴리오 버전에서는 Azure 리소스 상태와 환경 변수 구성에 따라 Blob Storage, Azure OpenAI 등 일부 기능이 제한될 수 있습니다. 프로젝트 진행 당시에는 Azure 환경을 구성하고 Streamlit 서비스의 배포 및 실행을 점검했습니다.

---

## Project Goal

이 프로젝트의 목표는 축구 데이터를 단순히 조회하는 서비스를 만드는 것이 아니라, **감독과 스카우터가 실제 의사결정을 내리는 과정에 필요한 정보를 하나의 서비스 안에서 확인할 수 있도록 만드는 것**이었습니다.

### Coach Mode

- 어떤 포메이션을 사용할 것인가?
- 현재 선수단에서 누구를 어떤 위치에 배치할 것인가?
- 구성한 라인업의 공격·중원·수비 밸런스는 어떤가?
- 상대 스쿼드와 비교했을 때 어떤 강점과 약점이 있는가?
- 수치화된 결과를 실제 전술 관점에서는 어떻게 해석할 수 있는가?

### Scout Mode

- 특정 역할이나 조건에 맞는 선수는 누구인가?
- 현재 연봉 대비 경기력이 좋은 선수는 누구인가?
- 특정 선수와 비슷한 유형의 선수는 누구인가?
- 여러 선수의 데이터와 시장 가치를 한 화면에서 어떻게 비교할 것인가?

---

## My Role

| Area | Contribution |
| --- | --- |
| Service Planning | Coach / Scout Mode의 핵심 기능, 화면 구성, 사용자 흐름 구체화 |
| UI/UX Design | 홈, Coach, Scout 화면의 정보 구조와 인터랙션 설계 |
| Frontend Development | Streamlit 기반 화면, 카드, 지표 패널, 피치 UI, 검색/결과/대시보드 구현 및 정리 |
| Coach Mode UI | 포메이션 선택, 선수 배치, 스쿼드 비교, 분석 결과 화면 구성 |
| Scout Mode UI | 검색 조건 입력, 검색 결과, 선수 가치 정보, 시장 대시보드 화면 구성 |
| Frontend-Backend Integration | 화면 입력값을 검색 / 평가 / 추천 로직으로 전달하고 결과를 다시 UI에 연결 |
| Backend Design Support | Coach/Scout 일부 데이터 흐름, payload, 상태 관리, 서비스 호출 구조 설계 및 연동 |
| Azure Deployment | Azure 서비스 연동 구조 점검, Web App 배포 설정 및 실행 환경 구성 |
| Documentation | 프로젝트 구조, 기능 흐름, 실행 방법, 배포 및 구현 내용을 문서로 정리 |

---

## Main Features

### Coach Mode

- FC Barcelona 선수단 기반 포메이션별 라인업 구성
- AI 추천 라인업 생성
- 선수별 포지션 배치 및 스쿼드 구성
- 팀 종합 점수 계산
- 공격 / 중원 / 수비 / 골키퍼 지표 제공
- 포지션 적합도 / 밸런스 / 시너지 평가
- VS 스쿼드 비교
- Azure OpenAI 기반 전술 코멘트 생성

### Scout Mode

- 역할 기반 선수 탐색
- 포지션 및 세부 조건 기반 검색
- 25/26 시즌 스탯 기반 연봉 가치 진단
- 유사 선수 탐색
- 검색 결과 비교 및 상세 정보 확인
- 전체 선수 시장 대시보드

---

## Frontend & UX

제가 가장 집중한 부분은 **복잡한 분석 로직을 사용자가 쉽게 사용할 수 있는 화면 흐름으로 바꾸는 것**이었습니다.

Streamlit의 기본 위젯을 단순히 나열하기보다, 화면별 목적을 구분하고 공통 컴포넌트와 CSS를 분리해 서비스 형태에 가깝게 구성했습니다.

### 1. 사용자 흐름 중심 화면 구성

```text
Home
├─ Coach Mode
│  ├─ My Squad
│  │  ├─ Formation 선택
│  │  ├─ 선수 배치
│  │  └─ 팀 지표 확인
│  ├─ VS Squad
│  │  └─ 상대 스쿼드와 비교
│  └─ Dashboard
│     └─ 팀 분석 결과 확인
│
└─ Scout Mode
   ├─ Search
   │  └─ 역할 / 조건 / 유사 선수 탐색
   ├─ Result
   │  └─ 후보 선수 비교 및 상세 분석
   └─ Market Dashboard
      └─ 전체 선수 시장 데이터 확인
```

### 2. 공통 UI 컴포넌트 분리

화면마다 동일한 UI 코드를 반복하지 않도록 다음 요소를 컴포넌트 단위로 관리했습니다.

- 카드 UI
- 페이지 레이아웃
- 내비게이션
- 지표 패널
- 축구장(Pitch) UI
- 선수 상세 정보 Modal
- Scout 가치 분석 Dashboard

### 3. 페이지별 스타일 분리

공통 스타일과 페이지 전용 스타일을 분리해 유지보수성을 높였습니다.

```text
styles/
├─ tokens.css
├─ base.css
├─ components.css
└─ pages/
   ├─ home.css
   ├─ coach_squad.css
   ├─ coach_vs_squad.css
   ├─ coach_dashboard.css
   ├─ scout_search.css
   ├─ scout_result.css
   └─ scout_market_dashboard.css
```

---

## Frontend-Backend Integration

프로젝트에서는 화면을 별도로 구현하는 것보다 **사용자의 입력이 실제 분석 로직까지 전달되고, 계산 결과가 다시 화면에 표현되는 흐름**을 중요하게 다뤘습니다.

### Coach Mode Flow

```text
사용자 포메이션 선택
        ↓
포메이션별 슬롯 생성
        ↓
선수 선택 / 배치
        ↓
Lineup Payload 생성
        ↓
선수 및 포지션 데이터 처리
        ↓
팀 지표 / 적합도 / 밸런스 / 시너지 계산
        ↓
Dashboard 및 VS 화면에 결과 표시
        ↓
필요 시 Azure OpenAI 전술 코멘트 요청
```

Coach Mode에서는 특히 다음 요소들을 연결했습니다.

- 포메이션 정의와 화면 슬롯 구성
- 선수 선택 상태와 Streamlit Session State 관리
- 선수 배치 결과와 라인업 payload 연결
- 팀 평가 지표 계산 결과를 UI 지표 패널에 표시
- VS Squad 비교 결과를 별도 화면에서 시각화
- Azure OpenAI 서비스 결과를 Coach 화면에 연결

### Scout Mode Flow

```text
사용자 검색 조건 입력
        ↓
검색 조건 / 역할 / 필터 정리
        ↓
Scout Query 실행
        ↓
선수 후보 추출
        ↓
연봉 가치 / 유사도 등 분석
        ↓
Result 화면 구성
        ↓
시장 Dashboard와 연계
```

Scout Mode에서는 검색 화면과 결과 화면이 분리되어 있어, 사용자가 입력한 조건이 검색 로직으로 전달되고 반환된 선수 데이터를 다시 카드·표·지표 형태로 확인할 수 있도록 구성했습니다.

---

## UI / Logic Separation

프로젝트가 커지면서 화면 코드 안에 데이터 처리, 점수 계산, 외부 서비스 호출이 모두 섞이지 않도록 역할을 나눴습니다.

```text
views/
→ 사용자가 실제로 보는 페이지와 사용자 입력 처리

components/
→ 여러 화면에서 재사용하는 UI

src/
→ Coach / Scout의 핵심 도메인 로직

services/
→ Azure Blob, Azure OpenAI, ONNX 등 외부 서비스 연결

styles/
→ 공통 및 페이지별 CSS
```

이 구조를 통해 UI 수정이 분석 로직에 직접 영향을 주지 않고, 백엔드 로직이나 Azure 연결 방식이 변경되더라도 화면 전체를 다시 작성하지 않도록 구성했습니다.

---

## Azure Architecture

프로젝트에서는 로컬 실행뿐 아니라 실제 배포까지 고려해 Azure 기반 서비스 연결 구조를 구성했습니다.

```text
Streamlit App
│
├─ Frontend / Views
│
├─ Coach / Scout Logic
│
├─ Azure Blob Storage
│  └─ 데이터 및 모델 자산
│
├─ ONNX Runtime
│  └─ 모델 추론
│
├─ Azure OpenAI
│  └─ Coach 전술 코멘트
│
└─ Azure Web App
   └─ Streamlit 서비스 배포
```

제가 참여한 배포 및 연동 범위는 다음과 같습니다.

- Azure Web App 환경에 맞는 Streamlit 실행 구조 확인
- `requirements.txt` / Azure용 requirements 관리
- `startup.azure.sh` 기반 실행 설정
- Azure 서비스 호출 구조와 환경 변수 연결 점검
- Blob Storage / Azure OpenAI 연동 코드와 화면 흐름 연결 확인
- 로컬 환경과 Azure 환경 차이로 발생하는 실행 문제 점검
- 배포 과정과 설정 내용을 문서화

---

## Development Notes

프로젝트를 진행하면서 단순 기능 구현 외에도 실제 서비스 형태로 동작시키기 위해 여러 연결 지점을 반복적으로 점검했습니다.

### Streamlit State 관리

포메이션, 선택 선수, 검색 조건처럼 화면 이동이나 재실행 이후에도 유지되어야 하는 값은 Streamlit의 Session State와 연결했습니다.

특히 Coach Mode에서는 사용자 조작에 따라 선수 배치 상태가 계속 변하기 때문에, **UI에서 보이는 상태와 실제 분석에 전달되는 데이터가 일치하도록 관리하는 것**이 중요했습니다.

### 검색 UX

Scout 검색은 단순히 하나의 필터만 제공하는 방식이 아니라 역할, 가치, 유사 선수, 세부 조건 등 여러 탐색 방식으로 나누어 설계했습니다.

검색 기능을 구현할 때는 다음과 같은 UX를 중요하게 봤습니다.

- 사용자가 어떤 기준으로 검색 중인지 명확하게 알 수 있을 것
- 입력한 조건을 검색 실행 전에 확인할 수 있을 것
- 결과 화면에서 어떤 기준으로 후보가 나온 것인지 이해할 수 있을 것
- 선수 이름 검색처럼 자주 사용하는 탐색은 가능한 한 직관적인 입력 방식으로 사용할 수 있을 것

### Local / Azure 실행 환경 차이

로컬에서는 정상적으로 실행되지만 Azure Web App에서는 다음 요소로 인해 문제가 발생할 수 있어 별도로 점검했습니다.

- Python dependency 차이
- Azure 환경 변수
- Streamlit startup command
- Blob Storage 접근 설정
- Azure OpenAI endpoint / key / deployment 설정
- 데이터 및 모델 파일 경로

외부 Azure 기능을 사용할 수 없는 상황에서도 서비스 구조를 확인할 수 있도록 로컬 데이터 또는 fallback 경로를 함께 고려했습니다.

---

## Tech Stack

| Category | Stack |
| --- | --- |
| Language | Python |
| Web App | Streamlit |
| Frontend | Streamlit Components, HTML/CSS |
| Data Processing | pandas, numpy |
| Visualization | Plotly, Streamlit |
| Machine Learning Runtime | ONNX Runtime, joblib |
| AI | Azure OpenAI |
| Storage | Azure Blob Storage |
| Deployment | Azure Web App / App Service |
| Collaboration | GitHub, Notion |

---

## Repository Structure

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
```

---

## Run Locally

### 1. Install dependencies

```powershell
pip install -r requirements.txt
```

### 2. Run Streamlit

```powershell
streamlit run app.py
```

### 3. Azure features

Azure Blob Storage나 Azure OpenAI를 사용하는 기능은 별도의 Azure 환경 변수 또는 Streamlit secrets 설정이 필요합니다.

환경 변수가 구성되지 않은 경우 일부 외부 연동 기능은 제한될 수 있습니다.

---

## What I Learned

이 프로젝트를 통해 단순히 화면을 만드는 것과 **서비스를 완성하는 것의 차이**를 경험했습니다.

특히 다음 부분을 직접 다뤘습니다.

- 데이터 분석 결과를 사용자가 이해할 수 있는 UI로 변환하는 방법
- Streamlit에서 복잡한 화면 상태를 관리하는 방법
- 화면 입력과 Python 분석 로직을 연결하는 방법
- 공통 컴포넌트와 페이지별 스타일을 분리하는 방법
- Frontend와 Backend의 역할 경계를 정리하는 방법
- 로컬 환경과 Cloud 배포 환경의 차이를 해결하는 방법
- Azure Storage / OpenAI / Web App을 실제 서비스 흐름에 연결하는 방법
- 팀 프로젝트의 구조와 실행 방법을 다른 사람이 이해할 수 있도록 문서화하는 방법

Money Football에서는 **기획 → 디자인 → Frontend 구현 → Backend 연동 → Cloud 배포 → 문서화**까지 서비스 개발의 전체 흐름을 경험했습니다.
