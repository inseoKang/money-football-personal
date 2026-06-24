from __future__ import annotations

import streamlit as st

from components.layout import page_title
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
    "AZURE_STORAGE_CONTAINER_NAME",
]


def render() -> None:
    st.session_state.current_page = "azure_connection_test"

    page_title(
        "Azure 연결 테스트",
        "Azure Blob Storage, Azure OpenAI, ONNX 모델 연결 상태를 확인합니다.",
    )

    st.warning(
        "이 페이지는 개발/배포 확인용입니다. 실제 서비스 메뉴에는 노출하지 않는 것을 권장합니다."
    )

    st.subheader("환경 변수 확인")
    st.dataframe(
        [{"key": key, "configured": has_secret(key)} for key in ENV_KEYS],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.subheader("Blob Storage CSV 테스트")
    blob_path = st.text_input(
        "Blob path",
        value="02_scout_app/scouter_backend_player_dataset_2025_2026.csv",
    )

    if st.button("스카우터 데이터 불러오기", use_container_width=True):
        try:
            df = load_csv_from_blob(blob_path)
            st.success(f"CSV 로드 성공: {df.shape[0]} rows x {df.shape[1]} columns")
            st.dataframe(df.head(), use_container_width=True)
        except Exception as exc:
            st.error(str(exc))

    st.divider()

    st.subheader("Azure OpenAI 테스트")

    test_prompt = st.text_area(
        "테스트 프롬프트",
        value="Barcelona의 4-3-3 라인업 강점을 3문장으로 설명해줘.",
        height=100,
    )

    if st.button("AI 코멘트 생성", use_container_width=True):
        try:
            comment = generate_comment(test_prompt)
            st.success("Azure OpenAI 호출 성공")
            st.write(comment)
        except Exception as exc:
            st.error(str(exc))

    st.divider()

    st.subheader("ONNX 모델 로드 테스트")

    if st.button("ONNX 모델 로드 확인", use_container_width=True):
        try:
            st.json(get_salary_model_io_info())
        except Exception as exc:
            st.error(str(exc))