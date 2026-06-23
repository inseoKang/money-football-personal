# Scout Third Button Spec: Similar Player Search

## Button Name

3번 버튼: `유사 선수 탐색`

프론트 표시 후보:

- `유사 선수 탐색`
- `비슷한 선수 찾기`
- `대체 후보 찾기`

## Button Purpose

사용자가 기준 선수를 선택하면, 해당 선수와 비슷한 능력치/역할/스타일을 가진 후보를 찾는다.

예시:

- 손흥민과 비슷한 공격수
- 창의형 미드필더와 비슷한 패스 성향의 선수
- 현재 팀 선수를 대체할 수 있는 비슷한 스타일의 저연봉 후보

## Current Data Basis

3번 버튼은 우선 다음 파일을 기준으로 시작한다.

- `data/processed/scout_player_view_2526.csv`

이 CSV에는 1번, 2번 버튼 작업에서 만든 다음 계열 컬럼이 포함되어 있다.

- 선수 기본 정보
- 포지션/리그/팀/나이/출전 시간
- 현재 연봉
- 역할 적합도 점수
- 공격/수비/압박/빌드업/창의성 proxy 점수
- 연봉 가치 진단 컬럼

## Input Design

3번 버튼은 단순히 선수 이름만 받으면 후보 결과가 너무 넓거나 애매해질 수 있다.  
그래서 필수 입력은 기준 선수 1개로 두되, 유사도 기준과 현실 조건을 선택 옵션으로 제공한다.

### Required Input

#### `base_player_id`

기준 선수.

프론트 UI:

- 검색 input
- autocomplete/selectbox

표시 형식:

```text
선수명 · 팀 · 리그 · 포지션 · 나이
```

예:

```text
Brajan Gruda · Brighton · Premier League · MF · 21세
```

### Optional Inputs

#### `similarity_focus`

어떤 기준으로 비슷한 선수를 찾을지 선택한다.

초기 선택지:

- `overall`: 전체 스타일 유사
- `role`: 역할 적합도 유사
- `attack`: 공격 성향 유사
- `passing`: 창의성/전개 성향 유사
- `defense`: 수비 성향 유사
- `physical`: 압박/활동량 유사
- `value`: 연봉 가치까지 고려한 대체 후보

기본값:

- `overall`

#### `position_scope`

포지션을 얼마나 엄격하게 제한할지 선택한다.

선택지:

- `same_position`: 같은 포지션 그룹만
- `adjacent_position`: 인접 포지션까지 허용
- `all`: 전체 포지션에서 탐색

기본값:

- `same_position`

#### `league`

리그 제한.

선택지:

- `ALL`
- `Premier League`
- `La Liga`
- `Serie A`
- `Bundesliga`
- `Ligue 1`

기본값:

- `ALL`

#### `age_max`

최대 나이 조건.

선택지:

- 제한 없음
- 23세 이하
- 26세 이하
- 30세 이하

기본값:

- 제한 없음

#### `max_salary`

최대 연봉 조건.

선택지:

- 제한 없음
- 1M EUR 이하
- 3M EUR 이하
- 5M EUR 이하
- 10M EUR 이하

기본값:

- 제한 없음

#### `min_minutes`

최소 출전 시간.

선택지:

- 제한 없음
- 300분 이상
- 700분 이상
- 1000분 이상
- 1500분 이상

기본값:

- 700분 이상

#### `top_n`

결과 개수.

기본값:

- 20

## Output Design

3번 버튼의 기본 출력은 후보 리스트다.

### Candidate Row Fields

프론트에서 각 후보 카드 또는 테이블에 사용할 값:

- `player_id`
- `player_name`
- `team`
- `league`
- `position_group`
- `age`
- `minutes`
- `salary_annual_gross_eur`
- `similarity_score`
- `similarity_label`
- `similarity_focus`
- `base_player_name`
- `salary_value_label`
- `salary_value_score`
- `data_quality_note`

### Similarity Label

유사도 점수에 따른 라벨:

- `매우 유사`: 85 이상
- `유사`: 70 이상
- `부분 유사`: 55 이상
- `낮은 유사도`: 55 미만

### Explanation Fields

가능하면 후보별 설명 문장을 함께 제공한다.

- `similarity_reason_summary`

예:

```text
역할 적합도와 공격/창의성 점수 분포가 기준 선수와 유사하며, 현재 연봉은 더 낮습니다.
```

## Backend Strategy

유사도 계산은 두 단계로 나눈다.

### 1. Feature Vector 생성

기준 선수와 후보 선수의 점수 컬럼을 벡터로 만든다.

예:

```text
overall:
overall_role_score
attack_score
shooting_score
chance_creation_score
pressing_score
defensive_action_score
salary_efficiency_score

role:
role_fit_finisher
role_fit_pressing_forward
role_fit_creative_midfielder
role_fit_progressive_passer
role_fit_ball_winning_midfielder
role_fit_ball_playing_defender
role_fit_defensive_stopper
role_fit_shot_stopper

attack:
attack_score
shooting_score
chance_creation_score

passing:
chance_creation_score
creative_pass_score
progressive_pass_score
build_up_score

defense:
defensive_action_score
ball_winning_score
aerial_defense_score

physical:
pressing_score
aerial_defense_score
minutes_percentile_by_position

value:
overall_role_score
salary_efficiency_score
salary_value_score
performance_percentile_by_position
salary_percentile_by_position
```

