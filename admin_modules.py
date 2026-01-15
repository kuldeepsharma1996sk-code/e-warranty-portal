import streamlit as st
import pandas as pd
import os
import tempfile
import zipfile
import io
from streamlit_quill import st_quill
from pdf_engine import generate_bulk_certificates

# --- MOCK DATA INIT (Function to be called from main.py) ---
def init_mock_data():
    if 'internal_companies' not in st.session_state:
        st.session_state.internal_companies = [
            {"id": "c1", "name": "TRIAD Technologies", "logo_url": None, "is_active": True},
            {"id": "c2", "name": "TRIAD Marketing", "logo_url": None, "is_active": True}
        ]

    if 'client_projects' not in st.session_state:
        st.session_state.client_projects = [
            {"id": "p1", "company_id": "c1", "client_name": "Rajasthan Gramin Bank", "terms_conditions": "Standard Terms", "is_active": True},
            {"id": "p2", "company_id": "c2", "client_name": "Axis Bank", "terms_conditions": "<b>Axis Terms</b>", "is_active": True}
        ]

    if 'profiles' not in st.session_state:
        st.session_state.profiles = [
            {"id": "u1", "email": "admin@triad.com", "role": "admin", "full_name": "Admin User"},
            {"id": "u2", "email": "user@triad.com", "role": "user", "full_name": "Ops User"}
        ]


# --- MODULE A: USER MANAGEMENT ---
def render_user_management():
    st.subheader("👥 User Management")
    
    # Create User
    with st.expander("Create New User"):
        with st.form("create_user"):
            c1, c2, c3 = st.columns(3)
            email = c1.text_input("Email")
            name = c2.text_input("Full Name")
            role = c3.selectbox("Role", ["user", "admin"])
            password = st.text_input("Temporary Password", type="password") # In Supabase this triggers invite or signup
            
            if st.form_submit_button("Create User"):
                st.session_state.profiles.append({
                    "id": f"u{len(st.session_state.profiles)+1}",
                    "email": email, "role": role, "full_name": name
                })
                st.success(f"User {email} created!")
                st.rerun()

    # List Users
    st.markdown("### Existing Users")
    df = pd.DataFrame(st.session_state.profiles)
    st.dataframe(df, use_container_width=True)


# --- MODULE B: INTERNAL COMPANY MANAGEMENT ---
def render_company_management():
    st.subheader("🏢 Internal Company Management")
    
    # Create
    with st.expander("Register New Internal Company"):
        name = st.text_input("Company Name (e.g. TRIAD Marketing)")
        logo = st.file_uploader("Upload Company Logo", type=['png', 'jpg'])
        
        if st.button("Create Company"):
            # Mock Upload logic
            logo_path = None
            if logo:
                os.makedirs("assets", exist_ok=True)
                logo_path = os.path.join("assets", logo.name)
                with open(logo_path, "wb") as f: f.write(logo.getbuffer())
            
            st.session_state.internal_companies.append({
                "id": f"c{len(st.session_state.internal_companies)+1}",
                "name": name, "logo_url": logo_path, "is_active": True
            })
            st.success("Internal Company Registered!")
            st.rerun()
            
    # List
    for c in st.session_state.internal_companies:
        with st.expander(f"{c['name']} (Status: {'Active' if c['is_active'] else 'Inactive'})"):
            c1, c2 = st.columns([1, 4])
            with c1:
                if c['logo_url']: st.image(c['logo_url'], width=50)
                else: st.text("No Logo")
            with c2:
                # Toggle Status
                if st.button(f"Toggle Status##{c['id']}"):
                    c['is_active'] = not c['is_active']
                    st.rerun()

# --- MODULE C: CLIENT PROJECT MANAGEMENT ---
def render_project_management():
    st.subheader("📁 Client Project Management")
    
    # Create
    with st.form("new_project"):
        st.markdown("#### Create New Client Project")
        # Select Parent Company
        companies = st.session_state.internal_companies
        c_names = {c['name']: c['id'] for c in companies if c['is_active']}
        
        c1, c2 = st.columns(2)
        company_name = c1.selectbox("Select Internal Company", list(c_names.keys()))
        client_name = c2.text_input("Client Name (e.g. Rajasthan Gramin Bank)")
        
        st.markdown("**Terms & Conditions**")
        terms = st_quill(placeholder="Enter legal terms here...", key="quill_new")
        
        if st.form_submit_button("Create Project"):
            st.session_state.client_projects.append({
                "id": f"p{len(st.session_state.client_projects)+1}",
                "company_id": c_names[company_name],
                "client_name": client_name,
                "terms_conditions": terms,
                "is_active": True
            })
            st.success(f"Project '{client_name}' created under '{company_name}'!")
            st.rerun()

    # List
    st.markdown("### Active Projects")
    projects = st.session_state.client_projects
    for p in projects:
        st.info(f"**{p['client_name']}** (Internal: {p['company_id']})")


# --- MODULE 3: WARRANTY GENERATOR (The Core Logic) ---
def render_warranty_generator():
    from generator_ui import render_generator_ui
    render_generator_ui()
