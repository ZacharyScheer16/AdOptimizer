import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io
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
    .high-priority { border: 2px solid #ff4b4b !important; background-color: #fffafa; }
    .low-priority { border: 1px solid #e9ecef !important; }
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
                res = requests.post("http://backend:8000/login", data=payload)
                if res.status_code == 200:
                    data = res.json()
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.session_state.token = data.get("access_token")
                    st.rerun() 
                else:
                    st.error("Invalid credentials or server error.")
            except Exception as e:
                st.error(f"Backend Error: {e}")

    with signup_tab:
        st.subheader("Register New User")
        new_user = st.text_input("Choose Username", key="reg_user")
        new_pass = st.text_input("Choose Password", type="password", key="reg_pwd")
        
        if st.button("Register Account", use_container_width=True):
            payload = {"username": new_user, "password": new_pass}
            try:
                res = requests.post("http://backend:8000/signup", json=payload)
                data = res.json()
                if res.status_code == 200 and data.get("status") == "success":
                    st.success("Account created! You can now switch to the Login tab.")
                else:
                    st.error(data.get("detail", "Signup failed."))
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
                response = requests.post(
                    "http://backend:8000/upload-logistics", 
                    files=files, 
                    headers=get_auth_header()
                )
                
                if response.status_code == 200:
                    full_payload = response.json()
                    results = full_payload["analysis"]
                    results_df = pd.DataFrame(results["detailed_results"])
                    
                    st.success(f"File analyzed and saved! (DB ID: {full_payload.get('database_id')})")

                    m1, m2, m3, m4, m5 = st.columns(5)
                    m1.metric("Ads Analyzed", f"{len(results_df):,}")
                    m2.metric("Avg CPC", f"${results_df['CPC'].mean():.2f}")
                    m3.metric("Avg CTR", f"{results_df['CTR'].mean():.3%}")
                    m4.metric("AI Confidence", f"{results['model_accuracy_score']:.1%}")
                    m5.metric("Waste Found", f"${full_payload['summary']['savings']:,.2f}")

                    st.divider()

                    fig = px.scatter(results_df, x="Spend", y="CPC", color="ad_group", 
                                   template="plotly_white", title="Spend vs Cost-Per-Click")
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
    
    # --- GLOBAL FILTER UI ---
    st.write("### 🎯 Targeting Filter")
    target_threshold = st.slider("Min Savings Target ($)", 0.0, 1000.0, 100.0, 10.0)
    st.caption(f"Showing which audits exceed ${target_threshold} in potential waste.")
    st.divider()

    try:
        h_res = requests.get("http://backend:8000/history", headers=get_auth_header())
        
        if h_res.status_code == 200:
            history_data = h_res.json()
            if history_data:
                for item in reversed(history_data):
                    # Fundamental: Call the Backend Filter Endpoint for each audit
                    f_url = f"http://backend:8000/filter-details/{item['id']}?min_savings_target={target_threshold}"
                    f_res = requests.get(f_url, headers=get_auth_header()).json()
                    
                    # Determine styling based on backend "status"
                    is_high = f_res.get("status") == "high_priority"
                    border_color = "#ff4b4b" if is_high else "#e9ecef"
                    
                    with st.container(border=True):
                        # Visual Cue: Red Label for High Risk
                        if is_high:
                            st.error(f"🔥 {f_res['message']}")
                        
                        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                        
                        with col1:
                            st.write(f"📄 **{item['filename']}**")
                            ts = pd.to_datetime(item['timestamp']).strftime('%Y-%m-%d %H:%M')
                            st.caption(f"Audit Date: {ts} | ID: {item['id']}")
                            
                            with st.expander("✏️ Rename"):
                                new_name = st.text_input("New Name", value=item['filename'], key=f"input_{item['id']}")
                                if st.button("Confirm Rename", key=f"ren_{item['id']}"):
                                    ren_res = requests.patch(
                                        f"http://backend:8000/rename-audit/{item['id']}?new_name={new_name}",
                                        headers=get_auth_header()
                                    )
                                    if ren_res.status_code == 200:
                                        st.rerun()

                        col2.metric("Waste", f"${item['potential_savings']:,.2f}")
                        col3.metric("Total Spend", f"${item['total_spend']:,.2f}")
                        
                        if col4.button("🗑️ Delete", key=f"del_{item['id']}", use_container_width=True):
                            del_res = requests.delete(
                                f"http://backend:8000/delete-audit/{item['id']}", 
                                headers=get_auth_header()
                            )
                            if del_res.status_code == 200:
                                st.rerun()
            else:
                st.info("No saved audits yet.")
        else:
            st.error("Session expired or server error.")
            
    except Exception as e:
        st.error(f"History connection error: {e}")