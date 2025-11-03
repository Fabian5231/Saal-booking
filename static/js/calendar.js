let currentMonth = new Date().getMonth();
let currentYear = new Date().getFullYear();
let selectedRaumId = null;
let raumName = '';
let buchungen = [];
let isAdminMode = false;

const monthNames = [
    'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
    'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'
];

const dayNames = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];

// Custom Confirm Dialog
function customConfirm(message, title = 'Bestätigung', options = {}) {
    return new Promise((resolve) => {
        const modal = document.getElementById('custom-confirm-modal');
        const titleElement = document.getElementById('confirm-title');
        const messageElement = document.getElementById('confirm-message');
        const yesButton = document.getElementById('confirm-yes');
        const noButton = document.getElementById('confirm-no');
        const inputContainer = document.getElementById('confirm-input-container');
        const inputElement = document.getElementById('confirm-input');
        const inputLabel = document.getElementById('confirm-input-label');

        // Setze Titel und Nachricht
        titleElement.textContent = title;
        messageElement.textContent = message;

        // Zeige oder verstecke Input-Feld
        if (options.showInput) {
            inputContainer.style.display = 'block';
            inputLabel.textContent = options.inputLabel || 'Nachricht:';
            inputElement.value = '';
        } else {
            inputContainer.style.display = 'none';
        }

        // Zeige Modal
        modal.style.display = 'block';

        // Event Handler für Ja-Button
        const handleYes = () => {
            const inputValue = options.showInput ? inputElement.value.trim() : null;
            cleanup();
            resolve({ confirmed: true, inputValue: inputValue });
        };

        // Event Handler für Nein-Button
        const handleNo = () => {
            cleanup();
            resolve({ confirmed: false, inputValue: null });
        };

        // Cleanup Funktion
        const cleanup = () => {
            modal.style.display = 'none';
            inputElement.value = '';
            inputContainer.style.display = 'none';
            yesButton.removeEventListener('click', handleYes);
            noButton.removeEventListener('click', handleNo);
        };

        // Füge Event Listener hinzu
        yesButton.addEventListener('click', handleYes);
        noButton.addEventListener('click', handleNo);
    });
}

// Custom Alert Dialog
function customAlert(message, title = 'Hinweis', type = 'info') {
    return new Promise((resolve) => {
        const modal = document.getElementById('custom-alert-modal');
        const modalContent = modal.querySelector('.alert-modal-content');
        const titleElement = document.getElementById('alert-title');
        const messageElement = document.getElementById('alert-message');
        const okButton = document.getElementById('alert-ok');

        // Entferne alte Typ-Klassen
        modalContent.classList.remove('success', 'error', 'warning', 'info');

        // Füge neue Typ-Klasse hinzu
        modalContent.classList.add(type);

        // Setze Titel und Nachricht
        titleElement.textContent = title;
        messageElement.textContent = message;

        // Zeige Modal
        modal.style.display = 'block';

        // Event Handler für OK-Button
        const handleOk = () => {
            cleanup();
            resolve();
        };

        // Cleanup Funktion
        const cleanup = () => {
            modal.style.display = 'none';
            okButton.removeEventListener('click', handleOk);
        };

        // Füge Event Listener hinzu
        okButton.addEventListener('click', handleOk);
    });
}

// Initialisierung
document.addEventListener('DOMContentLoaded', function() {
    // Hole Raum-ID und Name aus hidden inputs
    selectedRaumId = document.getElementById('raum-id').value;
    raumName = document.getElementById('raum-name').value;

    initEventListeners();
    loadBuchungen();
});

function initEventListeners() {
    // Monat Navigation
    document.getElementById('prev-month').addEventListener('click', () => {
        currentMonth--;
        if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }
        renderCalendar();
    });

    document.getElementById('next-month').addEventListener('click', () => {
        currentMonth++;
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        }
        renderCalendar();
    });

    // Buchungs-Modal schließen
    document.querySelector('.close').addEventListener('click', closeModal);
    document.getElementById('cancel-buchung').addEventListener('click', closeModal);

    // Detail-Modal schließen
    document.getElementById('detail-close').addEventListener('click', closeDetailModal);

    // Formular absenden
    document.getElementById('buchung-form').addEventListener('submit', submitBuchung);

    // Admin-Modus
    document.getElementById('admin-toggle-btn').addEventListener('click', toggleAdminMode);
    document.getElementById('pin-close').addEventListener('click', closePinModal);
    document.getElementById('cancel-pin').addEventListener('click', closePinModal);
    document.getElementById('pin-form').addEventListener('submit', verifyPin);

    // E-Mail-Einstellungen
    document.getElementById('save-saal-email-btn').addEventListener('click', saveSaalEmail);
}

