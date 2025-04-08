import streamlit as st
import sqlite3
from datetime import datetime
import calendar
from collections import Counter

# Verbindung zur Datenbank
conn = sqlite3.connect("data/buchungen.db", check_same_thread=False)
c = conn.cursor()

st.title("📊 Stoßzeitenanalyse")

# Lade alle Einlog-Zeiten
zeitdaten = c.execute("""
    SELECT zeitstempel FROM buchungen 
    WHERE action = 'Einloggen'
""").fetchall()

if not zeitdaten:
    st.info("Noch keine Daten für die Analyse vorhanden.")
else:
    # 📈 Nutzung nach Stunden
    stunden = [datetime.strptime(z[0], "%Y-%m-%d %H:%M:%S").hour for z in zeitdaten]
    verteilung = {stunde: 0 for stunde in range(24)}
    for s in stunden:
        verteilung[s] += 1

    st.markdown("**📈 Nutzung nach Stunden**")
    st.bar_chart(data=list(verteilung.values()), use_container_width=True)
    st.caption("Anzahl der Einlog-Vorgänge pro Stunde (aggregiert)")

    # 📆 Nutzung nach Wochentagen
    wochentagsdaten = [datetime.strptime(z[0], "%Y-%m-%d %H:%M:%S").weekday() for z in zeitdaten]
    wochentag_counter = Counter(wochentagsdaten)
    tage = [calendar.day_name[i] for i in range(7)]
    werte = [wochentag_counter.get(i, 0) for i in range(7)]

    st.markdown("**📆 Nutzung nach Wochentagen**")
    st.bar_chart(data=werte, use_container_width=True)
    st.caption("Anzahl der Einlog-Vorgänge pro Wochentag (Montag–Sonntag)")