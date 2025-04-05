import streamlit as st
import random
import cv2
import numpy as np
import sqlite3
from datetime import datetime, timedelta

# Verbindung zur SQLite-Datenbank
conn = sqlite3.connect("buchungen.db", check_same_thread=False)
c = conn.cursor()

# Erstelle Tabelle, falls sie noch nicht existiert
c.execute('''
    CREATE TABLE IF NOT EXISTS buchungen (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tisch TEXT,
        action TEXT,
        zeitstempel TEXT,
        reserviert_bis TEXT,
        nutzer TEXT
    )
''')
conn.commit()

if 'nutzerkennung' not in st.session_state:
    st.session_state.nutzerkennung = ''
if 'user_reservierung' not in st.session_state:
    st.session_state.user_reservierung = None

def ist_gueltige_matrikelnummer(eingabe):
    return eingabe.isdigit() and len(eingabe) == 7

if not ist_gueltige_matrikelnummer(st.session_state.nutzerkennung):
    st.title("🔐 Login")
    eingabe = st.text_input("Bitte gib deine Matrikelnummer ein (7 Ziffern):")
    if ist_gueltige_matrikelnummer(eingabe):
        st.session_state.nutzerkennung = eingabe
        # Lade aktuelle Aktion beim Login
        if st.session_state.user_reservierung is None:
            letzte = c.execute("SELECT tisch, action FROM buchungen WHERE nutzer = ? ORDER BY zeitstempel DESC", 
                               (st.session_state.nutzerkennung,)).fetchone()
            if letzte:
                if letzte[1] == "Reservieren":
                    st.session_state.user_reservierung = letzte[0]
                elif letzte[1] == "Einloggen":
                    st.session_state.user_reservierung = letzte[0]  # Zeigt auch Login-Tisch an
        st.rerun()
    else:
        st.stop()

# Aktuelle Sitzung anzeigen (wenn vorhanden)
letzte_aktion = c.execute("SELECT tisch, action, zeitstempel FROM buchungen WHERE nutzer = ? ORDER BY zeitstempel DESC", 
                          (st.session_state.nutzerkennung,)).fetchone()
if letzte_aktion and letzte_aktion[1] == "Einloggen":
    st.success(f"🪑 Du bist eingeloggt an: {letzte_aktion[0]} (seit {letzte_aktion[2]})")

# Session-Zeitübersicht (heutiger Tag)
heute = datetime.now().strftime("%Y-%m-%d")
buchungen_heute = c.execute("""
    SELECT action, zeitstempel FROM buchungen 
    WHERE nutzer = ? AND DATE(zeitstempel) = ? ORDER BY zeitstempel
""", (st.session_state.nutzerkennung, heute)).fetchall()

gesamt_minuten = 0
login_zeit = None

