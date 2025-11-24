"""
Authentication Module für Streamlit App

Einfaches Login-System mit Credentials aus .env Datei
"""

import streamlit as st
import os
from dotenv import load_dotenv

# Lade .env Datei
load_dotenv()

# Hole Credentials aus .env
VALID_USERNAME = os.getenv("APP_USERNAME", "admin")
VALID_PASSWORD = os.getenv("APP_PASSWORD", "changeme")


def check_password() -> bool:
    """
    Prüft ob der User eingeloggt ist.

    Returns:
        True wenn eingeloggt, False wenn nicht
    """
    # Prüfe ob bereits eingeloggt (Session State)
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    # Wenn bereits authentifiziert, return True
    if st.session_state["authenticated"]:
        return True

    # Zeige Login-Formular
    show_login_form()

    return False


def show_login_form():
    """
    Zeigt das Login-Formular an.
    """
    st.markdown("## 🔐 Login")
    # st.markdown("Bitte melden Sie sich an, um die Anwendung zu nutzen.")

    # Erstelle Login-Formular
    with st.form("login_form"):
        username = st.text_input("Benutzername", key="username_input")
        password = st.text_input("Passwort", type="password", key="password_input")
        submit = st.form_submit_button("Anmelden")

        if submit:
            if username == VALID_USERNAME and password == VALID_PASSWORD:
                st.session_state["authenticated"] = True
                st.success("✅ Erfolgreich angemeldet!")
                st.rerun()
            else:
                st.error("❌ Ungültige Anmeldedaten")


def logout():
    """
    Loggt den User aus.
    """
    st.session_state["authenticated"] = False
    st.rerun()
