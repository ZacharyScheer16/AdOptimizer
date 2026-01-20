import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

# --- 1. SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'token' not in st.session_state:
    st.session_state.token = None

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

# --- 3. HELPER FUNCTIONS ---
def get_auth_header():
    """Returns the security header needed for the Backend to identify the user."""
    return {"Authorization": f"Bearer {st.session_state.token}"}

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
                res = requests.post("http://backend:8000/login", json=payload)
                data = res.json()
                if data.get("status") == "success":
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    # CRITICAL: Store the JWT token for future requests
                    st.session_state.token = data.get("access_token")
                    st.rerun() 
                else:
                    st.error(data.get("message", "Invalid credentials."))
            except Exception:
                st.error("Backend Error: Is the backend container running?")

    with signup_tab:
        st.subheader("Register New User")
        new_user = st.text_input("Choose Username", key="reg_user")
        new_pass = st.text_input("Choose Password", type="password", key="reg_pwd")
        
        if st.button("Register Account", use_container_width=True):
            payload = {"username": new_user, "password": new_pass}
            try:
                res = requests.post("http://backend:8000/signup", json=payload)
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
    st.write(f"✅ **Logged in as:** {st.session_state.username}")
    
    if st.button("🚪 Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
        
    st.divider()
    st.info("Storage: SQLite (Internal Container)")

st.title("🎯 Marketing Intelligence Dashboard")

main_tab, audit_tab, history_tab = st.tabs(["📊 Executive Summary", "🔍 Detailed Audit", "📜 My History"])

with main_tab:
    uploaded_file = st.file_uploader("Upload Ad CSV", type="csv")

    if uploaded_file:
        with st.spinner('AI Clustering & Auto-Saving...'):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
                # Pass the Token in the headers so the backend knows who is uploading
                response = requests.post(
                    "http://backend:8000/upload-logistics", 
                    files=files, 
                    headers=get_auth_header()
                )
                
                if response.status_code == 200:
                    full_payload = response.json()
                    results = full_payload["analysis"]
                    results_df = pd.DataFrame(results["detailed_results"])
                    
                    st.success(f"File analyzed and saved to your history! (DB ID: {full_payload.get('database_id')})")

                    m1, m2, m3, m4, m5 = st.columns(5)
                    m1.metric("Ads Analyzed", f"{len(results_df):,}")
                    m2.metric("Avg CPC", f"${results_df['CPC'].mean():.2f}")
                    m3.metric("Avg CTR", f"{results_df['CTR'].mean():.3%}")
                    m4.metric("AI Confidence", f"{results['model_accuracy_score']:.1%}")
                    m5.metric("Waste Found", f"${full_payload['summary']['savings']:,.2f}")

                    st.divider()

                    fig = px.scatter(results_df, x="Spend", y="CPC", color="ad_group", template="plotly_white", title="Spend vs Cost-Per-Click")
                    st.plotly_chart(fig, use_container_width=True)

                    with audit_tab:
                        st.subheader("Waste Analysis (High Risk Clusters)")
                        risky_ids = [int(gid) for gid, info in results["group_insights"].items() if info["status"] == "Risky"]
                        st.dataframe(results_df[results_df['ad_group'].isin(risky_ids)], use_container_width=True)
                
                else:
                    st.error(f"Error {response.status_code}: {response.text}")

            except Exception as e:
                st.error(f"Analysis failed: {e}")

with history_tab:
    st.subheader(f"Personal Audit History for {st.session_state.username}")
    try:
        # We no longer pass the ID in the URL. The Header does the work!
        history_url = "http://backend:8000/history"
        h_res = requests.get(history_url, headers=get_auth_header())
        
        if h_res.status_code == 200:
            history_data = h_res.json()
            if history_data:
                # Show most recent first
                for item in reversed(history_data):
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([3, 1, 1])
                        col1.write(f"📄 **{item['filename']}**")
                        # Format the SQL timestamp
                        ts = pd.to_datetime(item['timestamp']).strftime('%Y-%m-%d %H:%M')
                        col1.caption(f"Audit Date: {ts}")
                        col2.metric("Waste Identified", f"${item['potential_savings']:,.2f}")
                        
                        '''if col3.button("🗑️ Delete", key=f"del_{item['id']}"):
                            del_res = requests.delete(
                                f"http://backend:8000/delete-audit/{item['id']}", 
                                headers=get_auth_header()
                            )
                            if del_res.status_code == 200:
                                st.rerun()'''
            else:
                st.info("No saved audits yet. Upload a file to start!")
        else:
            st.error("Could not retrieve history. Token might be expired.")
            
    except Exception as e:
        st.error(f"History connection error: {e}")