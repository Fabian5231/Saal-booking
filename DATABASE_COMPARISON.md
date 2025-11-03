# Datenbank-Vergleich für Raumbuchungssystem

## Warum nicht SQLite in Produktion?

SQLite ist großartig für Development, hat aber Limitierungen:

❌ **Probleme mit SQLite**:
- Nur ein Schreibvorgang gleichzeitig (Database Locking)
- Bei mehreren Benutzern: Performance-Probleme
- Keine echte Client-Server-Architektur
- Limitierte Skalierbarkeit
- Kein Remote-Zugriff
- Backup während Betrieb schwierig

---

## 🏆 Empfehlung: PostgreSQL

### Warum PostgreSQL?

✅ **Perfekt für diesen Use-Case**:
- **ACID-Compliant**: Wichtig für Buchungskonflikte
- **Concurrent Writes**: Mehrere Benutzer gleichzeitig
- **Transaktionale Integrität**: Keine Doppelbuchungen
- **Kostenlos & Open Source**
- **Ausgereifte Python-Integration**
- **Gute Performance** für kleine bis mittlere Projekte
- **Einfaches Backup**: pg_dump, pg_restore
- **JSON-Unterstützung**: Falls später benötigt
- **Große Community**: Viele Ressourcen

### Installation

#### Windows:
```bash
# Download von: https://www.postgresql.org/download/windows/
# Installer ausführen

# Oder mit Chocolatey:
choco install postgresql
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

#### Docker (empfohlen für Development):
```bash
docker run --name raumbuchung-db \
  -e POSTGRES_PASSWORD=dein-passwort \
  -e POSTGRES_DB=buchungen \
  -p 5432:5432 \
  -v postgres-data:/var/lib/postgresql/data \
  -d postgres:16
```

### Integration in Flask

#### 1. Installiere psycopg2:
```bash
pip install psycopg2-binary
```

#### 2. Aktualisiere requirements.txt:
```txt
# requirements.txt
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Mail==0.9.1
Flask-Limiter==3.5.0
itsdangerous==2.1.2
python-dotenv==1.0.0
psycopg2-binary==2.9.9  # Neu hinzufügen
```

#### 3. Aktualisiere .env:
```bash
# .env
DATABASE_URI=postgresql://username:password@localhost:5432/buchungen
```

#### 4. Aktualisiere app.py:
```python
# Keine Änderung nötig! SQLAlchemy unterstützt PostgreSQL automatisch
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
```

### Migration von SQLite zu PostgreSQL

```bash
# 1. Exportiere Daten aus SQLite
sqlite3 instance/buchungen.db .dump > backup.sql

# 2. Konvertiere zu PostgreSQL-Format (optional Tool verwenden)
# pgloader ist ein gutes Tool dafür

# 3. Oder: Python-Skript nutzen
python migrate_sqlite_to_postgres.py
```

### Backup-Strategie

```bash
# Manuelles Backup
pg_dump -U username buchungen > backup_$(date +%Y%m%d).sql

# Wiederherstellen
psql -U username buchungen < backup_20250103.sql

# Automatisches Backup (Cron-Job)
# Täglich um 2 Uhr nachts
0 2 * * * pg_dump -U username buchungen > /backups/buchungen_$(date +\%Y\%m\%d).sql
```

### Performance-Optimierung

```sql
-- Erstelle Indizes für häufige Queries
CREATE INDEX idx_buchung_dates ON buchung(start_datum, end_datum);
CREATE INDEX idx_buchung_active ON buchung(is_active);
CREATE INDEX idx_buchung_status ON buchung(status);
CREATE INDEX idx_buchung_raum ON buchung(raum_id);

