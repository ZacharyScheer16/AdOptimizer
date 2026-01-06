import streamlit as st
import pandas as pd
import plotly.express as px
from model import run_clustering

st.set_page_config(page_title="AdOptimizer AI", layout="wide", page_icon="🎯")

# Visibility CSS: Fixes the white-on-white text issue
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { color: #1c2b46 !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] { color: #495057 !important; }
    div[data-testid="column"] {
        background-color: #ffffff; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); border: 1px solid #e9ecef;
    }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.title("AdOptimizer v1.0 (Restored)")
    st.write(f"**User:** testuser@volleyball.com")
    st.divider()
    st.info("Logistics Module: High-Confidence Audit")

st.title("🎯 Marketing Intelligence Dashboard")
uploaded_file = st.file_uploader("Upload Ad CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    with st.spinner('Running original AI model...'):
        results = run_clustering(df)

    if "error" in results:
        st.error(results["error"])
    else:
        results_df = pd.DataFrame(results["detailed_results"])
        
        # Calculate Savings
        risky_ids = [int(gid) for gid, info in results["group_insights"].items() if info["status"] == "Risky"]
        potential_savings = results_df[results_df['ad_group'].isin(risky_ids)]['Spend'].sum()

        # Top Metric Row
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Ads Analyzed", f"{len(results_df):,}")
        m2.metric("Avg CPC", f"${results_df['CPC'].mean():.2f}")
        m3.metric("Avg CTR", f"{results_df['CTR'].mean():.3%}")
        m4.metric("AI Confidence", f"{results['model_accuracy_score']:.1%}")
        m5.metric("Potential Savings", f"${potential_savings:,.2f}", delta="Waste Identified", delta_color="inverse")

        st.divider()

        tab1, tab2, tab3 = st.tabs(["📊 Executive Summary", "🔍 Detailed Audit", "⚙️ Raw Data"])

        with tab1:
            st.subheader("Performance Segments")
            cols = st.columns(len(results["group_insights"]))
            for i, (group_id, stats) in enumerate(results["group_insights"].items()):
                with cols[i]:
                    color = "green" if stats['status'] == "Scalable" else "red" if stats['status'] == "Risky" else "orange"
                    st.markdown(f"### Group {group_id}")
                    st.markdown(f":{color}[**{stats['label'].upper()}**]")
                    st.write(f"**CPC:** ${stats['CPC']:.2f} | **CTR:** {stats['CTR']:.3%}")
                    st.caption(f"💡 {stats['recommendation']}")
            
            st.divider()
            fig = px.scatter(results_df, x="Spend", y="CPC", color="ad_group", size="Clicks",
                             title="High-Confidence Cluster Map", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("High-Risk Ad Audit")
            audit_df = results_df[results_df['ad_group'].isin(risky_ids)]
            if not audit_df.empty:
                st.warning(f"Found {len(audit_df)} ads classified as 'Risky' or 'Money Pits'.")
                st.dataframe(audit_df[['ad_id', 'Spend', 'Clicks', 'CPC', 'CTR', 'ad_group']].style.format({
                    'Spend': '${:.2f}', 'CPC': '${:.2f}', 'CTR': '{:.4%}'
                }), use_container_width=True)
            else:
                st.success("No high-risk ads found!")

        with tab3:
            st.dataframe(results_df, use_container_width=True)