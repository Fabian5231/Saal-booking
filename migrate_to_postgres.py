"""
Migrations-Skript: SQLite zu PostgreSQL
Migriert alle Daten von SQLite zu PostgreSQL
"""
import os
import sys
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

# Importiere Flask-App
from app import app, db, Buchung, Raum, Settings

def migrate_sqlite_to_postgres():
    """Migriert Daten von SQLite zu PostgreSQL"""

    sqlite_path = 'instance/buchungen.db'

    if not os.path.exists(sqlite_path):
        print("[FEHLER] SQLite Datenbank nicht gefunden: instance/buchungen.db")
        print("Nichts zu migrieren.")
        return

    print("\n" + "="*60)
    print("Migration: SQLite -> PostgreSQL")
    print("="*60 + "\n")

    # Prüfe ob PostgreSQL konfiguriert ist
    db_uri = os.getenv('DATABASE_URI', '')
    if 'postgresql' not in db_uri:
        print("[FEHLER] DATABASE_URI ist nicht auf PostgreSQL gesetzt!")
        print(f"Aktuelle URI: {db_uri}")
        print("\nBitte aktualisiere .env:")
        print("DATABASE_URI=postgresql://username:password@localhost:5432/buchungen")
        return

    with app.app_context():
        print("[1/5] Verbinde zu PostgreSQL...")
        try:
            # Teste Verbindung
            db.engine.connect()
            print("[OK] PostgreSQL Verbindung erfolgreich\n")
        except Exception as e:
            print(f"[FEHLER] Kann nicht zu PostgreSQL verbinden: {str(e)}")
            print("\nStelle sicher dass:")
            print("1. PostgreSQL läuft (docker-compose up -d)")
            print("2. DATABASE_URI in .env korrekt ist")
            return

        print("[2/5] Erstelle PostgreSQL Tabellen...")
        db.create_all()
        print("[OK] Tabellen erstellt\n")

        print("[3/5] Verbinde zu SQLite...")
        try:
            sqlite_conn = sqlite3.connect(sqlite_path)
            sqlite_conn.row_factory = sqlite3.Row
            sqlite_cursor = sqlite_conn.cursor()
            print("[OK] SQLite Verbindung erfolgreich\n")
        except Exception as e:
            print(f"[FEHLER] Kann nicht zu SQLite verbinden: {str(e)}")
            return

        # Statistik
        stats = {
            'raeume': 0,
            'buchungen': 0,
            'settings': 0,
            'fehler': 0
        }

        print("[4/5] Migriere Daten...\n")

        # Migriere Räume
        print("  -> Migriere Räume...")
        try:
            sqlite_cursor.execute("SELECT * FROM raum")
            raeume = sqlite_cursor.fetchall()

            for row in raeume:
                raum = Raum(
                    id=row['id'],
                    name=row['name'],
                    beschreibung=row['beschreibung'] if row['beschreibung'] else ''
                )
                db.session.merge(raum)
                stats['raeume'] += 1

            db.session.commit()
            print(f"  [OK] {stats['raeume']} Räume migriert")
        except Exception as e:
            print(f"  [FEHLER] Räume: {str(e)}")
            stats['fehler'] += 1
            db.session.rollback()

        # Migriere Buchungen
        print("  -> Migriere Buchungen...")
        try:
            sqlite_cursor.execute("SELECT * FROM buchung")
            buchungen = sqlite_cursor.fetchall()

            for row in buchungen:
                # Parse Datetime-Strings
                start_datum = datetime.fromisoformat(row['start_datum']) if isinstance(row['start_datum'], str) else row['start_datum']
                end_datum = datetime.fromisoformat(row['end_datum']) if isinstance(row['end_datum'], str) else row['end_datum']
                erstellt_am = datetime.fromisoformat(row['erstellt_am']) if row['erstellt_am'] and isinstance(row['erstellt_am'], str) else row['erstellt_am']

                # Prüfe ob neue Felder existieren
                is_active = True
                geloescht_am = None
                try:
                    is_active = bool(row['is_active']) if 'is_active' in row.keys() else True
                    geloescht_am = row['geloescht_am'] if 'geloescht_am' in row.keys() else None
                    if geloescht_am and isinstance(geloescht_am, str):
                        geloescht_am = datetime.fromisoformat(geloescht_am)
                except:
                    pass

                buchung = Buchung(
                    id=row['id'],
                    raum_id=row['raum_id'],
                    start_datum=start_datum,
                    end_datum=end_datum,
                    benutzer_name=row['benutzer_name'],
                    benutzer_email=row['benutzer_email'],
                    zweck=row['zweck'] if row['zweck'] else '',
                    status=row['status'],
                    is_active=is_active,
                    geloescht_am=geloescht_am,
                    erstellt_am=erstellt_am
                )
                db.session.merge(buchung)
                stats['buchungen'] += 1

            db.session.commit()
            print(f"  [OK] {stats['buchungen']} Buchungen migriert")
        except Exception as e:
            print(f"  [FEHLER] Buchungen: {str(e)}")
            stats['fehler'] += 1
            db.session.rollback()

        # Migriere Settings (falls vorhanden)
        print("  -> Migriere Settings...")
        try:
            sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
            if sqlite_cursor.fetchone():
                sqlite_cursor.execute("SELECT * FROM settings")
                settings = sqlite_cursor.fetchall()

                for row in settings:
                    setting = Settings(
                        id=row['id'],
                        key=row['key'],
                        value=row['value'] if row['value'] else '',
                        beschreibung=row['beschreibung'] if row['beschreibung'] else ''
                    )
                    db.session.merge(setting)
                    stats['settings'] += 1

                db.session.commit()
                print(f"  [OK] {stats['settings']} Settings migriert")
            else:
                print("  [INFO] Keine Settings-Tabelle vorhanden")
        except Exception as e:
            print(f"  [FEHLER] Settings: {str(e)}")
            stats['fehler'] += 1
            db.session.rollback()

        sqlite_conn.close()

        print("\n[5/5] Verifiziere Migration...")

        # Verifiziere Counts
        postgres_raeume = Raum.query.count()
        postgres_buchungen = Buchung.query.count()
        postgres_settings = Settings.query.count()

        print(f"  PostgreSQL Räume: {postgres_raeume}")
        print(f"  PostgreSQL Buchungen: {postgres_buchungen}")
        print(f"  PostgreSQL Settings: {postgres_settings}")

        print("\n" + "="*60)
        print("Migration abgeschlossen!")
        print("="*60)
        print(f"\nStatistik:")
        print(f"  Räume:     {stats['raeume']} migriert")
        print(f"  Buchungen: {stats['buchungen']} migriert")
        print(f"  Settings:  {stats['settings']} migriert")
        print(f"  Fehler:    {stats['fehler']}")

        if stats['fehler'] == 0:
            print("\n[OK] Migration erfolgreich! Alle Daten wurden übertragen.")
            print("\nNächste Schritte:")
            print("1. Teste die Anwendung: python app.py")
            print("2. Wenn alles funktioniert, benenne SQLite-DB um:")
            print("   mv instance/buchungen.db instance/buchungen.db.backup")
        else:
            print("\n[WARNUNG] Migration mit Fehlern abgeschlossen.")
            print("Bitte prüfe die Fehler oben und versuche es erneut.")

def verify_migration():
    """Verifiziert dass die Migration erfolgreich war"""
    with app.app_context():
        print("\nVerifizierung:")
        print("-" * 40)

        raeume = Raum.query.all()
        print(f"Räume: {len(raeume)}")
        for r in raeume:
            print(f"  - {r.name}")

        buchungen = Buchung.query.all()
        print(f"\nBuchungen: {len(buchungen)}")
        print(f"  Aktiv: {Buchung.query.filter_by(is_active=True).count()}")
        print(f"  Gelöscht: {Buchung.query.filter_by(is_active=False).count()}")
        print(f"  Ausstehend: {Buchung.query.filter_by(status='ausstehend').count()}")
        print(f"  Bestätigt: {Buchung.query.filter_by(status='bestätigt').count()}")
        print(f"  Abgelehnt: {Buchung.query.filter_by(status='abgelehnt').count()}")

        settings = Settings.query.all()
        print(f"\nSettings: {len(settings)}")
        for s in settings:
            print(f"  - {s.key}: {s.value}")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--verify':
        verify_migration()
    else:
        migrate_sqlite_to_postgres()
