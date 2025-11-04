# Raumbuchungssystem - Saal Raiffeisenstraße 12

Ein webbasiertes Buchungssystem für Raumreservierungen mit Admin-Panel und E-Mail-Benachrichtigungen.

## Features

- 📅 Kalenderansicht für Buchungen
- ✉️ E-Mail-Benachrichtigungen bei neuen Buchungen
- 👤 Admin-Panel mit PIN-Authentifizierung
- 📊 Statistiken und E-Mail-Verlauf
- 🔄 Soft-Delete für Buchungen (bleiben im System)
- ⚙️ Konfigurierbare E-Mail-Empfänger im Admin-Panel

## Technologie-Stack

- **Backend**: Flask 3.0.0
- **Datenbank**: SQLite (Development) / PostgreSQL (Production empfohlen)
- **E-Mail**: Flask-Mail
- **Rate Limiting**: Flask-Limiter
- **Frontend**: Vanilla JavaScript, CSS

## Voraussetzungen

- Python 3.9+
- pip

## Installation

### 1. Repository klonen

```bash
git clone <repository-url>
cd KalenderTool
```

### 2. Virtual Environment erstellen

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 4. Umgebungsvariablen konfigurieren

```bash
# Kopiere .env.example zu .env
cp .env.example .env

# Bearbeite .env und setze deine Werte
```

**Wichtig**: Generiere einen sicheren SECRET_KEY:
```python
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Datenbank initialisieren

```bash
python app.py
```

Die Datenbank wird automatisch erstellt beim ersten Start.

## Verwendung

### Development Server starten

```bash
python app.py
```

Die Anwendung ist dann verfügbar unter: http://localhost:5000

### Admin-Panel

1. Klicke auf das Zahnrad-Symbol oben rechts
2. Gib die Admin-PIN ein (Standard: siehe .env)
3. Im Admin-Panel kannst du:
   - Buchungen bestätigen/ablehnen
   - E-Mail-Verlauf sehen
   - Statistiken einsehen
   - Saal-Verantwortlichen-E-Mail konfigurieren

## Datenbank-Migration

Wenn du die Datenbank migrieren möchtest (z.B. nach Updates):

```bash
python migrate_db.py
```

Für einen kompletten Reset der Datenbank (ACHTUNG: Löscht alle Daten!):

```bash
python migrate_db.py --reset
```

## Projektstruktur

```
KalenderTool/
├── app.py                  # Hauptanwendung
├── migrate_db.py           # Datenbank-Migrations-Skript
├── requirements.txt        # Python-Dependencies
├── .env                    # Umgebungsvariablen (nicht in Git!)
├── .env.example            # Vorlage für Umgebungsvariablen
├── instance/               # Datenbank-Dateien
│   └── buchungen.db
├── static/                 # Statische Dateien
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── calendar.js
└── templates/              # HTML-Templates
    ├── index.html
    └── message.html
```

## Konfiguration

### E-Mail-Benachrichtigungen

Das System sendet E-Mails an zwei Empfänger:

1. **Admin-E-Mail**: Konfiguriert in `.env` (ADMIN_EMAIL)
2. **Saal-Verantwortlicher**: Konfigurierbar im Admin-Panel

### Rate Limiting

- Admin-PIN: Max 5 Versuche pro 15 Minuten
- Standard: 200 Requests pro Tag, 50 pro Stunde

## Sicherheit

⚠️ **WICHTIG**: Dieses System ist NICHT produktionsreif!

Vor dem Einsatz in Produktion, siehe: [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)

Kritische Sicherheitspunkte:
- `.env` Datei NICHT in Git committen
- Starken SECRET_KEY verwenden
- HTTPS in Produktion verwenden
- Admin-PIN durch stärkeres Passwort ersetzen
- PostgreSQL statt SQLite verwenden

## API-Endpunkte

### Öffentliche Endpunkte

- `GET /` - Hauptseite mit Kalender
- `GET /api/buchungen` - Liste aller aktiven Buchungen
- `POST /api/buchung` - Neue Buchung erstellen
- `GET /buchung/bestaetigen/<token>` - Buchung per E-Mail bestätigen
- `GET /buchung/ablehnen/<token>` - Buchung per E-Mail ablehnen
- `GET /buchung/stornieren/<token>` - Buchung stornieren

### Admin-Endpunkte (Authentifizierung erforderlich)

- `POST /api/admin/verify-pin` - Admin-PIN verifizieren
- `POST /api/admin/logout` - Admin ausloggen
- `GET /api/admin/logs` - E-Mail-Verlauf
- `GET /api/admin/stats` - Statistiken
- `GET /api/admin/settings` - E-Mail-Einstellungen abrufen
- `POST /api/admin/settings/saal-email` - Saal-E-Mail aktualisieren
- `POST /api/buchung/<id>/bestaetigen` - Buchung bestätigen
- `POST /api/buchung/<id>/ablehnen` - Buchung ablehnen
- `DELETE /api/buchung/<id>/loeschen` - Buchung löschen (Soft-Delete)

## Entwicklung

### Code-Style

Empfohlene Tools:
- `black` für Code-Formatierung
- `pylint` für Code-Qualität
- `mypy` für Type-Checking

### Testing

Aktuell keine Tests vorhanden. Siehe PRODUCTION_CHECKLIST.md für Test-Strategie.

## Lizenz

Alle Rechte vorbehalten.

## Support

Bei Fragen oder Problemen, bitte ein Issue erstellen.

---

**Status**: Development
**Version**: 0.1.0
**Letztes Update**: 2025-01-03
