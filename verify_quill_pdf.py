from pdf_engine import generate_certificate
import os

# Simulated Data
data = {
    'BRANCH NAME': 'Test Branch',
    'BRANCH CODE': '999',
    'BSC CODE': 'TEST000',
    'City': 'Test City',
    'District': 'Test Dist',
    'STATE': 'Test State',
    'Installation Date': '2025-01-01',
    'Complete Board_Fascia': '10x10', 
    'Complete Board_1 Qty': 1,
    'Complete Board_1 Sqft': 100
}

# Simulated Quill Output (HTML)
# st_quill returns HTML string
quill_html = """
<p><strong>Standard Warranty Terms</strong></p>
<p>1. This warranty covers <b>manufacturing defects</b> only.</p>
<p>2. Void if <i>physical damage</i> occurs.</p>
<p>For support contact <font color='blue'>support@triad.com</font>.</p>
"""

branding = {
    "logo_path": None,
    "client_name": "Test HTML Client",
    "terms_text": quill_html
}

output = "test_quill_render.pdf"

print("Generating PDF with HTML Terms...")
try:
    generate_certificate(data, {}, output, branding)
    print(f"Success! Generated {output}")
except Exception as e:
    print(f"FAILED: {e}")
