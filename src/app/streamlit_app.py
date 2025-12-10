"""
Climate Risk Premium Dashboard - Streamlit App

RESTRUCTURED VERSION using modular CSV outputs:
- transition_results.csv
- physical_results.csv  
- cashflow_results.csv
- credit_results.csv
- model_results.csv

Pages:
1. Model Overview - Structure diagram and data flow
2. Input Data - Documentation and raw input files
3. Transition Results - Policy/dispatch impacts
4. Physical Results - CLIMADA hazard impacts  
5. Cashflow Results - Revenue, costs, EBITDA
6. Credit Results - DSCR, ratings, spreads
7. Final Analysis - Combined model results
8. Run Model - Execute pipeline with custom scenarios
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

from src.data_loader import DataLoader
from src.outputs.csv_generator import run_full_pipeline

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Climate Risk Premium | Samcheok",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Colors
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

# Custom CSS
st.markdown("""
<style>
    .module-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1a5f7a;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# DATA LOADING
# =============================================================================

@st.cache_data
def load_module_results(base_dir: Path):
    """Load all module result CSVs."""
    modules_dir = base_dir / "results" / "modules"
    results = {}
    
    for csv_file in ["transition_results.csv", "physical_results.csv", 
                     "cashflow_results.csv", "credit_results.csv"]:
        path = modules_dir / csv_file
        if path.exists():
            results[csv_file.replace("_results.csv", "")] = pd.read_csv(path)
    
    combined_path = base_dir / "results" / "model_results.csv"
    if combined_path.exists():
        results["combined"] = pd.read_csv(combined_path)
    
    return results


@st.cache_data
def load_input_data(base_dir: Path):
    """Load input data for display."""
    loader = DataLoader(base_dir)
    return {
        'plant': loader.load_plant_parameters(),
        'transition': loader.load_transition_scenarios(),
        'physical': loader.load_physical_scenarios(),
        'market': loader.load_market_scenarios(),
        'credit_grid': loader.load_credit_rating_grid(),
        'power_plan': loader.load_korea_power_plan(),
    }


@st.cache_data
def load_documentation(filename: str):
    """Load markdown documentation."""
    doc_path = project_root / filename
    if doc_path.exists():
        return doc_path.read_text()
    return f"Documentation not found: {filename}"


# =============================================================================
# MODEL OVERVIEW PAGE
# =============================================================================

