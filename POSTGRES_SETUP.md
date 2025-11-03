# PostgreSQL Setup - Quick Start Guide

## Schritt 1: PostgreSQL mit Docker starten (5 Minuten)

### Voraussetzungen
- Docker Desktop installiert (https://www.docker.com/products/docker-desktop/)

### Starten

```bash
# 1. Navigiere zum Projektordner
cd C:\Users\admin\Desktop\KalenderTool

# 2. Starte PostgreSQL (und optional pgAdmin + Redis)
docker-compose up -d

# 3. Prüfe ob Container laufen
docker-compose ps
```

Du solltest sehen:
```
NAME                   STATUS
raumbuchung-db         Up (healthy)
raumbuchung-pgadmin    Up
raumbuchung-redis      Up (healthy)
```

### Container-Infos

| Service | Port | Zugangsdaten |
|---------|------|--------------|
| PostgreSQL | 5432 | User: admin, Password: changeme, DB: buchungen |
| pgAdmin | 5050 | Email: admin@example.com, Password: admin |
| Redis | 6379 | Kein Passwort |

---

## Schritt 2: Python Dependencies installieren (2 Minuten)

```bash
# PostgreSQL Adapter für Python
pip install psycopg2-binary

# Aktualisiere requirements.txt
echo psycopg2-binary==2.9.9 >> requirements.txt
```

---

## Schritt 3: .env Konfiguration (3 Minuten)

Aktualisiere deine `.env` Datei:

```bash
# Alte SQLite Zeile:
# DATABASE_URI=sqlite:///buchungen.db

# Neue PostgreSQL Zeile:
DATABASE_URI=postgresql://admin:changeme@localhost:5432/buchungen
```

**Wichtig für Produktion:** Ändere das Passwort!

```bash
# Sicheres Passwort generieren
python -c "import secrets; print(secrets.token_urlsafe(32))"

# In .env und docker-compose.yml einsetzen
```

---

## Schritt 4: Datenbank-Tabellen erstellen (1 Minute)

### Option A: Neue Installation (keine Daten)

```bash
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('[OK] Tabellen erstellt')"
```

### Option B: Migration von SQLite (mit bestehenden Daten)

```bash
# Migriere alle Daten von SQLite zu PostgreSQL
python migrate_to_postgres.py

# Verifiziere Migration
python migrate_to_postgres.py --verify
```

---

## Schritt 5: Anwendung testen (2 Minuten)

```bash
# Starte die Anwendung
python app.py
```

Öffne: http://localhost:5000

### Teste:
1. ✅ Kalender lädt
2. ✅ Neue Buchung erstellen
3. ✅ Admin-Panel öffnen
4. ✅ Buchung bestätigen/ablehnen

---

## pgAdmin Web-Interface (Optional)

pgAdmin ist ein Web-Tool zur Verwaltung von PostgreSQL.

### Zugriff:
1. Öffne: http://localhost:5050
2. Login: admin@example.com / admin
3. Add New Server:
   - Name: Raumbuchung
   - Host: db (oder localhost)
   - Port: 5432
   - Database: buchungen
   - Username: admin
   - Password: changeme

### pgAdmin Features:
- Tabellen anzeigen
- Queries ausführen
- Daten bearbeiten
- Backups erstellen
- Performance überwachen

---

## Backup & Restore

### Manuelles Backup

```bash
# Backup erstellen
docker exec raumbuchung-db pg_dump -U admin buchungen > backup_$(date +%Y%m%d).sql

# Oder mit docker-compose:
docker-compose exec db pg_dump -U admin buchungen > backup.sql
```

### Restore

```bash
# Aus Backup wiederherstellen
docker exec -i raumbuchung-db psql -U admin buchungen < backup_20250103.sql

# Oder:
cat backup.sql | docker exec -i raumbuchung-db psql -U admin buchungen
```

### Automatisches Backup (Windows Task Scheduler)

```batch
REM backup.bat
@echo off
cd C:\Users\admin\Desktop\KalenderTool
docker exec raumbuchung-db pg_dump -U admin buchungen > backups\backup_%date:~-4,4%%date:~-7,2%%date:~-10,2%.sql
```

Erstelle einen Task im Windows Task Scheduler:
- Aktion: backup.bat ausführen
- Trigger: Täglich um 2:00 Uhr

---

## Performance-Optimierung

### Indizes erstellen

```bash
# Mit Python
python -c "
from app import app, db

with app.app_context():
    # Erstelle Indizes
    db.engine.execute('''
        CREATE INDEX IF NOT EXISTS idx_buchung_dates ON buchung(start_datum, end_datum);
        CREATE INDEX IF NOT EXISTS idx_buchung_active ON buchung(is_active);
        CREATE INDEX IF NOT EXISTS idx_buchung_status ON buchung(status);
        CREATE INDEX IF NOT EXISTS idx_buchung_raum ON buchung(raum_id);
        CREATE INDEX IF NOT EXISTS idx_buchung_overlap ON buchung(raum_id, status, is_active, start_datum, end_datum);
    ''')
    print('[OK] Indizes erstellt')
"
```

### Connection Pool konfigurieren

Füge in `app.py` hinzu:

```python
# Nach app.config['SQLALCHEMY_DATABASE_URI'] = ...
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,        # Max 10 Verbindungen
    'pool_recycle': 3600,   # Recycle nach 1 Stunde
    'pool_pre_ping': True,  # Teste Verbindung vor Verwendung
}
```

---

## Monitoring

### Container Logs anzeigen

```bash
# PostgreSQL Logs
docker-compose logs -f db

# Alle Container Logs
docker-compose logs -f
```

### Container Status prüfen

```bash
docker-compose ps
```

### Ressourcen-Nutzung

```bash
docker stats raumbuchung-db
```

---

## Troubleshooting

### Problem: Container startet nicht

```bash
# Logs anzeigen
docker-compose logs db

# Container neu starten
docker-compose restart db

# Komplett neu starten
docker-compose down
docker-compose up -d
```

### Problem: Kann nicht verbinden

```bash
# Prüfe ob Port 5432 offen ist
netstat -an | findstr 5432

# Prüfe Container Status
docker-compose ps

# Teste Verbindung
docker exec raumbuchung-db psql -U admin -d buchungen -c "SELECT 1"
```

### Problem: Passwort vergessen

```bash
# Setze neues Passwort
docker exec raumbuchung-db psql -U admin -d postgres -c "ALTER USER admin WITH PASSWORD 'neues-passwort';"

# Aktualisiere .env
DATABASE_URI=postgresql://admin:neues-passwort@localhost:5432/buchungen
```

### Problem: Datenbank ist voll / beschädigt

```bash
# Datenbank neu erstellen (ACHTUNG: Löscht alle Daten!)
docker-compose down -v
docker-compose up -d
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

---

## Container-Befehle

### Starten/Stoppen

```bash
# Starten
docker-compose up -d

# Stoppen
docker-compose stop

# Stoppen und Container entfernen
docker-compose down

# Stoppen, Container UND Volumes entfernen (LÖSCHT DATEN!)
docker-compose down -v
```

### Logs

```bash
# Alle Logs
docker-compose logs

# Nur PostgreSQL
docker-compose logs db

# Live-Logs (Follow)
docker-compose logs -f db
```

### Shell im Container

```bash
# PostgreSQL Shell (psql)
docker exec -it raumbuchung-db psql -U admin -d buchungen

# Bash Shell
docker exec -it raumbuchung-db bash
```

---

## PostgreSQL vs SQLite - Unterschiede im Code

Gute Nachricht: **Fast keine Änderungen nötig!**

SQLAlchemy abstrahiert die Datenbank-Unterschiede.

### Diese Queries funktionieren identisch:

```python
# Filter
Buchung.query.filter_by(status='bestätigt').all()

# Joins
Buchung.query.join(Raum).all()

# Count
Buchung.query.count()

# Order
Buchung.query.order_by(Buchung.start_datum.desc()).all()
```

### Mögliche Unterschiede:

#### DateTime-Handling
SQLite speichert DateTime als String, PostgreSQL als TIMESTAMP.

**Kein Problem**, wenn du immer Python datetime verwendest:
```python
from datetime import datetime
buchung.start_datum = datetime.utcnow()  # Funktioniert überall
```

#### Boolean-Typ
- SQLite: 0 oder 1
- PostgreSQL: true/false

**Kein Problem**, SQLAlchemy konvertiert automatisch.

---

## Produktions-Konfiguration

### Für Live-Deployment:

```python
# app.py - Nur für Produktion

import os

if os.getenv('FLASK_ENV') == 'production':
    # Connection Pool
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 20,
        'max_overflow': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }

    # SSL für PostgreSQL-Verbindung
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI') + '?sslmode=require'
```

### Umgebungsvariablen für Produktion:

```bash
# .env (Produktion)
DATABASE_URI=postgresql://user:strong-password@production-server:5432/buchungen
FLASK_ENV=production
```

---

## Checkliste vor Go-Live

- [ ] Starkes Datenbank-Passwort gesetzt
- [ ] Backups funktionieren (getestet!)
- [ ] Indizes erstellt
- [ ] Connection Pool konfiguriert
- [ ] Monitoring eingerichtet
- [ ] SSL-Verbindung aktiviert (Produktion)
- [ ] Firewall: Nur notwendige Ports offen
- [ ] pgAdmin nur über VPN erreichbar (oder deaktiviert)
- [ ] Regelmäßige Updates eingeplant

---

## Nützliche Queries

### Tabellengrößen anzeigen

```sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Aktive Verbindungen

```sql
SELECT * FROM pg_stat_activity WHERE datname = 'buchungen';
```

### Slow Queries finden

```sql
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## Support

Bei Problemen:
1. Prüfe Logs: `docker-compose logs db`
2. Prüfe Verbindung: `docker exec raumbuchung-db psql -U admin -d buchungen -c "SELECT 1"`
3. Erstelle Issue mit Fehlermeldung

---

**Geschätzte Setup-Zeit:** 15 Minuten
**Schwierigkeit:** ⭐⭐ (Mittel)
**Status:** Produktionsreif ✅
