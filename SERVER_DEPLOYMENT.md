# Server Deployment Guide

## Antwort auf deine Frage:
**NEIN, nicht löschen!** Du kannst einfach `git pull` machen. Hier ist die Schritt-für-Schritt Anleitung:

---

## 🚀 Deployment auf bestehendem Server

### Option 1: Mit Docker (EMPFOHLEN)

#### Schritt 1: Git Pull
```bash
cd /pfad/zum/projekt
git pull origin main
```

#### Schritt 2: Docker & Docker Compose installieren (falls nicht vorhanden)
```bash
# Docker installieren (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose installieren
sudo apt-get update
sudo apt-get install docker-compose-plugin
```

#### Schritt 3: .env auf Server aktualisieren
```bash
# Bearbeite .env
nano .env

# Ändere diese Zeile:
# ALT: DATABASE_URI=sqlite:///buchungen.db
# NEU: DATABASE_URI=postgresql://admin:SICHERES-PASSWORT@localhost:5432/buchungen

# WICHTIG: Setze ein SICHERES Passwort!
```

#### Schritt 4: PostgreSQL mit Docker starten
```bash
# Starte PostgreSQL, Redis, pgAdmin
docker-compose up -d

# Prüfe ob Container laufen
docker-compose ps
```

#### Schritt 5: Python Dependencies installieren
```bash
# Aktiviere Virtual Environment (falls vorhanden)
source venv/bin/activate

# Oder erstelle neues venv
python3 -m venv venv
source venv/bin/activate

# Installiere neue Dependencies
pip install -r requirements.txt
```

#### Schritt 6: Daten migrieren
```bash
# Migriere Daten von SQLite zu PostgreSQL
python migrate_to_postgres.py

# Verifiziere Migration
python migrate_to_postgres.py --verify
```

#### Schritt 7: Anwendung neu starten
```bash
# Wenn mit systemd:
sudo systemctl restart raumbuchung

# Wenn mit Gunicorn manuell:
pkill gunicorn
gunicorn --bind 0.0.0.0:8000 --workers 4 app:app &

# Wenn mit screen/tmux:
# Alte Session beenden und neu starten
```

#### Schritt 8: Testen
```bash
# Prüfe ob Anwendung läuft
curl http://localhost:8000

# Oder öffne im Browser
# http://deine-server-ip:8000
```

---

### Option 2: Ohne Docker (PostgreSQL direkt installiert)

#### Schritt 1: Git Pull
```bash
cd /pfad/zum/projekt
git pull origin main
```

#### Schritt 2: PostgreSQL installieren (falls nicht vorhanden)
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# CentOS/RHEL
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup initdb
sudo systemctl start postgresql
```

#### Schritt 3: PostgreSQL Datenbank erstellen
```bash
# Als postgres User
sudo -u postgres psql

# In psql:
CREATE DATABASE buchungen;
CREATE USER admin WITH PASSWORD 'dein-sicheres-passwort';
GRANT ALL PRIVILEGES ON DATABASE buchungen TO admin;
\q
```

#### Schritt 4: .env aktualisieren
```bash
nano .env

# Ändere:
DATABASE_URI=postgresql://admin:dein-sicheres-passwort@localhost:5432/buchungen
```

#### Schritt 5: Dependencies installieren
```bash
source venv/bin/activate
pip install -r requirements.txt
```

#### Schritt 6: Daten migrieren
```bash
python migrate_to_postgres.py
python migrate_to_postgres.py --verify
```

#### Schritt 7: Anwendung neu starten
```bash
sudo systemctl restart raumbuchung
# oder
pkill gunicorn && gunicorn --bind 0.0.0.0:8000 --workers 4 app:app &
```

---

## ⚙️ Konfiguration für Produktion

### Wichtige .env Änderungen für Server:

```bash
# .env (Produktion)
SECRET_KEY=GENERIERE-EINEN-NEUEN-SICHEREN-KEY  # python -c "import secrets; print(secrets.token_hex(32))"
FLASK_ENV=production

# PostgreSQL
DATABASE_URI=postgresql://admin:SICHERES-PASSWORT@localhost:5432/buchungen

# E-Mail (deine bestehenden Werte behalten)
MAIL_SERVER=mailout.innos.cloud
MAIL_PORT=25
MAIL_USERNAME=besh
MAIL_PASSWORD=Besh149098#2020
MAIL_DEFAULT_SENDER_NAME=Reservierung Saal Raiffeinstraße
MAIL_DEFAULT_SENDER_EMAIL=Reservierung-Saal@besh.de

# Admin
ADMIN_EMAIL=fabian.klenk@besh.de
ADMIN_PIN=2502  # TODO: Durch längeres Passwort ersetzen!
```

### Gunicorn Konfiguration (wenn noch nicht vorhanden)

Erstelle `gunicorn.conf.py`:
```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"
```

Starten:
```bash
gunicorn --config gunicorn.conf.py app:app
```

### Systemd Service (wenn noch nicht vorhanden)

Erstelle `/etc/systemd/system/raumbuchung.service`:
```ini
[Unit]
Description=Raumbuchungssystem
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/pfad/zum/projekt
Environment="PATH=/pfad/zum/projekt/venv/bin"
ExecStart=/pfad/zum/projekt/venv/bin/gunicorn --config gunicorn.conf.py app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Aktivieren:
```bash
sudo systemctl daemon-reload
sudo systemctl enable raumbuchung
sudo systemctl start raumbuchung
```

