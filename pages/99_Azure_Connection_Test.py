from __future__ import annotations

import streamlit as st

from services.azure_blob_service import load_csv_from_blob
from services.azure_config import has_secret
from services.azure_onnx_model_service import get_salary_model_io_info
from services.azure_openai_service import generate_comment


ENV_KEYS = [
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_DEPLOYMENT",
    "AZURE_OPENAI_API_VERSION",
    "AZURE_STORAGE_CONNECTION_STRING",
    "AZURE_STORAGE_CONTAINER",
]


st.set_page_config(page_title="Money Football Azure Test", layout="wide")
st.title("Money Football Azure 연결 테스트")

st.subheader("환경 변수 확인")
st.dataframe(
    [{"key": key, "configured": has_secret(key)} for key in ENV_KEYS],
    use_container_width=True,
)

st.subheader("Blob Storage CSV 테스트")
blob_path = st.text_input(
    "Blob path",
    value="01_scout_app/scouter_backend_player_dataset_2025_2026.csv",
)
if st.button("스카우터 데이터 불러오기"):
    try:
        df = load_csv_from_blob(blob_path)
        st.success(f"CSV 로드 성공: {df.shape[0]} rows x {df.shape[1]} columns")
        st.dataframe(df.head(), use_container_width=True)
    except Exception as exc:
        st.error(str(exc))

st.subheader("Azure OpenAI 테스트")
if st.button("AI 코멘트 생성"):
    try:
        comment = generate_comment("한국 축구 대표팀의 강점을 3문장으로 설명해줘.")
        st.write(comment)
    except Exception as exc:
        st.error(str(exc))

st.subheader("ONNX 모델 로드 테스트")
if st.button("ONNX 모델 로드 확인"):
    try:
        st.json(get_salary_model_io_info())
    except Exception as exc:
        st.error(str(exc))
