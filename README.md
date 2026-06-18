# money-football
AI-based Korea national football lineup recommendation project

```text
money-football/
│
├─ app.py
├─ requirements.txt
├─ README.md
├─ .gitignore
│
├─ assets/
│
├─ components/
│
├─ data/
│
├─ pages/
│  ├─ 01_my_squad.py
│  ├─ 02_vs_comparison.py
│  └─ 03_player_dashboard.py
│
├─ prompts/
│
└─ src/
```


## 폴더 및 파일 설명
### app.py
Streamlit 앱의 메인 실행 파일입니다.
서비스 소개 화면 또는 각 페이지로 이동하는 진입 화면 역할을 합니다.

### requirements.txt
프로젝트 실행에 필요한 Python 패키지 목록을 저장합니다.
예: streamlit, pandas, numpy, scikit-learn, matplotlib 등

### README.md
프로젝트 소개, 폴더 구조, 실행 방법, 주요 기능 등을 정리하는 문서입니다.

### .gitignore
GitHub에 올리지 않을 파일이나 폴더를 지정합니다.
예: 가상환경 폴더, 캐시 파일, API 키 파일 등

### assets/
이미지, CSS 등 화면 구성에 필요한 정적 파일을 저장하는 폴더입니다.

### components/
Streamlit 화면에서 반복해서 사용하는 UI 구성 요소를 저장하는 폴더입니다.
페이지별로 같은 화면 요소를 여러 번 작성하지 않도록, 선수 카드, 경기장 화면, 지표 카드, 선수 상세 정보, 그래프 등을 컴포넌트 단위로 분리해서 관리합니다.
예: 선수 목록 카드, 포메이션 경기장, 팀 지표 카드, 선수 상세 정보 영역, 레이더 차트 등

### data/
서비스에서 사용하는 CSV, JSON 데이터를 저장하는 폴더입니다.

### pages/
Streamlit의 여러 페이지를 관리하는 폴더입니다.
각 화면별 기능을 분리해서 작성합니다.
#### 01_my_squad.py
내 선수 데이터를 기반으로 포메이션을 선택하고, 추천 라인업을 확인하는 메인 페이지입니다.
#### 02_vs_comparison.py
상대 국가를 선택하고, 상대에 맞는 추천 라인업과 매치업 분석을 확인하는 비교 페이지입니다.
#### 03_player_dashboard.py
전체 선수 데이터를 탐색하고, 선수별 능력치와 추천 포지션을 확인하는 대시보드 페이지입니다.

### prompts/
AI 코멘트 생성을 위한 프롬프트 파일을 저장하는 폴더입니다.

### src/
화면에서 사용하는 주요 기능과 계산 로직을 작성하는 폴더입니다.
Streamlit 화면 코드와 추천/계산 로직을 분리하기 위해 사용합니다.

