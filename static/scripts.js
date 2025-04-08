// Platzprüfungsfunktion
document.getElementById('checkPlatzBtn').addEventListener('click', function() {
    let statusDiv = document.getElementById('platzStatus');
    let randomStatus = Math.random() < 0.5 ? 'Plätze sind verfügbar!' : 'Leider keine freien Plätze verfügbar.';
    statusDiv.textContent = randomStatus;
});

// Gruppenraumprüfungsfunktion
document.getElementById('checkRaumBtn').addEventListener('click', function() {
    let statusDiv = document.getElementById('raumStatus');
    let randomStatus = Math.random() < 0.5 ? 'Ein Gruppenraum ist frei!' : 'Alle Gruppenräume sind belegt.';
    statusDiv.textContent = randomStatus;
});