# Server Deployment Guide

## 🚀 Super-Einfaches Docker Deployment

**Alles läuft in Docker - Flask App, PostgreSQL, Redis, und pgAdmin!**

Mit diesem Setup musst du auf dem Server nur noch:
```bash
git pull && docker-compose up -d
```

Das war's! Keine Python-Installation, keine manuellen Dependencies, kein Stress.

---

## 📋 Erstmaliges Setup auf dem Server

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose installieren
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Optional: Docker ohne sudo verwenden
sudo usermod -aG docker $USER
# Dann ausloggen und wieder einloggen!
```

### Schritt 2: Repository klonen
```bash
cd /var/www  # oder dein bevorzugter Pfad
git clone https://github.com/DEIN-REPO/raumbuchung.git
cd raumbuchung
```

### Schritt 3: .env Datei erstellen
```bash
# Kopiere die Beispiel-Datei
cp .env.example .env

# Bearbeite die .env Datei
nano .env
```

**WICHTIG:** Ändere mindestens diese Werte:
```bash
# Generiere einen sicheren Key:
# python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=HIER-EINEN-NEUEN-SICHEREN-KEY-EINFÜGEN

# Setze ein sicheres Datenbank-Passwort
DB_PASSWORD=HIER-EIN-SICHERES-PASSWORT
```

Die restlichen Werte (E-Mail, Admin) sind bereits korrekt vorkonfiguriert.

### Schritt 4: Starte alle Services
```bash
# Baue und starte alle Container
docker-compose up -d

# Prüfe ob alles läuft
docker-compose ps
```

Du solltest 4 Container sehen:
- ✅ `raumbuchung-app` (Flask Anwendung)
- ✅ `raumbuchung-db` (PostgreSQL)
- ✅ `raumbuchung-redis` (Redis)
- ✅ `raumbuchung-pgadmin` (pgAdmin)

### Schritt 5: Datenbank initialisieren
```bash
# Erstelle die Datenbank-Tabellen
docker-compose exec app python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Schritt 6: Teste die Anwendung
```bash
# Health Check
curl http://localhost:8000/health

# Öffne im Browser
http://deine-server-ip:8000
```

**Das war's!** Die Anwendung läuft jetzt vollständig in Docker.

---

## 🔄 Updates deployen (das wird dein Standard-Workflow!)

Wenn du Code-Änderungen deployest:

```bash
# 1. Hole neuesten Code
cd /var/www/raumbuchung
git pull origin main

# 2. Baue und starte neu
docker-compose up -d --build

# 3. Fertig!
```

Das war's! Docker kümmert sich um alles:
- Python Dependencies werden automatisch installiert
- Datenbank bleibt erhalten (Persistent Volume)
- Alte Container werden sauber ersetzt

---

## 🔧 Nützliche Docker-Befehle

```bash
# Status aller Container anzeigen
docker-compose ps

# Logs anschauen (alle Services)
docker-compose logs -f

# Logs nur von der App
docker-compose logs -f app

# Container neu starten
docker-compose restart app

# Alles stoppen
docker-compose down

# Alles stoppen UND Daten löschen (VORSICHT!)
docker-compose down -v

# In Container einsteigen (für Debugging)
docker-compose exec app bash
docker-compose exec db psql -U admin -d buchungen
```

---

## 📊 pgAdmin verwenden

pgAdmin ist eine Web-UI für PostgreSQL:

```bash
# Öffne im Browser
http://deine-server-ip:5050

# Login:
Email: admin@example.com
Password: admin  (oder dein PGADMIN_PASSWORD aus .env)
```

**Server verbinden:**
1. Add New Server
2. General > Name: `Raumbuchung`
3. Connection:
   - Host: `db` (nicht localhost!)
   - Port: `5432`
   - Database: `buchungen`
   - Username: `admin`
   - Password: dein `DB_PASSWORD` aus .env

---

## 🎯 Nginx Reverse Proxy (Optional aber empfohlen)

Für Produktion solltest du Nginx vor die App schalten:

```bash
sudo apt-get install nginx
```

Erstelle `/etc/nginx/sites-available/raumbuchung`:
```nginx
server {
    listen 80;
    server_name deine-domain.de;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Aktivieren:
```bash
sudo ln -s /etc/nginx/sites-available/raumbuchung /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### HTTPS mit Let's Encrypt
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d deine-domain.de
```

---

## 🔍 Troubleshooting

### Problem: Container starten nicht
```bash
# Prüfe Status
docker-compose ps

# Zeige Logs
docker-compose logs

# Baue neu ohne Cache
docker-compose build --no-cache
docker-compose up -d
```

### Problem: App kann nicht auf Datenbank zugreifen
```bash
# Prüfe ob DB-Container läuft
docker-compose ps db

# Zeige DB-Logs
docker-compose logs db

# Teste DB-Verbindung
docker-compose exec db psql -U admin -d buchungen -c "SELECT 1;"

# Prüfe Netzwerk
docker network ls
docker network inspect raumbuchung_network
```

### Problem: Port 8000 ist bereits belegt
```bash
# Finde Prozess
netstat -tulpn | grep 8000
# oder
lsof -i :8000

