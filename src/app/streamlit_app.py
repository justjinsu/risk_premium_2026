"""
Streamlit app for Climate Risk Premium analysis.
Interactive dashboard for scenario comparison and visualization.
"""
from __future__ import annotations

from pathlib import Path
import sys

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.pipeline.runner import CRPModelRunner
from src.reporting.plots import (
    plot_spreads, plot_cashflow_waterfall, plot_capacity_factor_trajectory,
    plot_npv_comparison
)
try:
    from src.climada.hazards import load_climada_hazards, get_hazard_description
except ImportError as e:
    import streamlit as st
    st.error(f"CRITICAL ERROR: Failed to import CLIMADA modules.")
    st.error(f"Error details: {e}")
    st.write("Debug Info - sys.path:", sys.path)
    st.stop()

# Professional Color Palette
COLORS = {
    "Baseline": "#2c3e50",
    "Transition": "#e74c3c",
    "Physical": "#f39c12",
    "Combined": "#c0392b",
    "Positive": "#27ae60",
    "Negative": "#c0392b",
    "Neutral": "#95a5a6",
    "Highlight": "#3498db"
}

st.set_page_config(
    page_title="Climate Risk Premium - Samcheok",
    page_icon="⚡",
    layout="wide",
)


def render_logic_flow():
    """Render the Mermaid diagram for model logic."""
    st.markdown("### Model Architecture & Logic Flow")
    st.markdown("""
    This diagram illustrates how physical hazards and transition risks cascade through the financial model 
    to impact credit ratings and ultimately the Cost of Capital (WACC).
    """)
    
    mermaid_code = """
    graph TD
        subgraph "External Risks"
            A[Physical Hazards<br/>(CLIMADA)] -->|Wildfire, Flood, SLR| B(Physical Impact)
            C[Transition Policy<br/>(11th Basic Plan)] -->|Carbon Tax, Phase-out| D(Transition Impact)
        end

        subgraph "Operational Impact"
            B -->|Outages, Derating| E[Generation Volume<br/>(MWh)]
            D -->|Utilization Cap| E
            E --> F[Revenue]
            D -->|Carbon Costs| G[O&M Costs]
        end

        subgraph "Financial Model"
            F --> H{EBITDA}
            G --> H
            H --> I[Cash Flow Available<br/>for Debt Service]
            I --> J[DSCR / LLCR]
        end

        subgraph "Valuation & Risk"
            J -->|KIS Methodology| K[Credit Rating<br/>(AAA to B)]
            K -->|Spread Matrix| L[Cost of Debt<br/>(Interest Rate)]
            L --> M[WACC<br/>(Discount Rate)]
            M --> N((NPV))
            I --> N
        end

        style A fill:#f39c12,stroke:#333,stroke-width:2px
        style C fill:#e74c3c,stroke:#333,stroke-width:2px
        style K fill:#3498db,stroke:#333,stroke-width:2px
        style N fill:#27ae60,stroke:#333,stroke-width:4px
    """
    st.graphviz_chart(mermaid_code)