function renderCalendar() {
    const calendar = document.getElementById('calendar');
    calendar.innerHTML = '';

    // Monat/Jahr Anzeige
    document.getElementById('current-month').textContent =
        `${monthNames[currentMonth]} ${currentYear}`;

    // Wochentage Header
    const headerRow = document.createElement('div');
    headerRow.className = 'calendar-header-row';
    dayNames.forEach(day => {
        const dayHeader = document.createElement('div');
        dayHeader.className = 'calendar-day-name';
        dayHeader.textContent = day;
        headerRow.appendChild(dayHeader);
    });
    calendar.appendChild(headerRow);

    // Tage des Monats
    const firstDay = new Date(currentYear, currentMonth, 1).getDay();
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();

    const daysGrid = document.createElement('div');
    daysGrid.className = 'calendar-days';

    // Leere Tage am Anfang
    for (let i = 0; i < firstDay; i++) {
        const emptyDay = document.createElement('div');
        emptyDay.className = 'calendar-day empty';
        daysGrid.appendChild(emptyDay);
    }

    // Tage des Monats
    for (let day = 1; day <= daysInMonth; day++) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day';

        const datum = new Date(currentYear, currentMonth, day);
        const datumStr = datum.toISOString().split('T')[0];

        // Prüfe ob Tag in der Vergangenheit liegt
        const heute = new Date();
        heute.setHours(0, 0, 0, 0);
        const istVergangenheit = datum < heute;

        if (istVergangenheit) {
            dayElement.classList.add('vergangen');
        }

        // Tag-Nummer
        const dayNumber = document.createElement('div');
        dayNumber.className = 'day-number';
        dayNumber.textContent = day;
        dayElement.appendChild(dayNumber);

        // Buchungen für diesen Tag
        const tagBuchungen = buchungen.filter(b => {
            const start = new Date(b.start_datum).toISOString().split('T')[0];
            return start === datumStr;
        });

        if (tagBuchungen.length > 0) {
            const buchungenContainer = document.createElement('div');
            buchungenContainer.className = 'day-buchungen';

            tagBuchungen.forEach(buchung => {
                const buchungElement = document.createElement('div');
                buchungElement.className = `buchung-indicator ${buchung.status}`;

                const startZeit = new Date(buchung.start_datum).toLocaleTimeString('de-DE', {
                    hour: '2-digit',
                    minute: '2-digit'
                });
                buchungElement.textContent = startZeit;

                // Nur bestätigte Buchungen sind klickbar
                if (buchung.status === 'bestätigt') {
                    buchungElement.title = `${buchung.benutzer_name} - Klicken für Details`;
                    buchungElement.style.cursor = 'pointer';

                    // Click Event für Buchungsdetails
                    buchungElement.addEventListener('click', (e) => {
                        e.stopPropagation(); // Verhindert, dass das Tag-Click-Event ausgelöst wird
                        openDetailModal(buchung);
                    });
                } else {
                    buchungElement.title = `${buchung.benutzer_name} - ${buchung.status}`;
                }

                buchungenContainer.appendChild(buchungElement);
            });

            dayElement.appendChild(buchungenContainer);
        }

        // Click Event für neue Buchung (nur für freie/zukünftige Tage)
        if (!istVergangenheit) {
            dayElement.addEventListener('click', () => openBuchungModal(datum));
            dayElement.style.cursor = 'pointer';
        }

        daysGrid.appendChild(dayElement);
    }

    calendar.appendChild(daysGrid);
}

function loadBuchungen() {
    if (!selectedRaumId) return;

    fetch(`/api/buchungen?raum_id=${selectedRaumId}&jahr=${currentYear}&monat=${currentMonth + 1}`)
        .then(response => response.json())
        .then(data => {
            buchungen = data;
            renderCalendar();
            renderBuchungsListe();
        })
        .catch(error => console.error('Fehler beim Laden der Buchungen:', error));
}