def page_model_overview():
    """Model Overview - Structure and Logic."""
    st.header("🏗️ Model Architecture")
    st.markdown("**Climate Risk Premium Model for Samcheok Blue Power Plant (2,100 MW)**")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 📊 Data Flow Diagram
        
        ```
        ┌─────────────────────────────────────────────────────────────┐
        │                      INPUT DATA (CSV)                        │
        │  plant_parameters, transition_scenarios, physical_scenarios  │
        │  korea_power_plan, market_scenarios, financing_parameters    │
        └─────────────────────────────┬───────────────────────────────┘
                                      │
                      ┌───────────────┴───────────────┐
                      │                               │
                      ▼                               ▼
              ┌───────────────┐               ┌───────────────┐
              │  🔄 TRANSITION │               │  🌡️ PHYSICAL   │
              │    MODULE     │               │    MODULE     │
              │               │               │               │
              │ • Dispatch    │               │ • Wildfire    │
              │ • Carbon $    │               │ • Flood       │
              │ • Retirement  │               │ • Sea Level   │
              └───────┬───────┘               └───────┬───────┘
                      │                               │
                      │    transition_results.csv     │  physical_results.csv
                      │                               │
                      └───────────────┬───────────────┘
                                      ▼
                              ┌───────────────┐
                              │  💰 CASHFLOW   │
                              │    MODULE     │
                              │               │
                              │ • Revenue     │
                              │ • Fuel Cost   │
                              │ • EBITDA      │
                              └───────┬───────┘
                                      │
                                      │ cashflow_results.csv
                                      ▼
                              ┌───────────────┐
                              │  📈 CREDIT    │
                              │    MODULE     │
                              │               │
                              │ • DSCR        │
                              │ • Rating      │
                              │ • Spread      │
                              └───────┬───────┘
                                      │
                                      │ credit_results.csv
                                      ▼
                              ┌───────────────┐
                              │  🎯 FINAL     │
                              │   RESULTS     │
                              └───────────────┘
                                      │
                                      ▼
                           model_results.csv + Excel
        ```
        """)
    
    with col2:
        st.markdown("### 📁 Module Status")
        results = load_module_results(project_root)
        
        modules = [
            ("🔄 Transition", "transition"),
            ("🌡️ Physical", "physical"),
            ("💰 Cashflow", "cashflow"),
            ("📈 Credit", "credit"),
            ("🎯 Combined", "combined"),
        ]
        
        for name, key in modules:
            if key in results:
                st.success(f"**{name}**: {len(results[key])} rows ✓")
            else:
                st.error(f"**{name}**: Not found ✗")
        
        if not results:
            st.warning("⚠️ Run the model first!")
    
    # Key insights
    st.markdown("---")
    st.subheader("🎯 Key Model Concepts")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### 🔄 Transition Risk
        Energy policy impacts from Korea's Power Plan:
        - Dispatch reduction: 85% → 20% by 2050
        - Carbon price escalation to $150/tCO2
        - Early retirement pressure from 11th Plan
        """)
    
    with col2:
        st.markdown("""
        #### 🌡️ Physical Risk
        CLIMADA-based climate hazards:
        - **Wildfire**: 1.2% → 4% outage rate
        - **Flood**: 0.2% → 0.6% outage rate
        - **Sea Level Rise**: 0 → 0.7m by 2060
        """)
    
    with col3:
        st.markdown("""
        #### 📈 Credit Death Spiral
        Endogenous feedback loop:
        1. Lower EBITDA → Lower DSCR
        2. Lower DSCR → Rating downgrade
        3. Lower rating → Higher cost of debt
        4. Higher interest → Even lower EBITDA
        """)


# =============================================================================
# INPUT DATA PAGE  
# =============================================================================

def page_input_data():
    """Input Data Documentation page."""
    st.header("📁 Input Data")
    
    tab1, tab2, tab3 = st.tabs(["📖 Documentation", "📊 Data Tables", "📈 Visualizations"])
    
    with tab1:
        doc = load_documentation("INPUT_DATA_DOCUMENTATION.md")
        st.markdown(doc)
    
    with tab2:
        inputs = load_input_data(project_root)
        
        st.subheader("🏭 Plant Parameters")
        plant_dict = inputs['plant'].to_dict()
        st.dataframe(pd.DataFrame([{"Parameter": k, "Value": v} for k, v in plant_dict.items()]), 
                     use_container_width=True, height=300)
        
        st.subheader("🔄 Transition Scenarios")
        trans_rows = [{"Scenario": n, "Dispatch Penalty": f"{t.dispatch_penalty:.0%}", 
                       "Retirement Years": t.retirement_years} 
                      for n, t in inputs['transition'].items()]
        st.dataframe(pd.DataFrame(trans_rows), use_container_width=True)
        
        st.subheader("🌡️ Physical Scenarios (CLIMADA)")
        phys_rows = [{"Scenario": n, "RCP": p.rcp_scenario, "Year": p.target_year,
                      "Wildfire": f"{p.wildfire_outage_rate:.1%}", "Flood": f"{p.flood_outage_rate:.2%}"}
                     for n, p in list(inputs['physical'].items())[:8]]
        st.dataframe(pd.DataFrame(phys_rows), use_container_width=True)
        
        st.subheader("📋 Korea Power Plan")
        st.dataframe(inputs['power_plan'], use_container_width=True, height=300)
    
    with tab3:
        inputs = load_input_data(project_root)
        plan_df = inputs['power_plan']
        
        fig = px.line(plan_df, x="year", y="implied_cf_samcheok", color="scenario_type",
                      title="Coal Dispatch Trajectory (전력수급계획)")
        fig.add_hline(y=0.5, line_dash="dash", line_color="red", annotation_text="Economic Threshold")
        st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# MODULE RESULT PAGES
