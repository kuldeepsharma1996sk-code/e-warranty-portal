import os
import pandas as pd
from pdf_engine import generate_certificate, generate_bulk_certificates

# Dummy Data
data = {
    'BRANCH NAME': 'TEST BRANCH',
    'BRANCH CODE': '101',
    'BSC CODE': 'TEST0000101',
    'CITY NAME': 'Test City',
    'District': 'Test Dist',
    'STATE': 'Test State',
    'Installation Date': '2025-01-01',
    'Complete Board_Fascia': '20x4',
    'Complete Board_1 Qty': 1,
    'Complete Board_1 Sqft': 80.0
}

# Dummy Branding
branding = {
    "company_name": "Antigravity Corp",
    "logo_path": None, # Should handle missing logo gracefully (or use dummy)
    "terms_text": "Clause 1: This is a test term.\nClause 2: Warranty void if seals broken."
}

output_path = "test_portal_cert.pdf"

# Test Single
print("Generating Single Certificate...")
try:
    generate_certificate(data, None, output_path, None, branding)
    if os.path.exists(output_path):
        print("SUCCESS: PDF Created")
    else:
        print("FAILURE: PDF not found")
except Exception as e:
    print(f"CRASH: {e}")

# Test Bulk logic (simulated)
print("Testing Bulk Logic...")
df = pd.DataFrame([data])
images_dict = {}
try:
    res = generate_bulk_certificates(df, images_dict, ".", None, branding)
    print(f"Bulk Result: {res}")
except Exception as e:
    print(f"Bulk CRASH: {e}")
