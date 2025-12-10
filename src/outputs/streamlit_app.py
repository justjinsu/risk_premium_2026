"""
Climate Risk Premium Dashboard - Streamlit App

Enhanced version showing model structure and all module results clearly.

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
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
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
    
    # Combined results
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
    st.header("🏗️ Model Overview")
    st.markdown("**Climate Risk Premium Model for Samcheok Blue Power Plant (2,100 MW)**")
    
    # Model flow diagram using Mermaid-style text
    st.subheader("📊 Model Architecture")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
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
              │  TRANSITION   │               │   PHYSICAL    │
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
                              │   CASHFLOW    │
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
                              │    CREDIT     │
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
                              │    FINAL      │
                              │   RESULTS     │
                              │               │
                              │ • NPV         │
                              │ • IRR         │
                              │ • CRP         │
                              └───────────────┘
                                      │
                                      ▼
                           model_results.csv + Excel
        ```
        """)
    
    with col2:
        st.markdown("### 📁 Module Outputs")
        
        results = load_module_results(project_root)
        
        modules_status = [
            ("🔄 Transition", "transition", COLORS["transition"]),
            ("🌡️ Physical", "physical", COLORS["physical"]),
            ("💰 Cashflow", "cashflow", COLORS["cashflow"]),
            ("📈 Credit", "credit", COLORS["credit"]),
            ("🎯 Combined", "combined", COLORS["primary"]),
        ]
        
        for name, key, color in modules_status:
            if key in results:
                rows = len(results[key])
                st.success(f"**{name}**: {rows} rows ✓")
            else:
                st.error(f"**{name}**: Not found ✗")
    
    # Key insights
    st.markdown("---")
    st.subheader("🎯 Key Model Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
        <h4>🔄 Transition Risk</h4>
        <p>Energy policy impacts from Korea's Power Plan:</p>
        <ul>
        <li>Dispatch reduction from 85% to 20% by 2050</li>
        <li>Carbon price escalation to $150/tCO2</li>
        <li>Early retirement pressure</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
        <h4>🌡️ Physical Risk</h4>
        <p>CLIMADA-based climate hazards:</p>
        <ul>
        <li>Wildfire: 1.2% → 4% outage rate</li>
        <li>Flood: 0.2% → 0.6% outage rate</li>
        <li>Sea Level Rise: 0 → 0.7m by 2060</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
        <h4>📈 Credit Death Spiral</h4>
        <p>Endogenous feedback loop:</p>
        <ul>
        <li>Lower EBITDA → Lower DSCR</li>
        <li>Lower DSCR → Rating downgrade</li>
        <li>Lower rating → Higher cost of debt</li>
        <li>Higher interest → Even lower EBITDA</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# INPUT DATA PAGE  
# =============================================================================

def page_input_data():
    """Input Data Documentation page."""
    st.header("📁 Input Data")
    st.markdown("All input data with sources and documentation.")
    
    tab1, tab2, tab3 = st.tabs(["📖 Documentation", "📊 Data Tables", "📈 Visualizations"])
    
    with tab1:
        doc = load_documentation("INPUT_DATA_DOCUMENTATION.md")
        st.markdown(doc)
    
    with tab2:
        inputs = load_input_data(project_root)
        
        st.subheader("🏭 Plant Parameters")
        plant_dict = inputs['plant'].to_dict()
        plant_df = pd.DataFrame([
            {"Parameter": k, "Value": v, "Unit": ""} 
            for k, v in plant_dict.items()
        ])
        st.dataframe(plant_df, use_container_width=True, height=300)
        
        st.subheader("🔄 Transition Scenarios")
        trans_rows = []
        for name, t in inputs['transition'].items():
            trans_rows.append({
                "Scenario": name,
                "Dispatch Penalty": f"{t.dispatch_penalty:.0%}",
                "Retirement Years": t.retirement_years,
                "Description": t.description[:50] + "..." if len(t.description) > 50 else t.description,
            })
        st.dataframe(pd.DataFrame(trans_rows), use_container_width=True)
        
        st.subheader("🌡️ Physical Scenarios (CLIMADA)")
        phys_rows = []
        for name, p in list(inputs['physical'].items())[:6]:  # Show first 6
            phys_rows.append({
                "Scenario": name,
                "RCP": p.rcp_scenario,
                "Year": p.target_year,
                "Wildfire": f"{p.wildfire_outage_rate:.1%}",
                "Flood": f"{p.flood_outage_rate:.2%}",
                "SLR": f"{p.slr_capacity_derate:.1%}",
            })
        st.dataframe(pd.DataFrame(phys_rows), use_container_width=True)
        
        st.subheader("📋 Korea Power Plan")
        st.dataframe(inputs['power_plan'].head(20), use_container_width=True, height=300)
    
    with tab3:
        inputs = load_input_data(project_root)
        
        # Power plan trajectory chart
        st.subheader("📉 Coal Dispatch Trajectory (전력수급계획)")
        plan_df = inputs['power_plan']
        
        fig = px.line(
            plan_df, x="year", y="implied_cf_samcheok",
            color="scenario_type",
            title="Samcheok Implied Capacity Factor by Year",
            labels={"implied_cf_samcheok": "Capacity Factor", "year": "Year"}
        )
        fig.add_hline(y=0.5, line_dash="dash", line_color="red", 
                      annotation_text="Economic Threshold (50%)")
        st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# TRANSITION RESULTS PAGE
# =============================================================================

def page_transition_results():
    """Transition Results page."""
    st.header("🔄 Transition Risk Results")
    st.markdown("""
    **What this module calculates:**
    - Year-by-year capacity factor based on Korea Power Plan dispatch curves
    - Carbon price trajectory and resulting carbon costs
    - Operating status (when plant becomes uneconomic)
    """)
    
    results = load_module_results(project_root)
    if "transition" not in results:
        st.warning("⚠️ No transition results found. Run the model first using '⚙️ Run Model' page.")
        return
    
    df = results["transition"]
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Starting CF", f"{df['capacity_factor'].iloc[0]:.0%}")
    with col2:
        final_cf = df[df['operating_flag'] == 1]['capacity_factor'].iloc[-1] if len(df[df['operating_flag'] == 1]) > 0 else 0
        st.metric("Final CF", f"{final_cf:.0%}")
    with col3:
        operating_years = df['operating_flag'].sum()
        st.metric("Operating Years", operating_years)
    with col4:
        max_carbon = df['carbon_price_usd_ton'].max()
        st.metric("Max Carbon Price", f"${max_carbon:.0f}/tCO2")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.area(
            df, x="year", y="capacity_factor",
            title="📉 Capacity Factor Decline Over Time",
            labels={"capacity_factor": "Capacity Factor", "year": "Year"},
            color_discrete_sequence=[COLORS["transition"]]
        )
        fig.add_hline(y=0.5, line_dash="dash", line_color="red", 
                      annotation_text="Economic Threshold")
        fig.add_hline(y=0.3, line_dash="dot", line_color="orange",
                      annotation_text="Critical Level")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.line(
            df, x="year", y="carbon_price_usd_ton",
            title="💨 Carbon Price Trajectory",
            labels={"carbon_price_usd_ton": "Carbon Price ($/tCO2)", "year": "Year"},
            color_discrete_sequence=[COLORS["danger"]]
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Raw data
    with st.expander("📊 View Raw Data"):
        st.dataframe(df, use_container_width=True)
        st.download_button(
            "📥 Download transition_results.csv",
            df.to_csv(index=False),
            "transition_results.csv",
            "text/csv"
        )


# =============================================================================
# PHYSICAL RESULTS PAGE
# =============================================================================

def page_physical_results():
    """Physical Risk Results page."""
    st.header("🌡️ Physical Risk Results")
    st.markdown("""
    **What this module calculates:**
    - CLIMADA hazard impacts: wildfire, flood, sea level rise
    - Forced outage rates from climate events
    - Capacity derating from long-term hazards (SLR)
    - Compound risk multiplier (hazard interactions)
    """)
    
    results = load_module_results(project_root)
    if "physical" not in results:
        st.warning("⚠️ No physical results found. Run the model first.")
        return
    
    df = results["physical"]
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Wildfire Outage", f"{df['wildfire_outage_rate'].mean():.1%}")
    with col2:
        st.metric("Flood Outage", f"{df['flood_outage_rate'].mean():.2%}")
    with col3:
        st.metric("Total Outage", f"{df['total_outage_rate'].mean():.1%}")
    with col4:
        st.metric("Max SLR", f"{df['slr_meters'].max():.2f}m")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["year"], y=df["wildfire_outage_rate"]*100, 
            name="🔥 Wildfire", fill='tozeroy',
            line=dict(color='#e74c3c')
        ))
        fig.add_trace(go.Scatter(
            x=df["year"], y=df["flood_outage_rate"]*100, 
            name="🌊 Flood", fill='tozeroy',
            line=dict(color='#3498db')
        ))
        fig.update_layout(
            title="🔥 Outage Rates by Hazard Type",
            yaxis_title="Outage Rate (%)",
            xaxis_title="Year"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.line(
            df, x="year", y="slr_meters",
            title="🌊 Sea Level Rise Projection",
            labels={"slr_meters": "SLR (meters)", "year": "Year"},
            color_discrete_sequence=["#1abc9c"]
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Compound risk
    fig = px.line(
        df, x="year", y="compound_multiplier",
        title="⚠️ Compound Hazard Multiplier (Hazard Interactions)",
        labels={"compound_multiplier": "Multiplier", "year": "Year"},
        color_discrete_sequence=[COLORS["warning"]]
    )
    fig.add_hline(y=1.0, line_dash="dash", annotation_text="No Interaction")
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("📊 View Raw Data"):
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Download physical_results.csv", df.to_csv(index=False), "physical_results.csv")


# =============================================================================
# CASHFLOW RESULTS PAGE
# =============================================================================

def page_cashflow_results():
    """Cashflow Results page."""
    st.header("💰 Cashflow Results")
    st.markdown("""
    **What this module calculates:**
    - Revenue = Generation (MWh) × Power Price ($/MWh)
    - Fuel Cost = Heat Rate × Generation × Coal Price
    - Carbon Cost = Emissions × Generation × Carbon Price
    - EBITDA = Revenue - Fuel - Carbon - OPEX
    - Free Cash Flow = EBITDA - Interest - Taxes
    """)
    
    results = load_module_results(project_root)
    if "cashflow" not in results:
        st.warning("⚠️ No cashflow results found. Run the model first.")
        return
    
    df = results["cashflow"]
    
    # Convert to millions
    for col in ["revenue_usd", "fuel_cost_usd", "carbon_cost_usd", "opex_usd", "ebitda_usd", "fcf_usd"]:
        if col in df.columns:
            df[col + "_M"] = df[col] / 1e6
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Revenue", f"${df['revenue_usd_M'].sum() / 1000:.1f}B")
    with col2:
        st.metric("Total EBITDA", f"${df['ebitda_usd_M'].sum() / 1000:.1f}B")
    with col3:
        st.metric("Total Carbon Cost", f"${df['carbon_cost_usd_M'].sum() / 1000:.1f}B")
    with col4:
        st.metric("Total FCF", f"${df['fcf_usd_M'].sum() / 1000:.1f}B")
    
    # EBITDA bar chart
    fig = px.bar(
        df, x="year", y="ebitda_usd_M",
        title="📊 EBITDA Over Time",
        labels={"ebitda_usd_M": "EBITDA ($M)", "year": "Year"},
        color="ebitda_usd_M",
        color_continuous_scale=["#e74c3c", "#f39c12", "#27ae60"]
    )
    fig.add_hline(y=0, line_color="black", line_width=2)
    st.plotly_chart(fig, use_container_width=True)
    
    # Revenue vs Costs stacked area
    col1, col2 = st.columns(2)
    
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["year"], y=df["revenue_usd_M"], 
                                  name="Revenue", line=dict(color=COLORS["success"], width=3)))
        fig.add_trace(go.Scatter(x=df["year"], y=df["fuel_cost_usd_M"], 
                                  name="Fuel Cost", line=dict(color=COLORS["danger"])))
        fig.add_trace(go.Scatter(x=df["year"], y=df["carbon_cost_usd_M"], 
                                  name="Carbon Cost", line=dict(color=COLORS["warning"])))
        fig.add_trace(go.Scatter(x=df["year"], y=df["opex_usd_M"], 
                                  name="OPEX", line=dict(color=COLORS["secondary"])))
        fig.update_layout(title="💵 Revenue vs Cost Components", yaxis_title="$ Million")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Waterfall for selected year
        selected_year = st.selectbox("Select Year for Waterfall", sorted(df["year"].unique()), index=5)
        year_data = df[df["year"] == selected_year].iloc[0]
        
        fig = go.Figure(go.Waterfall(
            name="", orientation="v",
            x=["Revenue", "Fuel", "Carbon", "OPEX", "EBITDA"],
            y=[year_data["revenue_usd_M"], -year_data["fuel_cost_usd_M"], 
               -year_data["carbon_cost_usd_M"], -year_data["opex_usd_M"], year_data["ebitda_usd_M"]],
            measure=["relative", "relative", "relative", "relative", "total"],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            increasing={"marker": {"color": COLORS["success"]}},
            decreasing={"marker": {"color": COLORS["danger"]}},
            totals={"marker": {"color": COLORS["primary"]}}
        ))
        fig.update_layout(title=f"💧 Cashflow Waterfall - {selected_year}")
        st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("📊 View Raw Data"):
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Download cashflow_results.csv", df.to_csv(index=False), "cashflow_results.csv")


