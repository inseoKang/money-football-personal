"""Salary value evaluation for scout Button 2."""

from __future__ import annotations

import csv
import io
import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.scout.azure_blob_loader import ScoutBlobLoader, scout_blob_paths
from src.scout.scout_features import parse_float


VALUE_STATUS_LABELS = {
    "undervalued": "저평가",
    "fair": "적정",
    "overvalued": "고평가",
    "unknown": "평가 불가",
}


@dataclass(frozen=True)
class SalaryModelAssets:
    """Local paths and metadata needed for salary prediction/explanation."""

    onnx_model_path: Path
    sklearn_model_path: Path | None
    config: dict[str, Any]


class SalaryValueService:
    """Evaluate current salary value with ONNX prediction and optional SHAP."""

    def __init__(
        self,
        backend_rows: list[dict[str, str]],
        onnx_input_rows: list[dict[str, str]],
        assets: SalaryModelAssets,
    ) -> None:
        if len(backend_rows) != len(onnx_input_rows):
            raise ValueError(
                "backend_rows and onnx_input_rows must have the same length; "
                "the current Blob contract joins them by row order"
            )
        self.backend_rows = backend_rows
        self.onnx_input_rows = onnx_input_rows
        self.assets = assets
        self.feature_columns = list(assets.config.get("all_feature_columns") or [])
        if not self.feature_columns:
            raise ValueError("model_config.json must include all_feature_columns")
        self._onnx_session = None
        self._sklearn_model = None
        self._shap_explainer = None

    @classmethod
    def from_blob(cls, loader: ScoutBlobLoader | None = None) -> "SalaryValueService":
        """Build a service from configured Azure Blob assets."""
        blob_loader = loader or ScoutBlobLoader()
        paths = scout_blob_paths()

        backend_rows = _read_csv_text(blob_loader.download_text(paths["backend_dataset"]))
        onnx_rows = _read_csv_text(blob_loader.download_text(paths["onnx_input_dataset"]))
        config = json.loads(blob_loader.download_text(paths["salary_model_config"], encoding="utf-8"))
        onnx_path = blob_loader.download_to_cache(paths["salary_onnx_model"], "salary_prediction_model.onnx")
        sklearn_path = blob_loader.download_to_cache(paths["salary_sklearn_model"], "salary_prediction_model.pkl")

        return cls(
            backend_rows,
            onnx_rows,
            SalaryModelAssets(onnx_model_path=onnx_path, sklearn_model_path=sklearn_path, config=config),
        )

    @classmethod
    def from_local_files(
        cls,
        backend_dataset_path: str | Path,
        onnx_input_dataset_path: str | Path,
        onnx_model_path: str | Path,
        model_config_path: str | Path,
        sklearn_model_path: str | Path | None = None,
    ) -> "SalaryValueService":
        """Build a service from local files for smoke tests and development."""
        backend_rows = _read_csv_path(backend_dataset_path)
        onnx_rows = _read_csv_path(onnx_input_dataset_path)
        config = json.loads(Path(model_config_path).read_text(encoding="utf-8"))
        assets = SalaryModelAssets(
            onnx_model_path=Path(onnx_model_path),
            sklearn_model_path=Path(sklearn_model_path) if sklearn_model_path else None,
            config=config,
        )
        return cls(backend_rows, onnx_rows, assets)

    def get_player_search_options(self, keyword: str = "", limit: int = 20) -> list[dict[str, object]]:
        """Return lightweight player options for frontend autocomplete/selectbox.

        If keyword is blank, return the first `limit` players from the same
        backend dataset used by the salary-value model. This keeps Button 2
        frontend selection and backend evaluation aligned.
        """
        needle = str(keyword or "").strip().lower()

        results: list[dict[str, object]] = []

        for row in self.backend_rows:
            name = row.get("player_name", "")

            if needle and needle not in name.lower():
                continue

            results.append(
                {
                    "player_id": row.get("player_id", ""),
                    "player_name": name,
                    "team": row.get("team", ""),
                    "league": row.get("league", ""),
                    "position_group": row.get("position_group", ""),
                    "age": _number(row.get("age")),
                    "label": _player_label(row),
                }
            )

            if len(results) >= limit:
                break

        return results

    def evaluate_player_value(
        self,
        player_id: str | None = None,
        player_name: str | None = None,
        include_shap: bool = True,
        top_features: int = 5,
    ) -> dict[str, object]:
        """Return Button 2 salary value evaluation for one player."""
        index, player = self._find_player(player_id=player_id, player_name=player_name)
        feature_row = self.onnx_input_rows[index]
        features = self._feature_array(feature_row)

        predicted_salary = self._predict_salary(features)
        current_salary = (
            parse_float(player.get("current_salary_annual_gross_eur"))
            or parse_float(player.get("salary_annual_gross_eur"))
            or 0.0
        )
        gap_eur = predicted_salary - current_salary if current_salary > 0 else None
        gap_pct = gap_eur / current_salary if gap_eur is not None and current_salary > 0 else None
        status = _classify_value(gap_pct)

        result: dict[str, object] = {
            "player_id": player.get("player_id", ""),
            "player_name": player.get("player_name", ""),
            "team": player.get("team", ""),
            "league": player.get("league", ""),
            "position_group": player.get("position_group", ""),
            "age": _number(player.get("age")),
            "minutes": _number(player.get("minutes")),
            "current_salary_annual_gross_eur": round(current_salary),
            "predicted_next_salary_annual_gross_eur": round(predicted_salary),
            "salary_gap_eur": round(gap_eur) if gap_eur is not None else None,
            "salary_gap_pct": round(gap_pct * 100, 2) if gap_pct is not None else None,
            "salary_value_status": status,
            "salary_value_label": VALUE_STATUS_LABELS[status],
            "prediction_model_version": self.assets.config.get("model_version", ""),
            "prediction_model_name": self.assets.config.get("model_name", ""),
            "prediction_r2_score": self.assets.config.get("r2_score"),
            "explanation": _build_value_summary(status, gap_pct),
            "warnings": self._row_warnings(player, feature_row),
        }

        if include_shap:
            result["shap_explanation"] = self.explain_prediction(features, top_features=top_features)
        return result

    def explain_prediction(self, features: list[float], top_features: int = 5) -> dict[str, object]:
        """Return SHAP feature contributions for one feature row.

        SHAP is optional at runtime. If the package or pkl model is unavailable,
        the response stays API-safe with explanation_available=false.
        """
        if self.assets.sklearn_model_path is None:
            return {"explanation_available": False, "reason": "sklearn_model_path_missing"}

        try:
            import numpy as np
            import shap
        except ImportError as exc:
            return {"explanation_available": False, "reason": f"missing_dependency:{exc.name}"}

        model = self._load_sklearn_model()
        if self._shap_explainer is None:
            self._shap_explainer = shap.TreeExplainer(model)

        matrix = np.asarray([features], dtype=float)
        shap_values = self._shap_explainer.shap_values(matrix)
        values = shap_values[0] if getattr(shap_values, "ndim", 1) > 1 else shap_values
        base_value = self._shap_explainer.expected_value
        if isinstance(base_value, (list, tuple)):
            base_value = base_value[0]
        if hasattr(base_value, "item"):
            base_value = base_value.item()

        ranked = sorted(
            zip(self.feature_columns, features, values),
            key=lambda item: abs(float(item[2])),
            reverse=True,
        )[:top_features]
        return {
            "explanation_available": True,
            "base_value_log_salary": round(float(base_value), 6),
            "top_features": [
                {
                    "feature": feature,
                    "value": round(float(value), 6),
                    "contribution_log_salary": round(float(contribution), 6),
                    "direction": "increase" if float(contribution) >= 0 else "decrease",
                }
                for feature, value, contribution in ranked
            ],
        }

    def _find_player(self, player_id: str | None, player_name: str | None) -> tuple[int, dict[str, str]]:
        if player_id:
            for index, row in enumerate(self.backend_rows):
                if row.get("player_id") == player_id:
                    return index, row
        if player_name:
            target = player_name.strip().lower()
            for index, row in enumerate(self.backend_rows):
                if row.get("player_name", "").strip().lower() == target:
                    return index, row
        raise ValueError("player_id or exact player_name was not found")

    def _feature_array(self, feature_row: dict[str, str]) -> list[float]:
        missing = [column for column in self.feature_columns if column not in feature_row]
        if missing:
            raise ValueError(f"ONNX input dataset is missing columns: {missing}")
        return [float(parse_float(feature_row.get(column)) or 0.0) for column in self.feature_columns]

    def _predict_salary(self, features: list[float]) -> float:
        try:
            import numpy as np
            import onnxruntime as ort
        except ImportError as exc:
            raise RuntimeError(f"missing dependency for ONNX salary prediction: {exc.name}") from exc

        if self._onnx_session is None:
            self._onnx_session = ort.InferenceSession(
                str(self.assets.onnx_model_path),
                providers=["CPUExecutionProvider"],
            )

        input_name = self._onnx_session.get_inputs()[0].name
        output = self._onnx_session.run(None, {input_name: np.asarray([features], dtype=np.float32)})[0]
        raw_prediction = float(output.reshape(-1)[0])
        if self.assets.config.get("target_transform") == "log1p":
            return float(math.expm1(raw_prediction))
        return raw_prediction

    def _load_sklearn_model(self) -> Any:
        if self._sklearn_model is None:
            import joblib

            self._sklearn_model = joblib.load(self.assets.sklearn_model_path)
        return self._sklearn_model

    def _row_warnings(self, player: dict[str, str], feature_row: dict[str, str]) -> list[str]:
        warnings: list[str] = []
        if player.get("data_quality_note"):
            warnings.append(player["data_quality_note"])
        if not player.get("player_id"):
            warnings.append("player_id_missing")
        if len(feature_row) != len(self.feature_columns):
            warnings.append("feature_column_count_mismatch")
        return warnings


