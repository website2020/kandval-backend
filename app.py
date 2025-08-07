import os
import smtplib
from email.message import EmailMessage
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные из .env

print("SMTP_USER =", os.getenv('SMTP_USER'))
print("SMTP_PASSWORD =", os.getenv('SMTP_PASSWORD'))

app = Flask(__name__)

SMTP_SERVER = 'smtp.zoho.eu'
SMTP_PORT = 465
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
EMAIL_TO = 'info@kandval.com'

ERROR_MSG = {
    "status": "error",
    "message": "Use the door, not the window.",
    "recommendation": ""
}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        message = request.form.get('message', '')
        file = request.files.get('file')

        # Проверка, что есть файл и имя файла id.txt
        if not file or file.filename != 'id.txt':
            return jsonify(ERROR_MSG)

        content = file.read().decode(errors='ignore').replace('\r', '')
        lines = content.split('\n')

        required_lines = [
            ("UserName=", 9),
            ("ComputerName=", 13),
            ("Domain=", 7),
            ("DiskSerial=", 11)
        ]

        # Проверка структуры файла
        for i, (prefix, length) in enumerate(required_lines):
            if i >= len(lines) or not lines[i].startswith(prefix):
                return jsonify(ERROR_MSG)

        computer_name = lines[1][13:].strip()
        disk_serial = lines[3][11:].strip()

        # Проверяем, что computer_name и disk_serial не пустые и не содержат пробелов
        if not computer_name or ' ' in computer_name:
            return jsonify(ERROR_MSG)

        if not disk_serial or ' ' in disk_serial:
            return jsonify(ERROR_MSG)

        # Если все проверки пройдены — формируем письмо и отправляем
        msg = EmailMessage()
        msg['Subject'] = 'Новая заявка с формы'
        msg['From'] = SMTP_USER
        msg['To'] = EMAIL_TO
        msg.set_content(f"Имя: {name}\nEmail: {email}\nСообщение: {message}")
        msg.add_attachment(content.encode(),
                           maintype='application',
                           subtype='octet-stream',
                           filename=file.filename)

        try:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)

            return jsonify(
                status="success",
                message="Заявка успешно отправлена!",
                recommendation="Скоро вы получите письмо с инструкциями."
            )

        except Exception:
            return jsonify(
                status="error",
                message="Ошибка отправки заявки",
                recommendation="Проверьте подключение к интернету или попробуйте позже."
            )

    # При GET запросе — просто вернуть форму
    return render_template("form.html")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

