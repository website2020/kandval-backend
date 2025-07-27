import os
import smtplib
from email.message import EmailMessage
from flask import Flask, render_template, request
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные из .env

print("SMTP_USER =", os.getenv('SMTP_USER'))
print("SMTP_PASSWORD =", os.getenv('SMTP_PASSWORD'))


app = Flask(__name__)

SMTP_SERVER = 'smtp.zoho.eu'
SMTP_PORT = 465
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')  # Секрет из .env
EMAIL_TO = 'info@kandval.com'


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        message = request.form.get('message', '')
        file = request.files.get('file')  # 👈 получаем файл

        msg = EmailMessage()
        msg['Subject'] = 'Новая заявка с формы'
        msg['From'] = SMTP_USER
        msg['To'] = EMAIL_TO
        msg.set_content(f"Имя: {name}\nEmail: {email}\nСообщение: {message}")

        # 📎 прикрепляем файл, если он есть
        if file and file.filename:
            file_data = file.read()
            msg.add_attachment(file_data,
                               maintype='application',
                               subtype='octet-stream',
                               filename=file.filename)

        try:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
            print("✅ Email успешно отправлен!")
            return "Форма успешно отправлена!"
        except Exception as e:
            print(f"❌ Ошибка отправки email: {e}")
            return "Ошибка отправки формы"

    return render_template('form.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