function openBuchungModal(datum) {
    document.getElementById('selected-raum-id').value = selectedRaumId;
    document.getElementById('selected-datum').value = datum.toISOString().split('T')[0];
    document.getElementById('selected-datum-anzeige').textContent =
        datum.toLocaleDateString('de-DE', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

    document.getElementById('buchung-modal').style.display = 'block';
}

function closeModal() {
    document.getElementById('buchung-modal').style.display = 'none';
    document.getElementById('buchung-form').reset();
}

function openDetailModal(buchung) {
    const startDatum = new Date(buchung.start_datum);
    const endDatum = new Date(buchung.end_datum);

    const detailContent = document.getElementById('detail-content');

    detailContent.innerHTML = `
        <div class="detail-row">
            <div class="detail-label">Reserviert von</div>
            <div class="detail-value">${buchung.benutzer_name}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">Datum</div>
            <div class="detail-value">${startDatum.toLocaleDateString('de-DE', {
                weekday: 'long',
                day: '2-digit',
                month: 'long',
                year: 'numeric'
            })}</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">Startzeit</div>
            <div class="detail-value">${startDatum.toLocaleTimeString('de-DE', {hour: '2-digit', minute: '2-digit'})} Uhr</div>
        </div>
        <div class="detail-row">
            <div class="detail-label">Endzeit</div>
            <div class="detail-value">${endDatum.toLocaleTimeString('de-DE', {hour: '2-digit', minute: '2-digit'})} Uhr</div>
        </div>
        ${buchung.zweck ? `
        <div class="detail-row">
            <div class="detail-label">Zweck</div>
            <div class="detail-value">${buchung.zweck}</div>
        </div>
        ` : ''}
        <div class="detail-row">
            <div class="detail-label">Status</div>
            <div class="detail-status ${buchung.status}">${buchung.status.charAt(0).toUpperCase() + buchung.status.slice(1)}</div>
        </div>
    `;

    document.getElementById('buchungsdetail-modal').style.display = 'block';
}

function closeDetailModal() {
    document.getElementById('buchungsdetail-modal').style.display = 'none';
}

async function submitBuchung(event) {
    event.preventDefault();

    const raumId = document.getElementById('selected-raum-id').value;
    const datum = document.getElementById('selected-datum').value;
    const startZeit = document.getElementById('start-zeit').value;
    const endZeit = document.getElementById('end-zeit').value;
    const benutzerName = document.getElementById('benutzer-name').value;
    const benutzerEmail = document.getElementById('benutzer-email').value;
    const zweck = document.getElementById('zweck').value;

    const startDatum = `${datum}T${startZeit}:00`;
    const endDatum = `${datum}T${endZeit}:00`;

    const buchungData = {
        raum_id: parseInt(raumId),
        start_datum: startDatum,
        end_datum: endDatum,
        benutzer_name: benutzerName,
        benutzer_email: benutzerEmail,
        zweck: zweck
    };

    fetch('/api/buchung', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(buchungData)
    })
    .then(response => response.json())
    .then(async data => {
        if (data.error) {
            await customAlert('Fehler: ' + data.error, 'Fehler', 'error');
        } else {
            await customAlert('Ihre Buchungsanfrage wurde gesendet und wartet auf Bestätigung!', 'Erfolg', 'success');
            closeModal();
            loadBuchungen();
        }
    })
    .catch(async error => {
        console.error('Fehler:', error);
        await customAlert('Es gab einen Fehler beim Senden der Buchungsanfrage.', 'Fehler', 'error');
    });
}

