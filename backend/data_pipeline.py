# -*- coding: utf-8 -*-
"""Data pipeline for EpiWatch.

This module orchestrates the extraction, transformation, and loading (ETL) of COVID‑19 data
from two public sources – the Johns Hopkins University (JHU) confirmed cases dataset and
the Our World in Data (OWID) COVID‑19 dataset. The pipeline merges these sources, engineers
epidemiological features, computes a simple risk score, and writes the processed data to
CSV files for downstream consumption.

All functions are fully typed and now include professional docstrings explaining the
parameters, return types, and any non‑trivial transformations. Inline comments highlight
key steps, especially where data is reshaped or diagnostic logging occurs.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

import pandas as pd
from pydantic import BaseModel, HttpUrl

# ---------------------------------------------------------------------------
# Configuration models
# ---------------------------------------------------------------------------


class DataSourceConfig(BaseModel):
    """URLs for the raw data sources.

    Attributes
    ----------
    jhu_confirmed_url: HttpUrl
        Direct link to the JHU time‑series CSV of confirmed cases.
    owid_url: HttpUrl
        Direct link to the OWID CSV containing a wide range of COVID‑19 metrics.
    """

    jhu_confirmed_url: HttpUrl
    owid_url: HttpUrl


class PipelineOutputConfig(BaseModel):
    """Filesystem locations for the pipeline outputs.

    Attributes
    ----------
    processed_path: Path
        Path where the fully processed ``processed.csv`` will be written.
    country_latest_path: Path
        Path for a snapshot containing the most recent record for each country.
    """

    processed_path: Path
    country_latest_path: Path


class PipelinePaths(BaseModel):
    """Root paths used by the pipeline.

    Attributes
    ----------
    repo_root: Path
        The repository root directory (two levels up from this file).
    data_dir: Path
        Directory where intermediate and final CSVs are stored.
    """

    repo_root: Path
    data_dir: Path


LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def configure_logging() -> None:
    """Configure the root logger for the module.

    Sets a simple INFO‑level format that includes timestamps, log level, logger name,
    and the message. The call is idempotent because ``basicConfig`` only configures the
    root logger on the first invocation.
    """

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def get_paths() -> PipelinePaths:
    """Resolve repository‑relative paths used throughout the pipeline.

    Returns
    -------
    PipelinePaths
        An object containing the absolute repository root and the ``data``
        sub‑directory. The ``data`` directory is created if it does not already
        exist.
    """

    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return PipelinePaths(repo_root=repo_root, data_dir=data_dir)


def get_data_sources() -> DataSourceConfig:
    """Instantiate a :class:`DataSourceConfig` with the current public URLs.

    Returns
    -------
    DataSourceConfig
        Object containing the JHU and OWID CSV URLs.
    """

    return DataSourceConfig(
        jhu_confirmed_url=(
            "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/"
            "csse_covid_19_data/csse_covid_19_time_series/"
            "time_series_covid19_confirmed_global.csv"
        ),
        owid_url=(
            "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/"
            "owid-covid-data.csv"
        ),
    )


def get_output_config(paths: PipelinePaths) -> PipelineOutputConfig:
    """Construct output file locations based on the resolved ``paths``.

    Parameters
    ----------
    paths: PipelinePaths
        The resolved repository and data directory paths.

    Returns
    -------
    PipelineOutputConfig
        Paths for the processed dataset and the per‑country latest snapshot.
    """

    return PipelineOutputConfig(
        processed_path=paths.data_dir / "processed.csv",
        country_latest_path=paths.data_dir / "country_latest.csv",
    )


# ---------------------------------------------------------------------------
# Data acquisition functions
# ---------------------------------------------------------------------------


def download_jhu_confirmed_cases(config: DataSourceConfig) -> pd.DataFrame:
    """Download and reshape the JHU confirmed cases time‑series.

    The raw JHU CSV is in a wide format where each date is a separate column.
    This function melts the table into a long format with three columns:
    ``country``, ``date`` and ``confirmed_cases``. The resulting DataFrame is
    aggregated to a daily total per country.

    Parameters
    ----------
    config: DataSourceConfig
        Configuration containing the JHU URL.

    Returns
    -------
    pd.DataFrame
        A tidy DataFrame with columns ``country`` (str), ``date`` (datetime) and
        ``confirmed_cases`` (int).
    """

    LOGGER.info("STEP 1: Downloading and transforming JHU confirmed cases data.")
    jhu_raw = pd.read_csv(str(config.jhu_confirmed_url))
    id_columns = ["Province/State", "Country/Region", "Lat", "Long"]
    date_columns = [col for col in jhu_raw.columns if col not in id_columns]
    jhu_long = jhu_raw.melt(
        id_vars=["Country/Region"],
        value_vars=date_columns,
        var_name="date",
        value_name="confirmed_cases",
    )
    jhu_long["date"] = pd.to_datetime(jhu_long["date"], format="%m/%d/%y", errors="coerce")
    jhu_long = jhu_long.dropna(subset=["date"])
    jhu_country_daily = (
        jhu_long.groupby(["Country/Region", "date"], as_index=False)["confirmed_cases"]
        .sum()
        .rename(columns={"Country/Region": "country"})
    )
    jhu_name_map = {"US": "United States of America"}
    jhu_country_daily["country"] = jhu_country_daily["country"].replace(jhu_name_map)
    return jhu_country_daily


def download_owid_data(config: DataSourceConfig) -> pd.DataFrame:
    """Download a curated subset of the OWID COVID‑19 dataset.

    Only a selection of columns required for downstream modeling is retained.
    The function also normalises column names and applies a country‑name mapping
    to align with the JHU dataset.

    Parameters
    ----------
    config: DataSourceConfig
        Configuration containing the OWID URL.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ``country``, ``date`` and a handful of metrics.
    """

    LOGGER.info("STEP 2: Downloading and filtering OWID COVID dataset.")
    selected_columns = [
        "date",
        "location",
        "new_cases",
        "new_deaths",
        "new_cases_smoothed",
        "people_vaccinated_per_hundred",
        "stringency_index",
        "population",
    ]
    owid = pd.read_csv(str(config.owid_url), usecols=selected_columns)
    owid["date"] = pd.to_datetime(owid["date"], errors="coerce")
    owid = owid.dropna(subset=["date"]).rename(columns={"location": "country"})
    country_name_map = {
        "United States": "United States of America",
        "South Korea": "Korea, South",
        "Czech Republic": "Czechia",
        "Taiwan": "Taiwan*",
        "Burma": "Myanmar",
        "Congo (Kinshasa)": "Democratic Republic of Congo",
        "Congo (Brazzaville)": "Congo",
        "Timor-Leste": "East Timor",
        "Holy See": "Vatican",
    }
    owid["country"] = owid["country"].replace(country_name_map)
    return owid


# ---------------------------------------------------------------------------
# Merging and feature engineering
# ---------------------------------------------------------------------------


def merge_datasets(jhu_df: pd.DataFrame, owid_df: pd.DataFrame) -> pd.DataFrame:
    """Merge JHU and OWID data on ``country`` and ``date``.

    A left join is used so that every JHU record is retained; OWID columns will be
    ``NaN`` where a match is missing. The result is sorted chronologically for each
    country.

    Parameters
    ----------
    jhu_df: pd.DataFrame
        DataFrame produced by :func:`download_jhu_confirmed_cases`.
    owid_df: pd.DataFrame
        DataFrame produced by :func:`download_owid_data`.

    Returns
    -------
    pd.DataFrame
        The merged dataset ready for feature engineering.
    """

    LOGGER.info("STEP 3: Merging JHU and OWID data on country/date.")
    merged = pd.merge(jhu_df, owid_df, on=["country", "date"], how="left")
    merged = merged.sort_values(["country", "date"]).reset_index(drop=True)
    LOGGER.info(
        f"Post-merge rows: {len(merged)}, countries: {merged['country'].nunique()}"
    )
    if "United States of America" in merged["country"].values:
        sample_data = merged[merged["country"] == "United States of America"].tail(3)
        if len(sample_data) > 0:
            LOGGER.info(f"Sample data for US: {len(sample_data)} rows found")
    return merged


def _assign_risk_category(risk_score: float) -> str:
    """Map a numeric risk score to a categorical risk level.

    The thresholds are based on domain‑specific heuristics used in the original
    prototype.
    """

    if risk_score > 75:
        return "critical"
    if risk_score >= 50:
        return "high"
    if risk_score >= 25:
        return "moderate"
    return "low"


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create epidemiological and risk‑assessment features.

    The function performs a series of transformations:

    * Compute daily new cases from the JHU cumulative ``confirmed_cases``.
    * Derive a 7‑day rolling average of daily cases.
    * Estimate the case growth rate as a week‑over‑week percent change.
    * Approximate the effective reproduction number ``rt_estimate`` using a
      heuristic based on the ratio of the rolling average to its 14‑day lag.
    * Normalise vaccination coverage and combine several signals into a composite
      ``risk_score`` which is then mapped to a categorical ``risk_category``.

    Parameters
    ----------
    df: pd.DataFrame
        The merged JHU/OWID dataset.

    Returns
    -------
    pd.DataFrame
        The input DataFrame enriched with the engineered columns.
    """

    LOGGER.info("STEP 4: Engineering epidemiological and risk features.")
    engineered = df.copy()
    engineered["new_cases_smoothed"] = engineered["new_cases_smoothed"].fillna(0.0)
    country_group = engineered.groupby("country", group_keys=False)
    engineered["daily_cases"] = country_group["confirmed_cases"].diff().clip(lower=0)
    engineered["rolling_7d_avg"] = country_group["daily_cases"].transform(
        lambda x: x.rolling(7, min_periods=1).mean()
    )
    if "United States of America" in engineered["country"].values:
        us_sample = engineered[engineered["country"] == "United States of America"]["rolling_7d_avg"].tail(3).values
        LOGGER.info(f"Sample rolling_7d_avg for US: {us_sample}")
    engineered["case_growth_rate"] = country_group["rolling_7d_avg"].transform(
        lambda s: s.pct_change(periods=7) * 100.0
    )
    engineered["case_growth_rate"] = engineered["case_growth_rate"].fillna(0.0).clip(lower=-100.0, upper=500.0)
    shifted_14 = country_group["rolling_7d_avg"].shift(14).replace(0.0, float("nan"))
    rt_raw = (engineered["rolling_7d_avg"] / shifted_14) ** (7.0 / 5.1)
    engineered["rt_estimate"] = rt_raw.clip(lower=0.0, upper=5.0).fillna(1.0)
    engineered["vax_coverage"] = engineered["people_vaccinated_per_hundred"].fillna(0.0).clip(lower=0.0, upper=100.0)
    raw_score = (
        ((engineered["rt_estimate"] / 3.0) * 40.0)
        + ((engineered["case_growth_rate"].clip(lower=0.0, upper=200.0) / 200.0) * 30.0)
        + (((100.0 - engineered["vax_coverage"]) / 100.0) * 20.0)
        + (((100.0 - engineered["stringency_index"].fillna(50.0)) / 100.0) * 10.0)
    )
    engineered["risk_score"] = raw_score.clip(lower=0.0, upper=100.0)
    engineered["risk_category"] = engineered["risk_score"].map(_assign_risk_category)
    return engineered


