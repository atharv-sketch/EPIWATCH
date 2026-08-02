from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import shap
from pydantic import BaseModel, Field
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

# Configure a basic logger for the module
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
LOGGER = logging.getLogger(__name__)

# Mapping from textual risk categories to integer labels used by the classifier
RISK_MAPPING: dict[str, int] = {"low": 0, "moderate": 1, "high": 2, "critical": 3}


class ForecastPoint(BaseModel):
    """A single forecast data point produced by Prophet.

    Attributes
    ----------
    ds: str
        The date string of the forecast point (e.g., "2023-01-01").
    yhat: float
        The predicted value.
    yhat_lower: float
        The lower bound of the confidence interval.
    yhat_upper: float
        The upper bound of the confidence interval.
    """

    ds: str
    yhat: float
    yhat_lower: float
    yhat_upper: float


class CountryForecastResult(BaseModel):
    """Container for all forecast points for a single country.

    Parameters
    ----------
    country: str
        ISO‑2 or country name identifier.
    points: list[ForecastPoint]
        List of forecast points ordered by date.
    """

    country: str
    points: list[ForecastPoint]


class ForecastOutput(BaseModel):
    """Top‑level model representing the output of a batch forecast run.

    Attributes
    ----------
    generated_at: str
        ISO‑8601 timestamp when the forecasts were generated.
    forecasts: dict[str, dict[str, Any]]
        Mapping from country name to its forecast dictionary.
    skipped: dict[str, str]
        Countries that were skipped together with the reason.
    """

    generated_at: str
    forecasts: dict[str, dict[str, Any]]
    skipped: dict[str, str]


@dataclass
class ForecastRegistry:
    """Collects successful forecasts and failures during a batch run.

    Attributes
    ----------
    results: dict[str, dict[str, list[Any]]]
        Successful forecasts keyed by country.
    failures: dict[str, str]
        Failure reasons keyed by country.
    """

    results: dict[str, dict[str, list[Any]]] = field(default_factory=dict)
    failures: dict[str, str] = field(default_factory=dict)


class CountryForecaster:
    """Utility class that validates input data and produces a simple linear trend forecast.

    The original implementation uses a handcrafted linear extrapolation rather than Prophet
    to keep the dependency footprint small. The logic is retained unchanged; only documentation
    and comments are added.
    """

    def validate(self, df: pd.DataFrame) -> tuple[bool, str]:
        """Validate a country's time‑series data before forecasting.

        Parameters
        ----------
        df: pd.DataFrame
            DataFrame containing at least a ``rolling_7d_avg`` column.

        Returns
        -------
        tuple[bool, str]
            ``True`` and an empty string if validation passes; otherwise ``False`` and a
            short reason code.
        """
        if len(df) < 30:
            return False, "insufficient_rows_<30"
        numeric_series = pd.to_numeric(df["rolling_7d_avg"], errors="coerce")
        if numeric_series.std(skipna=True) == 0:
            return False, "constant_or_all_zero_signal"
        nan_ratio = float(numeric_series.isna().mean())
        if nan_ratio > 0.5:
            return False, "nan_ratio_>50_percent"
        return True, ""

    def forecast(self, df: pd.DataFrame, periods: int = 30) -> dict[str, list[Any]]:
        """Generate a simple linear‑trend forecast for the next *periods* days.

        The method mirrors the Prophet workflow used elsewhere in the project but
        implements a deterministic linear extrapolation:

        1. Convert ``date`` and ``rolling_7d_avg`` to proper types.
        2. Keep only the most recent 60 days to capture short‑term trends.
        3. Fit a first‑order polynomial (straight line) to the data.
        4. Project the line forward ``periods`` steps, clipping negative values to ``0``.
        5. Derive a naive confidence band by scaling the forecast by ``0.82`` and ``1.18``.
        6. Return the forecast values together with the generated future dates.

        Parameters
        ----------
        df: pd.DataFrame
            Raw country‑level data containing ``date`` and ``rolling_7d_avg`` columns.
        periods: int, optional
            Number of future days to forecast (default is 30).

        Returns
        -------
        dict[str, list[Any]]
            Dictionary with keys ``dates``, ``yhat``, ``yhat_lower``, ``yhat_upper`` and
            ``last_actual``.
        """
        # Prepare data – ensure correct dtypes and drop rows with missing values
        prepared = df.loc[:, ["date", "rolling_7d_avg"]].copy()
        prepared["date"] = pd.to_datetime(prepared["date"], errors="coerce")
        prepared["rolling_7d_avg"] = pd.to_numeric(prepared["rolling_7d_avg"], errors="coerce")
        prepared = prepared.dropna(subset=["date", "rolling_7d_avg"]).sort_values("date").reset_index(drop=True)

        # Use the last 60 days for trend fitting – this smooths out long‑term seasonality
        y = prepared["rolling_7d_avg"].values[-60:]
        x = np.arange(len(y))

        # Fit a linear trend (degree 1 polynomial)
        coeffs = np.polyfit(x, y, 1)
        trend = np.poly1d(coeffs)

        # Project forward for the requested number of periods
        future_x = np.arange(len(y), len(y) + periods)
        yhat = np.maximum(trend(future_x), 0)  # enforce non‑negative forecasts
        yhat_lower = yhat * 0.82
        yhat_upper = yhat * 1.18

        # Generate future date strings matching the input format
        last_date = pd.to_datetime(prepared["date"].iloc[-1])
        future_dates = [
            (last_date + pd.Timedelta(days=i + 1)).strftime("%Y-%m-%d")
            for i in range(periods)
        ]

        return {
            "dates": future_dates,
            "yhat": yhat.tolist(),
            "yhat_lower": yhat_lower.tolist(),
            "yhat_upper": yhat_upper.tolist(),
            "last_actual": float(prepared["rolling_7d_avg"].iloc[-1]),
        }