# =============================================================================

def page_transition_results():
    """Transition Results page."""
    st.header("🔄 Transition Risk Results")
    st.markdown("""
    **Module outputs:** Capacity factor by year, carbon price trajectory, operating status
    
    **Sources:** Korea 10th/11th Power Plan, IEA carbon price scenarios
    """)
    
    results = load_module_results(project_root)
    if "transition" not in results:
        st.warning("⚠️ No transition results. Run the model first!")
        return
    
    df = results["transition"]
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Starting CF", f"{df['capacity_factor'].iloc[0]:.0%}")
    col2.metric("Final CF", f"{df['capacity_factor'].iloc[-1]:.0%}")
    col3.metric("Operating Years", df['operating_flag'].sum())
    col4.metric("Max Carbon", f"${df['carbon_price_usd_ton'].max():.0f}/tCO2")
    
    # Charts
    col1, col2 = st.columns(2)
    with col1:
        fig = px.area(df, x="year", y="capacity_factor", title="📉 Capacity Factor Decline",
                      color_discrete_sequence=[COLORS["transition"]])
        fig.add_hline(y=0.5, line_dash="dash", line_color="red", annotation_text="Economic Threshold")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.line(df, x="year", y="carbon_price_usd_ton", title="💨 Carbon Price",
                      color_discrete_sequence=[COLORS["danger"]])
        st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("📊 Raw Data"):
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Download CSV", df.to_csv(index=False), "transition_results.csv")


def page_physical_results():
    """Physical Risk Results page."""
    st.header("🌡️ Physical Risk Results")
    st.markdown("""
    **Module outputs:** Wildfire outage, flood outage, SLR derate, compound multiplier
    
    **Sources:** ETH CLIMADA, KMA Climate Assessment, IPCC AR6
    """)
    
    results = load_module_results(project_root)
    if "physical" not in results:
        st.warning("⚠️ No physical results. Run the model first!")
        return
    
    df = results["physical"]
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Wildfire", f"{df['wildfire_outage_rate'].mean():.1%}")
    col2.metric("Flood", f"{df['flood_outage_rate'].mean():.2%}")
    col3.metric("Total Outage", f"{df['total_outage_rate'].mean():.1%}")
    col4.metric("Max SLR", f"{df['slr_meters'].max():.2f}m")
    
    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["year"], y=df["wildfire_outage_rate"]*100, 
                                  name="🔥 Wildfire", fill='tozeroy'))
        fig.add_trace(go.Scatter(x=df["year"], y=df["flood_outage_rate"]*100, 
                                  name="🌊 Flood", fill='tozeroy'))
        fig.update_layout(title="Outage Rates by Hazard", yaxis_title="Outage Rate (%)")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.line(df, x="year", y="slr_meters", title="🌊 Sea Level Rise")
        st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("📊 Raw Data"):
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Download CSV", df.to_csv(index=False), "physical_results.csv")


