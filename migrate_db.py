"""
Migrations-Skript fuer die Datenbank
Fuegt is_active und geloescht_am Felder zur Buchung-Tabelle hinzu
"""
import os
import sys
from app import app, db

def migrate_database():
    """Migriert die Datenbank und fuegt neue Felder hinzu"""
    with app.app_context():
        print("Starte Datenbank-Migration...")

        # Backup der alten Datenbank erstellen
        db_path = 'instance/buchungen.db'
        if os.path.exists(db_path):
            import shutil
            backup_path = 'instance/buchungen_backup.db'
            shutil.copy2(db_path, backup_path)
            print(f"[OK] Backup erstellt: {backup_path}")

        # Fuehre SQL-Migration aus
        try:
            # Fuege neue Spalten hinzu, falls sie nicht existieren
            with db.engine.connect() as conn:
                # Pruefe ob Spalten bereits existieren
                result = conn.execute(db.text("PRAGMA table_info(buchung)"))
                columns = [row[1] for row in result]

                if 'is_active' not in columns:
                    conn.execute(db.text("ALTER TABLE buchung ADD COLUMN is_active BOOLEAN DEFAULT 1"))
                    conn.commit()
                    print("[OK] Spalte 'is_active' hinzugefuegt")
                else:
                    print("[OK] Spalte 'is_active' existiert bereits")

                if 'geloescht_am' not in columns:
                    conn.execute(db.text("ALTER TABLE buchung ADD COLUMN geloescht_am DATETIME"))
                    conn.commit()
                    print("[OK] Spalte 'geloescht_am' hinzugefuegt")
                else:
                    print("[OK] Spalte 'geloescht_am' existiert bereits")

            print("\n[OK] Migration erfolgreich abgeschlossen!")
            print("\nDie Anwendung kann nun gestartet werden mit: python app.py")

        except Exception as e:
            print(f"\n[FEHLER] Fehler bei der Migration: {str(e)}")
            print("\nFalls die Migration fehlschlaegt, koennen Sie die alte Datenbank")
            print("wiederherstellen aus: instance/buchungen_backup.db")
            sys.exit(1)

def reset_database():
    """Loescht die Datenbank und erstellt sie neu (ACHTUNG: Alle Daten gehen verloren!)"""
    with app.app_context():
        print("WARNUNG: Dies loescht ALLE Daten in der Datenbank!")
        confirm = input("Sind Sie sicher? Geben Sie 'JA' ein zum Fortfahren: ")

        if confirm != 'JA':
            print("Abgebrochen.")
            return

        # Loesche alle Tabellen
        db.drop_all()
        print("[OK] Alte Tabellen geloescht")

        # Erstelle neue Tabellen
        db.create_all()
        print("[OK] Neue Tabellen erstellt")

        # Erstelle Standard-Raum
        from app import Raum
        if Raum.query.count() == 0:
            raum = Raum(name='Saal Raifeinstrasse', beschreibung='')
            db.session.add(raum)
            db.session.commit()
            print("[OK] Standard-Raum erstellt")

        print("\n[OK] Datenbank wurde erfolgreich zurueckgesetzt!")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        reset_database()
    else:
        migrate_database()
