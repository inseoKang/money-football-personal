# Scout Button Function Spec

## Purpose

스카우터 검색 페이지의 4개 버튼별로 필요한 백엔드 함수를 정리한다.  
이 문서는 프론트엔드 개발자가 버튼, 입력 폼, 결과 화면을 설계할 때 참고할 수 있도록 함수의 사용 위치와 기능을 함께 설명한다.

## Common Assumption

모든 버튼은 원본 데이터를 직접 읽기보다, 사전에 가공된 스카우터 전용 데이터셋을 사용한다.

우선 기준 원본 데이터셋:
- `outputs/scout_player_base_2526/scout_player_base_2526_default.csv`

이 파일을 기반으로 만들 processed 데이터셋:
- `scout_player_view_2526.csv`
- `similar_player_matrix_2526.csv`
- `position_type_2526.csv`
- `scout_role_score_2526.csv`

공통 함수는 다음 파일에 배치하는 것을 권장한다.

- `src/scout/scout_dataset.py`
- `src/scout/scout_features.py`
- `src/scout/scout_query.py`
- `src/scout/scout_state.py`

---

## Button 1. 내가 원하는 선수 찾기

### Button Purpose

사용자가 원하는 역할, 포지션, 전술 조건을 선택하면 그 조건에 맞는 선수를 찾는다.

예시:
- 수비형 미드필더
- 공간을 창출하는 패스를 하는 선수
- 압박을 잘하는 공격수
- 빌드업이 가능한 센터백

### Frontend Input Candidates

- `position_group`: `ALL`, `FW`, `MF`, `DF`, `GK`
- `role_key`: 사전 정의 역할
- `tactical_need`: 사전 정의 전술 요구
- `priority_metrics`: 중요하게 볼 능력치 복수 선택
- `age_min`
- `age_max`
- `max_salary`
- `min_minutes`
- `league`
- `note`: 선택 메모

### Required Functions

#### `get_role_options(position_group: str | None) -> list[dict]`

사용 버튼:
- 1번 내가 원하는 선수 찾기
- 4번 세밀 조건 검색 일부

기능:
- 선택한 포지션에 맞는 역할 목록을 반환한다.
- 예: `MF` 선택 시 `Defensive Midfielder`, `Creative Midfielder`, `Progressive Passer` 등을 반환한다.
- 프론트엔드는 이 결과를 selectbox/card option으로 사용한다.

#### `get_tactical_need_options(role_key: str | None) -> list[dict]`

사용 버튼:
- 1번 내가 원하는 선수 찾기

기능:
- 역할에 맞는 전술 요구사항 선택지를 반환한다.
- 예: `Creative Midfielder` 선택 시 `전진 패스`, `찬스 메이킹`, `압박 회피` 같은 선택지를 제공한다.
- 사용자가 자유롭게 이상한 조건을 쓰지 않도록 선택지를 제한한다.

#### `calculate_role_fit_scores(players_df, role_key: str, priority_metrics: list[str]) -> DataFrame`

사용 버튼:
- 1번 내가 원하는 선수 찾기

기능:
- 선수별 역할 적합도 점수를 계산한다.
- `passing_score`, `midfield_score`, `defense_score`, `physical_score` 등 가공 컬럼을 조합한다.
- 가능하면 사전 계산해서 `scout_role_score_2526.csv` 또는 `scout_player_view_2526.csv`에 저장한다.

#### `find_role_based_players(filters: dict) -> DataFrame`

사용 버튼:
- 1번 내가 원하는 선수 찾기

기능:
- 사용자가 고른 역할, 포지션, 나이, 연봉, 출전 시간, 리그 조건을 적용한다.
- 역할 적합도 기준으로 후보를 정렬한다.
- 결과 화면에 넘길 Top N 선수 목록을 반환한다.

---

## Button 2. 25/26 시즌 스탯 기반 선수 측정

### Button Purpose

