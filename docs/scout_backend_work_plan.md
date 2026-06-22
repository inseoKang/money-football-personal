# Scout Backend Work Plan

## Goal

스카우터 검색 페이지의 4개 버튼이 공통 데이터셋을 기반으로 동작할 수 있도록, 원본 선수 데이터에서 스카우터 전용 view 데이터를 만들고 버튼별 입력 조건을 표준화한다.

## Current State

- 현재 작업 브랜치: `feature/scout-start-buttons-backend`
- 현재 `views/scouter/search.py`는 placeholder 상태다.
- 현재 `src/scout/scout_state.py`에는 1번 버튼인 `role_based` 흐름 일부만 정의되어 있다.
- 현재 `src/scout/scout_schema.py`에는 컬럼 alias 처리 기반만 있다.
- 관리자가 만든 `views/home.py`에서 스카우터 모드 진입 시 `scout_search` 페이지로 이동한다.

## Planned Scout Buttons

mockup 기준 4개 버튼은 다음 방향으로 잡는다.

1. 내가 원하는 선수 찾기
   - 목적: 우리 팀에 필요한 역할에 맞는 후보를 찾는다.
   - 예시: 창의형 미드필더, 압박형 공격수, 빌드업 센터백
   - 핵심 입력: 포지션, 역할 유형, 전술 요구, 나이, 예산, 최소 출전 시간, 리그

2. 25/26 시즌 스탯 기반 선수 측정
   - 목적: 현재 연봉이 선수의 스탯 대비 저평가, 적정, 고평가인지 측정한다.
   - 예시: 현재 연봉 대비 성능이 높은 선수, 연봉 대비 고평가된 선수
   - 핵심 입력: 기준 선수, 리그, 포지션, 측정 기준

3. 유사 선수 탐색
   - 목적: 기준 선수와 유사한 스타일의 대체 후보를 찾는다.
   - 예시: 손흥민과 비슷한 공격수
   - 핵심 입력: 기준 선수, 포지션 제한, 나이 조건, 예산, 유사도 기준

4. 세밀 조건 검색
   - 목적: 스카우터가 데이터셋에 존재하는 범위 안에서 상세 조건을 직접 조합해 검색한다.
   - 예시: U23, MF, 패스 점수 75 이상, 연봉 3M 이하
   - 핵심 입력: 포지션, 리그, 나이, 연봉, 출전 시간, 능력치 점수, 정렬 기준

## Proposed Data Outputs

기준 원본 데이터셋은 `outputs/scout_player_base_2526/scout_player_base_2526_default.csv`이다.

이 파일은 25/26 시즌 Big5 선수 2,839명 기준의 스카우터 베이스라인이며, 선수/리그/팀/포지션/연봉 매칭 컬럼과 일부 per90 가공 컬럼을 포함한다.

이 원본을 직접 화면에서 모두 사용하지 않고, 다음 형태의 processed 산출물을 우선 고려한다.

### `data/processed/scout_player_view_2526.csv`

스카우터 페이지에서 공통으로 사용하는 선수 단위 view.

예상 컬럼:
- `player_id`
- `player_name`
- `age`
- `nation`
- `team`
- `league`
- `position`
- `position_group`
- `minutes`
- `nineties`
- `salary_eur`
- `predicted_salary_eur`
- `market_value_eur`
- `overall_score`
- `attack_score`
- `passing_score`
- `midfield_score`
- `defense_score`
- `physical_score`
- `gk_score`
- `role_fit_*`
- `value_score`
- `salary_efficiency_score`
- `undervalued_score`
- `prospect_score`
- `risk_score`

### `data/processed/similar_player_matrix_2526.csv`

유사 선수 탐색 버튼에서 사용하는 선수 간 유사도 matrix 또는 long-form table.

권장 long-form 컬럼:
- `base_player_id`
- `base_player_name`
- `candidate_player_id`
- `candidate_player_name`
- `similarity_score`
- `position_similarity`
- `style_similarity`
- `role_similarity`
- `salary_gap`
- `age_gap`

### `data/processed/position_type_2526.csv`

