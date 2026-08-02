from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="EpiWatch API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Module-level loaded data
processed_df: pd.DataFrame | None = None
country_latest_df: pd.DataFrame | None = None
forecasts_dict: dict[str, Any] = {}
model_summary_dict: dict[str, Any] = {}
shap_df: pd.DataFrame | None = None
data_loaded_at: str | None = None

# Approximate global country coordinates for map rendering.
COUNTRY_COORDINATES: dict[str, tuple[float, float]] = {
    "Afghanistan": (33.9391, 67.71),
    "Albania": (41.1533, 20.1683),
    "Algeria": (28.0339, 1.6596),
    "Argentina": (-38.4161, -63.6167),
    "Australia": (-25.2744, 133.7751),
    "Austria": (47.5162, 14.5501),
    "Bangladesh": (23.685, 90.3563),
    "Belgium": (50.5039, 4.4699),
    "Bolivia": (-16.2902, -63.5887),
    "Brazil": (-14.235, -51.9253),
    "Bulgaria": (42.7339, 25.4858),
    "Cambodia": (12.5657, 104.991),
    "Cameroon": (7.3697, 12.3547),
    "Canada": (56.1304, -106.3468),
    "Chile": (-35.6751, -71.543),
    "China": (35.8617, 104.1954),
    "Colombia": (4.5709, -74.2973),
    "Costa Rica": (9.7489, -83.7534),
    "Croatia": (45.1, 15.2),
    "Cuba": (21.5218, -77.7812),
    "Czechia": (49.8175, 15.473),
    "Denmark": (56.2639, 9.5018),
    "Dominican Republic": (18.7357, -70.1627),
    "Ecuador": (-1.8312, -78.1834),
    "Egypt": (26.8206, 30.8025),
    "Ethiopia": (9.145, 40.4897),
    "Finland": (61.9241, 25.7482),
    "France": (46.2276, 2.2137),
    "Germany": (51.1657, 10.4515),
    "Ghana": (7.9465, -1.0232),
    "Greece": (39.0742, 21.8243),
    "Guatemala": (15.7835, -90.2308),
    "Haiti": (18.9712, -72.2852),
    "Honduras": (15.2, -86.2419),
    "Hungary": (47.1625, 19.5033),
    "India": (20.5937, 78.9629),
    "Indonesia": (-0.7893, 113.9213),
    "Iran": (32.4279, 53.688),
    "Iraq": (33.2232, 43.6793),
    "Ireland": (53.4129, -8.2439),
    "Israel": (31.0461, 34.8516),
    "Italy": (41.8719, 12.5674),
    "Japan": (36.2048, 138.2529),
    "Jordan": (30.5852, 36.2384),
    "Kenya": (-0.0236, 37.9062),
    "Lebanon": (33.8547, 35.8623),
    "Libya": (26.3351, 17.2283),
    "Malaysia": (4.2105, 101.9758),
    "Mexico": (23.6345, -102.5528),
    "Morocco": (31.7917, -7.0926),
    "Myanmar": (21.9162, 95.956),
    "Nepal": (28.3949, 84.124),
    "Netherlands": (52.1326, 5.2913),
    "New Zealand": (-40.9006, 174.886),
    "Nigeria": (9.082, 8.6753),
    "Norway": (60.472, 8.4689),
    "Pakistan": (30.3753, 69.3451),
    "Peru": (-9.19, -75.0152),
    "Philippines": (12.8797, 121.774),
    "Poland": (51.9194, 19.1451),
    "Portugal": (39.3999, -8.2245),
    "Romania": (45.9432, 24.9668),
    "Russia": (61.524, 105.3188),
    "Saudi Arabia": (23.8859, 45.0792),
    "South Africa": (-30.5595, 22.9375),
    "South Korea": (35.9078, 127.7669),
    "Spain": (40.4637, -3.7492),
    "Sri Lanka": (7.8731, 80.7718),
    "Sweden": (60.1282, 18.6435),
    "Switzerland": (46.8182, 8.2275),
    "Thailand": (15.87, 100.9925),
    "Tunisia": (33.8869, 9.5375),
    "Turkey": (38.9637, 35.2433),
    "Ukraine": (48.3794, 31.1656),
    "United Arab Emirates": (23.4241, 53.8478),
    "United Kingdom": (55.3781, -3.436),
    "United States": (37.0902, -95.7129),
    "Uruguay": (-32.5228, -55.7658),
    "Venezuela": (6.4238, -66.5897),
    "Vietnam": (14.0583, 108.2772),
}


class CountryRisk(BaseModel):
    country: str
    risk_score: float
    risk_category: str
    rt_estimate: float
    vax_coverage: float
    last_updated: str