def page_cashflow_results():
    """Cashflow Results page."""
    st.header("💰 Cashflow Results")
    st.markdown("""
    **Module outputs:** Revenue, fuel cost, carbon cost, OPEX, EBITDA, FCF by year
    
    **Calculation:** Revenue = MWh × Price, EBITDA = Revenue - Fuel - Carbon - OPEX
    """)
    
    results = load_module_results(project_root)
    if "cashflow" not in results:
        st.warning("⚠️ No cashflow results. Run the model first!")
        return
    
    df = results["cashflow"]
    
    # Add millions columns
    for col in ["revenue_usd", "fuel_cost_usd", "carbon_cost_usd", "ebitda_usd", "fcf_usd"]:
        if col in df.columns:
            df[col + "_M"] = df[col] / 1e6
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"${df['revenue_usd_M'].sum()/1000:.1f}B")
    col2.metric("Total EBITDA", f"${df['ebitda_usd_M'].sum()/1000:.1f}B")
    col3.metric("Total Carbon Cost", f"${df['carbon_cost_usd_M'].sum()/1000:.1f}B")
    col4.metric("Total FCF", f"${df['fcf_usd_M'].sum()/1000:.1f}B")
    
    fig = px.bar(df, x="year", y="ebitda_usd_M", title="📊 EBITDA by Year",
                 color="ebitda_usd_M", color_continuous_scale=["red", "yellow", "green"])
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["year"], y=df["revenue_usd_M"], name="Revenue", line=dict(color="green")))
        fig.add_trace(go.Scatter(x=df["year"], y=df["fuel_cost_usd_M"], name="Fuel", line=dict(color="red")))
        fig.add_trace(go.Scatter(x=df["year"], y=df["carbon_cost_usd_M"], name="Carbon", line=dict(color="orange")))
        fig.update_layout(title="💵 Revenue vs Costs", yaxis_title="$ Million")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        selected_year = st.selectbox("Waterfall Year", sorted(df["year"].unique()), index=5)
        yr = df[df["year"] == selected_year].iloc[0]
        fig = go.Figure(go.Waterfall(
            x=["Revenue", "Fuel", "Carbon", "OPEX", "EBITDA"],
            y=[yr["revenue_usd_M"], -yr["fuel_cost_usd_M"], -yr["carbon_cost_usd_M"], 
               -yr.get("opex_usd", 0)/1e6, yr["ebitda_usd_M"]],
            measure=["relative", "relative", "relative", "relative", "total"]
        ))
        fig.update_layout(title=f"Cashflow Waterfall - {selected_year}")
        st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("📊 Raw Data"):
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Download CSV", df.to_csv(index=False), "cashflow_results.csv")


def page_credit_results():
    """Credit Rating Results page."""
    st.header("📈 Credit Rating Results")
    st.markdown("""
    **Module outputs:** DSCR, credit rating, spread (bps), cost of debt
    
    **Methodology:** KIS (Korea Investors Service) rating thresholds
    """)
    
    results = load_module_results(project_root)
    if "credit" not in results:
        st.warning("⚠️ No credit results. Run the model first!")
        return
    
    df = results["credit"]
    valid_dscr = df[df['dscr'] < 100]['dscr']
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Average DSCR", f"{valid_dscr.mean():.2f}x")
    col2.metric("Minimum DSCR", f"{valid_dscr.min():.2f}x")
    col3.metric("Modal Rating", df["credit_rating"].mode()[0])
    col4.metric("Max Spread", f"{df['spread_bps'].max():.0f} bps")
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.line(df, x="year", y="dscr", title="📊 DSCR Over Time")
        fig.add_hline(y=1.5, line_dash="dash", line_color="green", annotation_text="Investment Grade")
        fig.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="Default")
        fig.update_yaxes(range=[0, min(5, valid_dscr.max() * 1.2)])
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.scatter(df, x="year", y="credit_rating", title="📉 Credit Rating Migration",
                         color="credit_rating", size_max=15)
        st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.area(df, x="year", y="spread_bps", title="📈 Credit Spread",
                      color_discrete_sequence=[COLORS["danger"]])
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.line(df, x="year", y="cost_of_debt", title="💵 Cost of Debt")
        fig.update_yaxes(tickformat='.1%')
        st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("📊 Raw Data"):
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Download CSV", df.to_csv(index=False), "credit_results.csv")


