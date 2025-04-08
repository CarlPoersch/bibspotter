import streamlit as st
import sqlite3
from datetime import datetime
import qrcode
from io import BytesIO

# Verbindung zur Datenbank
conn = sqlite3.connect("data/buchungen.db", check_same_thread=False)
c = conn.cursor()

st.title("📷 QR-Login & Freie Plätze")

# QR-Code für Login generieren
if 'nutzerkennung' in st.session_state and st.session_state.nutzerkennung:
    qr = qrcode.make(st.session_state.nutzerkennung)
    buf = BytesIO()
    qr.save(buf)
    st.image(buf.getvalue(), caption="Dein QR-Code zum Einchecken")

# Anzeige freier Plätze
st.subheader("📍 Freie Plätze anzeigen")

c.execute("SELECT tisch_nr FROM arbeitsplaetze WHERE status = 'frei'")
freie_tische = c.fetchall()

if freie_tische:
    st.success(f"Es sind {len(freie_tische)} Plätze frei:")
    for platz in freie_tische:
        st.markdown(f"🔹 Tisch {platz[0]}")
else:
    st.warning("Aktuell sind keine Plätze frei.")

# Logout
if st.button("🔓 Ausloggen"):
    st.session_state.nutzerkennung = ''
    st.success("Du wurdest ausgeloggt.")
