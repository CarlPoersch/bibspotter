import streamlit as st
import sqlite3
from datetime import datetime

# Verbindung zur SQLite-Datenbank
conn = sqlite3.connect("data/buchungen.db", check_same_thread=False)
c = conn.cursor()

# Session-Initialisierung
if 'nutzerkennung' not in st.session_state:
    st.session_state.nutzerkennung = ''
if 'user_reservierung' not in st.session_state:
    st.session_state.user_reservierung = None

# Prüfe gültige Matrikelnummer
def ist_gueltige_matrikelnummer(eingabe):
    return eingabe.isdigit() and len(eingabe) == 7

# Login
if not ist_gueltige_matrikelnummer(st.session_state.nutzerkennung):
    st.title("🔐 Login")
    eingabe = st.text_input("Bitte gib deine Matrikelnummer ein (7 Ziffern):")
    if ist_gueltige_matrikelnummer(eingabe):
        st.session_state.nutzerkennung = eingabe
        st.rerun()
    else:
        st.stop()

# Sidebar: Logout & Navigation
with st.sidebar:
    st.markdown(f"👤 Eingeloggt als: `{st.session_state.nutzerkennung}`")
    if st.button("🚪 Logout"):
        st.session_state.nutzerkennung = ''
        st.session_state.user_reservierung = None
        st.rerun()
    st.markdown("---")
    st.markdown("📂 Seiten findest du links im Menü")

# Optional: Intro auf der Startseite
st.title("📚 BibSpotter – Bibliotheksplatzfinder")
st.markdown("""
Willkommen beim **BibSpotter**!  
Hier kannst du:
- freie Arbeitsplätze in der Bibliothek finden
- einen Platz reservieren oder dich mit QR-Code einloggen
- deinen Buchungsverlauf einsehen
- Gruppenräume reservieren
- die Stoßzeiten der Bibliothek analysieren

👉 Verwende das Menü links, um zu den Funktionen zu navigieren.
""")

# Footer
st.markdown("---")
st.markdown("© 2025 BibSpotter – OTH Regensburg")