function renderBuchungsListe() {
    const liste = document.getElementById('buchungen-liste');
    liste.innerHTML = '';

    if (buchungen.length === 0) {
        liste.innerHTML = '<p style="text-align: center; color: #666; padding: 40px;">Keine Buchungen vorhanden.</p>';
        return;
    }

    buchungen.forEach(buchung => {
        const buchungElement = document.createElement('div');
        buchungElement.className = `buchung-item ${buchung.status}`;

        const startDatum = new Date(buchung.start_datum);
        const endDatum = new Date(buchung.end_datum);

        // Erstelle Action Buttons nur im Admin-Modus
        let buttons = [];

        // Nur im Admin-Modus: Buttons für ausstehende Buchungen
        if (isAdminMode && buchung.status === 'ausstehend') {
            buttons.push(`<button class="btn btn-success" onclick="bestaetigeBuchung(${buchung.id})">Bestätigen</button>`);
            buttons.push(`<button class="btn btn-danger" onclick="lehneAb(${buchung.id})">Ablehnen</button>`);
        }

        // Löschen-Button im Admin-Modus für alle Buchungen
        if (isAdminMode) {
            buttons.push(`<button class="btn btn-delete" onclick="loescheBuchung(${buchung.id})">Löschen</button>`);
        }

        // Formatiere Status für Anzeige
        const statusText = buchung.status.charAt(0).toUpperCase() + buchung.status.slice(1);

        // Erstelle HTML mit allen Buttons in einem Container
        const actionsHTML = buttons.length > 0 ? `
            <div class="buchung-actions">
                ${buttons.join('')}
            </div>
        ` : '';

        buchungElement.innerHTML = `
            <div class="buchung-header">
                <strong>${buchung.benutzer_name}</strong>
                <span class="status-badge ${buchung.status}">${statusText}</span>
            </div>
            <div class="buchung-details">
                <p><strong>Datum:</strong> ${startDatum.toLocaleDateString('de-DE', {
                    weekday: 'short',
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric'
                })}</p>
                <p><strong>Zeit:</strong> ${startDatum.toLocaleTimeString('de-DE', {hour: '2-digit', minute: '2-digit'})} - ${endDatum.toLocaleTimeString('de-DE', {hour: '2-digit', minute: '2-digit'})} Uhr</p>
                <p><strong>E-Mail:</strong> ${buchung.benutzer_email}</p>
                ${buchung.zweck ? `<p><strong>Zweck:</strong> ${buchung.zweck}</p>` : ''}
            </div>
            ${actionsHTML}
        `;

        liste.appendChild(buchungElement);
    });
}

async function bestaetigeBuchung(buchungId) {
    const result = await customConfirm('Möchten Sie diese Buchung wirklich bestätigen?', 'Buchung bestätigen');
    if (!result.confirmed) return;

    fetch(`/api/buchung/${buchungId}/bestaetigen`, {
        method: 'POST'
    })
    .then(response => {
        if (response.status === 401) {
            // Session abgelaufen
            customAlert('Ihre Admin-Session ist abgelaufen. Bitte melden Sie sich erneut an.', 'Session abgelaufen', 'warning');
            isAdminMode = false;
            updateAdminStatus();
            renderBuchungsListe();
            return Promise.reject('Session abgelaufen');
        }
        return response.json();
    })
    .then(async data => {
        if (data.error) {
            await customAlert('Fehler: ' + data.error, 'Fehler', 'error');
        } else {
            await customAlert('Buchung wurde bestätigt!', 'Erfolg', 'success');
            loadBuchungen();

            // Aktualisiere Admin-Panel wenn im Admin-Modus
            if (isAdminMode) {
                loadAdminLogs();
                loadAdminStats();
            }
        }
    })
    .catch(async error => {
        if (error !== 'Session abgelaufen') {
            console.error('Fehler:', error);
            await customAlert('Es gab einen Fehler beim Bestätigen der Buchung.', 'Fehler', 'error');
        }
    });
}

async function lehneAb(buchungId) {
    const result = await customConfirm(
        'Möchten Sie diese Buchung wirklich ablehnen?',
        'Buchung ablehnen',
        {
            showInput: true,
            inputLabel: 'Grund der Ablehnung (optional):'
        }
    );
    if (!result.confirmed) return;

    // Erstelle Request-Body mit optionaler Nachricht
    const requestBody = result.inputValue ? { message: result.inputValue } : {};

    fetch(`/api/buchung/${buchungId}/ablehnen`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
    })
    .then(response => {
        if (response.status === 401) {
            // Session abgelaufen
            customAlert('Ihre Admin-Session ist abgelaufen. Bitte melden Sie sich erneut an.', 'Session abgelaufen', 'warning');
            isAdminMode = false;
            updateAdminStatus();
            renderBuchungsListe();
            return Promise.reject('Session abgelaufen');
        }
        return response.json();
    })
    .then(async data => {
        await customAlert('Buchung wurde abgelehnt.', 'Erfolg', 'success');
        loadBuchungen();

        // Aktualisiere Admin-Panel wenn im Admin-Modus
        if (isAdminMode) {
            loadAdminLogs();
            loadAdminStats();
        }
    })
    .catch(async error => {
        if (error !== 'Session abgelaufen') {
            console.error('Fehler:', error);
            await customAlert('Es gab einen Fehler beim Ablehnen der Buchung.', 'Fehler', 'error');
        }
    });
}