-- Kombinierter Index für Überschneidungsprüfung
CREATE INDEX idx_buchung_overlap ON buchung(raum_id, status, is_active, start_datum, end_datum);
```

---

## Alternative: MySQL/MariaDB

### Wann MySQL wählen?

✅ **Vorteile**:
- Leichter als PostgreSQL
- Einfachere Verwaltung
- Weit verbreitet (Shared Hosting)
- Gute Performance für Read-Heavy Workloads

❌ **Nachteile**:
- Weniger Features als PostgreSQL
- Strengere Lizenz (MySQL ist Oracle)
- MariaDB ist bessere Alternative (Fork von MySQL)

### Installation

```bash
# MariaDB (empfohlen statt MySQL)
# Windows: https://mariadb.org/download/
# Linux:
sudo apt install mariadb-server
```

### Integration

```bash
pip install mysqlclient
# oder
pip install PyMySQL
```

```python
# .env
DATABASE_URI=mysql+pymysql://username:password@localhost/buchungen
```

---

## Alternative: Cloud-Datenbanken

### Wenn du Cloud-Hosting nutzt:

#### 1. **Supabase** (PostgreSQL as a Service)
- ✅ Kostenloser Tier: Bis zu 500 MB Datenbank
- ✅ Automatische Backups
- ✅ Einfaches Setup
- ✅ Web-Interface
- 💰 Free bis Professional: 25 €/Monat

```bash
# .env
DATABASE_URI=postgresql://user:pass@db.xxxx.supabase.co:5432/postgres
```

#### 2. **Railway.app** (PostgreSQL)
- ✅ Free Tier: 500 MB
- ✅ Einfaches Deployment
- ✅ Automatische Backups
- 💰 $5/Monat für mehr Ressourcen

#### 3. **Neon** (Serverless PostgreSQL)
- ✅ Free Tier: 3 GB Storage
- ✅ Serverless (skaliert automatisch)
- ✅ Branching-Support
- 💰 Free bis Pro: $19/Monat

#### 4. **PlanetScale** (MySQL)
- ✅ Free Tier: 5 GB Storage
- ✅ Serverless MySQL
- ✅ Automatische Backups
- 💰 Free bis Pro: $29/Monat

#### 5. **Managed Hosting Anbieter**

**Hetzner Cloud** (empfohlen für DE):
- 💰 Server ab 4,51 €/Monat
- Selbst PostgreSQL installieren
- Volle Kontrolle

**DigitalOcean Managed Database**:
- 💰 Ab $15/Monat
- Automatische Backups
- Automatische Updates

---

## Entscheidungshilfe

### Für dein Raumbuchungssystem:

| Kriterium | SQLite | PostgreSQL | MySQL/MariaDB | Cloud DB |
|-----------|--------|------------|---------------|----------|
| **Development** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Produktion** | ❌ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Concurrent Users** | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Setup-Komplexität** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Kosten** | Gratis | Gratis | Gratis | 0-25 €/Monat |
| **Backup** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Skalierbarkeit** | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Community Support** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

### Meine Empfehlung nach Szenario:

#### 📍 **Szenario 1: Kleines Projekt, Self-Hosted**
→ **PostgreSQL auf eigenem Server/VPS**
- Hetzner Cloud VPS (4,51 €/Monat)
- Selbst PostgreSQL installieren
- Volle Kontrolle, niedrige Kosten

#### 📍 **Szenario 2: Mittleres Projekt, wenig Zeit**
→ **Cloud PostgreSQL (Supabase/Railway)**
- Kein Server-Management
- Automatische Backups
- Schnelles Setup
- 0-25 €/Monat

#### 📍 **Szenario 3: Großes Projekt, Enterprise**
→ **Managed Database (DigitalOcean/Hetzner)**
- Professionelle Unterstützung
- SLA Garantien
- Automatisches Scaling
- 15-50 €/Monat

---

## 🎯 Konkrete Empfehlung für dich

Basierend auf deinem Projekt:
- **Ein Raumbuchungssystem für einen Saal**
- **Vermutlich < 100 Benutzer**
- **Kleine bis mittlere Datenmenge**

### Top-Wahl: PostgreSQL auf eigenem Server

**Warum:**
1. ✅ Kostenlos (außer Server: ~5 €/Monat)
2. ✅ Perfekte Balance zwischen Features und Komplexität
3. ✅ Zukunftssicher (kann leicht skalieren)
4. ✅ Beste ACID-Compliance (wichtig für Buchungen)
5. ✅ Große Community, viele Ressourcen

**Setup-Zeit:** 30 Minuten
**Monatliche Kosten:** 4-10 € (VPS)

---

## Migration Plan: SQLite → PostgreSQL

### Phase 1: Setup (30 Min)

```bash
# 1. PostgreSQL installieren (Docker)
docker run --name raumbuchung-db \
  -e POSTGRES_PASSWORD=sicheres-passwort \
  -e POSTGRES_DB=buchungen \
  -p 5432:5432 \
  -v C:/postgres-data:/var/lib/postgresql/data \
  -d postgres:16