for action, zeit in buchungen_heute:
    zeitpunkt = datetime.strptime(zeit, "%Y-%m-%d %H:%M:%S")
    if action == "Einloggen":
        login_zeit = zeitpunkt
    elif action in ("Ausloggen", "Geht bald") and login_zeit:
        gesamt_minuten += int((zeitpunkt - login_zeit).total_seconds() // 60)
        login_zeit = None

# Falls eingeloggt aber noch kein Ausloggen erfolgt ist, Dauer bis jetzt rechnen
if login_zeit:
    gesamt_minuten += int((datetime.now() - login_zeit).total_seconds() // 60)

if gesamt_minuten > 0:
    st.info(f"📊 Du warst heute insgesamt ca. {gesamt_minuten} Minute(n) aktiv in der Bibliothek.")

# Logout oben rechts
with st.sidebar:
    st.markdown(f"👤 Eingeloggt als: `{st.session_state.nutzerkennung}`")
    if st.button("🚪 Logout"):
        st.session_state.nutzerkennung = ''
        st.session_state.user_reservierung = None
        st.rerun()

# Sidebar mit Navigation über Seiten (via URL-Parameter)
st.sidebar.markdown("## 📂 Navigation")

pages = {
    "Startseite": "",
    "📷 QR-Login": "qr",
    "🚶 Ich gehe bald": "bald",
    "📚 Gruppenräume": "gruppen",
    "📋 Buchungsverlauf": "verlauf",
    "📊 Stoßzeitenanalyse": "statistik"
}

selected = st.sidebar.selectbox("Seite auswählen:", list(pages.keys()))
st.experimental_set_query_params(page=pages[selected])

query_params = st.experimental_get_query_params()
current_page = query_params.get("page", [""])[0]

zeige_start = current_page == ""
zeige_qr = current_page == "qr"
zeige_geht_bald = current_page == "bald"
zeige_gruppenraeume = current_page == "gruppen"
zeige_verlauf = current_page == "verlauf"
zeige_statistik = current_page == "statistik"

# Titel der App
st.title('BibSpotter - Bibliotheksplatzfinder')
st.markdown('Finde freie Plätze in der Bibliothek und überprüfe die Verfügbarkeit von Gruppenräumen.')

st.markdown("""
### 🗺️ Tischauswahl-Legende
- 🟥 **Belegt** – Der Platz ist aktuell besetzt
- 🟦 **Reserviert** – Eine Reservierung läuft (noch max. 30 Minuten)
- 🟧 **Geht bald** – Der Platz wird bald frei (angekündigt)
- 🟩 **Frei** – Sofort verfügbar
""")
# Abschnitt für die Platzsuche mit Live-Status
st.header('📍 Freie Plätze in der Bibliothek')

# Reservierte Tische mit verbleibender Zeit
aktive_reservierungen = []
alle_tische = [f"Tisch {i}" for i in range(1, 10)]
rows = c.execute("SELECT tisch, action, zeitstempel FROM buchungen ORDER BY zeitstempel").fetchall()
status = {}
for tisch, action, zeit in rows:
    zeitpunkt = datetime.strptime(zeit, "%Y-%m-%d %H:%M:%S")
    if tisch not in status or zeitpunkt > status[tisch][1]:
        status[tisch] = (action, zeitpunkt)

belegte_tische = []
now = datetime.now()

for tisch, (action, zeitpunkt) in status.items():
    if action == 'Einloggen':
        belegte_tische.append(tisch)
    elif action == 'Reservieren':
        delta = now - zeitpunkt
        if delta < timedelta(minutes=30):
            belegte_tische.append(tisch)
            verbleibend = 30 - int(delta.total_seconds() // 60)
            if verbleibend > 0:
                aktive_reservierungen.append((tisch, verbleibend))
    elif action == 'Geht bald':
        belegte_tische.append(tisch)

if aktive_reservierungen:
    st.markdown(f"🔒 **Reserviert:** {len(aktive_reservierungen)} Tische")
    for tisch, mins in aktive_reservierungen:
        st.markdown(f"– {tisch}: noch {mins} Minute(n) reserviert")
        st.progress((30 - mins) / 30)

freie_tische = [t for t in alle_tische if t not in belegte_tische]

st.markdown(f"**Belegte Tische:** {', '.join([t for t in belegte_tische if t]) if belegte_tische else 'Keine'}")
st.markdown(f"**Freie Tische:** {', '.join([t for t in freie_tische if t]) if freie_tische else 'Keine Plätze frei'}")

# Zeige alle laufenden Reservierungen mit verbleibender Zeit
st.subheader("⏳ Laufende Reservierungen")
# Ermittle letzte Aktion pro Tisch, um nur gültige Reservierungen anzuzeigen
aktionen = c.execute("SELECT tisch, action, zeitstempel FROM buchungen ORDER BY zeitstempel DESC").fetchall()
letzte_aktionen = {}
for tisch, action, zeit in aktionen:
    if tisch not in letzte_aktionen:
        letzte_aktionen[tisch] = (action, zeit)

anzeigen = []
for tisch, (action, zeit) in letzte_aktionen.items():
    if action == "Reservieren":
        zeitpunkt = datetime.strptime(zeit, "%Y-%m-%d %H:%M:%S")
        delta = now - zeitpunkt
        if delta < timedelta(minutes=30):
            verbleibend = 30 - int(delta.total_seconds() // 60)
            anzeigen.append((tisch, verbleibend))

if anzeigen:
    for tisch, mins in anzeigen:
        st.info(f"{tisch}: noch {mins} Minute(n) reserviert")
        st.progress((30 - mins) / 30)
else:
    st.write("Keine aktiven Reservierungen")

# Abschnitt für Gruppenräume
st.header("📚 Gruppenräume")
gruppenraeume = {
    "Raum 1": "6 Personen, Whiteboard",
    "Raum 2": "4 Personen, Beamer"
}

st.markdown("Wähle einen Gruppenraum und einen Zeitraum aus, um zu reservieren.")

raum = st.selectbox("Raum auswählen", list(gruppenraeume.keys()))
startzeit = st.time_input("Beginn der Reservierung", value=datetime.now().time())
endzeit = st.time_input("Ende der Reservierung", value=(datetime.now() + timedelta(hours=1)).time())

# Prüfe auf Zeitfehler
if datetime.combine(datetime.today(), endzeit) <= datetime.combine(datetime.today(), startzeit):
    st.warning("Endzeit muss nach Startzeit liegen.")
else:
    # Prüfe ob Raum in der Zeit bereits reserviert ist
    bestehende = c.execute("""
        SELECT zeitstempel, reserviert_bis FROM buchungen 
        WHERE tisch = ? AND action = 'Reservieren'
    """, (raum,)).fetchall()

    konflikt = False
    start_dt = datetime.combine(datetime.today(), startzeit)
    end_dt = datetime.combine(datetime.today(), endzeit)

    for zs, zb in bestehende:
        res_start = datetime.strptime(zs, "%Y-%m-%d %H:%M:%S")
        res_ende = datetime.strptime(zb, "%Y-%m-%d %H:%M:%S")
        if res_start < end_dt and res_ende > start_dt:
            konflikt = True
            break

    if konflikt:
        st.error("Dieser Zeitraum ist bereits belegt.")
    else:
        if st.button("Reservieren"):
            c.execute("INSERT INTO buchungen (tisch, action, zeitstempel, reserviert_bis, nutzer) VALUES (?, ?, ?, ?, ?)",
                      (raum, "Reservieren", start_dt.strftime("%Y-%m-%d %H:%M:%S"), end_dt.strftime("%Y-%m-%d %H:%M:%S"), st.session_state.nutzerkennung))
            conn.commit()
            st.success(f"{raum} wurde reserviert von {startzeit.strftime('%H:%M')} bis {endzeit.strftime('%H:%M')} – {gruppenraeume[raum]}")

st.subheader("🗓️ Kalenderansicht der Raumreservierungen (heute)")

reservierungen_heute = c.execute("""
    SELECT tisch, zeitstempel, reserviert_bis, nutzer FROM buchungen 
    WHERE DATE(zeitstempel) = ? AND action = 'Reservieren' AND tisch LIKE 'Raum %'
    ORDER BY zeitstempel
""", (datetime.now().strftime("%Y-%m-%d"),)).fetchall()

if reservierungen_heute:
    for raum in gruppenraeume:
        st.markdown(f"### {raum} – {gruppenraeume[raum]}")
        raum_reservierungen = [r for r in reservierungen_heute if r[0] == raum]
        if not raum_reservierungen:
            st.info("Keine Reservierungen für heute.")
        else:
            for res in raum_reservierungen:
                st.write(f"🕒 {res[1][11:16]} – {res[2][11:16]} | Matrikel: {res[3]}")
else:
    st.info("Heute sind keine Gruppenräume reserviert.")

# QR-Code Scanner
from streamlit_qrcode_scanner import qrcode_scanner

st.header('📷 QR-Code Scanner')
st.write("Scanne einen QR-Code, um einen Platz oder Gruppenraum zu reservieren.")

qr_result = qrcode_scanner()
if qr_result:
    if ist_gueltige_matrikelnummer(st.session_state.nutzerkennung):
        qr_data = qr_result.strip()
        if qr_data in alle_tische:
            st.success(f"{qr_data} erkannt – du wirst jetzt eingeloggt.")
            zeit = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO buchungen (tisch, action, zeitstempel, nutzer) VALUES (?, ?, ?, ?)", 
                      (qr_data, "Einloggen", zeit, st.session_state.nutzerkennung))
            conn.commit()
            st.balloons()
        else:
            st.error("QR-Code ist ungültig oder gehört zu keinem Tisch.")
    else:
        st.warning("Bitte gib deine gültige 7-stellige Matrikelnummer an, bevor du fortfährst.")

# Hinweis freiwillig: Bald frei
eingeloggte_tische = [tisch for tisch, (action, _) in status.items() if action == 'Einloggen']

if eingeloggte_tische:
    st.subheader("🚶 Ich gehe bald")
    geht_tisch = st.selectbox("Welchen Platz gibst du bald frei?", eingeloggte_tische)
    verlassen_in = st.select_slider("In wie vielen Minuten verlässt du den Platz?", options=[5, 10, 15])

    if st.button("Verlassen ankündigen"):
        zeit = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO buchungen (tisch, action, zeitstempel) VALUES (?, ?, ?)", (geht_tisch, 'Geht bald', zeit))
        conn.commit()
        st.success(f"{geht_tisch} wird in ca. {verlassen_in} Minuten frei.")
else:
    st.subheader("🚶 Ich gehe bald")
    st.info("Du bist aktuell an keinem Tisch eingeloggt.")

st.subheader("✍️ Tisch reservieren")

if st.session_state.user_reservierung:
    st.info(f"Du hast aktuell {st.session_state.user_reservierung} reserviert.")

    # Prüfe ob Reservierung noch aktiv ist
    tisch = st.session_state.user_reservierung
    letzte_res = c.execute("""
        SELECT zeitstempel FROM buchungen 
        WHERE tisch = ? AND nutzer = ? AND action = 'Reservieren'
        ORDER BY zeitstempel DESC LIMIT 1
    """, (tisch, st.session_state.nutzerkennung)).fetchone()

    reservierung_aktiv = False
    if letzte_res:
        zeitpunkt = datetime.strptime(letzte_res[0], "%Y-%m-%d %H:%M:%S")
        if datetime.now() - zeitpunkt < timedelta(minutes=30):
            reservierung_aktiv = True

    if reservierung_aktiv:
        mit_sicherheit = st.checkbox("Ich bin sicher, dass ich die Reservierung stornieren möchte.")
        if st.button("Reservierung stornieren", key="storno_button_confirmed") and mit_sicherheit:
            c.execute("INSERT INTO buchungen (tisch, action, zeitstempel, nutzer) VALUES (?, ?, ?, ?)",
                      (tisch, "Storno", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), st.session_state.nutzerkennung))
            conn.commit()
            st.success(f"Reservierung für {tisch} wurde aufgehoben.")
            st.session_state.user_reservierung = None
        elif st.button("Reservierung stornieren", key="storno_button_simple"):
            st.warning("Bitte bestätige die Stornierung über die Checkbox.")
    else:
        st.warning("Deine Reservierung ist bereits abgelaufen oder wurde überschrieben.")
        st.session_state.user_reservierung = None

else:
    for row in range(3):
        cols = st.columns(3)
        for col in range(3):
            tisch_id = f"Tisch {row * 3 + col + 1}"
            symbol = "⬜"
            beschreibung = "Unbekannt"

            if tisch_id in belegte_tische:
                symbol = "🟥"
                beschreibung = "Belegt"
            elif tisch_id in [t for t, _ in aktive_reservierungen]:
                symbol = "🟦"
                verbleibend = [m for t, m in aktive_reservierungen if t == tisch_id][0]
                beschreibung = f"Reserviert ({verbleibend} min)"
            elif tisch_id in [t for t, (a, z) in status.items() if a == 'Geht bald']:
                symbol = "🟧"
                beschreibung = "Wird bald frei"
            else:
                symbol = "🟩"
                beschreibung = "Frei"

            label = f"{symbol} {tisch_id}\n{beschreibung}"
            if tisch_id in freie_tische:
                if cols[col].button(label, help=beschreibung):
                    if ist_gueltige_matrikelnummer(st.session_state.nutzerkennung):
                        zeit = datetime.now()
                        zeitstempel = zeit.strftime("%Y-%m-%d %H:%M:%S")
                        reserviert_bis = (zeit + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
                        c.execute("INSERT INTO buchungen (tisch, action, zeitstempel, reserviert_bis, nutzer) VALUES (?, ?, ?, ?, ?)",
                                  (tisch_id, "Reservieren", zeitstempel, reserviert_bis, st.session_state.nutzerkennung))
                        conn.commit()
                        st.session_state.user_reservierung = tisch_id
                        st.success(f"{tisch_id} wurde für dich reserviert.")
                    else:
                        st.warning("Bitte gib deine gültige 7-stellige Matrikelnummer an, bevor du reservierst.")
            else:
                cols[col].button(label, disabled=True, help=beschreibung)

# Login-/Logout-Bereich
st.header("🔓 Ausloggen (nur bei vergessenem QR-Scan)")

eingeloggte_tische_logout = [tisch for tisch in belegte_tische if status[tisch][0] == 'Einloggen']

tisch = st.selectbox("Tisch auswählen (zum Ausloggen):", eingeloggte_tische_logout)

if tisch:
    st.write(f"Tisch {tisch} ist aktuell belegt.")
    if st.button("Jetzt ausloggen"):
        zeit = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO buchungen (tisch, action, zeitstempel) VALUES (?, ?, ?)", (tisch, 'Ausloggen', zeit))
        conn.commit()
        st.success(f"Tisch {tisch} wurde ausgeloggt um {zeit}")
st.caption("Reservierungen verfallen nach 30 Minuten automatisch, wenn kein QR-Login erfolgt.")

# Persönlicher Buchungsverlauf
st.subheader("📋 Deine letzten Aktivitäten")
meine_buchungen = c.execute("SELECT * FROM buchungen WHERE nutzer = ? ORDER BY zeitstempel DESC LIMIT 10", 
                            (st.session_state.nutzerkennung,)).fetchall()
for eintrag in meine_buchungen:
    st.write(f"{eintrag[3]} – {eintrag[1]} – {eintrag[2]} – {eintrag[4]}")

st.subheader("📊 Stoßzeiten-Analyse")

# Lade alle Einlog-Zeiten
zeitdaten = c.execute("""
    SELECT zeitstempel FROM buchungen 
    WHERE action = 'Einloggen'
""").fetchall()

# Stundenauswertung
stunden = [datetime.strptime(z[0], "%Y-%m-%d %H:%M:%S").hour for z in zeitdaten]
verteilung = {stunde: 0 for stunde in range(24)}
for s in stunden:
    verteilung[s] += 1

st.markdown("**📈 Nutzung nach Stunden**")
st.bar_chart(data=list(verteilung.values()), use_container_width=True)
st.caption("Anzahl der Einlog-Vorgänge pro Stunde (aggregiert)")

# Wochentagsauswertung
import calendar
from collections import Counter

wochentagsdaten = [datetime.strptime(z[0], "%Y-%m-%d %H:%M:%S").weekday() for z in zeitdaten]
wochentag_counter = Counter(wochentagsdaten)
tage = [calendar.day_name[i] for i in range(7)]
werte = [wochentag_counter.get(i, 0) for i in range(7)]

st.markdown("**📆 Nutzung nach Wochentagen**")
st.bar_chart(data=werte, use_container_width=True)
st.caption("Anzahl der Einlog-Vorgänge pro Wochentag (Montag–Sonntag)")

# Footer
st.markdown('---')
st.markdown('© 2025 BibSpotter - Alle Rechte vorbehalten.')