---

## 🔍 Troubleshooting

### Problem: "ImportError: No module named psycopg2"
```bash
pip install psycopg2-binary
```

### Problem: "Can't connect to PostgreSQL"
```bash
# Prüfe ob PostgreSQL läuft
sudo systemctl status postgresql
# oder (Docker):
docker-compose ps

# Prüfe ob Port offen ist
netstat -an | grep 5432

# Teste Verbindung
psql -U admin -d buchungen -h localhost
```

### Problem: "Migration failed"
```bash
# Prüfe ob alte SQLite-DB existiert
ls -la instance/buchungen.db

# Prüfe PostgreSQL-Verbindung
python -c "from app import app, db; app.app_context().push(); print(db.engine.url)"

# Erstelle Tabellen manuell
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Problem: "Anwendung startet nicht"
```bash
# Prüfe Logs
tail -f logs/error.log

# Oder direkt starten um Fehler zu sehen
python app.py
```

---

## 📊 Backup-Strategie für Server

### Automatisches tägliches Backup einrichten

```bash
# Erstelle Backup-Skript
cat > /usr/local/bin/backup-raumbuchung.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/raumbuchung"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# PostgreSQL Backup
docker exec raumbuchung-db pg_dump -U admin buchungen > $BACKUP_DIR/buchungen_$DATE.sql

# Alte Backups löschen (älter als 30 Tage)
find $BACKUP_DIR -name "buchungen_*.sql" -mtime +30 -delete

echo "Backup created: $BACKUP_DIR/buchungen_$DATE.sql"
EOF

# Ausführbar machen
chmod +x /usr/local/bin/backup-raumbuchung.sh

# Cron-Job erstellen (täglich um 2 Uhr)
sudo crontab -e
# Füge hinzu:
0 2 * * * /usr/local/bin/backup-raumbuchung.sh >> /var/log/raumbuchung-backup.log 2>&1
```

---

## 🔐 Sicherheits-Checkliste für Server

Vor Go-Live prüfen:

- [ ] .env hat sichere Passwörter (nicht die Beispiel-Werte!)
- [ ] SECRET_KEY ist einzigartig und stark
- [ ] FLASK_ENV=production (nicht development!)
- [ ] PostgreSQL läuft nur auf localhost (nicht öffentlich erreichbar)
- [ ] Firewall ist konfiguriert (nur Port 80/443 offen)
- [ ] HTTPS ist aktiviert (z.B. mit Let's Encrypt)
- [ ] Backup-System läuft
- [ ] Logs werden rotiert (logrotate)
- [ ] Nginx als Reverse Proxy konfiguriert

---

## 🔄 Zukünftige Updates deployen

Für zukünftige Updates ist es ganz einfach:

```bash
# 1. Code aktualisieren
cd /pfad/zum/projekt
git pull origin main

# 2. Dependencies aktualisieren (falls requirements.txt geändert)
pip install -r requirements.txt

# 3. Datenbank-Migrationen (falls nötig)
# Siehe migrate_db.py oder zukünftige Migrations-Skripte

# 4. Anwendung neu starten
sudo systemctl restart raumbuchung
```

**Das wars!** Kein Löschen, kein Neuaufsetzen nötig.

---

## 📝 Zusammenfassung: Was du tun musst

1. ✅ `git pull origin main` auf dem Server
2. ✅ PostgreSQL einrichten (Docker ODER direkt)
3. ✅ `.env` aktualisieren (DATABASE_URI ändern)
4. ✅ `pip install -r requirements.txt`
5. ✅ `python migrate_to_postgres.py`
6. ✅ Anwendung neu starten

**Zeit:** 10-20 Minuten
**Downtime:** ~2 Minuten (während Neustart)

---

## 💡 Wichtige Hinweise

1. **Backup vorher!** Erstelle ein Backup der alten SQLite-DB:
   ```bash
   cp instance/buchungen.db instance/buchungen.db.backup_$(date +%Y%m%d)
   ```

2. **Teste nach Migration**: Öffne die Anwendung und teste:
   - Kalender lädt
   - Bestehende Buchungen sind sichtbar
   - Neue Buchung erstellen funktioniert
   - Admin-Panel funktioniert

3. **Alte SQLite-DB behalten**: Lösche die alte SQLite-DB erst nach einigen Tagen erfolgreichen Betriebs mit PostgreSQL.

---

## 🆘 Support

Falls Probleme auftreten:

1. Prüfe Logs: `tail -f logs/error.log`
2. Prüfe Container: `docker-compose ps` und `docker-compose logs -f`
3. Teste Verbindung: `psql -U admin -d buchungen -h localhost`

Bei Fragen: GitHub Issue erstellen oder Admin kontaktieren.
