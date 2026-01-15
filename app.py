"""
E-Warranty Portal - TRIAD Technologies
Multi-tenant platform for managing warranty projects and generating certificates.
"""
import streamlit as st
import pandas as pd
import os
import tempfile
import zipfile
import io
from PIL import Image
from pdf_engine import generate_bulk_certificates

# Page Config
st.set_page_config(
    page_title="E-Warranty Portal",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header { font-size: 2rem; font-weight: bold; color: #2C3E50; }
    .project-card { padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #f9f9f9; margin-bottom: 10px; }
    .success-text { color: green; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if 'user' not in st.session_state:
    st.session_state.user = None

# Mock Database - Internal Companies
if 'internal_companies' not in st.session_state:
    st.session_state.internal_companies = [
        {"id": 1, "name": "TRIAD Technologies", "logo_path": None, "is_active": True, "created_at": "2025-01-01"},
        {"id": 2, "name": "TRIAD Marketing", "logo_path": None, "is_active": True, "created_at": "2025-01-15"}
    ]

# Mock Database - Projects (Client Projects)
if 'projects' not in st.session_state:
    st.session_state.projects = [
        {"id": 1, "company_id": 1, "client_name": "Rajasthan Gramin Bank", "warranty_issue": "Branch Signage Warranty", "terms_text": "", "created_at": "2025-01-01"},
        {"id": 2, "company_id": 1, "client_name": "Test Client Corp", "warranty_issue": "Equipment Installation", "terms_text": "Sample Terms", "created_at": "2025-02-01"}
    ]

if 'users_db' not in st.session_state:
    st.session_state.users_db = [
        {"id": "u1", "email": "admin@triad.com", "role": "admin", "project_id": None},
        {"id": "u2", "email": "user@client.com", "role": "user", "project_id": 1}
    ]

if 'current_view' not in st.session_state:
    st.session_state.current_view = "Generate Warranty"

# Success message handler
if 'success_message' not in st.session_state:
    st.session_state.success_message = None

def show_success(message):
    """Store success message in session state to display after rerun"""
    st.session_state.success_message = message

def get_project_by_id(pid):
    for p in st.session_state.projects:
        if p['id'] == pid: return p
    return None

def get_company_by_id(cid):
    for c in st.session_state.internal_companies:
        if c['id'] == cid: return c
    return None

def get_client_name(project):
    """Helper to get client name - supports both old ('name') and new ('client_name') data"""
    return project.get('client_name') or project.get('name', 'Unknown')


# ================= AUTHENTICATION =================
def login_page():
    st.markdown("<h1 style='text-align: center;'>🔐 E-Warranty Portal</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.subheader("Sign In")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign In")
            
            if submit:
                # Mock Login Logic
                valid_user = None
                for u in st.session_state.users_db:
                    if u['email'] == email: 
                        valid_user = u
                        break
                
                if valid_user:
                    st.session_state.user = valid_user
                    st.session_state.current_view = "Generate Warranty"
                    st.success(f"Logged in as {valid_user['role'].upper()}")
                    st.rerun()
                elif email == "admin" or email == "user":
                     role = "admin" if email == "admin" else "user"
                     st.session_state.user = {"email": email, "role": role, "project_id": 1 if role == "user" else None}
                     st.session_state.current_view = "Generate Warranty"
                     st.rerun()
                else:
                    st.error("Invalid credentials.")
        st.info("**Test Credentials**:\n- `admin@triad.com`\n- `user@client.com`")

# ================= VIEWS =================

def render_header(user):
    """Top Header with Profile Info"""
    role_color = "red" if user['role'] == 'admin' else "blue"
    st.markdown(f"""
    <div style='display: flex; justify-content: space-between; align-items: center; padding: 10px; background-color: #f0f2f6; border-radius: 5px; margin-bottom: 20px;'>
        <h2 style='margin: 0;'>🛡️ E-Warranty Portal</h2>
        <div>
            <span style='font-weight: bold;'>👤 {user['email']}</span> | 
            <span style='color: {role_color}; font-weight: bold;'>{user['role'].upper()}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ================= 1. CREATE PROJECT =================
def view_create_project():
    st.header("📁 Create Project")
    
    tab_create, tab_edit = st.tabs(["➕ Create New", "✏️ Edit Existing"])
    
    with tab_create:
        st.subheader("Add New Client Project")
        
        with st.form("create_project_form", clear_on_submit=True):
            client_name = st.text_input("Client Name *", placeholder="e.g., Rajasthan Gramin Bank")
            warranty_issue = st.text_input("Warranty Issue Name *", placeholder="e.g., Branch Signage Warranty")
            terms_text = st.text_area("Terms & Conditions", height=150, placeholder="Enter warranty terms and conditions...")
            
            submitted = st.form_submit_button("Create Project", type="primary")
            
            if submitted:
                # Validation
                if not client_name.strip():
                    st.error("❌ Client Name is required!")
                elif not warranty_issue.strip():
                    st.error("❌ Warranty Issue Name is required!")
                else:
                    # Check for duplicate client name
                    existing_names = [get_client_name(p).lower() for p in st.session_state.projects]
                    if client_name.strip().lower() in existing_names:
                        st.error(f"❌ A project with client name \"{client_name.strip()}\" already exists!")
                    else:
                        # Create project
                        new_id = max([p['id'] for p in st.session_state.projects], default=0) + 1
                        st.session_state.projects.append({
                            "id": new_id,
                            "client_name": client_name.strip(),
                            "warranty_issue": warranty_issue.strip(),
                            "terms_text": terms_text,
                            "created_at": "Now"
                        })
                        show_success(f"✅ Project \"{client_name}\" created successfully!")
                        st.rerun()
    
    with tab_edit:
        st.subheader("Manage Existing Projects")
        
        if not st.session_state.projects:
            st.info("No projects yet. Create one from the 'Create New' tab.")
        else:
            for p in st.session_state.projects:
                with st.expander(f"📁 {get_client_name(p)}"):
                    # Edit Form
                    col1, col2 = st.columns(2)
                    with col1:
                        new_client = st.text_input("Client Name", get_client_name(p), key=f"client_{p['id']}")
                    with col2:
                        new_warranty = st.text_input("Warranty Issue", p.get('warranty_issue', ''), key=f"warranty_{p['id']}")
                    
                    new_terms = st.text_area("Terms & Conditions", p.get('terms_text', ''), height=100, key=f"terms_{p['id']}")
                    
                    col_save, col_delete = st.columns([3, 1])
                    with col_save:
                        if st.button("💾 Save Changes", key=f"save_{p['id']}"):
                            if not new_client.strip():
                                st.error("❌ Client Name cannot be empty!")
                            else:
                                p['client_name'] = new_client.strip()
                                p['warranty_issue'] = new_warranty.strip()
                                p['terms_text'] = new_terms
                                show_success("✅ Project updated successfully!")
                                st.rerun()
                    
                    with col_delete:
                        if st.button("🗑️ Delete", key=f"del_{p['id']}", type="secondary"):
                            st.session_state.projects = [x for x in st.session_state.projects if x['id'] != p['id']]
                            show_success("✅ Project deleted.")
                            st.rerun()


# ================= 2. INTERNAL COMPANY =================
def view_internal_company():
    st.header("🏢 Internal Company")
    
    tab_create, tab_edit = st.tabs(["➕ Add New", "✏️ Manage Existing"])
    
    with tab_create:
        st.subheader("Register New Internal Company")
        
        with st.form("create_company_form", clear_on_submit=True):
            company_name = st.text_input("Company Name *", placeholder="e.g., TRIAD Technologies")
            logo_file = st.file_uploader("Upload Company Logo", type=['png', 'jpg', 'jpeg'])
            
            submitted = st.form_submit_button("Register Company", type="primary")
            
            if submitted:
                # Validation
                if not company_name.strip():
                    st.error("❌ Company Name is required!")
                else:
                    # Check for duplicate company name
                    existing_names = [c['name'].lower() for c in st.session_state.internal_companies]
                    if company_name.strip().lower() in existing_names:
                        st.error(f"❌ A company with name \"{company_name.strip()}\" already exists!")
                    else:
                        # Handle logo upload
                        logo_path = None
                        if logo_file:
                            try:
                                os.makedirs("assets", exist_ok=True)
                                logo_path = os.path.join("assets", f"company_{len(st.session_state.internal_companies)+1}_{logo_file.name}")
                                with open(logo_path, 'wb') as f:
                                    f.write(logo_file.getbuffer())
                            except Exception as e:
                                st.error(f"❌ Error uploading logo: {e}")
                                logo_path = None
                        
                        # Create company
                        new_id = max([c['id'] for c in st.session_state.internal_companies], default=0) + 1
                        st.session_state.internal_companies.append({
                            "id": new_id,
                            "name": company_name.strip(),
                            "logo_path": logo_path,
                            "is_active": True,
                            "created_at": "Now"
                        })
                        show_success(f"✅ Internal Company \"{company_name}\" registered successfully!")
                        st.rerun()
    
    with tab_edit:
        st.subheader("Manage Internal Companies")
        
        if not st.session_state.internal_companies:
            st.info("No companies yet. Add one from the 'Add New' tab.")
        else:
            for c in st.session_state.internal_companies:
                status_icon = "🟢" if c['is_active'] else "🔴"
                with st.expander(f"{status_icon} {c['name']}"):
                    col_logo, col_details = st.columns([1, 3])
                    
                    with col_logo:
                        if c.get('logo_path') and os.path.exists(c['logo_path']):
                            st.image(c['logo_path'], width=100)
                        else:
                            st.markdown("*No logo*")
                        
                        # Logo upload
                        new_logo = st.file_uploader("Update Logo", type=['png', 'jpg', 'jpeg'], key=f"logo_{c['id']}")
                    
                    with col_details:
                        new_name = st.text_input("Company Name", c['name'], key=f"name_{c['id']}")
                        
                        col_actions = st.columns(3)
                        with col_actions[0]:
                            if st.button("💾 Save", key=f"save_c_{c['id']}"):
                                if not new_name.strip():
                                    st.error("❌ Company Name cannot be empty!")
                                else:
                                    c['name'] = new_name.strip()
                                    
                                    # Handle new logo
                                    if new_logo:
                                        try:
                                            os.makedirs("assets", exist_ok=True)
                                            logo_path = os.path.join("assets", f"company_{c['id']}_{new_logo.name}")
                                            with open(logo_path, 'wb') as f:
                                                f.write(new_logo.getbuffer())
                                            c['logo_path'] = logo_path
                                        except Exception as e:
                                            st.error(f"❌ Error uploading logo: {e}")
                                    
                                    show_success("✅ Company updated successfully!")
                                    st.rerun()
                        
                        with col_actions[1]:
                            status_label = "Deactivate" if c['is_active'] else "Activate"
                            if st.button(f"🔄 {status_label}", key=f"toggle_{c['id']}"):
                                c['is_active'] = not c['is_active']
                                action = "activated" if c['is_active'] else "deactivated"
                                show_success(f"✅ Company {action}!")
                                st.rerun()
                        
                        with col_actions[2]:
                            if st.button("🗑️ Delete", key=f"del_c_{c['id']}", type="secondary"):
                                # Check if company has projects
                                linked_projects = [p for p in st.session_state.projects if p.get('company_id') == c['id']]
                                if linked_projects:
                                    st.error(f"❌ Cannot delete. {len(linked_projects)} project(s) linked to this company.")
                                else:
                                    st.session_state.internal_companies = [x for x in st.session_state.internal_companies if x['id'] != c['id']]
                                    show_success("✅ Company deleted.")
                                    st.rerun()


# ================= 3. GENERATE WARRANTY =================
def view_generate_warranty(user):
    st.header("🏭 Generate Warranty")
    
    # Get active companies
    companies = [c for c in st.session_state.internal_companies if c['is_active']]
    
    if not companies:
        st.error("❌ No internal companies available. Please create one first.")
        return
    
    if not st.session_state.projects:
        st.error("❌ No projects available. Please create a project first.")
        return

    # Selection Layout - Internal Company & Warranty Issue
    c1, c2 = st.columns(2)
    
    with c1:
        selected_company_name = st.selectbox(
            "Select Internal Company", 
            options=[c['name'] for c in companies],
            index=0
        )
        active_company = next(c for c in companies if c['name'] == selected_company_name)
    
    with c2:
        # Show warranty issues (projects) - can filter by company or show all
        project_options = st.session_state.projects
        warranty_issues = [p.get('warranty_issue', get_client_name(p)) for p in project_options]
        
        selected_warranty = st.selectbox(
            "Select Warranty Issue Name",
            options=warranty_issues,
            index=0
        )
        active_project = next(p for p in project_options if p.get('warranty_issue', get_client_name(p)) == selected_warranty)
    
    st.divider()
    
    # Files with inline help
    col_file, col_photo = st.columns(2)
    with col_file:
        excel_file = st.file_uploader("Upload Branch Data (Excel)", type=['xlsx', 'xls'])
        
        # Read pre-created template file for download
        template_path = "warranty_data_template.xlsx"
        if os.path.exists(template_path):
            with open(template_path, "rb") as f:
                template_bytes = f.read()
            st.download_button(
                label="📥 Download Sample Excel Template",
                data=template_bytes,
                file_name="warranty_data_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
        else:
            st.warning("Template file not found")
    with col_photo:
        photo_files = st.file_uploader("Upload Site Photos", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
        # Photo naming format guide
        st.markdown("""
**📸 Photo Naming Format:**
| Format | Type | Example |
|--------|------|---------|
| `branch_code_1.jpg` | Complete Board | `101_1.jpg` |
| `branch_code_2.jpg` | Only Fascia | `101_2.jpg` |
| `branch_code_3.jpg` | Fascia + LED | `101_3.jpg` |
""")

    # Action
    if excel_file and photo_files:
        if st.button("Generate Certificates", type="primary"):
            with st.spinner("Processing..."):
                try:
                    df = pd.read_excel(excel_file)
                    
                    images_dict = {}
                    with tempfile.TemporaryDirectory() as temp_dir:
                        for uploaded_file in photo_files:
                            file_path = os.path.join(temp_dir, uploaded_file.name)
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            name_without_ext = os.path.splitext(uploaded_file.name)[0]
                            images_dict[name_without_ext] = file_path
                        
                        # Branding from selected company and project
                        # Get client name from project (for "This warranty is issued to..." line)
                        project_client_name = active_project.get('client_name') or active_project.get('warranty_issue') or selected_warranty
                        branding = {
                            "company_name": active_company['name'],
                            "logo_path": active_company.get('logo_path'),
                            "client_name": project_client_name,
                            "terms_text": active_project.get('terms_text', ''),
                            "warranty_issue": selected_warranty
                        }
                        
                        legacy_letterhead = "triad_letterhead.jpg" if os.path.exists("triad_letterhead.jpg") else None
                        output_dir = os.path.join(temp_dir, "output")
                        os.makedirs(output_dir, exist_ok=True)
                        
                        generated = generate_bulk_certificates(
                            df, images_dict, output_dir, branding
                        )
                        
                        if generated:
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(zip_buffer, "w") as zf:
                                for pdf in generated:
                                    zf.write(pdf, arcname=os.path.basename(pdf))
                            st.success(f"✅ Generated {len(generated)} certificates for {active_company['name']}!")
                            st.download_button("Download ZIP", zip_buffer.getvalue(), f"Certificates_{active_company['name']}.zip", "application/zip")
                        else:
                            st.warning("⚠️ No files were generated.")
                except Exception as e:
                    st.error(f"❌ Error: {e}")


# ================= 4. MANAGE USERS =================
def view_manage_users():
    st.header("👥 Manage Users")
    
    # Create User
    with st.expander("➕ Add New User", expanded=True):
        c1, c2 = st.columns(2)
        u_email = c1.text_input("User Email *")
        u_password = c2.text_input("Password *", type="password")
        
        u_role = st.selectbox("Role", ["user", "admin"])
        
        if st.button("Add User"):
            if not u_email.strip():
                st.error("❌ Email is required!")
            elif not u_password.strip():
                st.error("❌ Password is required!")
            else:
                # Check for duplicate email
                existing_emails = [u['email'].lower() for u in st.session_state.users_db]
                if u_email.strip().lower() in existing_emails:
                    st.error(f"❌ A user with email \"{u_email.strip()}\" already exists!")
                else:
                    st.session_state.users_db.append({
                        "id": f"u{len(st.session_state.users_db)+1}",
                        "email": u_email.strip(),
                        "password": u_password.strip(),
                        "role": u_role
                    })
                    show_success(f"✅ User \"{u_email}\" added successfully!")
                    st.rerun()
            
    # List Users
    st.divider()
    st.subheader("Existing Users")
    user_data = []
    for u in st.session_state.users_db:
        user_data.append({"Email": u['email'], "Role": u['role']})
    
    st.table(pd.DataFrame(user_data))


# ================= DASHBOARD =================
def dashboard():
    user = st.session_state.user
    render_header(user)
    
    # Sidebar Navigation
    with st.sidebar:
        st.markdown("### 🧭 Menu")
        
        # 4 Menu Options
        options = ["Create Project", "Internal Company", "Generate Warranty"]
        if user['role'] == 'admin':
            options.append("Manage Users")
        
        # Ensure current_view is valid
        if st.session_state.current_view not in options:
            st.session_state.current_view = options[0]
            
        selection = st.radio(
            "Go to:", 
            options, 
            index=options.index(st.session_state.current_view)
        )
        st.session_state.current_view = selection
        
        st.divider()
        if st.button("🚪 Logout"):
            st.session_state.user = None
            st.rerun()
            
    # Render Views
    if selection == "Create Project":
        view_create_project()
    elif selection == "Internal Company":
        view_internal_company()
    elif selection == "Generate Warranty":
        view_generate_warranty(user)
    elif selection == "Manage Users":
        view_manage_users()
    
    # Display success message at bottom (after rerun)
    if st.session_state.success_message:
        st.success(st.session_state.success_message)
        st.session_state.success_message = None  # Clear after showing

# Run App
if st.session_state.user:
    dashboard()
else:
    login_page()
