from flask import Flask, render_template, request, jsonify, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta
from dotenv import load_dotenv
from functools import wraps
import os

# Lade Umgebungsvariablen aus .env Datei
load_dotenv()

app = Flask(__name__)

# Flask Konfiguration aus Umgebungsvariablen
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///buchungen.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

if not app.config['SECRET_KEY']:
    raise ValueError("SECRET_KEY muss in der .env Datei gesetzt sein!")

# E-Mail-Konfiguration aus Umgebungsvariablen
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 25))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'False').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = (
    os.getenv('MAIL_DEFAULT_SENDER_NAME'),
    os.getenv('MAIL_DEFAULT_SENDER_EMAIL')
)

# Session-Konfiguration für Admin-Authentifizierung
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # Session läuft nach 2h ab

db = SQLAlchemy(app)
mail = Mail(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Rate Limiting Konfiguration
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Hilfsfunktion zum Generieren von Tokens
def generate_token(buchung_id):
    return serializer.dumps(buchung_id, salt='buchung-confirm')

def verify_token(token, expiration=86400):  # 24 Stunden gültig
    try:
        buchung_id = serializer.loads(token, salt='buchung-confirm', max_age=expiration)
        return buchung_id
    except:
        return None

# Admin-Authentifizierung Decorator
def admin_required(f):
    """
    Decorator zum Schutz von Admin-Routen.
    Prüft, ob eine gültige Admin-Session existiert.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Prüfe ob Admin-Session existiert und gültig ist
        if not session.get('is_admin'):
            return jsonify({
                'error': 'Nicht autorisiert',
                'message': 'Admin-Authentifizierung erforderlich'
            }), 401

        # Prüfe Session-Ablaufzeit (zusätzliche Sicherheit)
        session_time = session.get('admin_login_time')
        if session_time:
            # Konvertiere zu datetime wenn als String gespeichert
            if isinstance(session_time, str):
                session_time = datetime.fromisoformat(session_time)

            # Prüfe ob Session abgelaufen ist (2 Stunden)
            if datetime.utcnow() - session_time > timedelta(hours=2):
                session.clear()
                return jsonify({
                    'error': 'Session abgelaufen',
                    'message': 'Bitte erneut anmelden'
                }), 401

        return f(*args, **kwargs)
    return decorated_function

# E-Mail-Versand-Funktion
def send_booking_request_email(buchung):
    try:
        token = generate_token(buchung.id)

        # Generiere Links mit absolutem URL
        confirm_url = url_for('confirm_buchung_email', token=token, _external=True)
        reject_url = url_for('reject_buchung_email', token=token, _external=True)

        start_datum = buchung.start_datum.strftime('%d.%m.%Y um %H:%M')
        end_datum = buchung.end_datum.strftime('%H:%M')

        html_body = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 0;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 30px;
                    border: 1px solid #ddd;
                }}
                .info-box {{
                    background: white;
                    padding: 20px;
                    margin: 20px 0;
                    border-left: 4px solid #667eea;
                    border-radius: 5px;
                }}
                .info-box p {{
                    margin: 10px 0;
                }}
                .button-container {{
                    text-align: center;
                    margin: 30px 0;
                }}
                .button {{
                    display: inline-block;
                    padding: 15px 30px;
                    margin: 10px;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 16px;
                }}
                .button-accept {{
                    background-color: #66bb6a;
                    color: white;
                }}
                .button-reject {{
                    background-color: #ef5350;
                    color: white;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    color: #777;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="content">
                    <p>Guten Tag,</p>
                    <p>Es ist eine neue Buchungsanfrage für den <strong>Saal Raifeinstraße</strong> eingegangen.</p>

                    <div class="info-box">
                        <h3>Buchungsdetails:</h3>
                        <p><strong>Name:</strong> {buchung.benutzer_name}</p>
                        <p><strong>E-Mail:</strong> {buchung.benutzer_email}</p>
                        <p><strong>Datum:</strong> {start_datum} - {end_datum} Uhr</p>
                        {f'<p><strong>Zweck:</strong> {buchung.zweck}</p>' if buchung.zweck else ''}
                    </div>

                    <div class="button-container">
                        <a href="{confirm_url}" class="button button-accept">Buchung Annehmen</a>
                        <a href="{reject_url}" class="button button-reject">Buchung Ablehnen</a>
                    </div>

                    <p style="font-size: 12px; color: #777; margin-top: 30px;">
                        Hinweis: Dieser Link ist 24 Stunden gültig.
                    </p>
                </div>
                <div class="footer">
                    <p>Raumbuchungssystem - Saal Raifeinstraße</p>
                </div>
            </div>
        </body>
        </html>
        '''

        msg = Message(
            subject=f'Neue Buchungsanfrage - {buchung.benutzer_name}',
            recipients=get_notification_emails(),
            html=html_body
        )

        mail.send(msg)
        return True
    except Exception as e:
        print(f"Fehler beim E-Mail-Versand: {str(e)}")
        return False

# E-Mail an Benutzer - Buchungsanfrage bestätigen
def send_user_request_confirmation(buchung):
    try:
        start_datum = buchung.start_datum.strftime('%d.%m.%Y um %H:%M')
        end_datum = buchung.end_datum.strftime('%H:%M')

        html_body = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 0;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 30px;
                    border: 1px solid #ddd;
                }}
                .info-box {{
                    background: white;
                    padding: 20px;
                    margin: 20px 0;
                    border-left: 4px solid #ffa726;
                    border-radius: 5px;
                }}
                .info-box p {{
                    margin: 10px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    color: #777;
                    font-size: 12px;
                }}
                .status {{
                    background: #ffa726;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 5px;
                    display: inline-block;
                    margin: 20px 0;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="content">
                    <p>Hallo {buchung.benutzer_name},</p>
                    <p>vielen Dank für Ihre Buchungsanfrage.</p>

                    <div class="status">Status: Ausstehend</div>

                    <div class="info-box">
                        <h3>Ihre Buchungsdetails:</h3>
                        <p><strong>Datum:</strong> {start_datum} - {end_datum} Uhr</p>
                        {f'<p><strong>Zweck:</strong> {buchung.zweck}</p>' if buchung.zweck else ''}
                    </div>

                    <p>Ihre Anfrage wird geprüft und Sie erhalten eine E-Mail, sobald Ihre Buchung bestätigt oder abgelehnt wurde.</p>
                </div>
                <div class="footer">
                    <p>Dies ist eine automatisch generierte E-Mail. Bitte antworten Sie nicht auf diese Nachricht.</p>
                </div>
            </div>
        </body>
        </html>
        '''

        msg = Message(
            subject='Ihre Buchungsanfrage für den Saal Raifeinstraße',
            recipients=[buchung.benutzer_email],
            html=html_body
        )

        mail.send(msg)
        return True
    except Exception as e:
        print(f"Fehler beim E-Mail-Versand an Benutzer: {str(e)}")
        return False

# E-Mail an Benutzer - Buchung bestätigt
def send_user_confirmation(buchung):
    try:
        start_datum = buchung.start_datum.strftime('%d.%m.%Y um %H:%M')
        end_datum = buchung.end_datum.strftime('%H:%M')

        # Generiere Stornierungslink
        token = generate_token(buchung.id)
        cancel_url = url_for('cancel_buchung_user', token=token, _external=True)

        html_body = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 0;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 30px;
                    border: 1px solid #ddd;
                }}
                .info-box {{
                    background: white;
                    padding: 20px;
                    margin: 20px 0;
                    border-left: 4px solid #66bb6a;
                    border-radius: 5px;
                }}
                .info-box p {{
                    margin: 10px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    color: #777;
                    font-size: 12px;
                }}
                .status {{
                    background: #66bb6a;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 5px;
                    display: inline-block;
                    margin: 20px 0;
                    font-weight: bold;
                }}
                .cancel-section {{
                    background: #fff3cd;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 5px;
                    border-left: 4px solid #ffa726;
                }}
                .button-cancel {{
                    display: inline-block;
                    padding: 12px 25px;
                    margin: 10px 0;
                    background-color: #ef5350;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="content">
                    <p>Hallo {buchung.benutzer_name},</p>
                    <p>gute Nachricht! Ihre Buchung wurde bestätigt.</p>

                    <div class="status">Status: Bestätigt</div>

                    <div class="info-box">
                        <h3>Ihre Buchungsdetails:</h3>
                        <p><strong>Datum:</strong> {start_datum} - {end_datum} Uhr</p>
                        {f'<p><strong>Zweck:</strong> {buchung.zweck}</p>' if buchung.zweck else ''}
                    </div>

                    <p>Wir freuen uns auf Ihren Besuch!</p>

                    <div class="cancel-section">
                        <h3>Buchung stornieren</h3>
                        <p>Falls Sie die Buchung stornieren möchten, klicken Sie bitte auf den folgenden Link:</p>
                        <a href="{cancel_url}" class="button-cancel">Buchung stornieren</a>
                        <p style="font-size: 12px; color: #777; margin-top: 10px;">
                            Hinweis: Dieser Link ist 24 Stunden gültig.
                        </p>
                    </div>
                </div>
                <div class="footer">
                    <p>Dies ist eine automatisch generierte E-Mail. Bitte antworten Sie nicht auf diese Nachricht.</p>
                </div>
            </div>
        </body>
        </html>
        '''

        msg = Message(
            subject='Buchung bestätigt - Saal Raifeinstraße',
            recipients=[buchung.benutzer_email],
            html=html_body
        )

        mail.send(msg)
        return True
    except Exception as e:
        print(f"Fehler beim E-Mail-Versand an Benutzer: {str(e)}")
        return False

# E-Mail an Benutzer - Buchung abgelehnt
def send_user_rejection(buchung, rejection_message=None):
    try:
        start_datum = buchung.start_datum.strftime('%d.%m.%Y um %H:%M')
        end_datum = buchung.end_datum.strftime('%H:%M')

        # Optionale Ablehnungsnachricht
        rejection_section = ''
        if rejection_message:
            rejection_section = f'''
                <div class="rejection-reason">
                    <h3>Grund der Ablehnung:</h3>
                    <p>{rejection_message}</p>
                </div>
            '''

        html_body = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 0;
                }}
                .header {{
                    background: linear-gradient(135deg, #ef5350 0%, #e53935 100%);
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 30px;
                    border: 1px solid #ddd;
                }}
                .info-box {{
                    background: white;
                    padding: 20px;
                    margin: 20px 0;
                    border-left: 4px solid #ef5350;
                    border-radius: 5px;
                }}
                .info-box p {{
                    margin: 10px 0;
                }}
                .rejection-reason {{
                    background: #fff3cd;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 5px;
                    border-left: 4px solid #ffa726;
                }}
                .rejection-reason h3 {{
                    margin-top: 0;
                    color: #000;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    color: #777;
                    font-size: 12px;
                }}
                .status {{
                    background: #ef5350;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 5px;
                    display: inline-block;
                    margin: 20px 0;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="content">
                    <p>Hallo {buchung.benutzer_name},</p>
                    <p>leider müssen wir Ihnen mitteilen, dass Ihre Buchungsanfrage abgelehnt wurde.</p>

                    <div class="status">Status: Abgelehnt</div>

                    <div class="info-box">
                        <h3>Buchungsdetails:</h3>
                        <p><strong>Datum:</strong> {start_datum} - {end_datum} Uhr</p>
                        {f'<p><strong>Zweck:</strong> {buchung.zweck}</p>' if buchung.zweck else ''}
                    </div>

                    {rejection_section}

                    <p>Falls Sie Fragen haben, können Sie uns gerne kontaktieren.</p>
                </div>
                <div class="footer">
                    <p>Dies ist eine automatisch generierte E-Mail. Bitte antworten Sie nicht auf diese Nachricht.</p>
                </div>
            </div>
        </body>
        </html>
        '''

        msg = Message(
            subject='Buchung abgelehnt - Saal Raifeinstraße',
            recipients=[buchung.benutzer_email],
            html=html_body
        )

        mail.send(msg)
        return True
    except Exception as e:
        print(f"Fehler beim E-Mail-Versand an Benutzer: {str(e)}")
        return False

# E-Mail an Admin - Stornierungsanfrage
def send_cancellation_notification(buchung):
    try:
        start_datum = buchung.start_datum.strftime('%d.%m.%Y um %H:%M')
        end_datum = buchung.end_datum.strftime('%H:%M')

        html_body = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 0;
                }}
                .header {{
                    background: linear-gradient(135deg, #ef5350 0%, #e53935 100%);
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 30px;
                    border: 1px solid #ddd;
                }}
                .info-box {{
                    background: white;
                    padding: 20px;
                    margin: 20px 0;
                    border-left: 4px solid #ef5350;
                    border-radius: 5px;
                }}
                .info-box p {{
                    margin: 10px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    color: #777;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Stornierungsanfrage</h1>
                </div>
                <div class="content">
                    <p>Guten Tag,</p>
                    <p><strong>{buchung.benutzer_name}</strong> hat die folgende Buchung storniert:</p>

                    <div class="info-box">
                        <h3>Buchungsdetails:</h3>
                        <p><strong>Name:</strong> {buchung.benutzer_name}</p>
                        <p><strong>E-Mail:</strong> {buchung.benutzer_email}</p>
                        <p><strong>Datum:</strong> {start_datum} - {end_datum} Uhr</p>
                        {f'<p><strong>Zweck:</strong> {buchung.zweck}</p>' if buchung.zweck else ''}
                    </div>

                    <p><strong>Die Buchung wurde automatisch gelöscht.</strong></p>
                </div>
                <div class="footer">
                    <p>Raumbuchungssystem - Saal Raifeinstraße</p>
                </div>
            </div>
        </body>
        </html>
        '''

        msg = Message(
            subject=f'Stornierung - {buchung.benutzer_name}',
            recipients=get_notification_emails(),
            html=html_body
        )

        mail.send(msg)
        return True
    except Exception as e:
        print(f"Fehler beim E-Mail-Versand: {str(e)}")
        return False

# Datenbank-Modelle
class Raum(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    beschreibung = db.Column(db.String(500))
    buchungen = db.relationship('Buchung', backref='raum', lazy=True)

class Buchung(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    raum_id = db.Column(db.Integer, db.ForeignKey('raum.id'), nullable=False)
    start_datum = db.Column(db.DateTime, nullable=False)
    end_datum = db.Column(db.DateTime, nullable=False)
    benutzer_name = db.Column(db.String(100), nullable=False)
    benutzer_email = db.Column(db.String(120), nullable=False)
    zweck = db.Column(db.String(500))
    status = db.Column(db.String(20), default='ausstehend')  # ausstehend, bestätigt, abgelehnt
    is_active = db.Column(db.Boolean, default=True)  # False = gelöscht/storniert
    geloescht_am = db.Column(db.DateTime)  # Zeitpunkt der Löschung/Stornierung
    erstellt_am = db.Column(db.DateTime, default=datetime.utcnow)

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(500))
    beschreibung = db.Column(db.String(500))

# Hilfsfunktionen für Einstellungen
def get_setting(key, default=None):
    """Holt eine Einstellung aus der Datenbank"""
    setting = Settings.query.filter_by(key=key).first()
    return setting.value if setting else default

def set_setting(key, value, beschreibung=None):
    """Setzt oder aktualisiert eine Einstellung"""
    setting = Settings.query.filter_by(key=key).first()
    if setting:
        setting.value = value
        if beschreibung:
            setting.beschreibung = beschreibung
    else:
        setting = Settings(key=key, value=value, beschreibung=beschreibung)
        db.session.add(setting)
    db.session.commit()

def get_notification_emails():
    """Gibt eine Liste von E-Mail-Adressen zurück, die Benachrichtigungen erhalten sollen"""
    emails = [os.getenv('ADMIN_EMAIL')]

    # Saal-Verantwortlichen E-Mail hinzufügen, falls gesetzt
    saal_email = get_setting('saal_verantwortlicher_email')
    if saal_email and saal_email.strip():
        emails.append(saal_email.strip())

    return emails

# Routen
@app.route('/')
def index():
    raeume = Raum.query.all()
    return render_template('index.html', raeume=raeume)

@app.route('/api/buchungen')
def get_buchungen():
    jahr = request.args.get('jahr', datetime.now().year, type=int)
    monat = request.args.get('monat', datetime.now().month, type=int)
    raum_id = request.args.get('raum_id', type=int)

    query = Buchung.query.filter_by(is_active=True)
    if raum_id:
        query = query.filter_by(raum_id=raum_id)

    buchungen = query.all()

    return jsonify([{
        'id': b.id,
        'raum_id': b.raum_id,
        'raum_name': b.raum.name,
        'start_datum': b.start_datum.isoformat(),
        'end_datum': b.end_datum.isoformat(),
        'benutzer_name': b.benutzer_name,
        'benutzer_email': b.benutzer_email,
        'zweck': b.zweck,
        'status': b.status
    } for b in buchungen])

@app.route('/api/buchung', methods=['POST'])
def create_buchung():
    data = request.json

    try:
        neue_buchung = Buchung(
            raum_id=data['raum_id'],
            start_datum=datetime.fromisoformat(data['start_datum']),
            end_datum=datetime.fromisoformat(data['end_datum']),
            benutzer_name=data['benutzer_name'],
            benutzer_email=data['benutzer_email'],
            zweck=data.get('zweck', ''),
            status='ausstehend'
        )

        # Prüfe auf Überschneidungen (nur aktive Buchungen)
        ueberschneidungen = Buchung.query.filter(
            Buchung.raum_id == neue_buchung.raum_id,
            Buchung.status == 'bestätigt',
            Buchung.is_active == True,
            Buchung.start_datum < neue_buchung.end_datum,
            Buchung.end_datum > neue_buchung.start_datum
        ).first()

        if ueberschneidungen:
            return jsonify({'error': 'Dieser Zeitraum ist bereits gebucht'}), 400

        db.session.add(neue_buchung)
        db.session.commit()

        # Sende Benachrichtigungs-E-Mail an Administrator
        email_sent = send_booking_request_email(neue_buchung)

        # Sende Bestätigungs-E-Mail an Benutzer
        user_email_sent = send_user_request_confirmation(neue_buchung)

        return jsonify({
            'message': 'Buchungsanfrage wurde gesendet' + (' und E-Mail wurde verschickt' if email_sent else ''),
            'buchung_id': neue_buchung.id,
            'status': 'ausstehend',
            'email_sent': email_sent,
            'user_email_sent': user_email_sent
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/buchung/<int:buchung_id>/bestaetigen', methods=['POST'])
@admin_required
def bestaetigen_buchung(buchung_id):
    buchung = Buchung.query.get_or_404(buchung_id)

    # Prüfe erneut auf Überschneidungen (nur aktive Buchungen)
    ueberschneidungen = Buchung.query.filter(
        Buchung.id != buchung_id,
        Buchung.raum_id == buchung.raum_id,
        Buchung.status == 'bestätigt',
        Buchung.is_active == True,
        Buchung.start_datum < buchung.end_datum,
        Buchung.end_datum > buchung.start_datum
    ).first()

    if ueberschneidungen:
        return jsonify({'error': 'Konflikt mit anderer Buchung'}), 400

    buchung.status = 'bestätigt'
    db.session.commit()

    # Sende Bestätigungs-E-Mail an Benutzer
    send_user_confirmation(buchung)

    return jsonify({'message': 'Buchung wurde bestätigt', 'status': 'bestätigt'})

@app.route('/api/buchung/<int:buchung_id>/ablehnen', methods=['POST'])
@admin_required
def ablehnen_buchung(buchung_id):
    buchung = Buchung.query.get_or_404(buchung_id)

    # Hole optionale Ablehnungsnachricht aus Request
    data = request.get_json() if request.is_json else {}
    rejection_message = data.get('message', None)

    buchung.status = 'abgelehnt'
    db.session.commit()

    # Sende Ablehnungs-E-Mail an Benutzer mit optionaler Nachricht
    send_user_rejection(buchung, rejection_message)

    return jsonify({'message': 'Buchung wurde abgelehnt', 'status': 'abgelehnt'})

@app.route('/api/buchung/<int:buchung_id>/loeschen', methods=['DELETE'])
@admin_required
def loeschen_buchung(buchung_id):
    buchung = Buchung.query.get_or_404(buchung_id)
    buchung.is_active = False
    buchung.geloescht_am = datetime.utcnow()
    db.session.commit()

    return jsonify({'message': 'Buchung wurde gelöscht'})

@app.route('/api/raeume')
def get_raeume():
    raeume = Raum.query.all()
    return jsonify([{
        'id': r.id,
        'name': r.name,
        'beschreibung': r.beschreibung
    } for r in raeume])

@app.route('/api/admin/logs')
@admin_required
def get_admin_logs():
    # Hole alle Buchungen sortiert nach Erstellungsdatum (inkl. gelöschte)
    buchungen = Buchung.query.order_by(Buchung.erstellt_am.desc()).limit(50).all()

    logs = []
    for b in buchungen:
        # Bestimme den Status-Text
        if not b.is_active:
            status = 'gelöscht'
            status_text = 'Gelöscht'
            if b.geloescht_am:
                details_suffix = f' (gelöscht am {b.geloescht_am.strftime("%d.%m.%Y %H:%M")})'
            else:
                details_suffix = ' (gelöscht)'
        else:
            status = b.status
            status_text = b.status.capitalize()
            details_suffix = ''

        logs.append({
            'id': b.id,
            'timestamp': b.erstellt_am.isoformat(),
            'type': 'buchung_erstellt',
            'status': status,
            'status_text': status_text,
            'message': f'Buchungsanfrage von {b.benutzer_name}',
            'details': f'{b.start_datum.strftime("%d.%m.%Y %H:%M")} - {b.end_datum.strftime("%H:%M")}{details_suffix}',
            'email': b.benutzer_email,
            'is_active': b.is_active
        })

    return jsonify(logs)

@app.route('/api/admin/stats')
@admin_required
def get_admin_stats():
    total = Buchung.query.count()
    pending = Buchung.query.filter_by(status='ausstehend', is_active=True).count()
    confirmed = Buchung.query.filter_by(status='bestätigt', is_active=True).count()
    rejected = Buchung.query.filter_by(status='abgelehnt', is_active=True).count()
    deleted = Buchung.query.filter_by(is_active=False).count()

    return jsonify({
        'total': total,
        'pending': pending,
        'confirmed': confirmed,
        'rejected': rejected,
        'deleted': deleted
    })

@app.route('/api/admin/verify-pin', methods=['POST'])
@limiter.limit("5 per 15 minutes")  # Max 5 Versuche pro 15 Minuten
def verify_admin_pin():
    """Verifiziere Admin-PIN serverseitig und erstelle Session"""
    data = request.json
    entered_pin = data.get('pin', '')
    correct_pin = os.getenv('ADMIN_PIN')

    if entered_pin == correct_pin:
        # Erstelle Admin-Session
        session.permanent = True
        session['is_admin'] = True
        session['admin_login_time'] = datetime.utcnow().isoformat()

        return jsonify({
            'valid': True,
            'message': 'PIN korrekt',
            'session_created': True
        })
    else:
        # Lösche eventuell vorhandene Session
        session.clear()
        return jsonify({
            'valid': False,
            'message': 'PIN falsch'
        }), 401

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    """Logout aus dem Admin-Modus"""
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Erfolgreich abgemeldet'
    })

@app.route('/api/admin/settings', methods=['GET'])
@admin_required
def get_admin_settings():
    """Holt die Admin-Einstellungen"""
    saal_email = get_setting('saal_verantwortlicher_email', '')
    admin_email = os.getenv('ADMIN_EMAIL', '')

    return jsonify({
        'admin_email': admin_email,
        'saal_verantwortlicher_email': saal_email
    })

@app.route('/api/admin/settings/saal-email', methods=['POST'])
@admin_required
def update_saal_email():
    """Aktualisiert die Saal-Verantwortlichen E-Mail"""
    data = request.json
    email = data.get('email', '').strip()

    # Validiere E-Mail-Format (einfache Validierung)
    if email and '@' not in email:
        return jsonify({'error': 'Ungültige E-Mail-Adresse'}), 400

    set_setting('saal_verantwortlicher_email', email, 'E-Mail-Adresse des Saal-Verantwortlichen')

    return jsonify({
        'success': True,
        'message': 'Saal-Verantwortlichen E-Mail wurde aktualisiert',
        'email': email
    })

# E-Mail-basierte Bestätigung/Ablehnung
@app.route('/buchung/bestaetigen/<token>')
def confirm_buchung_email(token):
    buchung_id = verify_token(token)

    if not buchung_id:
        return render_template('message.html',
                               title='Link abgelaufen',
                               message='Dieser Link ist nicht mehr gültig oder abgelaufen.',
                               typ='error')

    buchung = Buchung.query.get(buchung_id)
    if not buchung:
        return render_template('message.html',
                               title='Buchung nicht gefunden',
                               message='Diese Buchung existiert nicht mehr.',
                               typ='error')

    if buchung.status != 'ausstehend':
        status_text = 'bereits bestätigt' if buchung.status == 'bestätigt' else 'bereits abgelehnt'
        return render_template('message.html',
                               title='Bereits bearbeitet',
                               message=f'Diese Buchung wurde {status_text}.',
                               typ='warning')

    # Prüfe auf Überschneidungen (nur aktive Buchungen)
    ueberschneidungen = Buchung.query.filter(
        Buchung.id != buchung_id,
        Buchung.raum_id == buchung.raum_id,
        Buchung.status == 'bestätigt',
        Buchung.is_active == True,
        Buchung.start_datum < buchung.end_datum,
        Buchung.end_datum > buchung.start_datum
    ).first()

    if ueberschneidungen:
        return render_template('message.html',
                               title='Konflikt',
                               message='Diese Buchung kann nicht bestätigt werden, da es eine Überschneidung mit einer anderen Buchung gibt.',
                               typ='error')

    buchung.status = 'bestätigt'
    db.session.commit()

    # Sende Bestätigungs-E-Mail an Benutzer
    send_user_confirmation(buchung)

    return render_template('message.html',
                           title='Buchung bestätigt',
                           message=f'Die Buchung von {buchung.benutzer_name} wurde erfolgreich bestätigt.',
                           typ='success')

@app.route('/buchung/ablehnen/<token>')
def reject_buchung_email(token):
    buchung_id = verify_token(token)

    if not buchung_id:
        return render_template('message.html',
                               title='Link abgelaufen',
                               message='Dieser Link ist nicht mehr gültig oder abgelaufen.',
                               typ='error')

    buchung = Buchung.query.get(buchung_id)
    if not buchung:
        return render_template('message.html',
                               title='Buchung nicht gefunden',
                               message='Diese Buchung existiert nicht mehr.',
                               typ='error')

    if buchung.status != 'ausstehend':
        status_text = 'bereits bestätigt' if buchung.status == 'bestätigt' else 'bereits abgelehnt'
        return render_template('message.html',
                               title='Bereits bearbeitet',
                               message=f'Diese Buchung wurde {status_text}.',
                               typ='warning')

    buchung.status = 'abgelehnt'
    db.session.commit()

    return render_template('message.html',
                           title='Buchung abgelehnt',
                           message=f'Die Buchung von {buchung.benutzer_name} wurde abgelehnt.',
                           typ='success')

@app.route('/buchung/stornieren/<token>')
def cancel_buchung_user(token):
    buchung_id = verify_token(token)

    if not buchung_id:
        return render_template('message.html',
                               title='Link abgelaufen',
                               message='Dieser Link ist nicht mehr gültig oder abgelaufen.',
                               typ='error')

    buchung = Buchung.query.get(buchung_id)
    if not buchung:
        return render_template('message.html',
                               title='Buchung nicht gefunden',
                               message='Diese Buchung existiert nicht mehr.',
                               typ='error')

    if buchung.status != 'bestätigt':
        return render_template('message.html',
                               title='Stornierung nicht möglich',
                               message='Nur bestätigte Buchungen können storniert werden.',
                               typ='warning')

    # Sende Benachrichtigung an Admin
    send_cancellation_notification(buchung)

    # Markiere Buchung als gelöscht (statt sie zu löschen)
    buchung.is_active = False
    buchung.geloescht_am = datetime.utcnow()
    db.session.commit()

    return render_template('message.html',
                           title='Buchung storniert',
                           message=f'Ihre Buchung wurde erfolgreich storniert. Der Administrator wurde informiert.',
                           typ='success')

# Initialisierung
def init_db():
    with app.app_context():
        db.create_all()

        # Erstelle Raum, wenn noch keiner vorhanden ist
        if Raum.query.count() == 0:
            raum = Raum(name='Saal Raifeinstraße', beschreibung='')
            db.session.add(raum)
            db.session.commit()
            print("Raum 'Saal Raifeinstraße' wurde erstellt")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
