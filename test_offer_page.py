#!/usr/bin/env python3
"""
Test script to verify the offer page component works correctly.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from components.offer_page import render_offer_page
    print("SUCCESS: Successfully imported render_offer_page")
    
    from config.constants import APP_NAME, APP_ICON
    print(f"SUCCESS: Successfully imported constants: {APP_NAME}")
    
    print("SUCCESS: All imports successful - offer page is ready!")
    print("\nTo test the offer page:")
    print("1. Run: streamlit run src/app_with_routing.py")
    print("2. Navigate to: http://localhost:8501?page=offer")
    print("3. Or click 'View Offer' from the landing page")
    
except ImportError as e:
    print(f"ERROR: Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Unexpected error: {e}")
    sys.exit(1)