25/26 시즌 스탯과 현재 연봉을 기준으로 선수가 저평가, 적정, 고평가인지 측정한다.  
얼마나 저평가 또는 고평가인지 수치로 보여준다.

다음 시즌 예상 연봉을 보여줄지는 추후 결정한다.

### Frontend Input Candidates

- `player_name` 또는 `player_id`
- `league`
- `position_group`
- `salary_compare_mode`: `current_salary`, `predicted_salary_optional`
- `metric_focus`: `overall`, `attack`, `passing`, `defense`, `physical`, `balanced`

### Required Functions

#### `get_player_search_options(keyword: str) -> list[dict]`

사용 버튼:
- 2번 25/26 시즌 스탯 기반 선수 측정
- 3번 유사 선수 탐색

기능:
- 선수 이름 자동완성 또는 검색 후보를 반환한다.
- 동명이인 구분을 위해 팀, 리그, 나이를 함께 반환한다.
- 프론트엔드는 combobox/search select에 사용한다.

#### `calculate_expected_salary(players_df) -> DataFrame`

사용 버튼:
- 2번 25/26 시즌 스탯 기반 선수 측정
- 3번 유사 선수 탐색 보조
- 4번 세밀 조건 검색 보조

기능:
- 선수의 스탯, 포지션, 나이, 리그, 출전 시간 등을 기반으로 예상 연봉을 계산한다.
- 실제 예측 모델이 없을 경우 초기 버전에서는 산술식 기반 점수로 시작한다.
- 결과 컬럼 예: `predicted_salary_eur`

#### `calculate_salary_value_gap(players_df) -> DataFrame`

사용 버튼:
- 2번 25/26 시즌 스탯 기반 선수 측정

기능:
- 현재 연봉과 예상 연봉 또는 성능 점수 기반 기준값의 차이를 계산한다.
- 결과 컬럼 예:
  - `salary_gap_eur`
  - `salary_gap_pct`
  - `value_status`
- `value_status` 예: `저평가`, `적정`, `고평가`

#### `evaluate_player_value(player_id: str, options: dict) -> dict`

사용 버튼:
- 2번 25/26 시즌 스탯 기반 선수 측정

기능:
- 특정 선수 1명에 대한 평가 결과를 반환한다.
- 현재 연봉, 예상 연봉, 저평가/고평가 상태, 차이 수치, 핵심 근거 지표를 포함한다.
- 프론트엔드는 이 결과를 선수 평가 카드나 상세 패널에 사용한다.

---

## Button 3. 유사 선수 탐색

### Button Purpose

사용자가 좋아하는 선수 또는 기준 선수와 비슷한 능력치/스타일을 가진 후보를 찾는다.

단순히 이름만 받는 방식은 정보가 부족할 수 있으므로, 기준 선수 선택 후 어떤 기준으로 비슷한 선수를 찾을지 추가 질문을 제공한다.

### Frontend Input Candidates

- `base_player_id`
- `position_group`: 같은 포지션만 볼지, 전체에서 볼지 선택
- `similarity_focus`: `overall`, `role`, `attack`, `passing`, `defense`, `physical`, `value`
- `age_range`: 제한 없음, U23, U26, U30 등
- `max_salary`
- `min_minutes`
- `league`

### Required Functions

#### `get_similarity_focus_options() -> list[dict]`

사용 버튼:
- 3번 유사 선수 탐색

기능:
- 유사도 기준 선택지를 반환한다.
- 예: 전체 스타일 유사, 공격 스타일 유사, 패스 스타일 유사, 수비 스타일 유사, 연봉 대비 유사 대체자.
- 프론트엔드에서 유사도 기준 selectbox/card에 사용한다.

#### `build_player_feature_vector(players_df, focus: str) -> DataFrame`

사용 버튼:
- 3번 유사 선수 탐색

기능:
- 선수별 유사도 계산에 사용할 feature vector를 만든다.
- `focus`에 따라 사용할 컬럼 묶음이 달라진다.
- 예: `passing` focus면 패스 관련 지표 비중을 높인다.