# Ändere Port in docker-compose.yml
# ports:
#   - "8080:8000"  # Host:Container
```

### Problem: .env Variablen werden nicht geladen
```bash
# Prüfe ob .env existiert
ls -la .env

# Zeige aktuelle Umgebungsvariablen im Container
docker-compose exec app env | grep DB_PASSWORD

# Container mit neuer .env neu starten
docker-compose down
docker-compose up -d
```

### Problem: Datenbank-Tabellen existieren nicht
```bash
# Erstelle Tabellen
docker-compose exec app python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Prüfe ob Tabellen existiert
docker-compose exec db psql -U admin -d buchungen -c "\dt"
```

### Problem: "Build failed" beim ersten Start
```bash
# Prüfe ob Dockerfile existiert
ls -la Dockerfile

# Prüfe Docker-Logs
docker-compose logs app

# Häufige Ursachen:
# - requirements.txt fehlt
# - Syntax-Fehler in Dockerfile
# - Netzwerk-Probleme beim Download
```

---

## 💾 Backup-Strategie

### Manuelles Backup erstellen

```bash
# Backup erstellen
docker-compose exec db pg_dump -U admin buchungen > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup wiederherstellen
docker-compose exec -T db psql -U admin -d buchungen < backup_20250101_120000.sql
```

### Automatisches tägliches Backup einrichten

```bash
# Erstelle Backup-Skript
sudo cat > /usr/local/bin/backup-raumbuchung.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/raumbuchung"
DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="/var/www/raumbuchung"

mkdir -p $BACKUP_DIR

# PostgreSQL Backup
cd $PROJECT_DIR
docker-compose exec -T db pg_dump -U admin buchungen > $BACKUP_DIR/buchungen_$DATE.sql

# Komprimieren
gzip $BACKUP_DIR/buchungen_$DATE.sql

# Alte Backups löschen (älter als 30 Tage)
find $BACKUP_DIR -name "buchungen_*.sql.gz" -mtime +30 -delete

echo "Backup created: $BACKUP_DIR/buchungen_$DATE.sql.gz"
EOF

# Ausführbar machen
sudo chmod +x /usr/local/bin/backup-raumbuchung.sh

# Cron-Job erstellen (täglich um 2 Uhr)
sudo crontab -e
# Füge hinzu:
0 2 * * * /usr/local/bin/backup-raumbuchung.sh >> /var/log/raumbuchung-backup.log 2>&1
```

---

## 🔐 Sicherheits-Checkliste

Vor Go-Live prüfen:

- [ ] **.env hat sichere Passwörter** (nicht die Beispiel-Werte!)
  ```bash
  # Generiere neuen SECRET_KEY
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

- [ ] **FLASK_ENV=production** (nicht development!)

- [ ] **PostgreSQL Port ist NICHT öffentlich** (5433 nur für localhost)
  ```bash
  # In docker-compose.yml sollte stehen:
  # ports:
  #   - "127.0.0.1:5433:5432"  # Nur localhost!
  ```

- [ ] **Firewall konfiguriert**
  ```bash
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  sudo ufw allow 22/tcp  # SSH
  sudo ufw enable
  ```

- [ ] **HTTPS aktiviert** (Let's Encrypt)
- [ ] **Backup-System läuft**
- [ ] **Nginx Reverse Proxy** konfiguriert
- [ ] **Container haben restart policy** (already done: `restart: unless-stopped`)

---

## 🎉 Vorteile des Docker-Setups

**Auf deinem Desktop (Docker Desktop):**
- ✅ Gleiche Umgebung wie auf dem Server
- ✅ Keine Konflikte mit anderen Python-Projekten
- ✅ Einfaches Testen

**Auf dem Server:**
- ✅ `git pull && docker-compose up -d` - Fertig!
- ✅ Keine manuelle Python/pip-Installation
- ✅ Isolierte Umgebung
- ✅ Einfaches Rollback (alte Images bleiben)
- ✅ Skalierbar (einfach mehr Worker-Container hinzufügen)

**Unterschiede zwischen Desktop und Server:**
- **KEINE!** Genau dasselbe Setup, keine Überraschungen mehr!

---

## 📝 Quick Reference

### Tägliche Befehle
```bash
# Logs anschauen
docker-compose logs -f app

# App neu starten
docker-compose restart app

# Status prüfen
docker-compose ps
```

### Update deployen
```bash
git pull origin main && docker-compose up -d --build
```

### Backup erstellen
```bash
docker-compose exec db pg_dump -U admin buchungen > backup.sql
```

### Backup wiederherstellen
```bash
docker-compose exec -T db psql -U admin -d buchungen < backup.sql
```

---

## 🆘 Support & Debugging

**Container Logs:**
```bash
# Alle Logs
docker-compose logs -f

# Nur App
docker-compose logs -f app

# Nur Datenbank
docker-compose logs -f db

# Letzte 50 Zeilen
docker-compose logs --tail=50 app
```

**In Container einsteigen:**
```bash
# Flask-App
docker-compose exec app bash
# Dann: python, pip, etc.

# Datenbank
docker-compose exec db psql -U admin -d buchungen
# Dann: SQL-Befehle
```

**Performance prüfen:**
```bash
# Ressourcen-Verbrauch
docker stats

# Container-Details
docker inspect raumbuchung-app
```