// Admin-Modus Funktionen
function toggleAdminMode() {
    if (isAdminMode) {
        // Admin-Modus deaktivieren und Session beenden
        fetch('/api/admin/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            isAdminMode = false;
            updateAdminStatus();
            renderBuchungsListe();
        })
        .catch(error => {
            console.error('Fehler beim Logout:', error);
            // Auch bei Fehler lokal abmelden
            isAdminMode = false;
            updateAdminStatus();
            renderBuchungsListe();
        });
    } else {
        // PIN-Modal öffnen
        document.getElementById('pin-modal').style.display = 'block';
        document.getElementById('admin-pin').focus();
    }
}

function closePinModal() {
    document.getElementById('pin-modal').style.display = 'none';
    document.getElementById('pin-form').reset();
}

async function verifyPin(event) {
    event.preventDefault();
    const enteredPin = document.getElementById('admin-pin').value;

    // Verifiziere PIN serverseitig
    fetch('/api/admin/verify-pin', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ pin: enteredPin })
    })
    .then(response => {
        if (response.status === 429) {
            // Rate Limit erreicht
            customAlert('Zu viele Versuche! Bitte warten Sie 15 Minuten, bevor Sie es erneut versuchen.', 'Zu viele Versuche', 'warning');
            closePinModal();
            return Promise.reject('Rate limit exceeded');
        }
        return response.json();
    })
    .then(async data => {
        if (data.valid) {
            isAdminMode = true;
            updateAdminStatus();
            closePinModal();
            renderBuchungsListe();
        } else {
            await customAlert('Falsche PIN! Bitte versuchen Sie es erneut.', 'Falsche PIN', 'error');
            document.getElementById('admin-pin').value = '';
            document.getElementById('admin-pin').focus();
        }
    })
    .catch(async error => {
        if (error !== 'Rate limit exceeded') {
            console.error('Fehler bei PIN-Verifikation:', error);
            await customAlert('Fehler bei der PIN-Überprüfung. Bitte versuchen Sie es erneut.', 'Fehler', 'error');
            document.getElementById('admin-pin').value = '';
            document.getElementById('admin-pin').focus();
        }
    });
}

function updateAdminStatus() {
    const buttonElement = document.getElementById('admin-toggle-btn');
    const sidebar = document.getElementById('admin-sidebar');
    const container = document.getElementById('main-container');

    if (isAdminMode) {
        buttonElement.classList.add('active');
        buttonElement.title = 'Admin-Modus beenden';
        sidebar.classList.add('show');
        container.classList.add('admin-mode');

        // Lade Admin-Daten
        loadAdminSettings();
        loadAdminLogs();
        loadAdminStats();
    } else {
        buttonElement.classList.remove('active');
        buttonElement.title = 'Admin-Modus';
        sidebar.classList.remove('show');
        container.classList.remove('admin-mode');
    }
}

function loadAdminSettings() {
    fetch('/api/admin/settings')
        .then(response => {
            if (response.status === 401) {
                // Session abgelaufen
                isAdminMode = false;
                updateAdminStatus();
                renderBuchungsListe();
                return Promise.reject('Session abgelaufen');
            }
            return response.json();
        })
        .then(settings => {
            document.getElementById('admin-email-display').value = settings.admin_email;
            document.getElementById('saal-email-input').value = settings.saal_verantwortlicher_email || '';
        })
        .catch(error => {
            if (error !== 'Session abgelaufen') {
                console.error('Fehler beim Laden der Einstellungen:', error);
            }
        });
}

async function saveSaalEmail() {
    const emailInput = document.getElementById('saal-email-input');
    const email = emailInput.value.trim();

    // Validiere E-Mail-Format
    if (email && !email.includes('@')) {
        await customAlert('Bitte geben Sie eine gültige E-Mail-Adresse ein.', 'Ungültige E-Mail', 'error');
        return;
    }

    fetch('/api/admin/settings/saal-email', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: email })
    })
    .then(response => {
        if (response.status === 401) {
            // Session abgelaufen
            customAlert('Ihre Admin-Session ist abgelaufen. Bitte melden Sie sich erneut an.', 'Session abgelaufen', 'warning');
            isAdminMode = false;
            updateAdminStatus();
            renderBuchungsListe();
            return Promise.reject('Session abgelaufen');
        }
        return response.json();
    })
    .then(async data => {
        if (data.error) {
            await customAlert('Fehler: ' + data.error, 'Fehler', 'error');
        } else {
            await customAlert('Die Saal-Verantwortlichen E-Mail wurde erfolgreich aktualisiert!', 'Erfolg', 'success');
        }
    })
    .catch(async error => {
        if (error !== 'Session abgelaufen') {
            console.error('Fehler:', error);
            await customAlert('Es gab einen Fehler beim Speichern der E-Mail.', 'Fehler', 'error');
        }
    });
}

