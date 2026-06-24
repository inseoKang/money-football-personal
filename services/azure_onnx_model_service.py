"""ONNX salary model loader for Azure Blob Storage."""

from __future__ import annotations

import tempfile

import numpy as np

from services.azure_blob_service import load_binary_from_blob
from services.azure_config import get_secret


DEFAULT_MODEL_BLOB = "04_model/salary_prediction_model.onnx"
MODEL_BLOB_ENV = "SALARY_ONNX_MODEL_BLOB"


def _cache_resource(func):
    try:
        import streamlit as st

        return st.cache_resource(show_spinner=False)(func)
    except Exception:
        return func


@_cache_resource
def load_salary_model():
    """Load the salary ONNX model from Blob Storage into an InferenceSession."""
    try:
        import onnxruntime as ort
    except ImportError as exc:
        raise RuntimeError("onnxruntime is not installed") from exc

    blob_path = get_secret(MODEL_BLOB_ENV, DEFAULT_MODEL_BLOB)
    try:
        model_bytes = load_binary_from_blob(blob_path)
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".onnx")
        temp.write(model_bytes)
        temp.close()
        return ort.InferenceSession(temp.name, providers=["CPUExecutionProvider"])
    except Exception as exc:
        raise RuntimeError(f"Failed to load ONNX model from '{blob_path}': {exc}") from exc


def get_salary_model_io_info() -> dict[str, object]:
    """Return ONNX model input/output names and shapes."""
    session = load_salary_model()
    inputs = session.get_inputs()
    outputs = session.get_outputs()
    return {
        "inputs": [{"name": item.name, "shape": item.shape, "type": item.type} for item in inputs],
        "outputs": [{"name": item.name, "shape": item.shape, "type": item.type} for item in outputs],
    }


def predict_salary(input_array: np.ndarray):
    """Run salary prediction with the loaded ONNX model."""
    session = load_salary_model()
    try:
        features = np.asarray(input_array, dtype=np.float32)
        input_name = session.get_inputs()[0].name
        return session.run(None, {input_name: features})
    except Exception as exc:
        raise RuntimeError(f"ONNX salary prediction failed: {exc}") from exc