# =============================================================================
# CREDIT RESULTS PAGE
# =============================================================================

def page_credit_results():
    """Credit Rating Results page."""
    st.header("📈 Credit Rating Results")
    st.markdown("""
    **What this module calculates:**
    - **DSCR** = EBITDA / Debt Service (measures ability to pay debt)
    - **Credit Rating** = Based on KIS methodology thresholds
    - **Spread** = Additional yield required by lenders (basis points)
    - **Cost of Debt** = Risk-free rate + Spread
    
    **The Death Spiral:** Lower EBITDA → Lower DSCR → Downgrade → Higher Spread → Higher Interest → Even Lower EBITDA
    """)
    
    results = load_module_results(project_root)
    if "credit" not in results:
        st.warning("⚠️ No credit results found. Run the model first.")
        return
    
    df = results["credit"]
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    valid_dscr = df[df['dscr'] < 100]['dscr']
    with col1:
        st.metric("Average DSCR", f"{valid_dscr.mean():.2f}x")
    with col2:
        st.metric("Minimum DSCR", f"{valid_dscr.min():.2f}x")
    with col3:
        modal_rating = df["credit_rating"].mode()[0] if len(df) > 0 else "N/A"
        st.metric("Most Common Rating", modal_rating)
    with col4:
        st.metric("Max Spread", f"{df['spread_bps'].max():.0f} bps")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.line(
            df, x="year", y="dscr",
            title="📊 Debt Service Coverage Ratio (DSCR)",
            labels={"dscr": "DSCR", "year": "Year"},
            color_discrete_sequence=[COLORS["credit"]]
        )
        fig.add_hline(y=1.5, line_dash="dash", line_color="green", 
                      annotation_text="Investment Grade (1.5x)")
        fig.add_hline(y=1.25, line_dash="dash", line_color="orange",
                      annotation_text="Covenant (1.25x)")
        fig.add_hline(y=1.0, line_dash="dash", line_color="red",
                      annotation_text="Default Threshold (1.0x)")
        fig.update_yaxes(range=[0, max(3, valid_dscr.max() * 1.1)])
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Rating timeline with colors
        rating_order = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]
        rating_colors = {
            "AAA": "#1a5f7a", "AA": "#27ae60", "A": "#2ecc71",
            "BBB": "#f1c40f", "BB": "#e67e22", "B": "#e74c3c", "CCC": "#8e44ad"
        }
        
        fig = go.Figure()
        for rating in df["credit_rating"].unique():
            mask = df["credit_rating"] == rating
            fig.add_trace(go.Scatter(
                x=df.loc[mask, "year"],
                y=df.loc[mask, "credit_rating"],
                mode='markers',
                name=rating,
                marker=dict(size=12, color=rating_colors.get(rating, "#95a5a6"))
            ))
        fig.update_layout(
            title="📉 Credit Rating Migration",
            yaxis=dict(categoryorder='array', categoryarray=rating_order[::-1]),
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Spread and Cost of Debt
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.area(
            df, x="year", y="spread_bps",
            title="📈 Credit Spread Over Time",
            labels={"spread_bps": "Spread (bps)", "year": "Year"},
            color_discrete_sequence=[COLORS["danger"]]
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.line(
            df, x="year", y="cost_of_debt",
            title="💵 Cost of Debt Over Time",
            labels={"cost_of_debt": "Cost of Debt (%)", "year": "Year"},
            color_discrete_sequence=[COLORS["credit"]]
        )
        fig.update_yaxes(tickformat='.1%')
        st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("📊 View Raw Data"):
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Download credit_results.csv", df.to_csv(index=False), "credit_results.csv")


# =============================================================================
# FINAL ANALYSIS PAGE
# =============================================================================

def page_final_analysis():
    """Final Combined Analysis page."""
    st.header("🎯 Final Analysis")
    st.markdown("Combined results from all modules with summary metrics.")
    
    results = load_module_results(project_root)
    if "combined" not in results:
        st.warning("⚠️ No combined results found. Run the model first.")
        return
    
    df = results["combined"]
    
    # Key summary metrics
    st.subheader("📊 Summary Metrics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if 'revenue_usd' in df.columns:
            total_rev = df["revenue_usd"].sum() / 1e9
            st.metric("💵 Total Revenue", f"${total_rev:.1f}B")
    
    with col2:
        operating = df[df.get("operating_flag", pd.Series([1]*len(df))) == 1]
        st.metric("📅 Operating Years", len(operating))
    
    with col3:
        if 'dscr' in df.columns:
            valid_dscr = df[df['dscr'] < 100]['dscr']
            st.metric("📈 Avg DSCR", f"{valid_dscr.mean():.2f}x")
    
    with col4:
        if 'credit_rating' in df.columns:
            modal_rating = df["credit_rating"].mode()[0]
            st.metric("🏦 Modal Rating", modal_rating)
    
    with col5:
        if 'spread_bps' in df.columns:
            avg_spread = df["spread_bps"].mean()
            st.metric("📊 Avg Spread", f"{avg_spread:.0f} bps")
    
    # Combined timeline
    st.subheader("📈 Key Metrics Timeline")
    
    # Create multi-axis chart
    fig = go.Figure()
    
    if 'capacity_factor' in df.columns:
        fig.add_trace(go.Scatter(
            x=df["year"], y=df["capacity_factor"],
            name="Capacity Factor", yaxis="y1",
            line=dict(color=COLORS["transition"], width=2)
        ))
    
    if 'dscr' in df.columns:
        fig.add_trace(go.Scatter(
            x=df["year"], y=df["dscr"].clip(upper=5),
            name="DSCR", yaxis="y2",
            line=dict(color=COLORS["credit"], width=2)
        ))
    
    fig.update_layout(
        title="📊 Combined Metrics Over Time",
        xaxis=dict(title="Year"),
        yaxis=dict(title="Capacity Factor", side="left", range=[0, 1]),
        yaxis2=dict(title="DSCR", overlaying="y", side="right", range=[0, 5]),
        legend=dict(x=0.5, y=1.1, orientation="h")
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Full data table
    st.subheader("📋 Complete Results Table")
    st.dataframe(df, use_container_width=True, height=400)
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📥 Download model_results.csv",
            df.to_csv(index=False),
            "model_results.csv",
            "text/csv",
            use_container_width=True
        )
    with col2:
        excel_path = project_root / "results" / "Climate_Risk_Premium_Report.xlsx"
        if excel_path.exists():
            with open(excel_path, "rb") as f:
                st.download_button(
                    "📥 Download Excel Report",
                    f.read(),
                    "Climate_Risk_Premium_Report.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )


# =============================================================================
# RUN MODEL PAGE
# =============================================================================

def page_run_model():
    """Run Model page - execute pipeline with custom scenarios."""
    st.header("⚙️ Run Model")
    st.markdown("Execute the model pipeline with custom scenario selections.")
    
    inputs = load_input_data(project_root)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔄 Transition Settings")
        
        transition_scenario = st.selectbox(
            "Transition Scenario",
            list(inputs['transition'].keys()),
            index=0,
            help="Policy scenario affecting dispatch and carbon prices"
        )
        
        power_plan_options = ["official_10th_plan", "official_11th_plan", "none"]
        power_plan_scenario = st.selectbox(
            "Power Plan Scenario",
            power_plan_options,
            index=0,
            help="Korea government power supply plan for dispatch trajectory"
        )
    
    with col2:
        st.subheader("🌡️ Physical Settings")
        
        physical_scenario = st.selectbox(
            "Physical Scenario", 
            list(inputs['physical'].keys())[:8],  # First 8 options
            index=0,
            help="CLIMADA-based climate hazard scenario"
        )
        
        col_a, col_b = st.columns(2)
        with col_a:
            start_year = st.number_input("Start Year", 2024, 2050, 2024)
        with col_b:
            end_year = st.number_input("End Year", 2030, 2100, 2064)
    
    st.markdown("---")
    
    if st.button("🚀 Run Full Pipeline", type="primary", use_container_width=True):
        with st.spinner("Running model pipeline... This may take a few seconds."):
            try:
                results = run_full_pipeline(
                    base_dir=project_root,
                    transition_scenario=transition_scenario,
                    power_plan_scenario=power_plan_scenario if power_plan_scenario != "none" else None,
                    physical_scenario=physical_scenario,
                    start_year=start_year,
                    end_year=end_year,
                    save_outputs=True,
                )
                st.success("✅ Pipeline completed successfully!")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Transition Rows", len(results['transition']))
                with col2:
                    st.metric("Cashflow Rows", len(results['cashflow']))
                with col3:
                    st.metric("Combined Rows", len(results['combined']))
                
                st.info("📊 Results saved! Navigate to other pages to view the outputs.")
                st.cache_data.clear()
                
            except Exception as e:
                st.error(f"❌ Error running pipeline: {str(e)}")
                st.exception(e)


# =============================================================================
# SIDEBAR & MAIN
# =============================================================================

def main():
    st.sidebar.title("🔥 Climate Risk Premium")
    st.sidebar.markdown("**Samcheok Blue Power Analysis**")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "📑 Navigate",
        [
            "🏗️ Model Overview",
            "📁 Input Data",
            "🔄 Transition Results",
            "🌡️ Physical Results",
            "💰 Cashflow Results",
            "📈 Credit Results",
            "🎯 Final Analysis",
            "⚙️ Run Model",
        ]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📚 Data Sources")
    st.sidebar.markdown("""
    - 🇰🇷 MOTIE 10th/11th Power Plan
    - 🌍 ETH CLIMADA Platform
    - 🏦 KIS Rating Methodology
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Quick Stats")
    results = load_module_results(project_root)
    loaded = sum(1 for k in ["transition", "physical", "cashflow", "credit", "combined"] if k in results)
    st.sidebar.progress(loaded / 5)
    st.sidebar.caption(f"{loaded}/5 modules loaded")
    
    # Page routing
    if page == "🏗️ Model Overview":
        page_model_overview()
    elif page == "📁 Input Data":
        page_input_data()
    elif page == "🔄 Transition Results":
        page_transition_results()
    elif page == "🌡️ Physical Results":
        page_physical_results()
    elif page == "💰 Cashflow Results":
        page_cashflow_results()
    elif page == "📈 Credit Results":
        page_credit_results()
    elif page == "🎯 Final Analysis":
        page_final_analysis()
    elif page == "⚙️ Run Model":
        page_run_model()


if __name__ == "__main__":
    main()