def filter_last_year(df: pd.DataFrame) -> pd.DataFrame:
    """Retain only the most recent 365 days of data.

    Parameters
    ----------
    df: pd.DataFrame
        The fully engineered dataset.

    Returns
    -------
    pd.DataFrame
        A slice containing rows where ``date`` is within one year of the maximum
        date present in the input.
    """

    LOGGER.info("STEP 5: Filtering to the last 365 days.")
    max_date = df["date"].max()
    cutoff_date = max_date - pd.Timedelta(days=365)
    return df[df["date"] >= cutoff_date].copy()


def save_outputs(df: pd.DataFrame, output_config: PipelineOutputConfig) -> pd.DataFrame:
    """Persist the processed dataset and a per‑country latest snapshot.

    Parameters
    ----------
    df: pd.DataFrame
        The filtered, feature‑rich DataFrame.
    output_config: PipelineOutputConfig
        Destination paths for the CSV files.

    Returns
    -------
    pd.DataFrame
        The ``country_latest`` snapshot DataFrame.
    """

    LOGGER.info("STEP 6: Saving unified processed dataset to %s.", output_config.processed_path)
    df.to_csv(output_config.processed_path, index=False)
    LOGGER.info(
        "STEP 7: Creating latest-country snapshot at %s.",
        output_config.country_latest_path,
    )
    country_latest = (
        df.sort_values(["country", "date"]).groupby("country", as_index=False).tail(1)
    )
    country_latest.to_csv(output_config.country_latest_path, index=False)
    return country_latest


