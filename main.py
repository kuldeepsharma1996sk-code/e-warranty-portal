import streamlit as st
import os
from PIL import Image
import admin_modules

# Page Configuration
st.set_page_config(
    page_title="E-Warranty Portal",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .login-container { max-width: 400px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background: #fff; text-align: center; }
    .main-footer { text-align: center; color: #888; font-size: 0.8rem; margin-top: 50px; }
</style>
""", unsafe_allow_html=True)

# Session State Init
if 'user' not in st.session_state:
    st.session_state.user = None
if 'current_view' not in st.session_state:
    st.session_state.current_view = "generator"

# Initialize Mock Data consistently
admin_modules.init_mock_data()

# --- AUTHENTICATION VIEW ---
def login_view():
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        # 1. Logo
        logo_path = "assets/triad_tech_logo.jpg"
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
        else:
            st.markdown("## TRIAD Technologies")

        # 2. Login Card
        st.markdown("<div style='text-align: center; margin-bottom: 20px;'><h3>E-Warranty Portal</h3></div>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)
            
            if submitted:
                # Mock Auth Logic (Replace with auth.sign_in)
                user_found = None
                # Check mocked profiles in admin_modules
                # (We initialize them there, but might need to ensure they exist here or duplicate init)
                # To be safe, we rely on admin_modules mock init running once or check here.
                # Let's import the session state mock from admin_modules logic via a dummy call or check here.
                
                # Basic Mock Check if specific user
                if email == "admin@triad.com":
                    st.session_state.user = {"email": email, "role": "admin", "full_name": "System Admin"}
                    st.rerun()
                elif email == "user@triad.com":
                    st.session_state.user = {"email": email, "role": "user", "full_name": "Operations User"}
                    st.rerun()
                else:
                    st.error("Invalid Credentials. (Try admin@triad.com)")
                    
        st.markdown("<p style='text-align: center;'><a href='#'>Forgot Password?</a></p>", unsafe_allow_html=True)

# --- MAIN APP VIEW ---
def main_app():
    user = st.session_state.user
    role = user.get('role', 'user')
    
    # SYSTEM HEADER (Top Right Profile)
    # Using columns to create a header bar
    h1, h2 = st.columns([3, 1])
    with h2:
        st.markdown(f"<div style='text-align: right;'>👤 {user['email']} | <span style='color: blue;'>{role.upper()}</span></div>", unsafe_allow_html=True)
    st.divider()

    # SIDEBAR NAVIGATION
    with st.sidebar:
        # Small Logo
        if os.path.exists("assets/triad_tech_logo.jpg"):
            st.image("assets/triad_tech_logo.jpg", width=150)
        
        st.subheader("Menu")
        
        options = ["Warranty Generator"]
        if role == 'admin':
            options = ["Warranty Generator", "Client Projects", "Internal Companies", "User Management"]
            
        selection = st.radio("Go To", options)
        
        st.divider()
        if st.button("Log Out"):
            st.session_state.user = None
            st.rerun()
            
    # ROUTING
    if selection == "Warranty Generator":
        admin_modules.render_warranty_generator()
    elif selection == "User Management" and role == 'admin':
        admin_modules.render_user_management()
    elif selection == "Internal Companies" and role == 'admin':
        admin_modules.render_company_management()
    elif selection == "Client Projects" and role == 'admin':
        admin_modules.render_project_management()

    # GLOBAL FOOTER
    st.markdown("---")
    st.markdown("<div class='main-footer'>Powered by TRIAD Technologies</div>", unsafe_allow_html=True)


# --- ENTRY POINT ---
if __name__ == "__main__":
    if st.session_state.user:
        main_app()
    else:
        login_view()