### 2. Similarity Score 계산

초기 구현은 cosine similarity 또는 normalized distance 기반으로 간다.

권장 초기 방식:

```text
similarity_score = 100 - normalized weighted distance
```

이유:

- 현재 feature들이 대부분 0~100 점수라 거리 기반 계산이 해석하기 쉽다.
- 연봉처럼 단위가 큰 컬럼은 percentile 또는 log 변환 후 사용해야 한다.
- 초기 구현의 `value` focus는 raw 연봉 금액이 아니라 성능 percentile, 연봉 percentile, 연봉 효율, 연봉 가치 점수를 사용한다.

## Required Functions

### `get_similarity_focus_options() -> list[dict]`

사용 버튼:

- 3번 유사 선수 탐색

기능:

- 프론트가 표시할 유사도 기준 선택지를 반환한다.
- 각 option에는 `value`, `label`, `description`을 포함한다.

### `get_position_scope_options() -> list[dict]`

사용 버튼:

- 3번 유사 선수 탐색

기능:

- 같은 포지션만 볼지, 인접 포지션을 허용할지, 전체에서 찾을지 선택지를 반환한다.

### `build_player_feature_vector(player: dict, focus: str) -> dict[str, float]`

사용 버튼:

- 3번 유사 선수 탐색

기능:

- 선수 1명의 유사도 계산용 feature vector를 만든다.
- `focus`에 따라 사용하는 컬럼 조합이 달라진다.
- 결측값은 0 또는 중립값 50으로 보정한다.

### `calculate_similarity_score(base_vector: dict, candidate_vector: dict, focus: str) -> float`

사용 버튼:

- 3번 유사 선수 탐색

기능:

- 기준 선수와 후보 선수의 유사도 점수를 0~100으로 계산한다.
- 초기 구현에서는 weighted distance 기반으로 계산한다.

### `find_similar_players(filters: dict) -> list[dict]`

사용 버튼:

- 3번 유사 선수 탐색

기능:

- 기준 선수 ID와 사용자가 선택한 조건을 받아 유사 선수 후보를 반환한다.
- 기준 선수 본인은 결과에서 제외한다.
- 포지션 범위, 리그, 나이, 연봉, 최소 출전 시간을 필터링한다.
- 유사도 점수 높은 순으로 정렬한다.

예상 입력:

```python
{
    "base_player_id": "...",
    "similarity_focus": "overall",
    "position_scope": "same_position",
    "league": "ALL",
    "age_max": 26,
    "max_salary": 3000000,
    "min_minutes": 700,
    "top_n": 20,
}
```

예상 출력:

```python
[
    {
        "player_id": "...",
        "player_name": "...",
        "team": "...",
        "league": "...",
        "position_group": "MF",
        "age": 22,
        "minutes": 1200,
        "salary_annual_gross_eur": 1800000,
        "similarity_score": 82.4,
        "similarity_label": "유사",
        "similarity_focus": "overall",
        "base_player_name": "기준 선수명",
        "salary_value_label": "저평가",
        "salary_value_score": 71.2,
        "similarity_reason_summary": "역할 적합도와 공격/창의성 점수 분포가 기준 선수와 유사합니다.",
        "data_quality_note": "passing_proxy_limited",
    }
]
```

## Precompute vs Runtime

초기 구현은 runtime 계산으로 충분하다.

이유:

- 현재 선수 수는 2,839명으로 작다.
- 기준 선수와 후보 전체를 비교해도 부담이 크지 않다.
- 사용자가 선택한 `similarity_focus`, `position_scope`, 필터 조건에 따라 결과가 달라진다.

다만 나중에 성능 문제가 생기거나 화면에서 즉시 반응이 필요하면 다음 파일을 사전 생성할 수 있다.

- `data/processed/similar_player_matrix_2526.csv`

초기에는 만들지 않는다.

## Frontend Recommendation

초기 화면:

```text
[기준 선수 검색]
[유사도 기준 선택]
[포지션 범위 선택]
[나이 조건]
[예산 조건]
[최소 출전 시간]
[비슷한 선수 찾기 버튼]
```

결과 화면:

```text
기준 선수 카드
유사 후보 Top N
후보별 유사도 점수
연봉 가치 라벨
간단한 설명 문장
```

## Notes

- 3번 버튼은 1번/2번에서 만든 점수 컬럼을 재사용한다.
- 패스/빌드업 관련 점수는 현재 proxy이므로 `passing` focus의 프론트 라벨은 `창의성/전개 성향 유사`로 표현한다.
- 후보의 `data_quality_note`에 `passing_proxy_limited`가 있으면 결과 설명에서 정밀 패스 데이터 보강 후 재검증이 필요하다고 안내한다.
- `value` focus는 유사 스타일뿐 아니라 대체 후보의 경제성까지 함께 보려는 모드다.
