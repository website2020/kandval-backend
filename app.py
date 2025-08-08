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

# Информируем админа, что переменные загружены (не выводим пароль в явном виде)
logging.info("SMTP_USER = %s", SMTP_USER)
logging.info("SMTP_PASSWORD loaded: %s", bool(SMTP_PASSWORD))

app = Flask(__name__)

# Единый ответ для всех ошибок, связанных с файлом id.txt
ERROR_MSG = {
    "status": "error",
    "message": "Use the door, not the window.",
    "recommendation": ""
}

# Простая проверка формата email на сервере
_email_re = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
def is_valid_email(addr: str) -> bool:
    return bool(addr and _email_re.match(addr))


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        email = (request.form.get('email') or '').strip()
        message_text = (request.form.get('message') or '').strip()
        file = request.files.get('file')

        # Серверная проверка email (вежливое сообщение пользователю)
        if not is_valid_email(email):
            return jsonify({
                "status": "error",
                "message": "Invalid email address.",
                "recommendation": "Please check the email and try again (e.g. name@example.com)."
            })

        # —— Файловая логика: все ошибки в одном ответе (защита от "прямых" запросов)
        if not file or file.filename != 'id.txt':
            return jsonify(ERROR_MSG)

        content = file.read().decode(errors='ignore').replace('\r', '')
        lines = content.split('\n')

        prefixes = ['UserName=', 'ComputerName=', 'Domain=', 'DiskSerial=']

        # Структура файла
        for i, prefix in enumerate(prefixes):
            line = lines[i] if i < len(lines) else ''
            if not line.startswith(prefix):
                return jsonify(ERROR_MSG)

        computer_name = lines[1][len('ComputerName='):].strip()
        disk_serial = lines[3][len('DiskSerial='):].strip()

        # Дополнительные проверки (пустота/пробелы)
        if not computer_name or ' ' in computer_name:
            return jsonify(ERROR_MSG)
        if not disk_serial or ' ' in disk_serial:
            return jsonify(ERROR_MSG)

        # Формируем сообщение (вложение — содержимое ранее прочитанного файла)
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
                "message": "Заявка успешно отправлена!",
                "recommendation": "Скоро вы получите письмо с инструкциями."
            })

        except Exception as exc:
            # логируем полную ошибку, но пользователю отдаем вежливое сообщение
            logging.exception("Ошибка при отправке email: %s", exc)
            return jsonify({
                "status": "error",
                "message": "Ошибка отправки заявки",
                "recommendation": "Проверьте подключение к интернету или попробуйте позже."
            })

    # GET — отдать форму
    return render_template("form.html")


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
