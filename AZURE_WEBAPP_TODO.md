# Azure Web App TODO

이 문서는 기존 `app.py`, `requirements.txt`, `README.md`, `.gitignore`를 직접 수정하지 않고 Azure Web App 배포에 필요한 작업을 정리한다.

## 1. Azure Web App 배포 전 확인사항

- GitHub에는 코드와 예시 설정만 올린다.
- Azure OpenAI API Key, Blob Storage Connection String, `.streamlit/secrets.toml`은 GitHub에 올리지 않는다.
- Azure Web App의 Application Settings에 운영 환경변수를 등록한다.
- 로컬 개발에서는 `.streamlit/secrets.toml.example`을 참고해 직접 `.streamlit/secrets.toml`을 만들 수 있다.

## 2. Required Application Settings

```text
AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_API_KEY
AZURE_OPENAI_DEPLOYMENT
AZURE_OPENAI_API_VERSION
AZURE_STORAGE_CONNECTION_STRING
AZURE_STORAGE_CONTAINER
```

권장 추가 설정:

```text
SCOUT_BACKEND_DATASET_BLOB=01_scout_app/scouter_backend_player_dataset_2025_2026.csv
COACH_BACKEND_DATASET_BLOB=02_coach_app/coach_players_25_26_v1.csv
SCOUT_ONNX_INPUT_DATASET_BLOB=03_scout_model_input/scouter_onnx_salary_model_input_2025_2026.csv
SALARY_ONNX_MODEL_BLOB=04_model/salary_prediction_model.onnx
```

주의: Azure OpenAI SDK의 `model` 인자에는 실제 모델명이 아니라 Azure OpenAI Deployment name인 `AZURE_OPENAI_DEPLOYMENT` 값을 넣어야 한다.

## 3. Startup Command Candidates

Azure Web App Startup Command 후보:

```text
bash startup.azure.sh
```

또는:

```text
python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0
```

## 4. Blob Storage Path Structure

현재 배포 기준 Blob 구조:

```text
container: money-football-data

01_scout_app/
02_coach_app/
03_scout_model_input/
04_model/
```

현재 코드/문서에서 사용하는 대표 경로:

```text
01_scout_app/scouter_backend_player_dataset_2025_2026.csv
02_coach_app/coach_players_25_26_v1.csv
03_scout_model_input/scouter_onnx_salary_model_input_2025_2026.csv
04_model/salary_prediction_model.onnx
```

## 5. requirements.txt 병합 후보

기존 `requirements.txt`를 직접 수정하지 않았으므로, Azure 배포 시 아래 파일을 기준으로 병합 여부를 검토한다.

```text
requirements.azure.txt
```

추가 필요 패키지:

```text
azure-storage-blob
openai
onnxruntime
joblib
shap
scikit-learn==1.6.1
```

## 6. .gitignore 추가 후보

기존 `.gitignore`를 직접 수정하지 않았다. 배포 전 아래 항목 추가를 검토한다.

```text
.streamlit/secrets.toml
.env
*.key
**/__pycache__/
*.pyc
.venv/
venv/
```

## 7. Local Test

1. `.streamlit/secrets.toml.example`을 참고해 로컬에 `.streamlit/secrets.toml`을 직접 만든다.
2. 패키지를 설치한다.

```powershell
pip install -r requirements.azure.txt
```

3. Streamlit을 실행한다.

```powershell
python -m streamlit run app.py
```

4. 별도 테스트 페이지에 접속해 Blob CSV, Azure OpenAI, ONNX 모델 로드를 확인한다.

```text
pages/99_Azure_Connection_Test.py
```

## 8. Azure Web App Test Order

1. Application Settings 입력
2. Startup Command 설정
3. GitHub Deployment Center 연결
4. Web App 접속
5. Azure 연결 테스트 페이지에서 환경변수 True/False 확인
6. Blob CSV 로드 확인
7. Azure OpenAI 코멘트 생성 확인
8. ONNX 모델 IO 정보 확인

## 9. 기존 파일 미수정으로 남긴 항목

- `requirements.txt`에 Azure 배포 패키지를 병합할지 검토 필요
- `.gitignore`에 `.streamlit/secrets.toml`, `.env` 등을 추가할지 검토 필요
- `README.md`에 Azure Web App 배포 절차를 추가할지 검토 필요
- 기존 `app.py`의 커스텀 페이지 라우팅에 Azure 테스트 페이지를 연결할지 검토 필요
