import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

# --- 1. SESSION STATE INITIALIZATION ---
# user_id is now critical for the SQL foreign key relationship
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

st.set_page_config(page_title="AdOptimizer AI", layout="wide", page_icon="🎯")

# --- 2. UI STYLING ---
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

# --- 3. AUTHENTICATION FUNCTION ---
def show_auth_page():
    st.title("🔐 AdOptimizer Secure Access")
    st.write("Please log in to access your SQL-backed Logistics Module.")
    
    auth_tab, signup_tab = st.tabs(["Login", "Create Account"])
    
    with auth_tab:
        user = st.text_input("Username", key="login_user")
        pwd = st.text_input("Password", type="password", key="login_pwd")
        
        if st.button("Sign In", type="primary", use_container_width=True):
            payload = {"username": user, "password": pwd}
            try:
                res = requests.post("http://127.0.0.1:8000/login", json=payload)
                data = res.json()
                if data.get("status") == "success":
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    # Store the ID returned from SQL
                    st.session_state.user_id = data.get("user_id")
                    st.rerun() 
                else:
                    st.error(data.get("message", "Invalid credentials."))
            except Exception:
                st.error("Backend Error: Is uvicorn running?")

    with signup_tab:
        st.subheader("Register New User")
        new_user = st.text_input("Choose Username", key="reg_user")
        new_pass = st.text_input("Choose Password", type="password", key="reg_pwd")
        
        if st.button("Register Account", use_container_width=True):
            payload = {"username": new_user, "password": new_pass}
            try:
                res = requests.post("http://127.0.0.1:8000/signup", json=payload)
                data = res.json()
                if data.get("status") == "success":
                    st.success("Account created! You can now switch to the Login tab.")
                else:
                    st.error(data.get("message", "Signup failed."))
            except Exception:
                st.error("Backend connection lost.")

# --- 4. THE GATEKEEPER ---
if not st.session_state.logged_in:
    show_auth_page()
    st.stop() 

# --- 5. DASHBOARD CONTENT ---
with st.sidebar:
    st.title("AdOptimizer SQL")
    st.write(f"✅ **User:** {st.session_state.username}")
    st.write(f"🆔 **ID:** {st.session_state.user_id}")
    
    if st.button("🚪 Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
        
    st.divider()
    st.info("Storage: SQLite (adoptimizer.db)")

st.title("🎯 Marketing Intelligence Dashboard")

main_tab, audit_tab, history_tab = st.tabs(["📊 Executive Summary", "🔍 Detailed Audit", "📜 My History"])

with main_tab:
    uploaded_file = st.file_uploader("Upload Ad CSV", type="csv")

    if uploaded_file:
        with st.spinner('AI Clustering in progress...'):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
                response = requests.post("http://127.0.0.1:8000/upload-logistics", files=files)
                
                if response.status_code == 200:
                    full_payload = response.json()
                    results = full_payload["analysis"]
                    results_df = pd.DataFrame(results["detailed_results"])
                    
                    # Calculations
                    risky_ids = [int(gid) for gid, info in results["group_insights"].items() if info["status"] == "Risky"]
                    total_spend = float(results_df['Spend'].sum())
                    potential_savings = float(results_df[results_df['ad_group'].isin(risky_ids)]['Spend'].sum())

                    m1, m2, m3, m4, m5 = st.columns(5)
                    m1.metric("Ads Analyzed", f"{len(results_df):,}")
                    m2.metric("Avg CPC", f"${results_df['CPC'].mean():.2f}")
                    m3.metric("Avg CTR", f"{results_df['CTR'].mean():.3%}")
                    m4.metric("AI Confidence", f"{results['model_accuracy_score']:.1%}")
                    m5.metric("Waste Found", f"${potential_savings:,.2f}")

                    st.divider()

                    # --- NEW SQL SAVE LOGIC ---
                    st.subheader("Finalize SQL Audit")
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        if st.button("💾 Save to My Account", type="primary", use_container_width=True):
                            # We send the user_id so SQL knows who owns this record
                            audit_payload = {
                                "filename": uploaded_file.name,
                                "total_spend": total_spend,
                                "potential_savings": potential_savings,
                                "user_id": st.session_state.user_id 
                            }
                            save_res = requests.post("http://127.0.0.1:8000/save-audit", json=audit_payload)
                            if save_res.status_code == 200:
                                st.success(f"Audit Saved to SQLite!")
                            else:
                                st.error("Save failed.")
                    with c2:
                        st.info(f"Linking this audit to User ID: {st.session_state.user_id}")

                    # Performance charts
                    fig = px.scatter(results_df, x="Spend", y="CPC", color="ad_group", template="plotly_white", title="Spend vs Cost-Per-Click")
                    st.plotly_chart(fig, use_container_width=True)

                    with audit_tab:
                        st.subheader("Waste Analysis")
                        st.dataframe(results_df[results_df['ad_group'].isin(risky_ids)], use_container_width=True)
                
            except Exception as e:
                st.error(f"Analysis failed: {e}")

with history_tab:
    st.subheader(f"Personal Audit History for {st.session_state.username}")
    try:
        # We now query the personalized history endpoint
        history_url = f"http://127.0.0.1:8000/history/{st.session_state.user_id}"
        h_res = requests.get(history_url)
        
        if h_res.status_code == 200:
            history_data = h_res.json()
            if history_data:
                h_df = pd.DataFrame(history_data)
                # Cleaning up display
                if 'timestamp' in h_df.columns:
                    h_df['timestamp'] = pd.to_datetime(h_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
                
                st.dataframe(h_df[["timestamp", "filename", "total_spend", "potential_savings"]].sort_values("timestamp", ascending=False), use_container_width=True)
            else:
                st.info("No saved audits yet.")
    except Exception as e:
        st.error(f"History connection error: {e}")