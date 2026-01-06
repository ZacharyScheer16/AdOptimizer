import streamlit as st
import pandas as pd
import plotly.express as px
from model import run_clustering  # Logic from your model.py

# 1. Professional Page Setup
st.set_page_config(
    page_title="AdOptimizer AI | Logistics Module",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS Fix for Visibility (No more white-on-white!)
st.markdown("""
    <style>
    /* Main background */
    .main { background-color: #f8f9fa; }
    
    /* Force Metric text to be Black/Dark Blue for readability */
    [data-testid="stMetricValue"] {
        color: #1c2b46 !important;
        font-weight: bold !important;
    }
    [data-testid="stMetricLabel"] {
        color: #495057 !important;
    }
    
    /* Style the white metric cards */
    div[data-testid="column"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #e9ecef;
    }
    
    /* Clean up the Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1c2b46;
        color: white;
    }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] label {
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Sidebar for Settings & User Info
with st.sidebar:
    st.title("AdOptimizer v1.0")
    st.markdown("---")
    st.write("**User:** testuser@volleyball.com")
    st.write("**System:** Logistics Software v2.5")
    st.divider()
    st.info("This AI segments ads into clusters based on efficiency metrics (CPC/CTR).")

# 4. Main Header
st.title("🎯 Marketing Intelligence Dashboard")
uploaded_file = st.file_uploader("Upload marketing CSV (e.g., KAG_conversion_data.csv)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    with st.spinner('Calculating Performance Clusters...'):
        # results contains model_accuracy_score, group_insights, and detailed_results
        results = run_clustering(df)

    if "error" in results:
        st.error(results["error"])
    else:
        # 5. KPI Row (Now with readable text)
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Ads Analyzed", f"{len(df):,}")
        kpi2.metric("Avg. CPC", f"${df['CPC'].mean():.2f}")
        kpi3.metric("Avg. CTR", f"{df['CTR'].mean():.3%}")
        kpi4.metric("AI Confidence", f"{results['model_accuracy_score']:.1%}")

        st.divider()

        # 6. Tabbed Interface
        tab1, tab2, tab3 = st.tabs(["📊 Executive Summary", "🔍 Detailed Audit", "⚙️ Raw Data"])

        with tab1:
            st.subheader("AI Performance Segments")
            cols = st.columns(len(results["group_insights"]))
            
            for i, (group_id, stats) in enumerate(results["group_insights"].items()):
                with cols[i]:
                    # Color logic for labels
                    status_color = "green" if stats['status'] == "Scalable" else "red" if stats['status'] == "Risky" else "orange"
                    
                    st.markdown(f"### Group {group_id}")
                    st.markdown(f":{status_color}[**{stats['label'].upper()}**]")
                    st.write(f"**Avg CPC:** ${stats['CPC']:.2f}")
                    st.write(f"**Avg CTR:** {stats['CTR']:.4%}")
                    st.info(f"💡 {stats['recommendation']}")
            
            # Interactive Chart
            st.divider()
            st.subheader("Spend vs. Efficiency Map")
            results_df = pd.DataFrame(results["detailed_results"])
            fig = px.scatter(results_df, x="Spend", y="CPC", color="ad_group", 
                             size="Impressions", hover_data=['ad_id'],
                             title="Efficiency Clustering (Hover for Ad Details)",
                             template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("🔍 Individual Performance Audit")
            
            # Filter logic: Looking for 'Risky' status in group_insights
            risky_group_ids = [
                int(gid) for gid, info in results["group_insights"].items() 
                if info["status"] == "Risky"
            ]
            
            # Filter the main results dataframe
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
                st.success("✅ No 'Risky' ads found. All segments are performing optimally.")

        with tab3:
            st.subheader("All Analyzed Data")
            st.dataframe(results_df, use_container_width=True)
else:
    st.info("Please upload a CSV file to begin the AI analysis.")