class ForecastRunner:
    """Orchestrates batch forecasting for all countries in a CSV file.

    It validates each country's data, runs the forecast, and records successes and
    failures in a :class:`ForecastRegistry`. The final output is persisted as JSON.
    """

    def __init__(self) -> None:
        self.country_forecaster = CountryForecaster()
        self.registry = ForecastRegistry()

    def run_all(self, csv_path: Path, out_path: Path, periods: int = 30) -> ForecastOutput:
        """Run forecasts for every country present in ``csv_path``.

        Parameters
        ----------
        csv_path: Path
            Path to the processed CSV containing a ``country`` column.
        out_path: Path
            Destination path for the JSON output.
        periods: int, optional
            Number of future days to forecast (default 30).

        Returns
        -------
        ForecastOutput
            Pydantic model containing the generated forecasts and any skipped countries.
        """
        df = pd.read_csv(csv_path)
        for country, country_df in df.groupby("country", sort=True):
            is_valid, reason = self.country_forecaster.validate(country_df)
            if not is_valid:
                self.registry.failures[country] = reason
                continue
            try:
                self.registry.results[country] = self.country_forecaster.forecast(country_df, periods=periods)
            except Exception as exc:  # noqa: BLE001
                self.registry.failures[country] = f"forecast_error: {exc}"

        output = ForecastOutput(
            generated_at=datetime.now(timezone.utc).isoformat(),
            forecasts=self.registry.results,
            skipped=self.registry.failures,
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output.model_dump_json(indent=2), encoding="utf-8")
        return output


