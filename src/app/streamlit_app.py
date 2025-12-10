"""
Climate Risk Premium Dashboard - Streamlit App

Visualizes CRP model results for Samcheok Blue Power Plant (2,100 MW).

Data Sources:
- data/processed/scenario_comparison.csv (main results from CRPModelRunner)
- data/processed/cashflow_*.csv (time-series per scenario)
- data/processed/credit_ratings.csv (rating details)
- results/modules/*.csv (legacy module outputs)
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


@st.cache_data
def load_module_results():
    """Load legacy module results from results/modules/."""
    modules_dir = project_root / "results" / "modules"
    results = {}
    for csv_file in ["transition_results.csv", "physical_results.csv",
                     "cashflow_results.csv", "credit_results.csv"]:
        path = modules_dir / csv_file
        if path.exists():
            results[csv_file.replace("_results.csv", "")] = pd.read_csv(path)
    return results


# =============================================================================
# PAGE: MODEL OVERVIEW
# =============================================================================

def page_model_overview():
    """Model Overview - Architecture and Key Metrics."""
    st.header("🏗️ Climate Risk Premium Model")
    st.markdown("**Samcheok Blue Power Plant (2,100 MW Coal-Fired)**")

    # Load data
    df = load_scenario_comparison()

    if df is not None:
        # Key metrics from scenario comparison
        col1, col2, col3, col4 = st.columns(4)

        baseline = df[df['scenario'] == 'baseline']
        if len(baseline) > 0:
            col1.metric("🎯 Baseline CRP",
                       f"{baseline['counterfactual_crp_bps'].values[0]:.0f} bps",
                       help="Climate Risk Premium vs. A-rated counterfactual")
            col2.metric("📉 Baseline Rating",
                       baseline['scenario_rating_new'].values[0],
                       f"↓{baseline['notch_change'].values[0]:.0f} notches")

        col3.metric("📈 Max CRP", f"{df['counterfactual_crp_bps'].max():.0f} bps")
        col4.metric("🔻 Max Downgrade", f"{df['notch_change'].max():.0f} notches")

        st.markdown("---")

    # Architecture diagram
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        ### 📊 Model Architecture

        ```
        ┌─────────────────────────────────────────────────────────────┐
        │                      INPUT DATA (CSV)                       │
        │  plant_parameters, carbon_prices, climada_hazards           │
        └─────────────────────────────┬───────────────────────────────┘
                                      │
                      ┌───────────────┴───────────────┐
                      ▼                               ▼
              ┌───────────────┐               ┌───────────────┐
              │  TRANSITION   │               │   PHYSICAL    │
              │    MODULE     │               │    MODULE     │
              │ • Carbon $    │               │ • Wildfire    │
              │ • Dispatch    │               │ • Flood/SLR   │
              │ • 74% impact  │               │ • Literature  │
              └───────┬───────┘               └───────┬───────┘
                      │                               │
                      └───────────────┬───────────────┘
                                      ▼
                              ┌───────────────┐
                              │   CASHFLOW    │
                              │    MODULE     │
                              │ • Revenue     │
                              │ • EBITDA      │
                              │ • FCF         │
                              └───────┬───────┘
                                      ▼
                              ┌───────────────┐
                              │CREDIT RATING  │
                              │  (AAA → D)    │
                              │ • DSCR-based  │
                              │ • Distressed  │
                              └───────┬───────┘
                                      ▼
                              ┌───────────────┐
                              │     CRP       │
                              │ vs Counter-   │
                              │   factual     │
                              │ 1,020-3,500   │
                              │     bps       │
                              └───────────────┘
        ```
        """)

    with col2:
        st.markdown("### 📁 Data Status")

        # Check what data is available
        if df is not None:
            st.success(f"✅ **Scenarios**: {len(df)} loaded")
        else:
            st.error("❌ **Scenarios**: Not found")

        cashflows = load_all_cashflows()
        if cashflows:
            st.success(f"✅ **Cashflows**: {len(cashflows)} scenarios")
        else:
            st.warning("⚠️ **Cashflows**: None found")

        ratings = load_credit_ratings()
        if ratings is not None:
            st.success(f"✅ **Ratings**: {len(ratings)} rows")
        else:
            st.warning("⚠️ **Ratings**: Not found")

    # Key concepts
    st.markdown("---")
    st.subheader("🎯 Key Concepts")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        #### 🔄 Transition Risk (74%)
        - K-ETS carbon pricing: $8→$75/tCO2
        - Dispatch reduction from Power Plan
        - Carbon costs exceed revenue impact
        """)

    with col2:
        st.markdown("""
        #### 🌡️ Physical Risk (26%)
        - Wildfire: 1-5% outage rate
        - Flood: 1-6% outage rate
        - Literature-backed parameters
        """)

    with col3:
        st.markdown("""
        #### 📈 Credit Death Spiral
        1. Carbon costs → Negative EBITDA
        2. Low DSCR → Distressed rating
        3. CC/C/D → 1,500-5,000 bps spread
        4. **CRP = 1,020-3,500 bps**
        """)


# =============================================================================
# PAGE: CARBON IMPACT (Educational)
# =============================================================================

def page_carbon_impact():
    """Educational page showing the impact of carbon pricing."""
    st.header("🎓 Understanding Carbon Pricing Impact")

    st.markdown("""
    This page compares a **hypothetical no-carbon pricing world** with scenarios that include
    carbon costs. This helps understand how much of the climate risk premium is driven by
    carbon pricing policy vs. physical climate risks.
    """)

    df = load_scenario_comparison()
    if df is None:
        st.warning("⚠️ No data. Run the model first!")
        return

    # Check if no_carbon_baseline exists
    no_carbon = df[df['scenario'] == 'no_carbon_baseline']
    baseline = df[df['scenario'] == 'baseline']

    if len(no_carbon) == 0:
        st.info("💡 Run the model to include the 'no_carbon_baseline' scenario for this comparison.")
        return

    st.markdown("---")

    # Side-by-side comparison
    st.subheader("📊 No Carbon vs. Baseline Comparison")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🌿 No Carbon Pricing")
        st.markdown("*Hypothetical world without carbon costs*")

        if len(no_carbon) > 0:
            nc = no_carbon.iloc[0]
            st.metric("Credit Rating", nc.get('scenario_rating_new', 'N/A'))
            st.metric("Spread", f"{nc.get('spread_bps', 0):.0f} bps")
            st.metric("Average DSCR", f"{nc.get('avg_dscr', 0):.2f}x")
            if 'npv_million' in nc:
                st.metric("NPV", f"${nc['npv_million']:,.0f}M")

    with col2:
        st.markdown("### 🏭 With K-ETS Carbon Pricing")
        st.markdown("*Current policy: $8-75/tCO2 (2024-2050)*")

        if len(baseline) > 0:
            bl = baseline.iloc[0]

            # Calculate deltas
            rating_delta = ""
            spread_delta = None
            if len(no_carbon) > 0:
                nc = no_carbon.iloc[0]
                spread_delta = bl.get('spread_bps', 0) - nc.get('spread_bps', 0)

            st.metric("Credit Rating", bl.get('scenario_rating_new', 'N/A'))
            st.metric("Spread", f"{bl.get('spread_bps', 0):.0f} bps",
                     delta=f"+{spread_delta:.0f} bps" if spread_delta else None,
                     delta_color="inverse")
            st.metric("Average DSCR", f"{bl.get('avg_dscr', 0):.2f}x")
            if 'npv_million' in bl:
                npv_delta = None
                if len(no_carbon) > 0 and 'npv_million' in no_carbon.iloc[0]:
                    npv_delta = bl['npv_million'] - no_carbon.iloc[0]['npv_million']
                st.metric("NPV", f"${bl['npv_million']:,.0f}M",
                         delta=f"${npv_delta:,.0f}M" if npv_delta else None,
                         delta_color="inverse" if npv_delta and npv_delta < 0 else "normal")

    st.markdown("---")

    # Key insight box
    st.subheader("💡 Key Insight: Carbon Pricing Impact")

    if len(no_carbon) > 0 and len(baseline) > 0:
        nc = no_carbon.iloc[0]
        bl = baseline.iloc[0]

        spread_impact = bl.get('spread_bps', 0) - nc.get('spread_bps', 0)

        col1, col2, col3 = st.columns(3)
        col1.metric("Spread Impact from Carbon", f"+{spread_impact:.0f} bps",
                   help="Additional spread due to carbon pricing alone")

        if 'counterfactual_crp_bps' in bl and 'counterfactual_crp_bps' in nc:
            crp_diff = bl['counterfactual_crp_bps'] - nc.get('counterfactual_crp_bps', 0)
            col2.metric("CRP from Carbon Policy", f"{crp_diff:.0f} bps",
                       help="Climate Risk Premium attributable to carbon pricing")

        if 'avg_dscr' in bl and 'avg_dscr' in nc:
            dscr_impact = bl['avg_dscr'] - nc['avg_dscr']
            col3.metric("DSCR Impact", f"{dscr_impact:.2f}x",
                       help="Change in Debt Service Coverage Ratio")

        st.info(f"""
        **Interpretation:** Carbon pricing (K-ETS) adds approximately **{spread_impact:.0f} basis points**
        to the cost of debt financing for Samcheok. This represents the market's pricing of
        transition risk from climate policy.

        Without carbon costs, the plant would have a healthier financial profile.
        The carbon pricing creates a "death spiral" where:
        1. Carbon costs reduce EBITDA
        2. Lower EBITDA reduces DSCR
        3. Lower DSCR triggers rating downgrades
        4. Lower ratings increase borrowing costs
        """)

    st.markdown("---")

    # Cashflow comparison chart
    st.subheader("📈 Cashflow Comparison")

    cashflows = load_all_cashflows()
    if 'no_carbon_baseline' in cashflows and 'baseline' in cashflows:
        cf_nc = cashflows['no_carbon_baseline']
        cf_bl = cashflows['baseline']

        year_col = 'year' if 'year' in cf_nc.columns else cf_nc.columns[0]

        # EBITDA comparison
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=cf_nc[year_col], y=cf_nc['ebitda']/1e6,
            name="No Carbon", line=dict(color="green", width=3)
        ))
        fig.add_trace(go.Scatter(
            x=cf_bl[year_col], y=cf_bl['ebitda']/1e6,
            name="With K-ETS", line=dict(color="red", width=3)
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        fig.update_layout(
            title="EBITDA: No Carbon vs. K-ETS ($M)",
            xaxis_title="Year",
            yaxis_title="EBITDA ($M)",
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )
        st.plotly_chart(fig, use_container_width=True)

        # Carbon cost chart (only baseline has it)
        if 'carbon_costs' in cf_bl.columns:
            col1, col2 = st.columns(2)

            with col1:
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(
                    x=cf_bl[year_col], y=cf_bl['carbon_costs']/1e6,
                    name="Carbon Costs", marker_color="orange"
                ))
                fig2.update_layout(
                    title="Annual Carbon Costs ($M)",
                    xaxis_title="Year",
                    yaxis_title="Cost ($M)"
                )
                st.plotly_chart(fig2, use_container_width=True)

            with col2:
                # Cumulative carbon cost
                cumulative = cf_bl['carbon_costs'].cumsum() / 1e9
                fig3 = go.Figure()
                fig3.add_trace(go.Scatter(
                    x=cf_bl[year_col], y=cumulative,
                    fill='tozeroy', name="Cumulative",
                    line=dict(color="darkorange")
                ))
                fig3.update_layout(
                    title="Cumulative Carbon Costs ($B)",
                    xaxis_title="Year",
                    yaxis_title="Cost ($B)"
                )
                st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Run the model to see cashflow comparisons.")

    st.markdown("---")

    # Summary table
    st.subheader("📋 All Scenarios Summary")

    display_cols = ['scenario', 'scenario_rating_new', 'spread_bps', 'avg_dscr',
                   'counterfactual_crp_bps', 'npv_million']
    available_cols = [c for c in display_cols if c in df.columns]

    # Highlight no_carbon_baseline row
    def highlight_no_carbon(row):
        if row['scenario'] == 'no_carbon_baseline':
            return ['background-color: #d4edda'] * len(row)
        return [''] * len(row)

    styled_df = df[available_cols].style.apply(highlight_no_carbon, axis=1)
    st.dataframe(styled_df, use_container_width=True)


# =============================================================================
# PAGE: SCENARIO COMPARISON
# =============================================================================

def page_scenario_comparison():
    """Scenario Comparison - Main CRP Results."""
    st.header("📊 Scenario Comparison")

    df = load_scenario_comparison()
    if df is None:
        st.warning("⚠️ No scenario comparison data. Run the model first!")
        st.code("python -c \"from src.pipeline.runner import CRPModelRunner; "
               "from pathlib import Path; "
               "r = CRPModelRunner(Path.cwd()); "
               "results = r.run_multi_scenario(); "
               "r.export_results(results, Path('data/processed'))\"")
        return

    st.markdown("""
    **Counterfactual Baseline:** A-rated (no-carbon world) - 150 bps spread

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
    st.subheader("📈 Climate Risk Premium by Scenario")

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
    st.subheader("📉 Credit Rating Migration")

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
    st.subheader("📋 Summary Table")

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
        "📥 Download Full Results",
        df.to_csv(index=False),
        "scenario_comparison.csv",
        use_container_width=True
    )