# 2. Dependencies installieren
pip install psycopg2-binary

# 3. .env aktualisieren
DATABASE_URI=postgresql://postgres:sicheres-passwort@localhost:5432/buchungen
```

### Phase 2: Daten migrieren (15 Min)

Ich erstelle dir ein Migrations-Skript:

```python
# migrate_to_postgres.py
import sqlite3
import psycopg2
from app import app, db, Buchung, Raum, Settings

def migrate_data():
    with app.app_context():
        # Erstelle neue PostgreSQL-Tabellen
        db.create_all()
        print("[OK] PostgreSQL Tabellen erstellt")

        # Verbinde zu SQLite
        sqlite_conn = sqlite3.connect('instance/buchungen.db')
        sqlite_cursor = sqlite_conn.cursor()

        # Migriere Räume
        sqlite_cursor.execute("SELECT * FROM raum")
        raeume = sqlite_cursor.fetchall()
        for r in raeume:
            raum = Raum(id=r[0], name=r[1], beschreibung=r[2])
            db.session.merge(raum)
        db.session.commit()
        print(f"[OK] {len(raeume)} Räume migriert")

        # Migriere Buchungen
        sqlite_cursor.execute("SELECT * FROM buchung")
        buchungen = sqlite_cursor.fetchall()
        for b in buchungen:
            buchung = Buchung(
                id=b[0],
                raum_id=b[1],
                start_datum=b[2],
                end_datum=b[3],
                benutzer_name=b[4],
                benutzer_email=b[5],
                zweck=b[6],
                status=b[7],
                is_active=b[8] if len(b) > 8 else True,
                geloescht_am=b[9] if len(b) > 9 else None,
                erstellt_am=b[10] if len(b) > 10 else None
            )
            db.session.merge(buchung)
        db.session.commit()
        print(f"[OK] {len(buchungen)} Buchungen migriert")

        sqlite_conn.close()
        print("\n[OK] Migration abgeschlossen!")

if __name__ == '__main__':
    migrate_data()
```

### Phase 3: Testing (30 Min)

```bash
# 1. Teste neue Verbindung
python -c "from app import app, db; app.app_context().push(); print(db.engine.url)"

# 2. Teste Queries
python -c "from app import app, Buchung; app.app_context().push(); print(Buchung.query.count())"

# 3. Teste Anwendung
python app.py
# Öffne http://localhost:5000 und teste alle Funktionen
```

---

## Quick Start: PostgreSQL mit Docker

Die schnellste Methode für dich:

```bash
# 1. Erstelle docker-compose.yml
version: '3.8'
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: buchungen
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: dein-sicheres-passwort
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:

# 2. Starte PostgreSQL
docker-compose up -d

# 3. Aktualisiere .env
DATABASE_URI=postgresql://admin:dein-sicheres-passwort@localhost:5432/buchungen

# 4. Installiere psycopg2
pip install psycopg2-binary

# 5. Erstelle Tabellen
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# 6. Fertig!
python app.py
```

---

## Zusammenfassung

### ✅ Für dich: PostgreSQL

**Installation:** Docker (5 Minuten)
**Kosten:** Gratis (Development) / 5-10 €/Monat (Produktion)
**Schwierigkeit:** Mittel
**Zukunftssicher:** Ja

### Nächste Schritte:

1. ✅ PostgreSQL mit Docker starten (siehe Quick Start oben)
2. ✅ Dependencies installieren (`pip install psycopg2-binary`)
3. ✅ .env aktualisieren
4. ✅ Daten migrieren (optional, wenn schon Daten vorhanden)
5. ✅ Testen

**Geschätzte Zeit:** 1 Stunde

Soll ich dir ein vollständiges Migrations-Skript und Docker-Setup erstellen?
