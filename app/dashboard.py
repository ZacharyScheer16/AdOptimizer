import streamlit as st
import pandas as pd
import plotly.express as px
import requests  # This is the "Waiter" that talks to FastAPI

st.set_page_config(page_title="AdOptimizer AI", layout="wide", page_icon="🎯")

# --- UI STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { color: #1c2b46 !important; font-weight: bold !important; }
    div[data-testid="column"] {
        background-color: #ffffff; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); border: 1px solid #e9ecef;
    }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.title("AdOptimizer v1.0")
    st.write("**User:** testuser@volleyball.com")
    st.divider()
    st.info("Logistics Module: High-Confidence Audit")

st.title("🎯 Marketing Intelligence Dashboard")
uploaded_file = st.file_uploader("Upload Ad CSV", type="csv")

if uploaded_file:
    # --- THE FASTAPI CONNECTION ---
    with st.spinner('Waiting for FastAPI Backend...'):
        try:
            # 1. Prepare the file to be sent over HTTP
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
            
            # 2. POST the file to your FastAPI server
            # Note: Make sure your FastAPI is running on port 8000!
            response = requests.post("http://127.0.0.1:8000/upload-logistics", files=files)
            
            if response.status_code == 200:
                # 3. Get the AI results back from the API
                full_payload = response.json()
                results = full_payload["analysis"] # Extracting the 'analysis' key from your FastAPI return
                
                results_df = pd.DataFrame(results["detailed_results"])
                
                # --- UI LOGIC (METRICS) ---
                risky_ids = [int(gid) for gid, info in results["group_insights"].items() if info["status"] == "Risky"]
                potential_savings = results_df[results_df['ad_group'].isin(risky_ids)]['Spend'].sum()

                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("Ads Analyzed", f"{len(results_df):,}")
                m2.metric("Avg CPC", f"${results_df['CPC'].mean():.2f}")
                m3.metric("Avg CTR", f"{results_df['CTR'].mean():.3%}")
                m4.metric("AI Confidence", f"{results['model_accuracy_score']:.1%}")
                m5.metric("Potential Savings", f"${potential_savings:,.2f}", delta="Waste Identified", delta_color="inverse")

                st.divider()

                # --- TABS FOR RESULTS ---
                tab1, tab2 = st.tabs(["📊 Executive Summary", "🔍 Detailed Audit"])

                with tab1:
                    st.subheader("Performance Segments")
                    cols = st.columns(len(results["group_insights"]))
                    for i, (group_id, stats) in enumerate(results["group_insights"].items()):
                        with cols[i]:
                            color = "red" if stats['status'] == "Risky" else "green"
                            st.markdown(f"### Group {group_id}")
                            st.markdown(f":{color}[**{stats['label'].upper()}**]")
                            st.write(f"**CPC:** ${stats['CPC']:.2f} | **CTR:** {stats['CTR']:.3%}")
                    
                    fig = px.scatter(results_df, x="Spend", y="CPC", color="ad_group", size="Clicks")
                    st.plotly_chart(fig, use_container_width=True)

                with tab2:
                    st.subheader("Waste Audit")
                    audit_df = results_df[results_df['ad_group'].isin(risky_ids)]
                    st.dataframe(audit_df)
            
            else:
                st.error(f"Error from FastAPI: {response.text}")
                
        except requests.exceptions.ConnectionError:
            st.error("FRONTEND CANNOT FIND BACKEND: Did you run 'uvicorn main:app --reload'?")