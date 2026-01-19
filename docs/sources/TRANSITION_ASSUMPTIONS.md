# Transition Risk Data Sources

This document provides full citations for carbon pricing and policy data.

## Carbon Pricing Scenarios

### 1. Korea ETS Current (`korea_ets_current`)

**Description**: Korea ETS business-as-usual trajectory.

| Year | Price (USD/tCO2) | Source |
|------|------------------|--------|
| 2024 | 8 | KRX market data |
| 2025 | 10 | Projection |
| 2030 | 25 | Government target |
| 2040 | 50 | Projection |
| 2050 | 80 | Projection |

**Sources**:
1. **Korea Exchange (KRX)**
   - Title: Korea ETS Market Data
   - URL: https://ets.krx.co.kr/

2. **Ministry of Environment (Korea)**
   - Title: Korea ETS Allocation Plan Phase 3
   - Year: 2021-2025

### 2. Korea ETS Accelerated (`korea_ets_accelerated`)

**Description**: Carbon neutrality pathway.

| Year | Price (USD/tCO2) | Source |
|------|------------------|--------|
| 2030 | 50 | Carbon Neutrality Roadmap |
| 2050 | 200 | Target for net-zero |

**Sources**:
1. **Korea 2050 Carbon Neutrality Commission (2021)**
   - Title: 2050 탄소중립 시나리오
   - URL: https://www.2050cnc.go.kr/

### 3. IEA Net Zero 2050 (`iea_nze_2050`)

**Description**: IEA Net Zero Scenario for advanced economies.

| Year | Price (USD/tCO2) | Source |
|------|------------------|--------|
| 2030 | 130 | IEA NZE |
| 2050 | 250 | IEA NZE |

**Sources**:
1. **IEA (2023)**
   - Title: World Energy Outlook 2023
   - URL: https://www.iea.org/reports/world-energy-outlook-2023
   - Section: Net Zero Emissions Scenario

### 4. NGFS Scenarios

**Description**: Central bank climate scenarios.

| Scenario | 2030 | 2050 | Source |
|----------|------|------|--------|
| Orderly | 100 | 250 | NGFS 2023 |
| Disorderly | 30 | 350 | NGFS 2023 |
| Hot House | 10 | 20 | NGFS 2023 |

**Sources**:
1. **NGFS (2023)**
   - Title: NGFS Climate Scenarios
   - URL: https://www.ngfs.net/ngfs-scenarios-portal/

---

## Policy Scenarios

### 1. Korea 10th Basic Plan (`korea_10th_plan`)

**Description**: Official Korea power supply plan (2022).

| Year | Dispatch Factor | Coal Share Target |
|------|-----------------|-------------------|
| 2024 | 1.00 | Current |
| 2030 | 0.70 | ~30% |
| 2050 | 0.00 | Phase-out |

**Sources**:
1. **Ministry of Trade, Industry and Energy (2022)**
   - Title: 제10차 전력수급기본계획
   - English: 10th Basic Plan for Power Supply
   - Year: December 2022

2. **Korea Electric Power Corporation (KEPCO)**
   - Title: Power Statistics
   - URL: https://home.kepco.co.kr/

### 2. Korea Accelerated (`korea_accelerated`)

**Description**: Accelerated phase-out (2040 target).

| Year | Dispatch Factor |
|------|-----------------|
| 2030 | 0.50 |
| 2040 | 0.00 |

**Sources**:
1. **2050 Carbon Neutrality Commission**
   - Scenario A: Accelerated transition

### 3. EU Taxonomy Aligned (`eu_taxonomy_aligned`)

**Description**: No financing for coal under EU rules.

**Sources**:
1. **EU Commission (2021)**
   - Title: EU Taxonomy Climate Delegated Act
   - URL: https://ec.europa.eu/sustainable-finance-taxonomy/

---

## Coal Phase-Out Timeline Sources

### Global Context

| Region | Phase-out Year | Source |
|--------|----------------|--------|
| EU | 2030 (most) | EU Green Deal |
| UK | 2024 | Net Zero Strategy |
| Korea | 2050 | 10th Basic Plan |
| Japan | 2030s | GX Strategy |
| China | 2060 | Net Zero Pledge |

### References

1. **Global Energy Monitor (2024)**
   - Title: Global Coal Plant Tracker
   - URL: https://globalenergymonitor.org/

2. **Climate Analytics (2023)**
   - Title: 1.5°C Coal Phase-out Dates
   - URL: https://climateanalytics.org/

3. **IEA (2023)**
   - Title: Coal 2023 Analysis and Forecast
   - URL: https://www.iea.org/reports/coal-2023

---

## Methodology Notes

### Carbon Cost Calculation

```
Carbon Cost (USD/MWh) = Carbon Price (USD/tCO2) × Emissions Rate (tCO2/MWh)

For Samcheok: 0.85 tCO2/MWh (supercritical coal)
```

### Dispatch Factor Interpretation

- 1.0 = Full dispatch (baseline capacity factor)
- 0.7 = 70% of baseline (merit order effect)
- 0.0 = No dispatch (phase-out)

### Retirement Year Calculation

```python
remaining_life = min(natural_end, policy_retirement) - current_year
```