class CountryDetail(CountryRisk):
    forecast_dates: list[str]
    forecast_values: list[float]
    forecast_lower: list[float]
    forecast_upper: list[float]
    historical_dates: list[str]
    historical_cases: list[float]
    shap_features: dict[str, float]


class RiskMapEntry(BaseModel):
    country: str
    latitude: float
    longitude: float
    risk_score: float
    risk_category: str
    population: float


class WhatIfResult(BaseModel):
    country: str
    current_risk_score: float
    simulated_risk_score: float
    current_risk_category: str
    simulated_risk_category: str
    delta: float
    explanation: str


class FeatureImportance(BaseModel):
    feature: str
    importance: float


class GlobalStats(BaseModel):
    total_countries: int
    critical_count: int
    high_count: int
    moderate_count: int
    low_count: int
    global_avg_rt: float
    global_avg_risk_score: float
    highest_risk_country: str
    last_updated: str


def _risk_formula(rt_estimate: float, case_growth_rate: float, vax_coverage: float, stringency_index: float) -> float:
    # Reuses the linear relationship inferred from the processed pipeline output.
    score = (
        29.022729039829784
        + (13.364094247477302 * rt_estimate)
        + (0.05146151005445207 * case_growth_rate)
        - (0.19375330165780824 * vax_coverage)
        - (0.009735401842249095 * stringency_index)
    )
    return float(max(0.0, min(100.0, score)))


def _score_to_category(score: float) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "moderate"
    return "low"


def _require_data_loaded() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if processed_df is None or country_latest_df is None or shap_df is None:
        raise HTTPException(status_code=503, detail="Data not loaded yet")
    return processed_df, country_latest_df, shap_df


