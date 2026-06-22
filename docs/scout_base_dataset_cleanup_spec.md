# Scout Base Dataset Cleanup Spec

## Purpose

`outputs/scout_player_base_2526/scout_player_base_2526_default.csv`를 스카우터 첫 페이지 버튼들이 사용할 수 있는 안정적인 베이스라인 데이터로 정리하기 위한 기준을 정의한다.

이 문서는 아직 실제 CSV를 생성하지 않고, 생성 전에 확인해야 할 데이터 정리 규칙을 정리한 것이다.

## Source Dataset

- 원본 파일: `outputs/scout_player_base_2526/scout_player_base_2526_default.csv`
- 행 수: 2,839
- 컬럼 수: 150
- 시즌: 2025-2026
- 리그: Big5
- 주요 포지션 분포:
  - MF: 1,254
  - DF: 849
  - FW: 542
  - GK: 194

## Cleanup Direction

기본 원칙:

- 선수 식별자, 리그, 팀, 포지션, 나이, 출전 시간, 연봉 컬럼은 우선 신뢰한다.
- 앞쪽 원본 스탯 컬럼 중 일부는 컬럼명과 값이 밀린 흔적이 있으므로 바로 사용하지 않는다.
- `*_per90` 컬럼도 일부 이상치가 있으므로 clipping과 percentile scaling 이후에만 점수 계산에 사용한다.
- Streamlit 화면에서는 원본 CSV를 직접 쓰지 않고 processed CSV를 읽는다.

## Output Dataset

1번 버튼 작업의 첫 산출물은 다음 파일로 잡는다.

- `data/processed/scout_player_view_2526.csv`

이 파일은 이후 2번, 3번, 4번 버튼에서도 공통으로 확장해서 사용한다.

## Column Groups

### 1. Trusted Identity Columns

그대로 사용 가능하다.

- `stats_unique_key` -> `player_id`
- `stats_row_id`
- `Player` -> `player_name`
- `Nation` -> `nation`
- `Squad` -> `team`
- `league_canonical` -> `league`
- `league_country`
- `club_join_key`
- `player_join_key`

### 2. Trusted Player Context Columns

기본 필터에 사용한다.

- `Pos` -> `position`
- `main_position` -> `position_group`
- `Age` -> `age`
- `MP` -> `matches_played`
- `Starts` -> `starts`
- `Min` -> `minutes`
- `90s` -> `nineties`

정리 규칙:

- `age`, `matches_played`, `starts`, `minutes`, `nineties`는 숫자로 변환한다.
- `position_group`은 `FW`, `MF`, `DF`, `GK` 중 하나로 제한한다.
- `minutes <= 0`이거나 `nineties <= 0`인 선수는 점수 계산에서는 제외하거나 `score_available = False`로 표시한다.

### 3. Trusted Salary Columns

2번 버튼 및 필터에 사용한다.

- `salary_match_status`
- `salary_match_score`
- `salary_status`
- `salary_active`
- `salary_loan`
- `salary_verified`
- `salary_annual_gross_eur`
- `salary_total_gross_eur`
- `salary_annual_net_eur`
- `salary_total_net_eur`

정리 규칙:

- 연봉 숫자 컬럼은 numeric 변환한다.
- `salary_match_status != matched`이면 `salary_available = False`로 둔다.
- `salary_annual_gross_eur`가 없으면 `salary_total_gross_eur`로 보조할 수 있지만, 기본 기준은 `salary_annual_gross_eur`로 둔다.
- `salary_active`, `salary_loan`, `salary_verified`는 boolean으로 변환한다.

### 4. Stat Columns Requiring Validation

바로 사용하지 않고 검증 후 점수화한다.

- `Goals_per90`
- `Shots_per90`
- `SoT_per90`
- `SCA_per90`
- `GCA_per90`
- `Tkl_per90`
- `TklWon_per90`
- `TklDef3rd_per90`
- `TklMid3rd_per90`
- `TklAtt3rd_per90`
- `TklDriPast_per90`
- `Press_per90`
- `PresDef3rd_per90`
- `PresMid3rd_per90`
- `PresAtt3rd_per90`
- `Blocks_per90`
- `BlkSh_per90`
- `BlkPass_per90`
- `Int_per90`
- `Tkl+Int_per90`