def render_hazard_explorer(base_dir: Path):
    """Render the CLIMADA Hazard Explorer tab."""
    st.header("🌍 CLIMADA Hazard Explorer")
    
    climada_file = base_dir / "data" / "raw" / "climada_hazards.csv"
    if not climada_file.exists():
        st.warning("CLIMADA hazard data not found.")
        return

    df = pd.read_csv(climada_file)
    
    # Map visualization (Static placeholder for Samcheok)
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Hazard Data by Scenario")
        st.dataframe(df, use_container_width=True)
        
        # Bar chart of outage rates
        fig = px.bar(
            df, 
            x="scenario", 
            y=["wildfire_outage_rate", "flood_outage_rate", "slr_capacity_derate"],
            title="Physical Risk Components by Scenario",
            labels={"value": "Annual Rate (0-1)", "variable": "Hazard Type"},
            barmode="group"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Site Context")
        st.map(pd.DataFrame({'lat': [37.4404], 'lon': [129.1671]}), zoom=10)
        st.markdown("""
        **Samcheok Blue Power**
        - **Location**: Samcheok, Gangwon-do
        - **Coordinates**: 37.44°N, 129.17°E
        - **Terrain**: Coastal / Mountainous
        """)
        
        st.info("""
        **Hazard Definitions:**
        - **Wildfire**: Grid transmission outages due to fire in mountain corridors.
        - **Flood**: Riverine and coastal flooding affecting site access and cooling intake.
        - **SLR**: Sea Level Rise reducing cooling pump efficiency and capacity.
        """)


def main():
    st.title("⚡ Climate Risk Premium – Samcheok Power Plant")
    st.markdown("""
    **Risk-Efficiency Theory of Corporate Decarbonization**
    
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
    
    # Load CLIMADA scenarios
    climada_file = base_dir / "data" / "raw" / "climada_hazards.csv"
    climada_scenarios = []
    if climada_file.exists():
        df_climada = pd.read_csv(climada_file)
        climada_scenarios = df_climada["scenario"].tolist()
        # Filter out baseline if present to avoid duplicates
        climada_scenarios = [s for s in climada_scenarios if s != "baseline"]

    # Combine standard levels with CLIMADA scenarios
    physical_options = ["Low", "Medium", "High", "Extreme"] + climada_scenarios
    
    physical_risk = st.sidebar.selectbox(
        "Physical Risk Level",
        physical_options,
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
        # Show Logic Flow even before running
        render_logic_flow()
        return

    # Load results
    metrics_df = pd.read_csv(scenario_file)

    # Main tabs
    tab_logic, tab_profile, tab_hazards, tab_comparison, tab_financials, tab_crp, tab_ratings = st.tabs([
        "🧠 Logic Flow",
        "🏭 Company Profile",
        "🌍 Hazard Explorer",
        "📊 Scenario Comparison",
        "💰 Financial Metrics",
        "🔬 Risk Premium",
        "⭐ Credit Ratings"
    ])

    with tab_logic:
        render_logic_flow()

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
            """)
            
        with col2:
            st.info(f"""
            **Key Specs**
            - **Capacity:** {capacity:,.0f} MW
            - **Efficiency:** {float(plant_params.get('efficiency', 0.42))*100:.0f}% (USC)
            - **Fuel:** Bituminous Coal
            - **Life:** {int(plant_params.get('useful_life', 30))} Years
            """)

    with tab_hazards:
        render_hazard_explorer(base_dir)

    with tab_comparison:
        st.header("Scenario Comparison")
        
        # Key Findings
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
            st.subheader("NPV Waterfall")
            # Create a simplified waterfall chart
            if len(risk_scenarios) > 0:
                # Calculate deltas from baseline
                deltas = []
                labels = []
                
                # Baseline
                deltas.append(baseline['npv_million'])
                labels.append("Baseline")
                
                # Transition Effect (approximate from a transition scenario)
                trans_scen = metrics_df[metrics_df['scenario'].str.contains('transition')].iloc[0] if any(metrics_df['scenario'].str.contains('transition')) else baseline
                trans_impact = trans_scen['npv_million'] - baseline['npv_million']
                deltas.append(trans_impact)
                labels.append("Transition Impact")
                
                # Physical Effect
                phys_scen = metrics_df[metrics_df['scenario'].str.contains('physical')].iloc[0] if any(metrics_df['scenario'].str.contains('physical')) else baseline
                phys_impact = phys_scen['npv_million'] - baseline['npv_million']
                deltas.append(phys_impact)
                labels.append("Physical Impact")
                
                # Combined (Residual interaction)
                combined_scen = metrics_df[metrics_df['scenario'].str.contains('combined')].iloc[0] if any(metrics_df['scenario'].str.contains('combined')) else baseline
                # Interaction is the difference between combined and (baseline + trans + phys)
                interaction = combined_scen['npv_million'] - (baseline['npv_million'] + trans_impact + phys_impact)
                deltas.append(interaction)
                labels.append("Compound Interaction")
                
                # Final
                deltas.append(combined_scen['npv_million'])
                labels.append("Final NPV")
                
                fig = go.Figure(go.Waterfall(
                    name = "20", orientation = "v",
                    measure = ["absolute", "relative", "relative", "relative", "total"],
                    x = labels,
                    textposition = "outside",
                    text = [f"${x:,.0f}M" for x in deltas],
                    y = deltas,
                    connector = {"line":{"color":"rgb(63, 63, 63)"}},
                ))
                fig.update_layout(title = "NPV Bridge: Baseline to Combined Risk", showlegend = False)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Key Metrics Table")
            display_cols = ["scenario", "npv_million", "irr_pct", "avg_dscr", "min_dscr", "llcr"]
            display_df = metrics_df[display_cols].copy()
            display_df.columns = ["Scenario", "NPV (M$)", "IRR (%)", "Avg DSCR", "Min DSCR", "LLCR"]
            st.dataframe(display_df, use_container_width=True, hide_index=True)

    with tab_financials:
        st.header("Financial Metrics Deep Dive")
        
        # Load cashflow data
        cashflow_dfs = {}
        for scenario_name in metrics_df["scenario"]:
            cf_path = processed_dir / f"cashflow_{scenario_name}.csv"
            if cf_path.exists():
                cashflow_dfs[scenario_name] = pd.read_csv(cf_path)

        if cashflow_dfs:
            st.subheader("Cash Flow Projection")
            selected_scenario_cf = st.selectbox("Select Scenario", list(cashflow_dfs.keys()), key="cf_proj")
            
            if selected_scenario_cf in cashflow_dfs:
                cf_df = cashflow_dfs[selected_scenario_cf]
                
                fig_cf = go.Figure()
                fig_cf.add_trace(go.Scatter(x=cf_df["year"], y=cf_df["free_cash_flow"] / 1e6, name="Free Cash Flow", line=dict(color=COLORS["Positive"], width=3)))
                fig_cf.add_trace(go.Bar(x=cf_df["year"], y=cf_df["ebitda"] / 1e6, name="EBITDA", marker_color=COLORS["Baseline"], opacity=0.3))
                
                fig_cf.update_layout(title=f"Cash Flow: {selected_scenario_cf}", yaxis_title="USD Million", template="plotly_white")
                st.plotly_chart(fig_cf, use_container_width=True)

    with tab_crp:
        st.header("Climate Risk Premium Analysis")
        risk_scenarios = metrics_df[metrics_df["scenario"] != "baseline"].copy()
        
        if len(risk_scenarios) > 0:
            st.subheader("Debt Spreads & Climate Risk Premium")
            fig_crp = plot_spreads(risk_scenarios)
            st.plotly_chart(fig_crp, use_container_width=True)
            
            st.info("""
            **Climate Risk Premium (CRP)** represents the additional yield investors demand to hold assets exposed to climate risks.
            It is calculated as the difference between the risk-adjusted WACC and the baseline WACC.
            """)

    with tab_ratings:
        st.header("⭐ Credit Rating Migration")
        credit_file = processed_dir / "credit_ratings.csv"
        
        if credit_file.exists():
            credit_df = pd.read_csv(credit_file)
            
            st.subheader("Rating Migration Matrix")
            
            # Create rating heatmap
            rating_map = {"AAA": 1, "AA": 2, "A": 3, "BBB": 4, "BB": 5, "B": 6}
            scenarios = credit_df["scenario"].tolist()
            ratings = credit_df["overall_rating"].tolist()
            
            colors = ["#2ecc71" if r in ["AAA", "AA", "A", "BBB"] else "#e74c3c" for r in ratings]

            fig = go.Figure(data=[go.Bar(
                x=scenarios,
                y=[rating_map.get(r, 6) for r in ratings],
                text=ratings,
                textposition="auto",
                marker_color=colors
            )])

            fig.update_layout(
                title="Credit Rating by Scenario",
                yaxis=dict(tickvals=[1, 2, 3, 4, 5, 6], ticktext=['AAA', 'AA', 'A', 'BBB', 'BB', 'B'], autorange="reversed")
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Detailed Ratings Table")
            st.dataframe(credit_df, use_container_width=True)

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    **About this tool**
    Developed for climate risk analysis of the Samcheok Power Plant.
    """)

if __name__ == "__main__":
    main()