function loadAdminLogs() {
    fetch('/api/admin/logs')
        .then(response => {
            if (response.status === 401) {
                // Session abgelaufen
                customAlert('Ihre Admin-Session ist abgelaufen. Bitte melden Sie sich erneut an.', 'Session abgelaufen', 'warning');
                isAdminMode = false;
                updateAdminStatus();
                renderBuchungsListe();
                return Promise.reject('Session abgelaufen');
            }
            return response.json();
        })
        .then(logs => {
            const logContainer = document.getElementById('email-log');

            if (logs.length === 0) {
                logContainer.innerHTML = '<p class="loading">Keine Einträge vorhanden.</p>';
                return;
            }

            logContainer.innerHTML = '';
            logs.forEach(log => {
                const logEntry = document.createElement('div');
                logEntry.className = `log-entry ${getLogClass(log.status)}`;

                const timestamp = new Date(log.timestamp);
                const timeStr = timestamp.toLocaleString('de-DE', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });

                const statusText = log.status_text || log.status;

                logEntry.innerHTML = `
                    <div class="log-time">${timeStr}</div>
                    <div class="log-message"><strong>${log.message}</strong></div>
                    <div class="log-details">
                        ${log.details}<br>
                        <small>Email: ${log.email}</small><br>
                        <small>Status: <strong>${statusText}</strong></small>
                    </div>
                `;

                logContainer.appendChild(logEntry);
            });
        })
        .catch(error => {
            if (error !== 'Session abgelaufen') {
                console.error('Fehler beim Laden der Logs:', error);
                document.getElementById('email-log').innerHTML = '<p class="loading">Fehler beim Laden.</p>';
            }
        });
}

function loadAdminStats() {
    fetch('/api/admin/stats')
        .then(response => {
            if (response.status === 401) {
                // Session abgelaufen
                isAdminMode = false;
                updateAdminStatus();
                renderBuchungsListe();
                return Promise.reject('Session abgelaufen');
            }
            return response.json();
        })
        .then(stats => {
            document.getElementById('stat-total').textContent = stats.total;
            document.getElementById('stat-pending').textContent = stats.pending;
            document.getElementById('stat-confirmed').textContent = stats.confirmed;
            document.getElementById('stat-rejected').textContent = stats.rejected;
            document.getElementById('stat-deleted').textContent = stats.deleted;
        })
        .catch(error => {
            if (error !== 'Session abgelaufen') {
                console.error('Fehler beim Laden der Statistiken:', error);
            }
        });
}

function getLogClass(status) {
    switch(status) {
        case 'bestätigt':
            return 'success';
        case 'abgelehnt':
            return 'error';
        case 'ausstehend':
            return 'warning';
        case 'gelöscht':
            return 'deleted';
        default:
            return '';
    }
}

async function loescheBuchung(buchungId) {
    const result = await customConfirm('Möchten Sie diese Buchung wirklich löschen? Sie wird als inaktiv markiert und bleibt im Verlauf sichtbar.', 'Buchung löschen');
    if (!result.confirmed) return;

    fetch(`/api/buchung/${buchungId}/loeschen`, {
        method: 'DELETE'
    })
    .then(response => {
        if (response.status === 401) {
            // Session abgelaufen
            customAlert('Ihre Admin-Session ist abgelaufen. Bitte melden Sie sich erneut an.', 'Session abgelaufen', 'warning');
            isAdminMode = false;
            updateAdminStatus();
            renderBuchungsListe();
            return Promise.reject('Session abgelaufen');
        }
        return response.json();
    })
    .then(async data => {
        await customAlert('Buchung wurde erfolgreich gelöscht.', 'Erfolg', 'success');
        loadBuchungen();

        // Aktualisiere Admin-Panel wenn im Admin-Modus
        if (isAdminMode) {
            loadAdminLogs();
            loadAdminStats();
        }
    })
    .catch(async error => {
        if (error !== 'Session abgelaufen') {
            console.error('Fehler:', error);
            await customAlert('Es gab einen Fehler beim Löschen der Buchung.', 'Fehler', 'error');
        }
    });
}
