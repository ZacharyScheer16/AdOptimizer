import streamlit as st
import pandas as pd
import plotly.express as px
from model import run_clustering  # Importing your logic from model.py

# 1. Professional Page Setup
st.set_page_config(
    page_title="AdOptimizer AI | Logistics Module",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS for Contrast and Readability
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    
    /* Force Metric text to be Black/Dark Blue */
    [data-testid="stMetricValue"] {
        color: #1c2b46 !important;
        font-weight: bold !important;
    }
    [data-testid="stMetricLabel"] {
        color: #495057 !important;
    }
    
    /* Metric Card Styling */
    div[data-testid="column"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #e9ecef;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Sidebar
with st.sidebar:
    st.title("AdOptimizer v1.1")
    st.image("https://cdn-icons-png.flaticon.com/512/1055/1055644.png", width=80)
    st.write(f"**User:** testuser@volleyball.com") # Using your saved email
    st.write("**Module:** Logistics Marketing")
    st.divider()
    st.info("AI-powered clustering identifies budget waste in real-time.")

# 4. Main Header
st.title("🎯 Marketing Intelligence Dashboard")
uploaded_file = st.file_uploader("Upload Ad Export (CSV)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    with st.spinner('AI analyzing 1,000+ data points...'):
        results = run_clustering(df)

    if "error" in results:
        st.error(results["error"])
    else:
        # --- DATA PREP ---
        results_df = pd.DataFrame(results["detailed_results"])
        
        # 1. THE LIST COMPREHENSION: Identify risky groups
        # This converts string keys to integers to match the DataFrame
        risky_group_ids = [
            int(gid) for gid, info in results["group_insights"].items() 
            if info["status"] == "Risky"
        ]
        
        # 2. CALCULATE SAVINGS: Sum the 'Spend' of ads in those risky groups
        potential_savings = results_df[results_df['ad_group'].isin(risky_group_ids)]['Spend'].sum()

        # 5. KPI Row (Now with 5 columns)
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Ads Analyzed", f"{len(df):,}")
        k2.metric("Avg. CPC", f"${df['CPC'].mean():.2f}")
        k3.metric("Avg. CTR", f"{df['CTR'].mean():.3%}")
        k4.metric("AI Confidence", f"{results['model_accuracy_score']:.1%}")
        
        # Highlight the savings in a "Positive" green delta even though it's a reduction in cost
        k5.metric("Potential Savings", f"${potential_savings:,.2f}", delta="Budget Waste", delta_color="inverse")

        st.divider()

        # 6. Tabbed Interface
        tab1, tab2, tab3 = st.tabs(["📊 Executive Summary", "🔍 Detailed Audit", "⚙️ Raw Data"])

        with tab1:
            st.subheader("AI Performance Segments")
            cols = st.columns(len(results["group_insights"]))
            
            for i, (group_id, stats) in enumerate(results["group_insights"].items()):
                with cols[i]:
                    status_color = "green" if stats['status'] == "Scalable" else "red" if stats['status'] == "Risky" else "orange"
                    st.markdown(f"### Group {group_id}")
                    st.markdown(f":{status_color}[**{stats['label'].upper()}**]")
                    st.write(f"**Avg CPC:** ${stats['CPC']:.2f}")
                    st.write(f"**Avg CTR:** {stats['CTR']:.4%}")
                    st.info(f"💡 {stats['recommendation']}")
            
            # Interactive Plotly Chart
            st.divider()
            st.subheader("Spend vs. Efficiency Map")
            fig = px.scatter(results_df, x="Spend", y="CPC", color="ad_group", 
                             size="Clicks", hover_data=['ad_id'],
                             title="Efficiency Clusters (Bubble size = Clicks)",
                             template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("🔍 Individual Performance Audit")
            
            # Filter the main results dataframe for the audit list
            audit_df = results_df[results_df['ad_group'].isin(risky_group_ids)]

            if not audit_df.empty:
                st.warning(f"⚠️ Found {len(audit_df)} ads classified as 'Risky' or 'Money Pits'.")
                st.dataframe(
                    audit_df[['ad_id', 'Spend', 'Clicks', 'CPC', 'CTR', 'ad_group']].style.format({
                        'Spend': '${:.2f}',
                        'CPC': '${:.2f}',
                        'CTR': '{:.4%}'
                    }),
                    use_container_width=True
                )
            else:
                st.success("✅ No 'Risky' ads found. Performance is optimal.")

        with tab3:
            st.subheader("Full Dataset Table")
            st.dataframe(results_df, use_container_width=True)
else:
    st.info("Ready for analysis. Please upload your CSV file.")