def _read_csv_text(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


@lru_cache(maxsize=1)
def get_salary_value_service() -> SalaryValueService:
    """Return a process-local cached SalaryValueService from Blob assets."""
    return SalaryValueService.from_blob()


def _read_csv_path(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _number(value: object) -> float | int | None:
    parsed = parse_float(value)
    if parsed is None:
        return None
    return int(parsed) if float(parsed).is_integer() else parsed


def _player_label(row: dict[str, str]) -> str:
    parts = [
        row.get("player_name", ""),
        row.get("team", ""),
        row.get("league", ""),
        row.get("position_group", ""),
        f"{row.get('age')}세" if row.get("age") else "",
    ]
    return " · ".join(part for part in parts if part)


def _classify_value(gap_pct: float | None) -> str:
    if gap_pct is None:
        return "unknown"
    if gap_pct >= 0.20:
        return "undervalued"
    if gap_pct <= -0.20:
        return "overvalued"
    return "fair"


def _build_value_summary(status: str, gap_pct: float | None) -> str:
    if gap_pct is None:
        return "현재 연봉 또는 예측값이 부족해 평가를 확정할 수 없습니다."
    label = VALUE_STATUS_LABELS[status]
    return f"모델 예측 연봉과 현재 연봉의 차이를 기준으로 {label}로 분류했습니다."