주의:

- `SCA_per90`, `Press_per90` 등 일부 컬럼은 비정상적으로 큰 값이 확인되었다.
- 따라서 raw 값을 그대로 role score에 넣지 않는다.

## Normalization Rules

### Numeric Conversion

모든 점수 후보 컬럼은 numeric 변환한다.

변환 실패:

- 빈 값은 `NaN`
- 문자열 오류는 `NaN`
- 이후 점수 계산 시 `NaN`은 해당 컬럼의 최저 점수 또는 포지션별 중앙값으로 처리할지 선택한다.

초기 권장:

- 필터용 주요 컬럼: `NaN`이면 제외
- 점수용 스탯 컬럼: 포지션별 중앙값 대체

### Outlier Clipping

역할 점수 계산용 스탯은 포지션 그룹별로 clipping한다.

권장 방식:

- `lower = position_group별 1 percentile`
- `upper = position_group별 99 percentile`
- 값이 범위를 벗어나면 lower/upper로 자른다.

데이터가 작거나 이상치가 심한 컬럼은 5~95 percentile을 검토한다.

### Percentile Scaling

clipping 이후 포지션 그룹별 percentile score를 만든다.

예시:

- `Goals_per90` -> `goals_score`
- `SCA_per90` -> `chance_creation_score_part`
- `Tkl_per90` -> `tackle_score_part`

스코어 범위:

- 0~100

이렇게 해야 FW와 DF처럼 역할이 다른 선수들이 같은 절대값 기준으로 부당하게 비교되지 않는다.

## 1번 버튼용 확정 추가 컬럼

`scout_player_view_2526.csv`에 다음 컬럼을 만든다.

### Base Scores

- `attack_score`
- `shooting_score`
- `chance_creation_score`
- `progressive_pass_score`
- `creative_pass_score`
- `pressing_score`
- `defensive_action_score`
- `ball_winning_score`
- `build_up_score`
- `aerial_defense_score`
- `goalkeeper_score`

### Role Fit Scores

- `role_fit_finisher`
- `role_fit_pressing_forward`
- `role_fit_creative_midfielder`
- `role_fit_progressive_passer`
- `role_fit_ball_winning_midfielder`
- `role_fit_ball_playing_defender`
- `role_fit_defensive_stopper`
- `role_fit_shot_stopper`

### Data Quality Columns

- `score_available`
- `salary_available`
- `minutes_bucket`
- `data_quality_note`

## Initial Role Score Formula

초기 버전은 모델이 아니라 가중 평균 산술식으로 간다.

- `Finisher`
  - `shooting_score * 0.7 + attack_score * 0.3`

- `Pressing Forward`
  - `pressing_score * 0.5 + attack_score * 0.3 + defensive_action_score * 0.2`

- `Creative Midfielder`
  - `chance_creation_score * 0.4 + creative_pass_score * 0.35 + progressive_pass_score * 0.25`

- `Progressive Passer`
  - `progressive_pass_score * 0.55 + build_up_score * 0.45`

- `Ball Winning Midfielder`
  - `ball_winning_score * 0.45 + defensive_action_score * 0.35 + pressing_score * 0.2`

- `Ball Playing Defender`
  - `build_up_score * 0.45 + progressive_pass_score * 0.3 + defensive_action_score * 0.25`

- `Defensive Stopper`
  - `defensive_action_score * 0.45 + aerial_defense_score * 0.3 + ball_winning_score * 0.25`

- `Shot Stopper`
  - `goalkeeper_score`

## Pending Checks Before Generation

실제 생성 전에 확인할 것:

