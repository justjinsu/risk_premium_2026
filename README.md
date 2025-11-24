# Climate Risk Premium (CRP) Model: Samcheok Blue Power

## 📉 Project Overview
This project is a sophisticated financial modeling engine designed to quantify the **Climate Risk Premium (CRP)** for the Samcheok Blue Power coal-fired power plant. It bridges the gap between **physical climate science** (CLIMADA) and **corporate finance** (Credit Ratings & WACC).

The model answers the critical question: **"How much value is destroyed by climate risks, and how does this translate into a higher cost of capital?"**

## 🎯 Key Outputs
The model produces three layers of output, each building on the last:

1.  **Credit Rating Migration (The Signal)**
    *   *What it is:* The downgrade of the company's creditworthiness due to climate risks.
    *   *Example:* Downgrade from **AA- (Stable)** to **A+ (Negative)**.
    *   *Driver:* Deteriorating financial ratios (EBITDA/Interest, Debt/EBITDA) caused by lower utilization and higher costs.

2.  **Climate Risk Premium (The Cost)**
    *   *What it is:* The additional spread (interest rate) investors demand to hold this risky asset.
    *   *Example:* **+45 basis points** on debt.
    *   *Mechanism:* Lower credit rating $\to$ Higher probability of default $\to$ Higher bond yields.

3.  **Valuation Impact (The Bottom Line)**
    *   *What it is:* The total Net Present Value (NPV) loss.
    *   *Visualization:* A **Waterfall Chart** decomposing the loss into Transition Risk (Carbon Tax, Phase-out), Physical Risk (Wildfire, Flood), and Financing Costs.

## 🚀 Features
*   **Advanced Physical Risk**: Integrates **CLIMADA** hazard data with **non-linear compound risk logic** (Wildfire + Flood + Sea Level Rise = Systemic Stress).
*   **Structural Credit Modeling**: Uses the **KIS Pricing (Korea Rating)** methodology to dynamically calculate credit ratings based on projected financial metrics.
*   **Interactive Dashboard**: A professional **Streamlit** application with:
    *   **Logic Flow Diagram**: Visualizing the model architecture.
    *   **Hazard Explorer**: Mapping and analyzing raw climate data.
    *   **Scenario Waterfall**: Bridging baseline vs. risk-adjusted valuation.
*   **Robust Engineering**: Fully automated test suite, type-safe implementations, and explicit dependency management.

## 🛠️ Installation & Usage

### Prerequisites
*   Python 3.10+
*   Poetry or Pip

### Setup
1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application
Use the provided entry point script to launch the dashboard:
```bash
python run_app.py
```
*Do not run `streamlit run` directly to avoid path issues.*

## 📂 Project Structure
*   `src/app`: Streamlit dashboard code.
*   `src/climada`: Physical risk engine and hazard data loaders.
*   `src/risk`: Financial risk logic (Credit Ratings, Financing).
*   `src/scenarios`: Scenario definitions (Transition, Market).
*   `data/raw`: Input parameters (Plant specs, Market scenarios, KIS Rating Grid).

## 📊 Data Sources
*   **Physical**: CLIMADA (ERA5 Historical, CMIP6 Projections).
*   **Transition**: 10th & 11th Basic Plan for Electricity Supply (MOTIE).
*   **Financial**: KIS Pricing Credit Rating Methodology (Thermal Power).