def page_final_analysis():
    """Final Combined Analysis page."""
    st.header("🎯 Final Analysis")
    
    results = load_module_results(project_root)
    if "combined" not in results:
        st.warning("⚠️ No combined results. Run the model first!")
        return
    
    df = results["combined"]
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("💵 Total Revenue", f"${df.get('revenue_usd', pd.Series([0])).sum() / 1e9:.1f}B")
    col2.metric("📅 Operating Years", len(df[df.get("operating_flag", pd.Series([1]*len(df))) == 1]))
    col3.metric("📈 Avg DSCR", f"{df[df.get('dscr', pd.Series([0]*len(df))) < 100]['dscr'].mean():.2f}x")
    col4.metric("🏦 Modal Rating", df.get("credit_rating", pd.Series(["N/A"])).mode()[0])
    col5.metric("📊 Avg Spread", f"{df.get('spread_bps', pd.Series([0])).mean():.0f} bps")
    
    st.subheader("📋 Complete Results")
    st.dataframe(df, use_container_width=True, height=400)
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("📥 Download model_results.csv", df.to_csv(index=False), 
                          "model_results.csv", use_container_width=True)
    with col2:
        excel_path = project_root / "results" / "Climate_Risk_Premium_Report.xlsx"
        if excel_path.exists():
            with open(excel_path, "rb") as f:
                st.download_button("📥 Download Excel Report", f.read(), 
                                  "Climate_Risk_Premium_Report.xlsx", use_container_width=True)


def page_run_model():
    """Run Model page."""
    st.header("⚙️ Run Model")
    
    inputs = load_input_data(project_root)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔄 Transition Settings")
        transition = st.selectbox("Transition Scenario", list(inputs['transition'].keys()))
        power_plan = st.selectbox("Power Plan", ["official_10th_plan", "official_11th_plan", "none"])
    
    with col2:
        st.subheader("🌡️ Physical Settings")
        physical = st.selectbox("Physical Scenario", list(inputs['physical'].keys())[:8])
        col_a, col_b = st.columns(2)
        start_year = col_a.number_input("Start Year", 2024, 2050, 2024)
        end_year = col_b.number_input("End Year", 2030, 2100, 2064)
    
    if st.button("🚀 Run Full Pipeline", type="primary", use_container_width=True):
        with st.spinner("Running..."):
            try:
                results = run_full_pipeline(
                    base_dir=project_root,
                    transition_scenario=transition,
                    power_plan_scenario=power_plan if power_plan != "none" else None,
                    physical_scenario=physical,
                    start_year=start_year,
                    end_year=end_year,
                    save_outputs=True,
                )
                st.success(f"✅ Complete! {len(results['combined'])} rows generated.")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"❌ Error: {e}")
                st.exception(e)


# =============================================================================
# MAIN
# =============================================================================

def main():
    st.sidebar.title("🔥 Climate Risk Premium")
    st.sidebar.markdown("**Samcheok Blue Power (2,100 MW)**")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio("📑 Navigate", [
        "🏗️ Model Overview",
        "📁 Input Data",
        "🔄 Transition Results",
        "🌡️ Physical Results",
        "💰 Cashflow Results",
        "📈 Credit Results",
        "🎯 Final Analysis",
        "⚙️ Run Model",
    ])
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📚 Data Sources")
    st.sidebar.markdown("• MOTIE 10th/11th Power Plan\n• ETH CLIMADA\n• KIS Rating Methodology")
    
    # Progress
    results = load_module_results(project_root)
    loaded = sum(1 for k in ["transition", "physical", "cashflow", "credit", "combined"] if k in results)
    st.sidebar.progress(loaded / 5)
    st.sidebar.caption(f"{loaded}/5 modules loaded")
    
    # Route pages
    if page == "🏗️ Model Overview": page_model_overview()
    elif page == "📁 Input Data": page_input_data()
    elif page == "🔄 Transition Results": page_transition_results()
    elif page == "🌡️ Physical Results": page_physical_results()
    elif page == "💰 Cashflow Results": page_cashflow_results()
    elif page == "📈 Credit Results": page_credit_results()
    elif page == "🎯 Final Analysis": page_final_analysis()
    elif page == "⚙️ Run Model": page_run_model()


if __name__ == "__main__":
    main()