#### `calculate_player_similarity(players_df, base_player_id: str, focus: str) -> DataFrame`

사용 버튼:
- 3번 유사 선수 탐색

기능:
- 기준 선수와 다른 선수 간 유사도를 계산한다.
- 가능하면 미리 계산해서 `similar_player_matrix_2526.csv`에 저장한다.
- 결과 컬럼 예:
  - `base_player_id`
  - `candidate_player_id`
  - `similarity_score`
  - `style_similarity`
  - `role_similarity`

#### `find_similar_players(filters: dict) -> DataFrame`

사용 버튼:
- 3번 유사 선수 탐색

기능:
- 기준 선수, 유사도 기준, 포지션, 나이, 연봉, 리그 조건을 적용한다.
- 유사도 높은 순서로 후보를 반환한다.
- 후보에서 기준 선수 본인은 제외한다.

---

## Button 4. 세밀 조건 검색

### Button Purpose

스카우터가 최대한 상세하게 조건을 설정해 선수를 검색한다.  
다만 모든 질문은 데이터셋에 존재하는 컬럼과 미리 정의한 선택지 안에서만 제공한다.

### Frontend Input Candidates

- `position_group`
- `league`
- `team`
- `age_min`
- `age_max`
- `salary_min`
- `salary_max`
- `minutes_min`
- `salary_available_only`
- `score_available_only`
- `salary_value_status`
- `overall_role_score_min`
- `attack_score_min`
- `shooting_score_min`
- `chance_creation_score_min`
- `progressive_pass_score_min`
- `creative_pass_score_min`
- `pressing_score_min`
- `defensive_action_score_min`
- `ball_winning_score_min`
- `build_up_score_min`
- `aerial_defense_score_min`
- `goalkeeper_score_min`
- `salary_value_score_min`
- `salary_efficiency_score_min`
- `role_fit_*_min`
- `sort_by`
- `sort_direction`
- `top_n`

### Required Functions

#### `get_advanced_filter_schema() -> dict`

사용 버튼:
- 4번 세밀 조건 검색

기능:
- 프론트엔드가 렌더링할 수 있는 필터 질문지를 반환한다.
- 각 필터의 타입, 라벨, 최소/최대값, 선택지, 기본값을 포함한다.
- 이 함수가 있어야 프론트엔드가 임의 입력이 아니라 백엔드가 허용한 범위 안에서 UI를 만들 수 있다.
- 리그/팀/연봉 가치 상태 선택지는 현재 `scout_player_view_2526.csv`에서 읽어 생성한다.

예상 반환 구조:

```python
{
    "age": {"type": "range", "label": "나이", "min_key": "age_min", "max_key": "age_max"},
    "position_group": {"type": "select", "label": "포지션 그룹", "options": ["ALL", "FW", "MF", "DF", "GK"]},
    "score_filters": [{"key": "creative_pass_score_min", "column": "creative_pass_score", "type": "slider"}],
}
```

#### `validate_advanced_filters(filters: dict) -> dict`

사용 버튼:
- 4번 세밀 조건 검색

기능:
- 사용자가 보낸 필터가 허용된 schema 안에 있는지 검증한다.
- 범위를 벗어난 값은 기본값으로 보정하고 `_warnings` 배열에 보정 사유를 담는다.
- `top_n`은 1~100으로 제한한다.
- `sort_by`와 `sort_direction`은 허용 목록 안에서만 사용한다.
- 백엔드와 프론트엔드 사이의 안전장치 역할을 한다.

#### `apply_advanced_filters(filters: dict, players: list | None = None) -> list[dict]`

사용 버튼:
- 4번 세밀 조건 검색

기능:
- 세밀 조건 검색의 실제 필터링을 수행한다.
- 나이, 포지션, 리그, 팀, 연봉, 출전 시간, 연봉 가치 상태, 능력치 점수, 역할 적합도 점수를 조합해 후보를 줄인다.
- 반환값은 아직 프론트 출력용으로 축약하지 않은 raw row 리스트다.

