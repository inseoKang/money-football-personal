# Scout Azure Blob Environment

스카우터 백엔드는 큰 CSV와 모델 파일을 Git에 포함하지 않고 Azure Blob Storage에서 읽는다.

## Blob Layout

```text
container: money-football-data

01_scout_app/
  scouter_backend_player_dataset_2025_2026.csv

03_scout_model_input/
  scouter_onnx_salary_model_input_2025_2026.csv

04_model/
  model_config.json
  salary_prediction_model.onnx
  salary_prediction_model.pkl
```

## Required Environment Variables

```text
AZURE_STORAGE_CONNECTION_STRING=<do not commit>
AZURE_STORAGE_CONTAINER_NAME=money-football-data

SCOUT_BACKEND_DATASET_BLOB=01_scout_app/scouter_backend_player_dataset_2025_2026.csv
SCOUT_ONNX_INPUT_DATASET_BLOB=03_scout_model_input/scouter_onnx_salary_model_input_2025_2026.csv

SALARY_MODEL_CONFIG_BLOB=04_model/model_config.json
SALARY_ONNX_MODEL_BLOB=04_model/salary_prediction_model.onnx
SALARY_SKLEARN_MODEL_BLOB=04_model/salary_prediction_model.pkl
```

The code has the non-secret Blob paths above as defaults, so only the connection
string and container name are strictly required in local development.

## Asset Roles

- `01_scout_app/scouter_backend_player_dataset_2025_2026.csv`
  - 화면 표시, 검색, API 응답, 유사 선수 탐색 기준 데이터셋.
- `03_scout_model_input/scouter_onnx_salary_model_input_2025_2026.csv`
  - ONNX 모델에 통과시키는 24개 feature 입력 데이터셋.
- `04_model/salary_prediction_model.onnx`
  - 2번 버튼의 다음 시즌 연봉 예측에 사용.
- `04_model/salary_prediction_model.pkl`
  - SHAP 설명값 계산에 사용.
- `04_model/model_config.json`
  - feature 순서, target transform, 모델 메타데이터 확인에 사용.

## Important Contract

현재 `01_scout_app` CSV와 `03_scout_model_input` CSV는 같은 원천에서 같은 순서로 생성되었다는 전제로 row index를 맞춘다.

장기적으로는 모델 입력 CSV에도 `player_id`를 포함한 별도 매핑 파일을 두는 방식이 더 안전하다. 단, ONNX에 넣는 실제 입력은 `model_config.json`의 `all_feature_columns` 24개만 사용해야 한다.

## Runtime Notes

- ONNX 예측 결과는 `model_config.json`의 `target_transform=log1p` 기준으로 `expm1` 후처리를 적용해 EUR 연봉으로 복원한다.
- SHAP은 `salary_prediction_model.pkl`을 로드하므로 학습 당시 버전과 맞추기 위해 `scikit-learn==1.6.1`을 사용한다.
- Blob 파일은 앱 런타임의 임시/cache 디렉터리에 내려받아 사용한다.