# =============================================================================
# PAGE: CASHFLOW ANALYSIS
# =============================================================================

def page_cashflow_analysis():
    """Cashflow Analysis - Time Series by Scenario."""
    st.header("💰 Cashflow Analysis")

    cashflows = load_all_cashflows()
    if not cashflows:
        st.warning("⚠️ No cashflow data found.")
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
    if 'carbon_cost' in df.columns:
        col3.metric("Total Carbon Cost", f"${df['carbon_cost'].sum()/1e9:.1f}B")
    if 'fcf' in df.columns:
        col4.metric("Total FCF", f"${df['fcf'].sum()/1e9:.1f}B")

    # EBITDA chart
    if 'ebitda' in df.columns:
        st.subheader("📊 EBITDA Over Time")
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
        if all(c in df.columns for c in ['revenue', 'fuel_cost', 'carbon_cost']):
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df[year_col], y=df['revenue']/1e6,
                                    name="Revenue", line=dict(color="green")))
            fig.add_trace(go.Scatter(x=df[year_col], y=df['fuel_cost']/1e6,
                                    name="Fuel Cost", line=dict(color="red")))
            fig.add_trace(go.Scatter(x=df[year_col], y=df['carbon_cost']/1e6,
                                    name="Carbon Cost", line=dict(color="orange")))
            fig.update_layout(title="Revenue vs Costs ($M)", yaxis_title="$ Million")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Waterfall for selected year
        years = sorted(df[year_col].unique())
        selected_year = st.selectbox("Waterfall Year", years, index=min(5, len(years)-1))
        yr_data = df[df[year_col] == selected_year].iloc[0]

        if all(c in df.columns for c in ['revenue', 'fuel_cost', 'carbon_cost', 'ebitda']):
            opex = yr_data.get('opex', yr_data.get('fixed_opex', 0))
            fig = go.Figure(go.Waterfall(
                x=["Revenue", "Fuel", "Carbon", "OPEX", "EBITDA"],
                y=[yr_data['revenue']/1e6, -yr_data['fuel_cost']/1e6,
                   -yr_data['carbon_cost']/1e6, -opex/1e6, yr_data['ebitda']/1e6],
                measure=["relative", "relative", "relative", "relative", "total"],
                connector={"line": {"color": "rgb(63, 63, 63)"}}
            ))
            fig.update_layout(title=f"Waterfall - {selected_year}")
            st.plotly_chart(fig, use_container_width=True)

    # Raw data
    with st.expander("📊 Raw Data"):
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Download", df.to_csv(index=False), f"cashflow_{selected}.csv")