#### `sort_scout_results(rows: list[dict], sort_by: str, descending: bool = True) -> list[dict]`

사용 버튼:
- 1번 내가 원하는 선수 찾기
- 2번 25/26 시즌 스탯 기반 선수 측정
- 3번 유사 선수 탐색
- 4번 세밀 조건 검색

기능:
- 버튼별 결과를 지정 기준으로 정렬한다.
- 예: `overall_role_score`, `salary_value_score`, `attack_score`, `creative_pass_score`, `minutes`, `salary_annual_gross_eur`, `role_fit_*`

#### `advanced_search_players(filters: dict, players: list | None = None) -> list[dict]`

사용 버튼:
- 4번 세밀 조건 검색

기능:
- 4번 버튼의 최종 진입 함수다.
- 프론트엔드는 이 함수 하나만 호출하면 된다.
- 내부에서 `validate_advanced_filters` -> `apply_advanced_filters` -> `sort_scout_results` 순서로 처리한다.
- 결과는 프론트 카드/테이블에 바로 사용할 수 있도록 필요한 필드만 반환한다.

반환 필드:

- `player_id`
- `player_name`
- `team`
- `league`
- `position_group`
- `age`
- `minutes`
- `salary_annual_gross_eur`
- `overall_role_score`
- `salary_value_label`
- `salary_value_score`
- `salary_efficiency_score`
- `selected_sort_by`
- `selected_sort_score`
- `data_quality_note`

#### `_build_advanced_result_row(row: dict, sort_by: str) -> dict`

사용 버튼:
- 4번 세밀 조건 검색 내부 보조

기능:
- raw row에서 프론트 출력에 필요한 필드만 정리한다.
- 정렬 기준 점수를 `selected_sort_score`로 함께 반환한다.

#### `_passes_score_filters(row: dict, filters: dict) -> bool`

사용 버튼:
- 4번 세밀 조건 검색 내부 보조

기능:
- 능력치 점수와 역할 적합도 점수의 최소 조건을 검사한다.
- 점수형 필터가 많기 때문에 메인 필터링 함수에서 분리한다.

---

## Shared Backend Functions

### `load_scout_player_view(season: str = "2526") -> DataFrame`

사용 버튼:
- 1번, 2번, 3번, 4번 전체

기능:
- 스카우터 전용 선수 view CSV를 로드한다.
- 모든 버튼의 기본 데이터 진입점이다.

### `normalize_source_columns(raw_df) -> DataFrame`

사용 버튼:
- 데이터셋 구축 단계

기능:
- 원본 데이터의 컬럼명을 표준 컬럼명으로 변환한다.
- `Player`, `Name`, `player_name`처럼 섞인 컬럼을 `player_name`으로 맞춘다.

### `build_scout_player_view(raw_df) -> DataFrame`

사용 버튼:
- 데이터셋 구축 단계

기능:
- 원본 데이터에서 스카우터 페이지에 필요한 컬럼만 추출한다.
- 포지션 그룹, 지표 점수, 가치 점수, 리스크 점수 등 추가 컬럼을 계산한다.
- 결과는 `scout_player_view_2526.csv`로 저장한다.

### `save_processed_dataset(df, output_path: str) -> None`

사용 버튼:
- 데이터셋 구축 단계

기능:
- 가공된 데이터셋을 CSV로 저장한다.
- 나중에 Streamlit 화면에서는 저장된 CSV만 읽게 한다.

---

## Recommended Development Order

1. 원본 데이터 컬럼 확인
2. `normalize_source_columns`
3. `build_scout_player_view`
4. 1번 버튼용 `find_role_based_players`
5. 2번 버튼용 `evaluate_player_value`
6. 3번 버튼용 `find_similar_players`
7. 4번 버튼용 `get_advanced_filter_schema`, `apply_advanced_filters`
8. 프론트엔드 입력 폼 연결
