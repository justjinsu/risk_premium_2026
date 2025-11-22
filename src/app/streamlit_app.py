"""
Streamlit app for Climate Risk Premium analysis.
Interactive dashboard for scenario comparison and visualization.
"""
from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import streamlit as st

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.pipeline.runner import CRPModelRunner
from src.reporting.plots import (
    plot_spreads, plot_cashflow_waterfall, plot_capacity_factor_trajectory,
    plot_npv_comparison
)


st.set_page_config(
    page_title="Climate Risk Premium - Samcheok",
    page_icon="⚡",
    layout="wide",
)


def main():
    st.title("⚡ Climate Risk Premium – Samcheok Power Plant")
    st.markdown("""
    Quantifying how climate risks (transition policies + physical hazards) increase financing costs
    for coal-fired power infrastructure.
    """)

    # Sidebar configuration
    st.sidebar.header("Configuration")

    base_dir = Path(__file__).parent.parent.parent
    processed_dir = base_dir / "data" / "processed"

    # New Configuration Options
    st.sidebar.subheader("Custom Scenario Settings")
    
    power_plan = st.sidebar.selectbox(
        "Power Plan Scenario",
        ["10th Basic Plan (Baseline)", "11th Basic Plan (Aggressive)"],
        index=0
    )
    
    physical_risk = st.sidebar.selectbox(
        "Physical Risk Level",
        ["Low", "Medium", "High", "Extreme"],
        index=0
    )

    run_model = st.sidebar.button("🚀 Run Model", type="primary")

    # Check if results exist
    scenario_file = processed_dir / "scenario_comparison.csv"
    results_exist = scenario_file.exists()

    if run_model:
        with st.spinner("Running multi-scenario analysis..."):
            try:
                runner = CRPModelRunner(base_dir)
                
                # Define scenarios to run
                # Start with standard set
                scenarios_to_run = [
                    {"name": "baseline", "transition": "baseline", "physical": "baseline"},
                    {"name": "moderate_transition", "transition": "moderate_transition", "physical": "baseline"},
                    {"name": "aggressive_transition", "transition": "aggressive_transition", "physical": "baseline"},
                    {"name": "high_physical", "transition": "baseline", "physical": "high_physical"},
                    {"name": "combined_aggressive", "transition": "aggressive_transition", "physical": "high_physical"},
                ]
                
                # Add Custom Scenario
                plan_map = {
                    "10th Basic Plan (Baseline)": "official_10th_plan",
                    "11th Basic Plan (Aggressive)": "official_11th_plan"
                }
                
                custom_name = f"Custom: {power_plan.split(' ')[0]} + {physical_risk} Risk"
                scenarios_to_run.append({
                    "name": custom_name,
                    "transition": "baseline", # Base transition params (carbon price etc)
                    "physical": physical_risk,
                    "power_plan": plan_map[power_plan]
                })
                
                results = runner.run_multi_scenario(scenarios_to_run)
                runner.export_results(results, processed_dir)
                st.sidebar.success(f"✅ Ran {len(results)} scenarios successfully!")
                results_exist = True
            except Exception as e:
                st.sidebar.error(f"❌ Error running model: {e}")
                st.exception(e)

    if not results_exist:
        st.info("👈 Click 'Run Model' in the sidebar to generate results")
        return

    # Load results
    metrics_df = pd.read_csv(scenario_file)

    # Main tabs
    tab_profile, tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏭 Company Profile",
        "📊 Scenario Comparison",
        "💰 Financial Metrics",
        "📈 Cash Flow Analysis",
        "🔬 Climate Risk Premium",
        "⭐ Credit Rating Migration"
    ])

    with tab_profile:
        st.header("🏭 Samcheok Blue Power (POSCO)")
        
        # Load plant params for dynamic display
        plant_df = pd.read_csv(base_dir / "data" / "raw" / "plant_parameters.csv")
        plant_params = dict(zip(plant_df['param_name'], plant_df['value']))
        
        capex_trillion = float(plant_params.get('total_capex_million', 4900)) / 1000 * 1.3 # Approx conversion to KRW
        bond_yield = float(plant_params.get('debt_interest_rate', 0.061)) * 100
        capacity = float(plant_params.get('capacity_mw', 2100))
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            ### Project Overview
            **Samcheok Blue Power** is a {capacity:,.0f} MW ultra-supercritical coal-fired power plant in Samcheok, Gangwon Province. It is the **last coal plant** to be built in South Korea.
            
            - **Owner:** Samcheok Blue Power Co., Ltd. (Subsidiary of POSCO)
            - **Status:** Unit 1 (Commercial Operation May 2024), Unit 2 (Oct 2024)
            - **Total Investment:** ~{capex_trillion:.1f} Trillion KRW (Model Input: ${plant_params.get('total_capex_million'):,.0f}M)
            - **Financing:** Project Finance + Corporate Bonds
            
            ### Financial Context
            The project has faced significant financing challenges due to the global coal phase-out trend ("Coal Exit").
            
            - **Credit Rating:** AA- (Negative Outlook) $\\to$ A+ (Downgraded due to ESG concerns)
            - **Bond Yields:** Model uses **{bond_yield:.1f}%**, reflecting the "Coal Premium" over standard A+ rates.
            - **Refinancing Risk:** Large volume of corporate bonds maturing in 2024-2026.
            
            ### Policy Environment (11th Basic Plan)
            - **Coal Phase-out:** Korea aims to phase out all coal plants by the 2040s.
            - **Conversion:** Plans to convert aging coal plants to LNG/Hydrogen.
            - **Risk:** Samcheok, being the newest, faces the highest risk of becoming a **Stranded Asset** if forced to retire early (e.g., 2040) before recovering its 30-year useful life.
            """)
            
        with col2:
            st.info(f"""
            **Key Specs**
            - **Capacity:** {capacity:,.0f} MW
            - **Efficiency:** {float(plant_params.get('efficiency', 0.42))*100:.0f}% (USC)
            - **Fuel:** Bituminous Coal
            - **Life:** {int(plant_params.get('useful_life', 30))} Years
            """)
            
            st.warning("""
            **Risk Factors**
            - **Transition:** Carbon Tax, Early Retirement
            - **Market:** Low Demand, Renewable Competition
            - **Physical:** Drought (Water Cooling), Wildfires
            """)

    with tab1:
        st.header("Scenario Comparison")
        
        # Move Key Findings to top
        st.subheader("Key Findings")
        baseline_row = metrics_df[metrics_df["scenario"] == "baseline"]
        if len(baseline_row) > 0:
            baseline = baseline_row.iloc[0]
            risk_scenarios = metrics_df[metrics_df["scenario"] != "baseline"]
            
            if len(risk_scenarios) > 0:
                worst_idx = risk_scenarios["npv_million"].idxmin()
                worst_case = risk_scenarios.loc[worst_idx]
                
                k1, k2, k3 = st.columns(3)
                k1.metric("Baseline NPV", f"${baseline['npv_million']:,.0f}M")
                k2.metric("Worst Case NPV", f"${worst_case['npv_million']:,.0f}M", 
                         delta=f"{(worst_case['npv_million'] - baseline['npv_million']):,.0f}M", delta_color="inverse")
                k3.metric("Max Climate Risk Premium", f"{worst_case.get('crp_bps', 0):.0f} bps",
                         delta="Cost of Capital Spike", delta_color="inverse")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("NPV & IRR Comparison")
            fig = plot_npv_comparison(metrics_df)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Key Metrics Table")
            display_cols = ["scenario", "npv_million", "irr_pct", "avg_dscr", "min_dscr", "llcr"]
            display_df = metrics_df[display_cols].copy()
            display_df.columns = ["Scenario", "NPV (M$)", "IRR (%)", "Avg DSCR", "Min DSCR", "LLCR"]
            st.dataframe(display_df, use_container_width=True, hide_index=True)

    with tab2:
        st.header("Financial Metrics Deep Dive")

        # Scenario selector
        scenarios = metrics_df["scenario"].unique()
        selected_scenario = st.selectbox("Select Scenario", scenarios)

        scenario_data = metrics_df[metrics_df["scenario"] == selected_scenario].iloc[0]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("NPV", f"${scenario_data['npv_million']:.1f}M")
        with col2:
            st.metric("IRR", f"{scenario_data['irr_pct']:.2f}%")
        with col3:
            st.metric("Avg DSCR", f"{scenario_data['avg_dscr']:.2f}")
        with col4:
            st.metric("LLCR", f"{scenario_data['llcr']:.2f}")

        # Full metrics table
        st.subheader("All Metrics")
        st.dataframe(metrics_df, use_container_width=True, hide_index=True)

    with tab3:
        st.header("Cash Flow Analysis")

        # Load cashflow data
        cashflow_dfs = {}
        for scenario_name in metrics_df["scenario"]:
            cf_path = processed_dir / f"cashflow_{scenario_name}.csv"
            if cf_path.exists():
                cashflow_dfs[scenario_name] = pd.read_csv(cf_path)

        if cashflow_dfs:
            # Capacity factor trajectory
            st.subheader("Capacity Factor Trajectory")
            fig_cf = plot_capacity_factor_trajectory(cashflow_dfs)
            st.plotly_chart(fig_cf, use_container_width=True)
            
            # Market Price Trajectory
            st.subheader("Power Price Trajectory")
            import plotly.express as px
            
            price_data = []
            for name, df in cashflow_dfs.items():
                if "price" in df.columns:
                    for _, row in df.iterrows():
                        price_data.append({"Year": row["year"], "Price ($/MWh)": row["price"], "Scenario": name})
            
            if price_data:
                price_df = pd.DataFrame(price_data)
                fig_price = px.line(price_df, x="Year", y="Price ($/MWh)", color="Scenario",
                                  title="Wholesale Power Price Forecast")
                st.plotly_chart(fig_price, use_container_width=True)

            # Waterfall chart
            st.subheader("Cash Flow Breakdown")
            waterfall_scenario = st.selectbox("Select Scenario for Waterfall", list(cashflow_dfs.keys()))
            if waterfall_scenario in cashflow_dfs:
                fig_wf = plot_cashflow_waterfall(cashflow_dfs[waterfall_scenario], waterfall_scenario)
                st.plotly_chart(fig_wf, use_container_width=True)

            # Time series table
            st.subheader("Annual Cash Flows")
            ts_scenario = st.selectbox("Select Scenario for Time Series", list(cashflow_dfs.keys()), key="ts")
            if ts_scenario in cashflow_dfs:
                st.dataframe(cashflow_dfs[ts_scenario], use_container_width=True, hide_index=True)
        else:
            st.warning("No cash flow data found")

    with tab4:
        st.header("Climate Risk Premium Analysis")

        # Filter to risk scenarios only
        risk_scenarios = metrics_df[metrics_df["scenario"] != "baseline"].copy()

        if len(risk_scenarios) > 0 and "crp_bps" in risk_scenarios.columns:
            # CRP visualization
            st.subheader("Debt Spreads & Climate Risk Premium")
            fig_crp = plot_spreads(risk_scenarios)
            st.plotly_chart(fig_crp, use_container_width=True)

            # Summary cards
            st.subheader("Risk Impact Summary")

            baseline_row = metrics_df[metrics_df["scenario"] == "baseline"]
            if len(baseline_row) > 0:
                baseline = baseline_row.iloc[0]

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Baseline NPV", f"${baseline['npv_million']:.1f}M")

                # Find worst case
                worst_idx = risk_scenarios["crp_bps"].idxmax()
                worst_case = risk_scenarios.loc[worst_idx]

                with col2:
                    npv_loss = baseline['npv_million'] - worst_case['npv_million']
                    st.metric(
                        "Max NPV Loss",
                        f"${npv_loss:.1f}M",
                        delta=f"-{(npv_loss/baseline['npv_million']*100):.1f}%",
                        delta_color="inverse"
                    )

                with col3:
                    st.metric(
                        "Max CRP",
                        f"{worst_case['crp_bps']:.0f} bps",
                        delta=f"{worst_case['scenario']}",
                        delta_color="off"
                    )

            # Detailed risk table
            st.subheader("Risk Scenario Details")
            risk_cols = ["scenario", "expected_loss_pct", "npv_loss_million", "crp_bps",
                        "debt_spread_bps", "wacc_baseline_pct", "wacc_adjusted_pct"]
            risk_display = risk_scenarios[risk_cols].copy()
            risk_display.columns = ["Scenario", "Expected Loss (%)", "NPV Loss (M$)", "CRP (bps)",
                                   "Debt Spread (bps)", "Baseline WACC (%)", "Adjusted WACC (%)"]
            st.dataframe(risk_display, use_container_width=True, hide_index=True)
        else:
            st.warning("No risk scenario data available. Run the model first.")

    with tab5:
        st.header("⭐ Credit Rating Migration Analysis")
        st.markdown("""
        Credit ratings based on **Korea Investors Service (KIS)** methodology for Private Power Generation (IPP).
        Quantitative assessment across 6 metrics: capacity, profitability, coverage, and leverage ratios.
        """)

        # Check if credit ratings exist
        credit_file = processed_dir / "credit_ratings.csv"
        if credit_file.exists():
            credit_df = pd.read_csv(credit_file)

            # Rating migration summary
            st.subheader("Rating Migration Summary")

            if "baseline" in credit_df["scenario"].values:
                baseline_rating = credit_df[credit_df["scenario"] == "baseline"].iloc[0]

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Baseline Rating",
                        baseline_rating["overall_rating"],
                        delta=f"{baseline_rating['spread_bps']:.0f} bps"
                    )

                # Find worst rating
                worst_idx = credit_df["rating_numeric"].idxmax()
                worst_rating = credit_df.loc[worst_idx]

                with col2:
                    notch_change = worst_rating["rating_numeric"] - baseline_rating["rating_numeric"]
                    st.metric(
                        "Worst-Case Rating",
                        worst_rating["overall_rating"],
                        delta=f"↓ {notch_change:.0f} notches",
                        delta_color="inverse"
                    )

                with col3:
                    spread_increase = worst_rating["spread_bps"] - baseline_rating["spread_bps"]
                    st.metric(
                        "Spread Increase",
                        f"{spread_increase:.0f} bps",
                        delta=worst_rating["scenario"]
                    )

                with col4:
                    investment_grade = "Yes" if baseline_rating["rating_numeric"] <= 4 else "No"
                    worst_ig = "Yes" if worst_rating["rating_numeric"] <= 4 else "No"
                    ig_loss = "Lost" if investment_grade == "Yes" and worst_ig == "No" else "Maintained"
                    st.metric(
                        "Investment Grade",
                        worst_ig,
                        delta=ig_loss,
                        delta_color="inverse" if ig_loss == "Lost" else "normal"
                    )

            # Rating migration matrix
            st.subheader("Rating by Scenario")

            import plotly.graph_objects as go

            # Create rating heatmap
            rating_map = {"AAA": 1, "AA": 2, "A": 3, "BBB": 4, "BB": 5, "B": 6}
            scenarios = credit_df["scenario"].tolist()
            ratings = credit_df["overall_rating"].tolist()
            spreads = credit_df["spread_bps"].tolist()

            colors = ["#2ecc71" if r in ["AAA", "AA", "A", "BBB"] else "#e74c3c" for r in ratings]

            fig = go.Figure(data=[go.Bar(
                x=scenarios,
                y=[rating_map.get(r, 6) for r in ratings],
                text=[f"{r}<br>{s:.0f} bps" for r, s in zip(ratings, spreads)],
                textposition="auto",
                marker_color=colors,
                hovertemplate="<b>%{x}</b><br>Rating: %{text}<extra></extra>"
            )])

            fig.update_layout(
                title="Credit Rating by Scenario",
                xaxis_title="Scenario",
                yaxis_title="Rating Level (1=AAA, 6=B)",
                yaxis=dict(
                    tickmode='array',
                    tickvals=[1, 2, 3, 4, 5, 6],
                    ticktext=['AAA', 'AA', 'A', 'BBB', 'BB', 'B'],
                    autorange="reversed"
                ),
                height=500,
                shapes=[
                    dict(
                        type='line',
                        x0=-0.5,
                        x1=len(scenarios)-0.5,
                        y0=4.5,
                        y1=4.5,
                        line=dict(color='red', width=2, dash='dash'),
                    )
                ],
                annotations=[
                    dict(
                        x=len(scenarios)/2,
                        y=4.5,
                        text="Investment Grade Threshold",
                        showarrow=False,
                        yshift=10,
                        font=dict(color="red", size=12)
                    )
                ]
            )

            st.plotly_chart(fig, use_container_width=True)

            # Component ratings breakdown
            st.subheader("Component Ratings Breakdown")

            component_cols = ["scenario", "capacity_rating", "profitability_rating", "coverage_rating",
                            "net_debt_leverage_rating", "equity_leverage_rating", "asset_leverage_rating"]

            if all(col in credit_df.columns for col in component_cols):
                selected_scenario = st.selectbox(
                    "Select Scenario for Detailed Breakdown",
                    credit_df["scenario"].tolist(),
                    key="rating_scenario"
                )

                scenario_data = credit_df[credit_df["scenario"] == selected_scenario].iloc[0]

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Business Stability**")
                    st.metric("Capacity", scenario_data["capacity_rating"],
                             delta=f"{scenario_data['capacity_mw']:.0f} MW")
                    st.metric("Profitability (EBITDA/Fixed Assets)",
                             scenario_data["profitability_rating"],
                             delta=f"{scenario_data['ebitda_to_fixed_assets']:.2f}%")

                    st.markdown("**Coverage**")
                    st.metric("EBITDA/Interest", scenario_data["coverage_rating"],
                             delta=f"{scenario_data['ebitda_to_interest']:.2f}x")

                with col2:
                    st.markdown("**Leverage Ratios**")
                    st.metric("Net Debt/EBITDA", scenario_data["net_debt_leverage_rating"],
                             delta=f"{scenario_data['net_debt_to_ebitda']:.2f}x")
                    st.metric("Debt/Equity", scenario_data["equity_leverage_rating"],
                             delta=f"{scenario_data['debt_to_equity']:.2f}%")
                    st.metric("Debt/Assets", scenario_data["asset_leverage_rating"],
                             delta=f"{scenario_data['debt_to_assets']:.2f}%")

            # Full ratings table
            st.subheader("Detailed Ratings Table")
            display_cols = ["scenario", "overall_rating", "spread_bps", "capacity_rating",
                          "profitability_rating", "coverage_rating", "net_debt_leverage_rating",
                          "equity_leverage_rating", "asset_leverage_rating"]
            if all(col in credit_df.columns for col in display_cols):
                display_df = credit_df[display_cols].copy()
                display_df.columns = ["Scenario", "Overall", "Spread (bps)", "Capacity",
                                     "Profitability", "Coverage", "Net Debt", "Equity", "Assets"]
                st.dataframe(display_df, use_container_width=True, hide_index=True)

            # KIS Rating Criteria Reference
            with st.expander("📚 KIS Rating Criteria Reference"):
                st.markdown("""
                ### Korea Investors Service (KIS) Rating Grid

                | Metric | AAA | AA | A | BBB | BB | B |
                |--------|-----|----|----|-----|----|----|
                | **Capacity (MW)** | ≥2000 | ≥800 | ≥400 | ≥100 | ≥20 | <20 |
                | **EBITDA/Fixed Assets (%)** | ≥15 | ≥11 | ≥8 | ≥4 | ≥1 | <1 |
                | **EBITDA/Interest (x)** | ≥12 | ≥6 | ≥4 | ≥2 | ≥1 | <1 |
                | **Net Debt/EBITDA (x)** | ≤1 | ≤4 | ≤7 | ≤10 | ≤12 | >12 |
                | **Debt/Equity (%)** | ≤80 | ≤150 | ≤250 | ≤300 | ≤400 | >400 |
                | **Debt/Assets (%)** | ≤20 | ≤40 | ≤60 | ≤80 | ≤90 | >90 |

                **Rating Spreads:**
                - AAA: 50 bps
                - AA: 100 bps
                - A: 150 bps
                - **BBB: 250 bps** (Investment Grade Floor)
                - BB: 400 bps
                - B: 600 bps

                **Investment Grade:** AAA, AA, A, BBB (rating_numeric ≤ 4)
                **Speculative Grade:** BB, B (rating_numeric > 4)
                """)

        else:
            st.warning("No credit rating data found. Run the model to generate ratings.")

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    **About this tool**

    **Features:**
    - Climate Risk Premium (CRP) analysis
    - KIS credit rating assessment
    - Multi-scenario comparison
    - Rating migration analysis

    Developed for climate risk analysis of the Samcheok Power Plant.
    Open-source framework for quantifying climate-finance risks.

    **Methodologies:**
    - Expected loss framework
    - KIS quantitative rating grid
    - Project finance metrics (DSCR, LLCR)
    """)


if __name__ == "__main__":
    main()
