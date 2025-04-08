import streamlit as st
import sqlite3
from datetime import datetime

# Verbindung zur Datenbank
conn = sqlite3.connect("data/buchungen.db", check_same_thread=False)
c = conn.cursor()

st.title("🚶 Ich gehe bald")

if 'nutzerkennung' in st.session_state and st.session_state.nutzerkennung:
    c.execute("""
        SELECT id, tisch_nr, beginn, ende FROM buchungen
        WHERE nutzer = ? AND ende IS NULL
        ORDER BY beginn DESC LIMIT 1
    """, (st.session_state.nutzerkennung,))
    reservierung = c.fetchone()

    if reservierung:
        st.info(f"Du bist aktuell an Tisch {reservierung[1]} seit {reservierung[2]}.")
        if st.button("Ich verlasse meinen Platz"):
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("UPDATE buchungen SET ende = ? WHERE id = ?", (now, reservierung[0]))
            c.execute("UPDATE arbeitsplaetze SET status = 'frei' WHERE tisch_nr = ?", (reservierung[1],))
            conn.commit()
            st.success("Dein Platz wurde freigegeben.")
    else:
        st.warning("Du hast aktuell keine aktive Buchung.")
else:
    st.error("Bitte logge dich zuerst ein.")