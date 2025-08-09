import os
import logging
import smtplib
from email.message import EmailMessage
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import re

# -------------- Настройка --------------
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

SMTP_SERVER = 'smtp.zoho.eu'
SMTP_PORT = 465
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
EMAIL_TO = 'info@kandval.com'

logging.info("SMTP_USER = %s", SMTP_USER)
logging.info("SMTP_PASSWORD loaded: %s", bool(SMTP_PASSWORD))

app = Flask(__name__)

_email_re = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
def is_valid_email(addr: str) -> bool:
    return bool(addr and _email_re.match(addr))


# Мульти-язычные сообщения
MESSAGES = {
    "ru": {
        "success": {
            "message": "Заявка успешно отправлена!",
            "recommendation": "Скоро вы получите письмо с инструкциями."
        },
        "send_error": {
            "message": "Ошибка отправки заявки",
            "recommendation": "Проверьте подключение к интернету или попробуйте позже."
        },
        "invalid_email": {
            "message": "Некорректный адрес электронной почты.",
            "recommendation": "Пожалуйста, проверьте email и попробуйте снова (например: name@example.com)."
        },
        "file_error": {
            "message": "Используйте дверь, а не окно.",
            "recommendation": ""
        }
    },
    "en": {
        "success": {
            "message": "Request sent successfully!",
            "recommendation": "You will receive an email with instructions shortly."
        },
        "send_error": {
            "message": "Error sending request",
            "recommendation": "Check your internet connection or try again later."
        },
        "invalid_email": {
            "message": "Invalid email address.",
            "recommendation": "Please check the email and try again (e.g., name@example.com)."
        },
        "file_error": {
            "message": "Use the door, not the window.",
            "recommendation": ""
        }
    }
}


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        lang = (request.form.get('lang') or 'en').lower()
        name = (request.form.get('name') or '').strip()
        email = (request.form.get('email') or '').strip()
        message_text = (request.form.get('message') or '').strip()
        file = request.files.get('file')
    else:
        lang = (request.args.get('lang') or 'en').lower()
        # При GET остальные переменные можно не брать или ставить пустыми
        name = email = message_text = ''
        file = None

    if lang not in MESSAGES:
        lang = 'en'
    texts = MESSAGES[lang]

        # Проверка email
        if not is_valid_email(email):
            return jsonify({
                "status": "error",
                **texts["invalid_email"]
            })

        if not file or file.filename != 'id.txt':
            return jsonify({
                "status": "error",
                **texts["file_error"]
            })

        content = file.read().decode(errors='ignore').replace('\r', '')
        lines = content.split('\n')
        prefixes = ['UserName=', 'ComputerName=', 'Domain=', 'DiskSerial=']

        for i, prefix in enumerate(prefixes):
            line = lines[i] if i < len(lines) else ''
            if not line.startswith(prefix):
                return jsonify({
                    "status": "error",
                    **texts["file_error"]
                })

        computer_name = lines[1][len('ComputerName='):].strip()
        disk_serial = lines[3][len('DiskSerial='):].strip()

        if not computer_name or ' ' in computer_name:
            return jsonify({
                "status": "error",
                **texts["file_error"]
            })
        if not disk_serial or ' ' in disk_serial:
            return jsonify({
                "status": "error",
                **texts["file_error"]
            })

        msg = EmailMessage()
        msg['Subject'] = 'Новая заявка с формы'
        msg['From'] = SMTP_USER
        msg['To'] = EMAIL_TO
        msg.set_content(f"Имя: {name}\nEmail: {email}\nСообщение: {message_text}")
        msg.add_attachment(content.encode(),
                           maintype='application',
                           subtype='octet-stream',
                           filename=file.filename)

        try:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)

            return jsonify({
                "status": "success",
                **texts["success"]
            })

        except Exception as exc:
            logging.exception("Ошибка при отправке email: %s", exc)
            return jsonify({
                "status": "error",
                **texts["send_error"]
            })

    else:
        # <<< добавлено для мультиязычности >>>
        lang = request.args.get('lang', 'en').lower()
        if lang not in MESSAGES:
            lang = 'en'
        return render_template("form.html", lang=lang)  # передаём lang в шаблон


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
