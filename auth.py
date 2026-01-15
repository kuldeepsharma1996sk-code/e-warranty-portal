"""
Authentication Helper for E-Warranty Portal
Handles connection to Supabase for Login, Signup, and Password Reset.
"""
import streamlit as st
from supabase import create_client, Client

# Initialize these with actual values from the user
SUPABASE_URL = "YOUR_SUPABASE_URL_HERE"
SUPABASE_KEY = "YOUR_SUPABASE_KEY_HERE"

@st.cache_resource
def init_supabase() -> Client:
    """Initialize Supabase client."""
    if SUPABASE_URL == "YOUR_SUPABASE_URL_HERE":
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Failed to connect to Supabase: {e}")
        return None

def sign_in(email, password):
    """Sign in user with email and password."""
    supabase = init_supabase()
    if not supabase:
        return None
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response
    except Exception as e:
        return {"error": str(e)}

def sign_up(email, password):
    """Register a new user."""
    supabase = init_supabase()
    if not supabase:
        return None
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        return response
    except Exception as e:
        return {"error": str(e)}

def reset_password(email):
    """Send password reset email."""
    supabase = init_supabase()
    if not supabase:
        return None
    try:
        response = supabase.auth.reset_password_for_email(email)
        return response
    except Exception as e:
        return {"error": str(e)}
