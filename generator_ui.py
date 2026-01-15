import streamlit as st
import pandas as pd
import io
import os
import zipfile
import tempfile
from pdf_engine import generate_bulk_certificates

def create_sample_excel():
    """Generates a sample Excel file in memory for the user to download."""
    data = {
        'branch_code': [101, 102],
        'ifsc_code': ['RBGB0000101', 'RBGB0000102'],
        'installation_date': ['2025-01-01', '2025-01-05'],
        'type_of_office': ['Branch Office', 'Sub-Office'],
        'branch_name': ['Jaipur Main', 'Udaipur City'],
        'branch_person_name': ['Rajesh Kumar', 'Amit Singh'],
        'contact_number': ['9876543210', '9876543211'],
        'city_name': ['Jaipur', 'Udaipur'],
        'address': ['MG Road, Near City Center', 'Lake View Road'],
        'district': ['Jaipur', 'Udaipur'],
        'state': ['Rajasthan', 'Rajasthan'],
        'rbd': ['Jaipur Zone', 'Udaipur Zone'],
        'complete_board_size': ['8x4', None],
        'complete_board_qty': [1, 0],
        'complete_board_sqft': [32, 0],
        'only_fascia_replacement_size': [None, '10x5'],
        'only_fascia_replacement_qty': [0, 1],
        'only_fascia_replacement_sqft': [0, 50],
        'fascia_+_led_replacement_size': [None, None],
        'fascia_+_led_replacement_qty': [0, 0],
        'fascia_+_led_replacement_sqft': [0, 0],
        'led_module_qty': [0, 0],
        'power_supply_watt': [0, 0]
    }
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def check_photo_match(df, uploaded_images):
    """
    Validates which rows in the DataFrame have matching photos uploaded.
    Returns: A DataFrame with validation status.
    """
    # 1. Map Uploaded Filenames (normalize)
    # We define what we HAVE
    # uploaded_images is a list of UploadedFile objects or paths
    # We store valid keys: "3_1", "101_2" etc (No extension)
    
    available_keys = set()
    for img in uploaded_images:
        # Handle both UploadedFile object and string path (if zip extracted)
        name = img.name if hasattr(img, 'name') else os.path.basename(img)
        key = os.path.splitext(name)[0]
        available_keys.add(key)
        
    # 2. Iterate Excel to calculate EXPECTED keys
    validation_rows = []
    
    for idx, row in df.iterrows():
        try:
            b_code = str(row.get('branch_code', '')).split('.')[0]
            if not b_code: continue
            
            # Check for Warranty Types
            # Type 1: Complete Board
            if pd.notna(row.get('complete_board_size')):
                expected = f"{b_code}_1"
                status = "✅ Ready" if expected in available_keys else "❌ Missing"
                validation_rows.append({
                    "Branch": b_code,
                    "Type ID": "1 (Complete)",
                    "Expected Photo": f"{expected}.jpg",
                    "Status": status
                })

            # Type 2: Fascia Only
            if pd.notna(row.get('only_fascia_replacement_size')):
                expected = f"{b_code}_2"
                status = "✅ Ready" if expected in available_keys else "❌ Missing"
                validation_rows.append({
                    "Branch": b_code,
                    "Type ID": "2 (Fascia)",
                    "Expected Photo": f"{expected}.jpg",
                    "Status": status
                })
                
            # Type 3: Fascia + LED
            if pd.notna(row.get('fascia_+_led_replacement_size')):
                expected = f"{b_code}_3"
                status = "✅ Ready" if expected in available_keys else "❌ Missing"
                validation_rows.append({
                    "Branch": b_code,
                    "Type ID": "3 (Fascia+LED)",
                    "Expected Photo": f"{expected}.jpg",
                    "Status": status
                })
                
        except Exception as e:
            validation_rows.append({
                "Branch": "Error",
                "Type ID": "-",
                "Expected Photo": str(e),
                "Status": "⚠️ Data Error"
            })
            
    return pd.DataFrame(validation_rows)


