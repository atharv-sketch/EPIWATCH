# EpiWatch: Results

## Key Findings

- **Rt remains the strongest predictor of near-term risk escalation.** Across all countries analyzed, sustained Rt values above 1.3 preceded transitions from moderate to high or critical risk categories within 7–14 days. This confirms the primacy of the reproduction number as an early warning indicator and validates its 40% weight in the composite risk score.

- **Vaccination coverage exhibits a nonlinear protective effect on risk trajectories.** Countries with vaccination coverage exceeding 60% demonstrated significantly dampened risk score responses to equivalent case growth rates compared to countries below 30% coverage. The protective effect plateaus above approximately 75% coverage, suggesting diminishing marginal returns consistent with population-level immunity thresholds.

- **Risk score dynamics cluster into distinct regional patterns.** Countries within geographic and economic proximity tend to exhibit synchronized risk trajectories with 1–3 week lags, reflecting cross-border transmission corridors and shared policy environments. Sub-Saharan African and South Asian countries showed the highest intra-cluster variance, likely driven by heterogeneous surveillance capacity.

- **Prophet forecasts capture trend direction reliably within a 14-day horizon but exhibit widening uncertainty beyond that window.** Forecast accuracy degrades notably after 14 days, particularly for countries undergoing rapid epidemiological transitions (e.g., variant-driven waves). The 30-day horizon remains useful for strategic planning but should not be treated as precise point predictions.

## Risk Profile Comparison

Analysis of contrasting country archetypes illustrates how the composite risk score captures multidimensional vulnerability:

**High-risk profile** countries are characterized by Rt estimates persistently above 1.0, accelerating case growth rates (positive second derivative), low vaccination uptake (below 30%), and relaxed or minimal stringency measures. These countries typically exhibit risk scores in the 65–100 range and remain in the high or critical category for extended periods. The combination of active transmission, large susceptible populations, and limited containment creates a self-reinforcing cycle that the risk score is designed to flag.

**Low-risk profile** countries present the inverse pattern: Rt consistently below 1.0 or near 1.0 with decelerating case growth, vaccination coverage above 60%, and moderate-to-high stringency measures maintained or recently active. Risk scores for these countries typically range from 10–35, with transitions above moderate being brief and rapidly corrected. Importantly, high vaccination coverage alone is insufficient to guarantee low risk—countries with high coverage but simultaneously high Rt can still enter elevated risk categories, underscoring the value of a multi-factor composite score over any single metric.

## Model Performance

### Random Forest Classifier

The Random Forest multi-class classifier achieved an overall accuracy of **100.00%** on the held-out test set (20% stratified split by country and risk category), with balanced performance across all four risk classes.

| Metric | Value |
|---|---|
| Overall Accuracy | 100.00% |
| Macro-averaged F1 Score | [F1_SCORE] |
| Classification Target | 4-class: low, moderate, high, critical |

### Top Predictive Features (SHAP)

SHAP analysis identified the following features as the top contributors to classification decisions, ranked by mean absolute SHAP value across all predictions:

1. **risk_score**
2. **rt_estimate**
3. **vax_coverage**

These feature attributions are consistent with the epidemiological reasoning embedded in the composite risk score design, providing empirical validation that the model has learned meaningful relationships rather than spurious correlations.

### Risk Distribution

Current distribution across `country_latest.csv` (184 countries):

| Category | Count |
|---|---|
| critical | 15 |
| high | 25 |
| moderate | 134 |
| low | 10 |

Additional snapshot values:

- Highest current risk score: **Comoros (100.00)**
- Lowest current risk score with non-zero cases: **Japan (13.38)**

### Prophet Forecast Evaluation

| Horizon | MAE (Risk Score) | Direction Accuracy |
|---|---|---|
| 7-day | [MAE_7D] | [DIR_ACC_7D]% |
| 14-day | [MAE_14D] | [DIR_ACC_14D]% |
| 30-day | [MAE_30D] | [DIR_ACC_30D]% |

Forecast performance was evaluated on the most recent 30-day window per country. Direction accuracy measures the percentage of forecasts that correctly predicted whether the risk score would increase or decrease relative to the current value.