1. 앞쪽 스탯 컬럼 중 패스 관련 컬럼이 밀려 있는지 확인한다.
2. `*_per90` 컬럼의 산출 방식이 올바른지 확인한다.
3. `SCA_per90`, `Press_per90`처럼 이상치가 큰 컬럼을 쓸지, 원본 컬럼에서 다시 계산할지 결정한다.
4. GK 전용 점수에 사용할 수 있는 골키퍼 지표가 충분한지 확인한다.
5. 연봉 미매칭 선수 237명을 화면에서 포함할지 제외할지 결정한다.

## Recommendation

1번 버튼 생성 전에는 다음 순서로 작업한다.

1. 신뢰 컬럼만 추출한 thin view를 만든다.
2. `*_per90` 컬럼 값 범위 리포트를 만든다.
3. 이상치가 심한 컬럼은 제외하거나 다시 계산한다.
4. 최종 사용할 stat column map을 확정한다.
5. 그 다음 `scout_player_view_2526.csv`를 생성한다.

## Implemented Baseline

현재 1번 버튼용 baseline 함수는 다음 파일에 구현한다.

- `src/scout/scout_features.py`
  - `build_scout_player_view_rows`
  - `build_and_save_scout_player_view`

- `src/scout/scout_query.py`
  - `get_role_options`
  - `get_tactical_need_options`
  - `load_scout_player_view`
  - `find_role_based_players`

- `scripts/build_scout_player_view_2526.py`
  - `data/processed/scout_player_view_2526.csv` 생성용 실행 스크립트

현재 구현은 패스 계열 원본 컬럼의 밀림 가능성을 고려해, 안전한 `*_per90` 컬럼만 사용한다.

1차 사용 컬럼:

- `Goals_per90`
- `Shots_per90`
- `SoT_per90`
- `GCA_per90`
- `Tkl_per90`
- `PresAtt3rd_per90`
- `Blocks_per90`
- `BlkSh_per90`
- `BlkPass_per90`
- `Int_per90`

주의:

- `SCA_per90`, `Press_per90`, `TklAtt3rd_per90`, `PKatt_per90`는 이상치가 매우 커서 1차 점수 계산에서 제외했다.
- 패스 전용 신뢰 컬럼이 부족하므로 `creative_pass_score`, `progressive_pass_score`, `build_up_score`는 proxy 점수다.
- 이 한계는 `data_quality_note`의 `passing_proxy_limited`로 표시한다.

## Button 2 Salary Diagnosis Columns

2번 버튼은 `25/26 시즌 스탯 기반 선수 측정`이며, 선수 1명을 선택해 연봉 가치 진단 결과를 보여준다.

초기 구현은 다음 시즌 연봉 예측 모델이 붙기 전에도 UI와 백엔드 계약을 검증할 수 있도록 `baseline_percentile_v1` 예측값을 사용한다.  
향후 ML 모델이 준비되면 같은 컬럼에 모델 예측값을 저장하면 된다.

추가 컬럼:

- `current_salary_annual_gross_eur`
- `performance_percentile_by_position`
- `salary_percentile_by_position`
- `salary_percentile_by_league`
- `minutes_percentile_by_position`
- `salary_efficiency_score`
- `predicted_next_salary_annual_gross_eur`
- `predicted_next_salary_log`
- `prediction_model_version`
- `prediction_confidence`
- `salary_gap_eur`
- `salary_gap_pct`
- `salary_value_score`
- `salary_value_status`
- `salary_value_label`
- `value_reason_summary`

현재 baseline 예측 방식:

1. `overall_role_score`를 같은 포지션 그룹 안에서 percentile로 변환한다.
2. 같은 포지션 그룹의 연봉 분포에서 성능 percentile 위치의 연봉을 baseline 예측 연봉으로 둔다.
3. 현재 연봉과 baseline 예측 연봉의 차이로 저평가, 적정, 고평가를 분류한다.

주의:

- 이 값은 아직 실제 다음 시즌 연봉 예측 모델이 아니다.
- `prediction_model_version`이 `baseline_percentile_v1`이면 프론트는 "모델 연결 전 기준 평가" 또는 내부용 표시로 처리할 수 있다.
- 저연봉 선수는 `salary_gap_pct`가 크게 튈 수 있으므로, 화면에서는 차이율만 단독 강조하지 않는다.