def render_generator_ui():
    st.header("🏭 Warranty Generator")
    
    # --- SECTION 1: CONTEXT SELECTION ---
    if 'internal_companies' not in st.session_state:
        st.error("Session not initialized.")
        return

    # Filter Active Companies
    companies = [c for c in st.session_state.internal_companies if c['is_active']]
    
    col_ctx1, col_ctx2 = st.columns(2)
    with col_ctx1:
        sel_comp_name = st.selectbox("1. Internal Company", [c['name'] for c in companies])
        sel_company = next((c for c in companies if c['name'] == sel_comp_name), None)
    
    with col_ctx2:
        if sel_company:
            ps = [p for p in st.session_state.client_projects if p['company_id'] == sel_company['id'] and p['is_active']]
            sel_proj_name = st.selectbox("2. Client Project", [p['client_name'] for p in ps])
            sel_project = next((p for p in ps if p['client_name'] == sel_proj_name), None)
        else:
            sel_project = None

    if not sel_company or not sel_project:
        st.info("Please select a project to proceed.")
        return

    st.markdown("---")
    
    # --- SECTION 2: UPLOAD ZONE ---
    col_up1, col_up2 = st.columns(2)
    
    with col_up1:
        excel_file = st.file_uploader("3. Upload Excel Data (.xlsx)", type=['xlsx', 'xls'])
        # Sample download directly under Excel upload
        sample_bytes = create_sample_excel()
        st.download_button(
            label="📥 Download Sample Excel Template",
            data=sample_bytes,
            file_name="warranty_data_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col_up2:
        photo_files = st.file_uploader("4. Upload Site Photos", type=['jpg', 'jpeg', 'png', 'zip'], accept_multiple_files=True)
        # Photo naming guide directly under photo upload
        st.markdown("""
        **📸 Photo Naming Format:**
        | Format | Type | Example |
        |--------|------|---------|
        | `branch_code_1.jpg` | Complete Board | `101_1.jpg` |
        | `branch_code_2.jpg` | Only Fascia | `101_2.jpg` |
        | `branch_code_3.jpg` | Fascia + LED | `101_3.jpg` |
        """)

    # --- SECTION 3: LIVE PREVIEW & VALIDATION ---
    
    if excel_file and photo_files:
        st.subheader("🔍 Validation Dashboard")
        
        try:
            df = pd.read_excel(excel_file)
            
            # A. Data Preview
            with st.expander("📄 Excel Data Preview (First 5 Rows)", expanded=True):
                st.dataframe(df.head(), use_container_width=True)
            
            # B. Photo Validation
            st.markdown("**📸 Photo Match Status**")
            
            # Normalize photos input (handle list vs zip later if needed, prompt implies multi-select logic mainly)
            # If user uploads zip, we might need to peek inside, but standard st.file_uploader returns list of files if multiple=True.
            # If zip is single file, we need extraction logic. Assuming multi-file for now or simple handling.
            
            validation_df = check_photo_match(df, photo_files)
            
            # Styling validation table
            def color_status(val):
                color = '#d4edda' if 'Ready' in val else '#f8d7da'
                return f'background-color: {color}'
            
            st.dataframe(validation_df.style.applymap(color_status, subset=['Status']), use_container_width=True)
            
            # Check if likely safe to proceed
            ready_count = len(validation_df[validation_df['Status'].str.contains("Ready")])
            total_count = len(validation_df)
            
            if ready_count < total_count:
                st.warning(f"⚠️ Warning: Only {ready_count}/{total_count} items have matching photos. Missing items will generate without images.")

            # --- SECTION 4: GENERATE ACTION ---
            if st.button(f"Generate {ready_count} Certificates", type="primary"):
                with st.spinner("Generating..."):
                     # Prepare Images Dict
                    images_dict = {}
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Save uploaded photos to temp
                        for pf in photo_files:
                            # If it's a ZIP, extract it? For now assume individual files as per verification plan
                            # But if zip:
                            if pf.name.endswith('.zip'):
                                with zipfile.ZipFile(pf) as z:
                                    z.extractall(temp_dir)
                                    for name in z.namelist():
                                        if name.lower().endswith(('.jpg', '.jpeg', '.png')):
                                            key = os.path.splitext(os.path.basename(name))[0]
                                            images_dict[key] = os.path.join(temp_dir, name)
                            else:
                                path = os.path.join(temp_dir, pf.name)
                                with open(path, "wb") as f: f.write(pf.getbuffer())
                                key = os.path.splitext(pf.name)[0]
                                images_dict[key] = path
                        
                        # Config
                        branding = {
                            "logo_path": sel_company.get('logo_url'),
                            "client_name": sel_project['client_name'],
                            "terms_text": sel_project.get('terms_conditions', '')
                        }
                        
                        output_dir = os.path.join(temp_dir, "output")
                        os.makedirs(output_dir, exist_ok=True)
                        
                        # Generate
                        generated = generate_bulk_certificates(df, images_dict, output_dir, branding)
                        
                        if generated:
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(zip_buffer, "w") as zf:
                                for pdf in generated:
                                    zf.write(pdf, arcname=os.path.basename(pdf))
                            st.success(f"✅ Successfully generated {len(generated)} certificates!")
                            st.download_button("Download Certificates ZIP", zip_buffer.getvalue(), "Certificates.zip", "application/zip")
                        else:
                            st.error("No certificates were generated. Check errors.")

        except Exception as e:
            st.error(f"Error parsing data: {e}")
