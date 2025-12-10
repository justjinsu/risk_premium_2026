"""
Climate Risk Premium Dashboard - Streamlit App

Visualizes CRP model results for Samcheok Blue Power Plant (2,100 MW).

Data Sources:
- data/processed/scenario_comparison.csv (main results from CRPModelRunner)
- data/processed/cashflow_*.csv (time-series per scenario)
- data/processed/credit_ratings.csv (rating details)

Note: This model focuses on dispatch (transition) and physical risks.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Climate Risk Premium | Samcheok",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Colors for consistent theming
COLORS = {
    "primary": "#1a5f7a",
    "secondary": "#159895",
    "accent": "#57c5b6",
    "warning": "#f39c12",
    "danger": "#e74c3c",
    "success": "#27ae60",
    "transition": "#3498db",
    "physical": "#e74c3c",
    "cashflow": "#27ae60",
    "credit": "#9b59b6",
}

# Rating color map
RATING_COLORS = {
    "AAA": "#006400", "AA": "#228B22", "A": "#32CD32",
    "BBB": "#90EE90", "BB": "#FFD700", "B": "#FFA500",
    "CCC": "#FF6347", "CC": "#FF4500", "C": "#DC143C", "D": "#8B0000"
}


# =============================================================================
# DATA LOADING
# =============================================================================

@st.cache_data
def load_scenario_comparison():
    """Load main scenario comparison results."""
    path = project_root / "data" / "processed" / "scenario_comparison.csv"
    if path.exists():
        return pd.read_csv(path)
    return None


@st.cache_data
def load_cashflow_data(scenario_name: str):
    """Load cashflow time-series for a specific scenario."""
    path = project_root / "data" / "processed" / f"cashflow_{scenario_name}.csv"
    if path.exists():
        return pd.read_csv(path)
    return None


@st.cache_data
def load_all_cashflows():
    """Load all available cashflow files."""
    processed_dir = project_root / "data" / "processed"
    cashflows = {}
    for f in processed_dir.glob("cashflow_*.csv"):
        scenario_name = f.stem.replace("cashflow_", "")
        cashflows[scenario_name] = pd.read_csv(f)
    return cashflows


@st.cache_data
def load_credit_ratings():
    """Load credit ratings detail."""
    path = project_root / "data" / "processed" / "credit_ratings.csv"
    if path.exists():
        return pd.read_csv(path)
    return None


# =============================================================================
# PAGE: MODEL OVERVIEW
# =============================================================================

def page_model_overview():
    """Model Overview - Architecture and Key Metrics."""
    st.header("Climate Risk Premium Model")
    st.markdown("**Samcheok Blue Power Plant (2,100 MW Coal-Fired)**")

    # Load data
    df = load_scenario_comparison()

    if df is not None:
        # Key metrics from scenario comparison
        col1, col2, col3, col4 = st.columns(4)

        baseline = df[df['scenario'] == 'baseline']
        if len(baseline) > 0:
            col1.metric("Baseline CRP",
                       f"{baseline['counterfactual_crp_bps'].values[0]:.0f} bps",
                       help="Climate Risk Premium vs. A-rated counterfactual")
            col2.metric("Baseline Rating",
                       baseline['scenario_rating_new'].values[0],
                       f"{baseline['notch_change'].values[0]:.0f} notches")

        col3.metric("Max CRP", f"{df['counterfactual_crp_bps'].max():.0f} bps")
        col4.metric("Max Downgrade", f"{df['notch_change'].max():.0f} notches")

        st.markdown("---")

    # Architecture diagram
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        ### Model Architecture

        ```
        INPUT DATA (CSV)
          plant_parameters, climada_hazards, policy scenarios
                              |
              +---------------+---------------+
              v                               v
        +---------------+               +---------------+
        |  TRANSITION   |               |   PHYSICAL    |
        |    MODULE     |               |    MODULE     |
        | - Dispatch    |               | - Wildfire    |
        | - Retirement  |               | - Flood/SLR   |
        +-------+-------+               +-------+-------+
                |                               |
                +---------------+---------------+
                                v
                        +---------------+
                        |   CASHFLOW    |
                        |    MODULE     |
                        | - Revenue     |
                        | - EBITDA      |
                        | - FCF         |
                        +-------+-------+
                                v
                        +---------------+
                        | CREDIT RATING |
                        |  (AAA -> D)   |
                        | - DSCR-based  |
                        | - Distressed  |
                        +-------+-------+
                                v
                        +---------------+
                        |     CRP       |
                        | vs Counter-   |
                        |   factual     |
                        +---------------+
        ```
        """)

    with col2:
        st.markdown("### Data Status")

        # Check what data is available
        if df is not None:
            st.success(f"**Scenarios**: {len(df)} loaded")
        else:
            st.error("**Scenarios**: Not found")

        cashflows = load_all_cashflows()
        if cashflows:
            st.success(f"**Cashflows**: {len(cashflows)} scenarios")
        else:
            st.warning("**Cashflows**: None found")

        ratings = load_credit_ratings()
        if ratings is not None:
            st.success(f"**Ratings**: {len(ratings)} rows")
        else:
            st.warning("**Ratings**: Not found")

    # Key concepts
    st.markdown("---")
    st.subheader("Key Concepts")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        #### Transition Risk
        - Dispatch reduction from policy
        - Early retirement scenarios
        - Capacity factor penalties
        """)

    with col2:
        st.markdown("""
        #### Physical Risk
        - Wildfire: 1-5% outage rate
        - Flood: 1-6% outage rate
        - Literature-backed parameters
        """)

    with col3:
        st.markdown("""
        #### Credit Death Spiral
        1. Revenue reduction
        2. Low DSCR -> Distressed rating
        3. Higher spreads -> Higher cost
        4. **CRP = spread differential**
        """)


# =============================================================================
# PAGE: SCENARIO COMPARISON
# =============================================================================

def page_scenario_comparison():
    """Scenario Comparison - Main CRP Results."""
    st.header("Scenario Comparison")

    df = load_scenario_comparison()
    if df is None:
        st.warning("No scenario comparison data. Run the model first!")
        st.code("python -c \"from src.pipeline.runner import CRPModelRunner; "
               "from pathlib import Path; "
               "r = CRPModelRunner(Path.cwd()); "
               "results = r.run_multi_scenario(); "
               "r.export_results(results, Path('data/processed'))\"")
        return

    st.markdown("""
    **Counterfactual Baseline:** A-rated (no-risk world) - 150 bps spread

    CRP = Climate Risk Premium = Additional cost of capital when climate risks are priced in
    """)

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    baseline = df[df['scenario'] == 'baseline']
    if len(baseline) > 0:
        col1.metric("Baseline CRP", f"{baseline['counterfactual_crp_bps'].values[0]:.0f} bps")
        col2.metric("Baseline Rating", baseline['scenario_rating_new'].values[0])
    col3.metric("Max CRP", f"{df['counterfactual_crp_bps'].max():.0f} bps")
    col4.metric("Scenarios", len(df))

    # CRP Bar Chart
    st.subheader("Climate Risk Premium by Scenario")

    # Sort by CRP for better visualization
    df_sorted = df.sort_values('counterfactual_crp_bps', ascending=True)

    fig = px.bar(
        df_sorted,
        x='scenario',
        y='counterfactual_crp_bps',
        color='scenario_rating_new',
        color_discrete_map=RATING_COLORS,
        title="CRP vs. Counterfactual (A-rated = 150 bps)",
        labels={'counterfactual_crp_bps': 'CRP (basis points)', 'scenario': 'Scenario',
                'scenario_rating_new': 'Rating'}
    )
    fig.add_hline(y=1000, line_dash="dash", line_color="orange",
                  annotation_text="1,000 bps threshold")
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    # Rating Migration
    st.subheader("Credit Rating Migration")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            df_sorted,
            x='scenario',
            y='notch_change',
            color='scenario_rating_new',
            color_discrete_map=RATING_COLORS,
            title="Rating Notches Down from Counterfactual (A)",
            labels={'notch_change': 'Notches Down', 'scenario': 'Scenario'}
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.scatter(
            df,
            x='avg_dscr',
            y='counterfactual_crp_bps',
            color='scenario_rating_new',
            color_discrete_map=RATING_COLORS,
            size='spread_bps',
            hover_name='scenario',
            title="CRP vs. DSCR",
            labels={'avg_dscr': 'Average DSCR', 'counterfactual_crp_bps': 'CRP (bps)'}
        )
        fig.add_vline(x=1.0, line_dash="dash", line_color="red",
                     annotation_text="DSCR = 1.0x")
        st.plotly_chart(fig, use_container_width=True)

    # Summary Table
    st.subheader("Summary Table")

    display_cols = ['scenario', 'scenario_rating_new', 'spread_bps', 'avg_dscr',
                   'counterfactual_crp_bps', 'notch_change', 'rating_migration',
                   'npv_million', 'wacc_adjusted_pct']
    available_cols = [c for c in display_cols if c in df.columns]

    # Format for display
    df_display = df[available_cols].copy()
    if 'npv_million' in df_display.columns:
        df_display['npv_million'] = df_display['npv_million'].apply(lambda x: f"${x:,.0f}M")
    if 'wacc_adjusted_pct' in df_display.columns:
        df_display['wacc_adjusted_pct'] = df_display['wacc_adjusted_pct'].apply(lambda x: f"{x:.1f}%")

    st.dataframe(df_display, use_container_width=True)

    # Download
    st.download_button(
        "Download Full Results",
        df.to_csv(index=False),
        "scenario_comparison.csv",
        use_container_width=True
    )


# =============================================================================
# PAGE: CASHFLOW ANALYSIS
# =============================================================================

def page_cashflow_analysis():
    """Cashflow Analysis - Time Series by Scenario."""
    st.header("Cashflow Analysis")

    cashflows = load_all_cashflows()
    if not cashflows:
        st.warning("No cashflow data found.")
        return

    # Scenario selector
    scenarios = list(cashflows.keys())
    selected = st.selectbox("Select Scenario", scenarios, index=scenarios.index("baseline") if "baseline" in scenarios else 0)

    df = cashflows[selected]

    # Check for year column
    year_col = 'year' if 'year' in df.columns else df.columns[0]

    st.markdown(f"**Scenario:** {selected}")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    if 'revenue' in df.columns:
        col1.metric("Total Revenue", f"${df['revenue'].sum()/1e9:.1f}B")
    if 'ebitda' in df.columns:
        col2.metric("Total EBITDA", f"${df['ebitda'].sum()/1e9:.1f}B")
    if 'free_cash_flow' in df.columns:
        col3.metric("Total FCF", f"${df['free_cash_flow'].sum()/1e9:.1f}B")
    if 'total_costs' in df.columns:
        col4.metric("Total Costs", f"${df['total_costs'].sum()/1e9:.1f}B")

    # EBITDA chart
    if 'ebitda' in df.columns:
        st.subheader("EBITDA Over Time")
        fig = px.bar(
            df, x=year_col, y='ebitda',
            title=f"EBITDA - {selected}",
            color='ebitda',
            color_continuous_scale=['red', 'yellow', 'green']
        )
        fig.add_hline(y=0, line_dash="solid", line_color="black")
        st.plotly_chart(fig, use_container_width=True)

    # Revenue vs Costs
    col1, col2 = st.columns(2)

    with col1:
        if all(c in df.columns for c in ['revenue', 'fuel_costs', 'total_costs']):
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df[year_col], y=df['revenue']/1e6,
                                    name="Revenue", line=dict(color="green")))
            fig.add_trace(go.Scatter(x=df[year_col], y=df['fuel_costs']/1e6,
                                    name="Fuel Cost", line=dict(color="red")))
            fig.add_trace(go.Scatter(x=df[year_col], y=df['total_costs']/1e6,
                                    name="Total Costs", line=dict(color="orange")))
            fig.update_layout(title="Revenue vs Costs ($M)", yaxis_title="$ Million")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Waterfall for selected year
        years = sorted(df[year_col].unique())
        selected_year = st.selectbox("Waterfall Year", years, index=min(5, len(years)-1))
        yr_data = df[df[year_col] == selected_year].iloc[0]

        if all(c in df.columns for c in ['revenue', 'fuel_costs', 'ebitda']):
            fixed_opex = yr_data.get('fixed_opex', 0)
            variable_opex = yr_data.get('variable_opex', 0)
            fig = go.Figure(go.Waterfall(
                x=["Revenue", "Fuel", "Fixed O&M", "Var O&M", "EBITDA"],
                y=[yr_data['revenue']/1e6, -yr_data['fuel_costs']/1e6,
                   -fixed_opex/1e6, -variable_opex/1e6, yr_data['ebitda']/1e6],
                measure=["relative", "relative", "relative", "relative", "total"],
                connector={"line": {"color": "rgb(63, 63, 63)"}}
            ))
            fig.update_layout(title=f"Waterfall - {selected_year}")
            st.plotly_chart(fig, use_container_width=True)

    # Raw data
    with st.expander("Raw Data"):
        st.dataframe(df, use_container_width=True)
        st.download_button("Download", df.to_csv(index=False), f"cashflow_{selected}.csv")


# =============================================================================
# PAGE: CREDIT RATING ANALYSIS
# =============================================================================

def page_credit_analysis():
    """Credit Rating Analysis - Rating Methodology."""
    st.header("Credit Rating Analysis")

    df = load_scenario_comparison()
    ratings_df = load_credit_ratings()

    if df is None:
        st.warning("No data found. Run the model first.")
        return

    st.markdown("""
    Credit ratings are assessed using project finance methodology with DSCR as the primary metric.
    - Counterfactual comparison vs. A-rated no-risk world
    - Rating migration quantifies credit deterioration
    """)

    # Rating distribution
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Rating Distribution")
        rating_counts = df['scenario_rating_new'].value_counts()
        fig = px.pie(values=rating_counts.values, names=rating_counts.index,
                    color=rating_counts.index, color_discrete_map=RATING_COLORS,
                    title="Scenarios by Rating")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Investment Grade Status")
        if 'is_investment_grade' in df.columns:
            ig_counts = df['is_investment_grade'].value_counts()
            labels = ['Investment Grade' if x else 'Speculative/Distressed' for x in ig_counts.index]
            fig = px.pie(values=ig_counts.values, names=labels,
                        color=labels, color_discrete_map={'Investment Grade': 'green', 'Speculative/Distressed': 'red'},
                        title="Investment Grade vs. Speculative")
            st.plotly_chart(fig, use_container_width=True)

    # Rating details table
    st.subheader("Rating Details")

    if ratings_df is not None:
        st.dataframe(ratings_df, use_container_width=True)
    else:
        rating_cols = ['scenario', 'scenario_rating_new', 'spread_bps',
                      'rating_migration', 'notch_change', 'is_investment_grade', 'is_distressed']
        available_cols = [c for c in rating_cols if c in df.columns]
        st.dataframe(df[available_cols], use_container_width=True)

    # DSCR vs Rating
    st.subheader("DSCR vs. Credit Rating")

    fig = px.scatter(
        df,
        x='avg_dscr',
        y='spread_bps',
        color='scenario_rating_new',
        color_discrete_map=RATING_COLORS,
        hover_name='scenario',
        size='notch_change',
        title="DSCR vs. Spread",
        labels={'avg_dscr': 'Average DSCR', 'spread_bps': 'Credit Spread (bps)'}
    )
    fig.add_vline(x=1.3, line_dash="dash", line_color="orange",
                 annotation_text="BBB threshold (1.3x)")
    fig.add_vline(x=1.0, line_dash="dash", line_color="red",
                 annotation_text="Distress (1.0x)")
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# PAGE: RUN MODEL
# =============================================================================

def page_run_model():
    """Run Model - Execute Pipeline."""
    st.header("Run Model")

    st.markdown("""
    Execute the CRP model pipeline to generate results.

    **Default Scenarios:**
    - baseline: No transition or physical risk
    - moderate_transition: 10% dispatch penalty
    - aggressive_transition: 25% dispatch penalty
    - moderate_physical: Medium climate hazards
    - high_physical: Severe climate hazards
    - combined_moderate/aggressive: Both risks combined
    """)

    if st.button("Run Full Pipeline", type="primary"):
        with st.spinner("Running model..."):
            try:
                from src.pipeline.runner import CRPModelRunner
                runner = CRPModelRunner(project_root)

                st.info("Running scenarios...")
                results = runner.run_multi_scenario()

                st.info("Exporting results...")
                paths = runner.export_results(results, project_root / "data" / "processed")

                st.success(f"Completed! {len(results)} scenarios processed.")

                # Show summary
                for name, result in results.items():
                    rating = result.credit_rating.overall_rating.name if result.credit_rating else "N/A"
                    crp = result.financing.crp_bps if result.financing else 0
                    st.write(f"- **{name}**: Rating={rating}, CRP={crp:.0f} bps")

                # Clear cache to reload data
                st.cache_data.clear()
                st.info("Refresh the page to see updated results.")

            except Exception as e:
                st.error(f"Error: {e}")
                st.exception(e)


# =============================================================================
# MAIN
# =============================================================================

def main():
    st.sidebar.title("Climate Risk Premium")
    st.sidebar.markdown("**Samcheok Blue Power**")
    st.sidebar.markdown("2,100 MW Coal-Fired")
    st.sidebar.markdown("---")

    page = st.sidebar.radio("Navigate", [
        "Model Overview",
        "Scenario Comparison",
        "Cashflow Analysis",
        "Credit Rating",
        "Run Model",
    ])

    st.sidebar.markdown("---")

    # Data status
    df = load_scenario_comparison()
    if df is not None:
        st.sidebar.success(f"{len(df)} scenarios loaded")

        # Quick stats
        baseline = df[df['scenario'] == 'baseline']
        if len(baseline) > 0:
            st.sidebar.metric("Baseline CRP",
                            f"{baseline['counterfactual_crp_bps'].values[0]:.0f} bps")
    else:
        st.sidebar.warning("No data - run model")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Sources")
    st.sidebar.markdown("- CLIMADA Physical\n- KIS Credit Rating")

    st.sidebar.markdown("---")
    if st.sidebar.button("Clear Cache"):
        st.cache_data.clear()
        st.rerun()

    # Route pages
    if page == "Model Overview":
        page_model_overview()
    elif page == "Scenario Comparison":
        page_scenario_comparison()
    elif page == "Cashflow Analysis":
        page_cashflow_analysis()
    elif page == "Credit Rating":
        page_credit_analysis()
    elif page == "Run Model":
        page_run_model()


if __name__ == "__main__":
    main()
