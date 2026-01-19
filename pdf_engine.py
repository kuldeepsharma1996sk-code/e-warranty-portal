from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Spacer, PageBreak, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
import pandas as pd
import os
from dateutil.relativedelta import relativedelta
from datetime import datetime

# Color Constants
TRIAD_ORANGE = colors.Color(0.9, 0.4, 0.1)  # Approx Orange/Rust
BANK_GREEN = colors.Color(0.0, 0.5, 0.0)    # Dark Green
HEADER_BG_COLOR = colors.whitesmoke
BORDER_COLOR = colors.black

def draw_header_footer(canvas, doc, branding_config):
    """
    Draws the Header (Logo + Title) and Footer on every page.
    branding_config: {
        'logo_path': str (path to Internal Company Logo),
        'client_name': str (e.g. Rajasthan Gramin Bank),
        'terms_text': str
    }
    """
    width, height = A4
    canvas.saveState()
    
    # --- HEADER ---
    # Logo (Top Left)
    logo_path = branding_config.get('logo_path')
    if logo_path and os.path.exists(logo_path):
        try:
            # Draw Internal Company Logo
            # Position: Top Left, small margin
            canvas.drawImage(logo_path, 0.5*inch, height - 1.2*inch, width=1.5*inch, height=0.8*inch, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    # Title (Centered)
    canvas.setFont("Helvetica-Bold", 20)
    canvas.drawCentredString(width/2, height - 1.0*inch, "WARRANTY CERTIFICATE")
    
    # Sub-Branding (Issued To...)
    client_name = branding_config.get('client_name', 'Client')
    canvas.setFont("Helvetica", 12)
    # canvas.drawCentredString(width/2, height - 1.3*inch, f"Issued to: {client_name}")
    # Moved to Body for "Green Bold" requirement, but header checks? 
    # User said: "Branding: 'This warranty is issued to Rajasthan Gramin Bank' (Client Name in Green/Bold)."
    # We will put that in the flowable story, not the fixed header, to control styling better.
    
    # --- FOOTER ---
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawCentredString(width/2, 0.5*inch, "This is a computer-generated warranty certificate. No signature required.")
    canvas.drawCentredString(width/2, 0.35*inch, "This document contains confidential terms and proprietary information")
    
    canvas.restoreState()


def generate_certificate(data_row, photos_map, output_path, branding_config):
    """
    Generates a single PDF certificate.
    data_row: dict of excel row data
    photos_map: dict of {filename_key: file_path} (e.g. '3_1': 'path/to/img')
    branding_config: dict
    """
    doc = SimpleDocTemplate(
        output_path, 
        pagesize=A4,
        rightMargin=0.5*inch, leftMargin=0.5*inch, 
        topMargin=1.5*inch, bottomMargin=1.0*inch
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # 1. Branding / "Issued To" Line
    client_name = branding_config.get('client_name', 'Client')
    
    # Custom Style for the green client name
    style_issued = ParagraphStyle(
        'IssuedTo',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    # "This warranty is issued to <font color=green><b>CLIENT NAME</b></font>"
    story.append(Paragraph(f"This warranty is issued to <font color='#008000'><b>{client_name}</b></font>", style_issued))
    story.append(Spacer(1, 10))

    # 2. Branch Details (Single Table)
    # Extract Data - using new column names
    branch_name = str(data_row.get('branch_name', 'N/A'))
    branch_code = str(data_row.get('branch_code', 'N/A')).split('.')[0]  # Clean float
    ifsc = str(data_row.get('ifsc_code', 'N/A'))
    city = str(data_row.get('city_name', 'N/A'))
    address = str(data_row.get('address', 'N/A'))
    district = str(data_row.get('district', 'N/A'))
    state = str(data_row.get('state', 'N/A'))
    
    # Installation Date & Warranty Period
    install_date_raw = data_row.get('installation_date', datetime.today())
    if isinstance(install_date_raw, str):
        try:
            install_date = datetime.strptime(install_date_raw, "%Y-%m-%d")
        except:
            install_date = datetime.today()
            try: install_date = datetime.strptime(install_date_raw, "%d-%m-%Y") 
            except: pass
    else:
        install_date = install_date_raw

    expiry_date = install_date + relativedelta(months=36)
    
    install_str = install_date.strftime("%d-%m-%Y")
    expiry_str = expiry_date.strftime("%d-%m-%Y")

    # Branch Info Table
    branch_data = [
        [f"Branch Code: {branch_code} | IFSC: {ifsc}", f"Branch Name: {branch_name}"],
        [f"City: {city}", f"District: {district} | State: {state}"],
        [f"Address: {address}", ""],
        [f"Installation Date: {install_str}", f"Warranty Valid Until: {expiry_str}"]
    ]
    
    t_branch = Table(branch_data, colWidths=[3.5*inch, 3.5*inch])
    t_branch.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.white),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 1, colors.lightgrey),
        # Span address across both columns
        ('SPAN', (0,2), (1,2)),
        # Highlight Warranty Dates
        ('TEXTCOLOR', (0,3), (1,3), TRIAD_ORANGE),
    ]))
    story.append(t_branch)
    story.append(Spacer(1, 20))

    # 3. Dynamic Warranty Sections (Core Logic)
    # We check for 3 types: 
    # Type 1: Complete Board (Suffix 1)
    # Type 2: Only Fascia (Suffix 2)
    # Type 3: Fascia + LED (Suffix 3)
    
    # Using new column names:
    # complete_board_size, complete_board_qty, complete_board_sqft
    # only_fascia_replacement_size, only_fascia_replacement_qty, only_fascia_replacement_sqft
    # fascia_+_led_replacement_size, fascia_+_led_replacement_qty, fascia_+_led_replacement_sqft
    # led_module_qty, power_supply_watt
    
    warranties = []
    
    # Get LED module data (shared across types)
    led_module_qty = data_row.get('led_module_qty', 0)
    power_supply_watt = data_row.get('power_supply_watt', 0)
    
    # --- Type 1 logic: Complete Board ---
    if pd.notna(data_row.get('complete_board_size')):
        warranties.append({
            'type_id': '1',
            'title': 'Complete Board',
            'size': data_row.get('complete_board_size'),
            'qty': data_row.get('complete_board_qty', 1),
            'sqft': data_row.get('complete_board_sqft', 0),
            'led_power_display': 'comprehensive',  # Merged cell showing "Comprehensive Warranty"
        })
        
    # --- Type 2 logic: Only Fascia ---
    if pd.notna(data_row.get('only_fascia_replacement_size')):
        warranties.append({
            'type_id': '2',
            'title': 'Only Fascia Replacement',
            'size': data_row.get('only_fascia_replacement_size'),
            'qty': data_row.get('only_fascia_replacement_qty', 1),
            'sqft': data_row.get('only_fascia_replacement_sqft', 0),
            'led_power_display': 'blank',  # Leave blank
        })

    # --- Type 3 logic: Fascia + LED ---
    if pd.notna(data_row.get('fascia_+_led_replacement_size')):
        warranties.append({
            'type_id': '3',
            'title': 'Fascia + LED Replacement',
            'size': data_row.get('fascia_+_led_replacement_size'),
            'qty': data_row.get('fascia_+_led_replacement_qty', 1),
            'sqft': data_row.get('fascia_+_led_replacement_sqft', 0),
            'led_power_display': 'values',  # Show actual LED qty and Power watt
            'led_qty': led_module_qty,
            'power_watt': power_supply_watt,
        })

    # Render Warranties side-by-side or stacked
    # Implementation: Render each as a block
    
    # Render all warranties in a single horizontal table
    if warranties:
        story.append(Paragraph("<b><i>Signage Specifications</i></b>", styles['Heading4']))
        story.append(Spacer(1, 5))
        
        # Table header
        spec_data = [
            ['Warranty Coverage', 'Board Size', 'Total Sqft', 'LED Module (Qty)', 'Power Supply']
        ]
        
        # Track which rows need merged cells (for "Comprehensive Warranty")
        merge_rows = []
        
        # Add rows for each warranty type
        for idx, w in enumerate(warranties):
            row_idx = idx + 1  # +1 for header row
            
            if w['led_power_display'] == 'comprehensive':
                # Complete Board: Merge LED and Power columns, show "Comprehensive Warranty"
                spec_data.append([
                    w['title'],
                    str(w['size']),
                    str(w['sqft']),
                    'Comprehensive Warranty',
                    ''  # Will be merged
                ])
                merge_rows.append(row_idx)
            elif w['led_power_display'] == 'blank':
                # Only Fascia: Leave LED and Power blank
                spec_data.append([
                    w['title'],
                    str(w['size']),
                    str(w['sqft']),
                    '',
                    ''
                ])
            else:
                # Fascia + LED: Show actual values
                spec_data.append([
                    w['title'],
                    str(w['size']),
                    str(w['sqft']),
                    str(w.get('led_qty', '')),
                    str(w.get('power_watt', ''))
                ])
        
        t_spec = Table(spec_data, colWidths=[1.8*inch, 1.0*inch, 1.0*inch, 1.5*inch, 1.5*inch])
        
        # Base style
        style_commands = [
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ALIGN', (1,1), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
        ]
        
        # Add merge commands for "Comprehensive Warranty" rows
        for row_idx in merge_rows:
            style_commands.append(('SPAN', (3, row_idx), (4, row_idx)))
        
        t_spec.setStyle(TableStyle(style_commands))
        story.append(t_spec)
        story.append(Spacer(1, 15))
        
        # Photos section - show all available photos
        for w in warranties:
            photo_key_specific = f"{branch_code}_{w['type_id']}"
            photo_key_generic = f"{branch_code}"
            
            img_path = None
            if photo_key_specific in photos_map:
                img_path = photos_map[photo_key_specific]
            elif photo_key_generic in photos_map:
                img_path = photos_map[photo_key_generic]
                
            if img_path:
                try:
                    # Add label above photo: "Size (Warranty Type)"
                    size_label = f"<b>{w['size']} ({w['title']})</b>"
                    story.append(Paragraph(size_label, styles['Normal']))
                    story.append(Spacer(1, 5))
                    
                    img = Image(img_path, width=4*inch, height=2.5*inch)
                    story.append(img)
                    story.append(Spacer(1, 15))
                except:
                    pass
        
        # If no photos found at all
        if not any(f"{branch_code}_{w['type_id']}" in photos_map or f"{branch_code}" in photos_map for w in warranties):
            story.append(Paragraph("<i>[No Photo Available]</i>", styles['Normal']))
        
        story.append(Spacer(1, 20))
        
    # 4. Terms & Conditions Page
    story.append(PageBreak())
    story.append(Paragraph("<b>Terms & Conditions</b>", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    terms_text = branding_config.get('terms_text', 'Standard Warranty Terms Apply.')
    # Handle simple newlines in text
    for line in terms_text.split('\n'):
        if line.strip():
            story.append(Paragraph(line, styles['Normal']))
            story.append(Spacer(1, 6))

    # Build
    doc.build(story, onFirstPage=lambda c, d: draw_header_footer(c, d, branding_config), 
              onLaterPages=lambda c, d: draw_header_footer(c, d, branding_config))


def generate_bulk_certificates(df, images_dict, output_dir, branding_config):
    """
    df: Pandas DataFrame
    images_dict: { 'filename_no_ext': 'abspath' }
    output_dir: output folder
    branding_config: { ... }
    """
    generated_files = []
    
    for _, row in df.iterrows():
        try:
            b_code_raw = row.get('branch_code', '0')
            b_code = str(b_code_raw).split('.')[0]
            b_name = str(row.get('branch_name', 'Unknown')).replace('/', '-')
            
            filename = f"Certificate_{b_code}_{b_name}.pdf"
            output_path = os.path.join(output_dir, filename)
            
            generate_certificate(row, images_dict, output_path, branding_config)
            
            if os.path.exists(output_path):
                generated_files.append(output_path)
        except Exception as e:
            print(f"Error generating {b_code}: {e}")
            continue
            
    return generated_files


