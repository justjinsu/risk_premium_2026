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

    run_model = st.sidebar.button("🚀 Run Model", type="primary")

    # Check if results exist
    scenario_file = processed_dir / "scenario_comparison.csv"
    results_exist = scenario_file.exists()

    if run_model:
        with st.spinner("Running multi-scenario analysis..."):
            try:
                runner = CRPModelRunner(base_dir)
                results = runner.run_multi_scenario()
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
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Scenario Comparison",
        "💰 Financial Metrics",
        "📈 Cash Flow Analysis",
        "🔬 Climate Risk Premium"
    ])

    with tab1:
        st.header("Scenario Comparison")

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

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    **About this tool**
    Developed for climate risk analysis of the Samcheok Power Plant.
    Open-source framework for quantifying Climate Risk Premium (CRP).
    """)


if __name__ == "__main__":
    main()
