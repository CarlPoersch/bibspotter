import streamlit as st
import sqlite3
from datetime import datetime
import qrcode
from io import BytesIO

# Verbindung zur Datenbank
conn = sqlite3.connect("data/buchungen.db", check_same_thread=False)
c = conn.cursor()

# Tabelle 'arbeitsplaetze' anlegen, falls sie nicht existiert
c.execute("""
CREATE TABLE IF NOT EXISTS arbeitsplaetze (
    tisch_nr INTEGER PRIMARY KEY,
    status TEXT
)
""")
conn.commit()

# Testdaten nur einfügen, wenn Tabelle leer ist
c.execute("SELECT COUNT(*) FROM arbeitsplaetze")
if c.fetchone()[0] == 0:
    c.executemany(
        "INSERT INTO arbeitsplaetze (tisch_nr, status) VALUES (?, ?)",
        [(1, 'frei'), (2, 'belegt'), (3, 'frei')]
    )
    conn.commit()

st.title("📷 QR-Login & Freie Plätze")

# DEBUG: Zeige vorhandene Tabellen
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tabellen = [t[0] for t in c.fetchall()]
st.write("📋 Tabellen in der Datenbank:", tabellen)

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
