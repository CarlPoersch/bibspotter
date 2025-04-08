import streamlit as st
import sqlite3
import pandas as pd

# Verbindung zur Datenbank
conn = sqlite3.connect("data/buchungen.db", check_same_thread=False)
c = conn.cursor()

st.title("📋 Buchungsverlauf")

if 'nutzerkennung' in st.session_state and st.session_state.nutzerkennung:
    c.execute("""
        SELECT tisch_nr, beginn, ende
        FROM buchungen
        WHERE nutzer = ?
        ORDER BY beginn DESC
    """, (st.session_state.nutzerkennung,))
    daten = c.fetchall()

    if daten:
        df = pd.DataFrame(daten, columns=["Tisch", "Beginn", "Ende"])
        st.dataframe(df)
    else:
        st.info("Du hast bisher keine Buchungen vorgenommen.")
else:
    st.error("Bitte logge dich zuerst ein.")