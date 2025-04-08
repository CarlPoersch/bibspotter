import streamlit as st
import sqlite3
from datetime import datetime, timedelta

# Verbindung zur Datenbank
conn = sqlite3.connect("data/buchungen.db", check_same_thread=False)
c = conn.cursor()

st.title("📚 Gruppenräume buchen")

if 'nutzerkennung' in st.session_state and st.session_state.nutzerkennung:
    # Raumliste abrufen
    c.execute("SELECT raum_nr FROM gruppenraeume")
    raeume = [row[0] for row in c.fetchall()]
    
    raumauswahl = st.selectbox("Wähle einen Gruppenraum:", raeume)
    datum = st.date_input("Datum", datetime.today())
    startzeit = st.time_input("Beginn")
    endzeit = st.time_input("Ende")

    if st.button("Reservieren"):
        start_dt = datetime.combine(datum, startzeit)
        end_dt = datetime.combine(datum, endzeit)

        if start_dt >= end_dt:
            st.error("Endzeit muss nach der Startzeit liegen.")
        else:
            # Verfügbarkeitsprüfung
            c.execute("""
                SELECT * FROM gruppenraum_buchungen
                WHERE raum_nr = ?
                AND (
                    (? BETWEEN beginn AND ende)
                    OR (? BETWEEN beginn AND ende)
                    OR (? < beginn AND ? > ende)
                )
            """, (raumauswahl, start_dt, end_dt, start_dt, end_dt))
            konflikte = c.fetchall()

            if konflikte:
                st.warning("Der Raum ist in diesem Zeitraum bereits belegt.")
            else:
                c.execute("""
                    INSERT INTO gruppenraum_buchungen (raum_nr, nutzer, beginn, ende)
                    VALUES (?, ?, ?, ?)
                """, (raumauswahl, st.session_state.nutzerkennung, start_dt, end_dt))
                conn.commit()
                st.success("Raum erfolgreich reserviert.")
else:
    st.error("Bitte logge dich zuerst ein.")