# =============================================================================
# PAGE: CREDIT RATING ANALYSIS
# =============================================================================

def page_credit_analysis():
    """Credit Rating Analysis."""
    st.header("📈 Credit Rating Analysis")

    st.markdown("""
    **Enhanced Methodology:**
    - Extended rating scale: AAA to D (10 levels)
    - DSCR-based assessment (primary metric)
    - Handles negative EBITDA with distressed ratings (CCC, CC, C, D)
    - Counterfactual comparison vs. A-rated no-carbon world
    """)

    df = load_scenario_comparison()
    if df is None:
        st.warning("⚠️ No data. Run the model first!")
        return

    # Rating distribution
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Rating Distribution")
        rating_counts = df['scenario_rating_new'].value_counts()
        fig = px.pie(values=rating_counts.values, names=rating_counts.index,
                    title="Scenarios by Rating",
                    color=rating_counts.index,
                    color_discrete_map=RATING_COLORS)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📈 Spread by Rating")
        fig = px.bar(
            df.sort_values('spread_bps'),
            x='scenario',
            y='spread_bps',
            color='scenario_rating_new',
            color_discrete_map=RATING_COLORS,
            title="Credit Spread (bps)"
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    # DSCR Analysis
    st.subheader("📉 DSCR Analysis")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            df.sort_values('avg_dscr', ascending=False),
            x='scenario',
            y='avg_dscr',
            color='scenario_rating_new',
            color_discrete_map=RATING_COLORS,
            title="Average DSCR by Scenario"
        )
        fig.add_hline(y=1.3, line_dash="dash", line_color="green",
                     annotation_text="Investment Grade (1.3x)")
        fig.add_hline(y=1.0, line_dash="dash", line_color="red",
                     annotation_text="Default (1.0x)")
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # DSCR to Rating mapping
        dscr_thresholds = pd.DataFrame({
            'DSCR Range': ['< 0', '0-0.5x', '0.5-0.8x', '0.8-1.0x', '1.0-1.1x',
                          '1.1-1.3x', '1.3-1.6x', '1.6-2.0x', '2.0-2.5x', '> 2.5x'],
            'Rating': ['D', 'C', 'CC', 'CCC', 'B', 'BB', 'BBB', 'A', 'AA', 'AAA'],
            'Spread': [5000, 2500, 1500, 900, 600, 400, 250, 150, 100, 50]
        })
        st.markdown("**DSCR → Rating Thresholds**")
        st.dataframe(dscr_thresholds, use_container_width=True, hide_index=True)

    # Component ratings
    st.subheader("🔍 Component Ratings")

    component_cols = ['capacity_rating', 'profitability_rating', 'coverage_rating',
                     'dscr_rating', 'net_debt_leverage_rating']
    available = [c for c in component_cols if c in df.columns]

    if available:
        # Melt for visualization
        df_melt = df[['scenario'] + available].melt(
            id_vars=['scenario'],
            var_name='Component',
            value_name='Rating'
        )
        df_melt['Component'] = df_melt['Component'].str.replace('_rating', '')

        fig = px.bar(
            df_melt,
            x='scenario',
            y='Rating',
            color='Component',
            barmode='group',
            title="Component Ratings by Scenario"
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# PAGE: RUN MODEL
# =============================================================================

def page_run_model():
    """Run Model page."""
    st.header("⚙️ Run Model")

    st.markdown("""
    Run the CRP model pipeline to generate fresh results.

    **Pipeline steps:**
    1. Load scenarios from CSV
    2. Calculate transition & physical adjustments
    3. Generate cashflow time series
    4. Assess credit ratings (AAA-D)
    5. Calculate CRP vs. counterfactual
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📋 Default Scenarios")
        st.markdown("""
        - baseline
        - moderate_transition
        - aggressive_transition
        - moderate_physical
        - high_physical
        - combined_moderate
        - combined_aggressive
        - low_demand
        - severe_drought
        """)

    with col2:
        st.subheader("🔧 Configuration")
        st.info("Using default scenario configuration. Edit data/raw/*.csv to customize.")

    if st.button("🚀 Run Full Pipeline", type="primary", use_container_width=True):
        with st.spinner("Running CRP model..."):
            try:
                from src.pipeline.runner import CRPModelRunner

                runner = CRPModelRunner(project_root)
                results = runner.run_multi_scenario()
                paths = runner.export_results(results, project_root / "data" / "processed")

                st.success(f"✅ Complete! {len(results)} scenarios processed.")

                # Show summary
                st.subheader("📊 Results Summary")
                for name, result in results.items():
                    rating = result.credit_rating.overall_rating.name if result.credit_rating else "N/A"
                    crp = result.financing.crp_bps if result.financing else 0
                    st.write(f"• **{name}**: Rating={rating}, CRP={crp:.0f} bps")

                # Clear cache to reload data
                st.cache_data.clear()
                st.info("Refresh the page to see updated results.")

            except Exception as e:
                st.error(f"❌ Error: {e}")
                st.exception(e)


# =============================================================================
# MAIN
# =============================================================================

def main():
    st.sidebar.title("🔥 Climate Risk Premium")
    st.sidebar.markdown("**Samcheok Blue Power**")
    st.sidebar.markdown("2,100 MW Coal-Fired")
    st.sidebar.markdown("---")

    page = st.sidebar.radio("📑 Navigate", [
        "🏗️ Model Overview",
        "🎓 Carbon Impact",
        "📊 Scenario Comparison",
        "💰 Cashflow Analysis",
        "📈 Credit Rating",
        "⚙️ Run Model",
    ])

    st.sidebar.markdown("---")

    # Data status
    df = load_scenario_comparison()
    if df is not None:
        st.sidebar.success(f"✅ {len(df)} scenarios loaded")

        # Quick stats
        baseline = df[df['scenario'] == 'baseline']
        if len(baseline) > 0:
            st.sidebar.metric("Baseline CRP",
                            f"{baseline['counterfactual_crp_bps'].values[0]:.0f} bps")
    else:
        st.sidebar.warning("⚠️ No data - run model")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📚 Sources")
    st.sidebar.markdown("• K-ETS Carbon Pricing\n• CLIMADA Physical\n• KIS Credit Rating")

    # Route pages
    if page == "🏗️ Model Overview":
        page_model_overview()
    elif page == "🎓 Carbon Impact":
        page_carbon_impact()
    elif page == "📊 Scenario Comparison":
        page_scenario_comparison()
    elif page == "💰 Cashflow Analysis":
        page_cashflow_analysis()
    elif page == "📈 Credit Rating":
        page_credit_analysis()
    elif page == "⚙️ Run Model":
        page_run_model()


if __name__ == "__main__":
    main()