def _latest_row_for_country(country_name: str) -> pd.Series:
    _, latest, _ = _require_data_loaded()
    matches = latest[latest["country"].astype(str).str.lower() == country_name.lower()]
    if matches.empty:
        raise HTTPException(status_code=404, detail=f"Country '{country_name}' not found")
    return matches.iloc[0]


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next: Any) -> Any:
    start = datetime.now(timezone.utc)
    response = await call_next(request)
    duration_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000
    LOGGER.info(
        "request method=%s path=%s status=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.on_event("startup")
def load_data_on_startup() -> None:
    global processed_df, country_latest_df, forecasts_dict, model_summary_dict, shap_df, data_loaded_at
    data_dir = Path(__file__).resolve().parents[1] / "data"
    processed_df = pd.read_csv(data_dir / "processed.csv")
    processed_df["date"] = pd.to_datetime(processed_df["date"], errors="coerce")
    country_latest_df = pd.read_csv(data_dir / "country_latest.csv")
    country_latest_df["date"] = pd.to_datetime(country_latest_df["date"], errors="coerce")
    forecasts_dict = json.loads((data_dir / "forecasts.json").read_text(encoding="utf-8"))
    model_summary_dict = json.loads((data_dir / "model_summary.json").read_text(encoding="utf-8"))
    shap_df = pd.read_csv(data_dir / "shap_values.csv")
    data_loaded_at = datetime.now(timezone.utc).isoformat()
    LOGGER.info("Loaded API data from %s", data_dir)


@app.get("/api/health")
def health() -> dict[str, str]:
    _require_data_loaded()
    return {"status": "ok", "data_loaded_at": data_loaded_at or datetime.now(timezone.utc).isoformat()}


@app.get("/api/countries", response_model=list[CountryRisk])
def list_countries() -> list[CountryRisk]:
    _, latest, _ = _require_data_loaded()
    sorted_latest = latest.sort_values("risk_score", ascending=False)
    result: list[CountryRisk] = []
    for _, row in sorted_latest.iterrows():
        result.append(
            CountryRisk(
                country=str(row["country"]),
                risk_score=float(row["risk_score"]),
                risk_category=str(row["risk_category"]),
                rt_estimate=float(row["rt_estimate"]),
                vax_coverage=float(row["vax_coverage"]),
                last_updated=pd.to_datetime(row["date"]).strftime("%Y-%m-%d"),
            )
        )
    return result


@app.get("/api/country/{country_name}", response_model=CountryDetail)
def country_detail(country_name: str) -> CountryDetail:
    processed, _, shap_values = _require_data_loaded()
    row = _latest_row_for_country(country_name)
    country_rows = (
        processed[processed["country"].astype(str).str.lower() == country_name.lower()]
        .sort_values("date")
        .tail(90)
    )
    forecasts_data = forecasts_dict.get("forecasts", {}).get(str(row["country"]), {})
    shap_means = shap_values.mean(numeric_only=True).to_dict()
    return CountryDetail(
        country=str(row["country"]),
        risk_score=float(row["risk_score"]),
        risk_category=str(row["risk_category"]),
        rt_estimate=float(row["rt_estimate"]),
        vax_coverage=float(row["vax_coverage"]),
        last_updated=pd.to_datetime(row["date"]).strftime("%Y-%m-%d"),
        forecast_dates=[str(x) for x in forecasts_data.get("dates", [])],
        forecast_values=[float(x) for x in forecasts_data.get("yhat", [])],
        forecast_lower=[float(x) for x in forecasts_data.get("yhat_lower", [])],
        forecast_upper=[float(x) for x in forecasts_data.get("yhat_upper", [])],
        historical_dates=[d.strftime("%Y-%m-%d") for d in pd.to_datetime(country_rows["date"], errors="coerce")],
        historical_cases=[float(v) for v in pd.to_numeric(country_rows["rolling_7d_avg"], errors="coerce").fillna(0.0)],
        shap_features={str(k): float(v) for k, v in shap_means.items()},
    )


@app.get("/api/risk-map", response_model=list[RiskMapEntry])
def risk_map() -> list[RiskMapEntry]:
    _, latest, _ = _require_data_loaded()
    rows: list[RiskMapEntry] = []
    for _, row in latest.iterrows():
        country_name = str(row["country"])
        if country_name not in COUNTRY_COORDINATES:
            continue
        lat, lon = COUNTRY_COORDINATES[country_name]
        rows.append(
            RiskMapEntry(
                country=country_name,
                latitude=float(lat),
                longitude=float(lon),
                risk_score=float(row["risk_score"]),
                risk_category=str(row["risk_category"]),
                population=float(row["population"]),
            )
        )
    return rows


@app.get("/api/what-if", response_model=WhatIfResult)
def what_if(
    country: str = Query(...),
    mobility_change: float = Query(0.0),
    vaccination_boost: float = Query(0.0),
) -> WhatIfResult:
    row = _latest_row_for_country(country)
    current_rt = float(row["rt_estimate"])
    current_vax = float(row["vax_coverage"])
    current_growth = float(row["case_growth_rate"])
    current_stringency = float(row["stringency_index"])
    current_score = float(row["risk_score"])
    current_category = str(row["risk_category"])

    new_rt = float(max(0.0, min(5.0, current_rt * (1 + (mobility_change / 100.0)))))
    new_vax = float(min(100.0, current_vax + vaccination_boost))
    simulated_score = _risk_formula(new_rt, current_growth, new_vax, current_stringency)
    simulated_category = _score_to_category(simulated_score)
    delta = simulated_score - current_score

    outcome = "reduced" if delta < 0 else "increased" if delta > 0 else "maintained"
    explanation = (
        f"For {row['country']}, changing mobility by {mobility_change:.1f}% and boosting vaccination by "
        f"{vaccination_boost:.1f} points {outcome} projected risk from {current_score:.2f} to {simulated_score:.2f}."
    )

    return WhatIfResult(
        country=str(row["country"]),
        current_risk_score=current_score,
        simulated_risk_score=simulated_score,
        current_risk_category=current_category,
        simulated_risk_category=simulated_category,
        delta=float(delta),
        explanation=explanation,
    )


@app.get("/api/feature-importance", response_model=list[FeatureImportance])
def feature_importance() -> list[FeatureImportance]:
    importances = model_summary_dict.get("feature_importances", {})
    return [
        FeatureImportance(feature=str(feature), importance=float(value))
        for feature, value in sorted(importances.items(), key=lambda item: item[1], reverse=True)
    ]


@app.get("/api/global-stats", response_model=GlobalStats)
def global_stats() -> GlobalStats:
    _, latest, _ = _require_data_loaded()
    risk_category = latest["risk_category"].astype(str).str.lower()
    highest_row = latest.sort_values("risk_score", ascending=False).iloc[0]
    last_date = pd.to_datetime(latest["date"], errors="coerce").max()
    return GlobalStats(
        total_countries=int(latest["country"].nunique()),
        critical_count=int((risk_category == "critical").sum()),
        high_count=int((risk_category == "high").sum()),
        moderate_count=int((risk_category == "moderate").sum()),
        low_count=int((risk_category == "low").sum()),
        global_avg_rt=float(pd.to_numeric(latest["rt_estimate"], errors="coerce").mean()),
        global_avg_risk_score=float(pd.to_numeric(latest["risk_score"], errors="coerce").mean()),
        highest_risk_country=str(highest_row["country"]),
        last_updated=last_date.strftime("%Y-%m-%d") if pd.notna(last_date) else "",
    )
