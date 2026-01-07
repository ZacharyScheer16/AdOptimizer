import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

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

# --- SIDEBAR ---
with st.sidebar:
    st.title("AdOptimizer v1.0")
    st.write("**User:** testuser@volleyball.com")
    st.divider()
    st.info("Logistics Module: High-Confidence Audit")
    
    if st.button("🔄 Refresh Application"):
        st.rerun()

st.title("🎯 Marketing Intelligence Dashboard")

# --- TABS SETUP ---
main_tab, audit_tab, history_tab = st.tabs(["📊 Executive Summary", "🔍 Detailed Audit", "📜 Audit History"])

with main_tab:
    uploaded_file = st.file_uploader("Upload Ad CSV", type="csv")

    if uploaded_file:
        with st.spinner('Analyzing Logistics Data...'):
            try:
                # 1. POST file to FastAPI
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
                response = requests.post("http://127.0.0.1:8000/upload-logistics", files=files)
                
                if response.status_code == 200:
                    full_payload = response.json()
                    results = full_payload["analysis"]
                    results_df = pd.DataFrame(results["detailed_results"])
                    
                    # --- METRICS CALCULATION ---
                    risky_ids = [int(gid) for gid, info in results["group_insights"].items() if info["status"] == "Risky"]
                    total_spend = float(results_df['Spend'].sum())
                    potential_savings = float(results_df[results_df['ad_group'].isin(risky_ids)]['Spend'].sum())

                    m1, m2, m3, m4, m5 = st.columns(5)
                    m1.metric("Ads Analyzed", f"{len(results_df):,}")
                    m2.metric("Avg CPC", f"${results_df['CPC'].mean():.2f}")
                    m3.metric("Avg CTR", f"{results_df['CTR'].mean():.3%}")
                    m4.metric("AI Confidence", f"{results['model_accuracy_score']:.1%}")
                    m5.metric("Potential Savings", f"${potential_savings:,.2f}", delta="Waste Identified", delta_color="inverse")

                    st.divider()

                    # --- THE SAVE LOGIC ---
                    st.subheader("Finalize Audit")
                    col_btn, col_txt = st.columns([1, 2])
                    
                    with col_txt:
                        st.write(f"**Ready to log:** `{uploaded_file.name}`")
                        st.write(f"Total identified waste to be tracked: **${potential_savings:,.2f}**")

                    with col_btn:
                        # Prepare JSON summary
                        audit_summary = {
                            "filename": uploaded_file.name,
                            "total_spend": total_spend,
                            "potential_savings": potential_savings,
                            "ads_count": len(results_df)
                        }
                        
                        if st.button("💾 Save Audit to History", type="primary"):
                            save_res = requests.post("http://127.0.0.1:8000/save-audit", json=audit_summary)
                            if save_res.status_code == 200:
                                st.success(f"Audit Logged! ID: {save_res.json().get('entry_id')}")
                            else:
                                st.error("Save Failed.")

                    st.divider()

                    # --- PERFORMANCE VISUALS ---
                    st.subheader("AI Performance Segments")
                    cols = st.columns(len(results["group_insights"]))
                    for i, (group_id, stats) in enumerate(results["group_insights"].items()):
                        with cols[i]:
                            color = "red" if stats['status'] == "Risky" else "green"
                            st.markdown(f"### Group {group_id}")
                            st.markdown(f":{color}[**{stats['label'].upper()}**]")
                            st.write(f"**CPC:** ${stats['CPC']:.2f}")
                            st.write(f"**CTR:** {stats['CTR']:.3%}")
                    
                    fig = px.scatter(results_df, x="Spend", y="CPC", color="ad_group", size="Clicks", template="plotly_white")
                    st.plotly_chart(fig, width="stretch")

                    # --- POPULATE AUDIT TAB ---
                    with audit_tab:
                        st.subheader("Waste Audit (High Priority Items)")
                        audit_df = results_df[results_df['ad_group'].isin(risky_ids)]
                        if not audit_df.empty:
                            st.dataframe(audit_df, width="stretch")
                        else:
                            st.success("No risky ads detected in this dataset.")
                
                else:
                    st.error(f"Error from FastAPI: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("FRONTEND CANNOT FIND BACKEND: Is uvicorn running?")

# --- HISTORY TAB ---
with history_tab:
    st.subheader("Database Audit Logs")
    try:
        history_response = requests.get("http://127.0.0.1:8000/history")
        if history_response.status_code == 200:
            history_data = history_response.json()
            if history_data:
                h_df = pd.DataFrame(history_data)
                # Ensure columns exist before ordering
                available_cols = ["Timestamp", "filename", "total_spend", "potential_savings", "ads_count"]
                display_cols = [c for c in available_cols if c in h_df.columns]
                
                st.dataframe(h_df[display_cols].sort_values(by="Timestamp", ascending=False), width="stretch")
            else:
                st.info("The history is currently empty. Save an audit to see it here.")
    except Exception as e:
        st.error(f"Could not load history: {e}")