class EpidemicForecaster:
    """High‑level wrapper that loads processed data and provides per‑country forecasts.

    The class mirrors the functionality of :class:`ForecastRunner` but offers a more
    object‑oriented API for interactive use.
    """

    def __init__(self, data_path: Path) -> None:
        self.data_path = data_path
        self.data = self.load_data()
        self.runner = ForecastRunner()
        self.forecasts: dict[str, dict[str, list[Any]]] = {}

    def load_data(self) -> pd.DataFrame:
        """Load the ``processed.csv`` file and ensure dates are parsed.

        Returns
        -------
        pd.DataFrame
            DataFrame sorted by ``country`` and ``date``.
        """
        csv_path = self.data_path / "processed.csv"
        df = pd.read_csv(csv_path)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        return df.sort_values(["country", "date"]).reset_index(drop=True)

    def forecast_country(self, country: str, periods: int = 30) -> dict | None:
        """Forecast a single country.

        Returns ``None`` if the country does not have enough data.
        """
        try:
            df = self.data[self.data["country"] == country].copy()
            df = df.dropna(subset=["rolling_7d_avg"])
            if len(df) < 30:
                return None

            # Re‑use the same linear‑trend logic as ``CountryForecaster.forecast``
            y = df["rolling_7d_avg"].values[-60:]
            x = np.arange(len(y))

            # fit linear trend
            coeffs = np.polyfit(x, y, 1)
            trend = np.poly1d(coeffs)

            # project forward
            future_x = np.arange(len(y), len(y) + periods)
            yhat = np.maximum(trend(future_x), 0)
            yhat_lower = yhat * 0.82
            yhat_upper = yhat * 1.18

            last_date = pd.to_datetime(df["date"].iloc[-1])
            future_dates = [
                (last_date + pd.Timedelta(days=i + 1)).strftime("%Y-%m-%d")
                for i in range(periods)
            ]

            return {
                "dates": future_dates,
                "yhat": yhat.tolist(),
                "yhat_lower": yhat_lower.tolist(),
                "yhat_upper": yhat_upper.tolist(),
                "last_actual": float(df["rolling_7d_avg"].iloc[-1])
            }
        except Exception as e:
            logging.error(f"Forecast failed for {country}: {e}")
            return None

    def forecast_all_countries(self) -> dict[str, dict[str, list[Any]]]:
        """Run forecasts for every country in the dataset.

        Returns
        -------
        dict[str, dict[str, list[Any]]]
            Mapping of country name to its forecast dictionary.
        """
        countries = sorted(self.data["country"].dropna().unique().tolist())
        results: dict[str, dict[str, list[Any]]] = {}
        for idx, country in enumerate(countries, start=1):
            forecast = self.forecast_country(country)
            if forecast is not None:
                results[country] = forecast
            if idx % 10 == 0:
                LOGGER.info("Forecast progress: %s/%s countries processed", idx, len(countries))
        self.forecasts = results
        return results

    def save_forecasts(self, output_path: Path) -> None:
        """Persist the aggregated forecasts to ``output_path`` as JSON.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "forecasts": self.forecasts,
        }
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class RiskClassifier:
    """Trains a RandomForest model to classify risk categories and computes SHAP values.
    """

    def __init__(self, data_path: Path) -> None:
        self.data_path = data_path
        self.data = pd.read_csv(self.data_path / "processed.csv")
        self.feature_names = ["rt_estimate", "case_growth_rate", "vax_coverage", "stringency_index"]
        self.model: RandomForestClassifier | None = None
        self.x_test: pd.DataFrame | None = None
        self.results: dict[str, Any] = {}

    def prepare_features(self) -> tuple[pd.DataFrame, pd.Series]:
        """Prepare feature matrix and target vector for model training.

        Missing values are imputed with the median of each feature.
        """
        features = self.data.loc[:, self.feature_names].apply(pd.to_numeric, errors="coerce")
        medians = features.median(numeric_only=True)
        features = features.fillna(medians)
        target = self.data["risk_category"].astype(str).str.lower().map(RISK_MAPPING)
        valid_rows = target.notna()
        return features.loc[valid_rows], target.loc[valid_rows].astype(int)

    def train(self) -> dict[str, Any]:
        """Train the RandomForest classifier and store performance metrics.
        """
        x, y = self.prepare_features()
        x_train, x_test, y_train, y_test = train_test_split(
            x, y, test_size=0.2, random_state=42, stratify=y
        )
        model = RandomForestClassifier(n_estimators=200, random_state=42)
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        accuracy = float(accuracy_score(y_test, predictions))
        report = classification_report(y_test, predictions, digits=4)
        importances = {
            feature: float(value) for feature, value in zip(self.feature_names, model.feature_importances_)
        }
        self.model = model
        self.x_test = x_test
        self.results = {
            "accuracy": accuracy,
            "classification_report": report,
            "feature_importances": importances,
        }
        return self.results

    def compute_shap_values(self) -> pd.DataFrame:
        """Compute SHAP values for the test set to explain model predictions.
        """
        if self.model is None or self.x_test is None:
            raise RuntimeError("Model must be trained before SHAP computation.")
        explainer = shap.TreeExplainer(self.model)
        shap_values = explainer.shap_values(self.x_test)
        if isinstance(shap_values, list):
            stacked = np.stack(shap_values, axis=0)
            values = np.mean(np.abs(stacked), axis=0)
        else:
            values = np.abs(shap_values)
        if values.ndim == 3:
            values = values.mean(axis=2)
        return pd.DataFrame(values, columns=self.feature_names, index=self.x_test.index)

    def save_results(self, output_dir: Path) -> None:
        """Write model summary and SHAP values to ``output_dir``.
        """
        if not self.results:
            raise RuntimeError("No training results available. Run train() first.")
        output_dir.mkdir(parents=True, exist_ok=True)
        summary = {
            "accuracy": float(self.results["accuracy"]),
            "feature_importances": self.results["feature_importances"],
            "countries_count": int(self.data["country"].nunique()),
            "trained_at": datetime.now(timezone.utc).isoformat(),
        }
        (output_dir / "model_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        shap_df = self.compute_shap_values()
        shap_df.to_csv(output_dir / "shap_values.csv", index=False)


def main() -> None:
    """Entry‑point for the module when executed as a script.

    It runs the full forecasting pipeline, saves the results, and trains the risk
    classifier, logging progress along the way.
    """
    root = Path(__file__).resolve().parents[1]
    data_dir = root / "data"

    os.environ["PYTHONWARNINGS"] = "ignore"

    forecaster = EpidemicForecaster(data_dir)
    all_forecasts = forecaster.forecast_all_countries()
    forecaster.save_forecasts(data_dir / "forecasts.json")
    LOGGER.info("Saved forecasts for %s countries", len(all_forecasts))

    runner = ForecastRunner()
    runner.run_all(data_dir / "processed.csv", data_dir / "forecasts_registry.json")

    classifier = RiskClassifier(data_dir)
    train_results = classifier.train()
    classifier.save_results(data_dir)
    LOGGER.info("Model trained successfully. Accuracy: %.4f", train_results["accuracy"])


if __name__ == "__main__":
    main()