def run_pipeline() -> Tuple[int, int]:
    """Execute the full ETL pipeline.

    Returns
    -------
    Tuple[int, int]
        ``(row_count, country_count)`` where ``row_count`` is the number of rows
        in the final filtered dataset and ``country_count`` is the number of
        distinct countries in the latest‑snapshot CSV.
    """

    configure_logging()
    paths = get_paths()
    data_sources = get_data_sources()
    output_config = get_output_config(paths)
    jhu = download_jhu_confirmed_cases(data_sources)
    owid = download_owid_data(data_sources)
    jhu_countries = set(jhu["country"].unique())
    owid_countries = set(owid["country"].unique())
    only_jhu = jhu_countries - owid_countries
    only_owid = owid_countries - jhu_countries
    LOGGER.warning(
        "DIAG: JHU countries: %d | OWID countries: %d",
        len(jhu_countries),
        len(owid_countries),
    )
    LOGGER.warning(
        "DIAG: In JHU but NOT OWID (%d): %s",
        len(only_jhu),
        sorted(only_jhu),
    )
    LOGGER.warning(
        "DIAG: In OWID but NOT JHU (%d): %s",
        len(only_owid),
        sorted(only_owid),
    )
    LOGGER.warning("DIAG: JHU rows before merge: %d", len(jhu))
    merged = merge_datasets(jhu, owid)
    LOGGER.warning(
        "DIAG: Rows AFTER merge: %d (lost %d rows = %.1f%%)",
        len(merged),
        len(jhu) - len(merged),
        (1 - len(merged) / max(len(jhu), 1)) * 100,
    )
    LOGGER.warning("DIAG: Countries after merge: %d", merged["country"].nunique())
    featured = engineer_features(merged)
    nan_pct = featured["new_cases_smoothed"].isna().mean() * 100
    zero_pct = (featured["new_cases_smoothed"] == 0).mean() * 100
    LOGGER.warning(
        "DIAG: new_cases_smoothed NaN%%: %.2f%% | Zero%%: %.2f%%",
        nan_pct,
        zero_pct,
    )
    recent = filter_last_year(featured)
    country_latest = save_outputs(recent, output_config)
    row_count = len(recent)
    country_count = country_latest["country"].nunique()
    LOGGER.info("Pipeline complete. processed_rows=%d countries=%d", row_count, country_count)
    return row_count, country_count


if __name__ == "__main__":
    run_pipeline()