포지션, 역할, 지표 그룹을 연결하는 설정성 데이터.

예상 컬럼:
- `position_group`
- `role_key`
- `role_label`
- `primary_metrics`
- `secondary_metrics`
- `min_required_minutes`
- `default_age_min`
- `default_age_max`

### `data/processed/scout_role_score_2526.csv`

역할별 점수를 미리 계산한 테이블. 데이터가 크지 않으면 `scout_player_view_2526.csv`에 wide 컬럼으로 합쳐도 된다.

권장 long-form 컬럼:
- `player_id`
- `role_key`
- `role_fit_score`
- `role_rank`
- `score_components`

## Precompute vs Runtime

기본 방향은 "무거운 계산은 미리 저장, 가벼운 필터와 정렬은 런타임 처리"가 좋다.

미리 계산할 항목:
- 포지션 그룹 정규화
- 공격/패스/수비/피지컬/GK 등 능력치 그룹 점수
- 역할별 적합도 점수
- 예상 연봉 또는 가치 대비 효율 점수
- 유사 선수 matrix
- 유망주 성장성 점수
- 리스크 점수

런타임 처리할 항목:
- 사용자가 고른 포지션, 나이, 예산, 리그 필터
- 버튼별 정렬 기준 선택
- Top N 후보 추출
- 화면 표시용 요약 문구 생성

## Button Input Contract

사용자 자유 입력은 최소화하고, selectbox/multiselect/slider 중심으로 제한한다.

### 1. 내가 원하는 선수 찾기

- `position_group`: `ALL`, `FW`, `MF`, `DF`, `GK`
- `role_key`: 사전 정의된 역할
- `tactical_need`: 사전 정의된 전술 요구
- `priority_metrics`: 사전 정의된 지표 그룹 복수 선택
- `age_min`
- `age_max`
- `max_salary`
- `min_minutes`
- `league`
- `note`: 선택 입력

### 2. 25/26 시즌 스탯 기반 선수 측정

- `player_id` 또는 `player_name`
- `league`
- `position_group`
- `salary_compare_mode`: `current_salary`, `predicted_salary_optional`
- `metric_focus`: `overall`, `attack`, `passing`, `defense`, `physical`, `balanced`

### 3. 유사 선수 탐색

- `base_player_id` 또는 `base_player_name`
- `position_group`
- `similarity_focus`: `overall`, `attack`, `passing`, `defense`, `physical`, `value`
- `age_max`
- `max_salary`
- `min_minutes`
- `league`

### 4. 세밀 조건 검색

- `position`
- `position_group`
- `league`
- `team`
- `age_min`
- `age_max`
- `salary_min`
- `salary_max`
- `min_minutes`
- `overall_score_min`
- `attack_score_min`
- `passing_score_min`
- `midfield_score_min`
- `defense_score_min`
- `physical_score_min`
- `gk_score_min`
- `value_score_min`
- `sort_by`
- `top_n`

## Suggested Code Structure

- `views/scouter/search.py`
  - 4개 버튼 UI와 선택된 버튼별 입력 폼 진입

- `views/scouter/forms.py`
  - 버튼별 입력 폼 렌더링

- `src/scout/scout_state.py`
  - 버튼별 session_state 저장/조회/reset

- `src/scout/scout_schema.py`
  - 원본 데이터 컬럼 alias 및 표준 컬럼 매핑

- `src/scout/scout_dataset.py`
  - 원본 데이터 로드, 컬럼 정규화, processed csv 생성

- `src/scout/scout_features.py`
  - 산술식/스코어 계산 함수

- `src/scout/scout_query.py`
  - 버튼별 필터링/정렬/Top N 추출 함수

## Next Step

다음 턴에서 원본 데이터 파일을 받으면:

1. 컬럼 목록과 샘플 row를 확인한다.
2. 원본 컬럼을 표준 컬럼으로 매핑한다.
3. 계산 가능한 점수와 불가능한 점수를 구분한다.
4. 우선 `scout_player_view_2526.csv` 생성 스크립트부터 만든다.
5. 이후 버튼별 입력 폼과 query 함수를 연결한다.
