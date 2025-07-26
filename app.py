from flask import Flask, request, redirect, render_template_string
from werkzeug.utils import secure_filename
import os
import smtplib
from email.message import EmailMessage

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
EMAIL_TO = 'info@kandval.com'  # Получатель писем (можно оставить себя же)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Убедись, что папка для загрузок существует
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 🔐 Твои SMTP-данные Zoho
SMTP_SERVER = 'smtp.zoho.eu'
SMTP_PORT = 465
SMTP_USER = 'admin@kandval.com'
SMTP_PASSWORD = 'PJp9QwFu3X6Z'  # заменишь позже 

# HTML форма
HTML_FORM = '''
<!DOCTYPE html>
<html>
<head>
    <title>Форма заказа</title>
</head>
<body>
    <h2>Заказать рабочую версию</h2>
    <form action="/" method="POST" enctype="multipart/form-data">
        <label>Имя Фамилия: <input type="text" name="name" required></label><br><br>
        <label>Email: <input type="email" name="email" required></label><br><br>
        <label>Прикрепить файл: <input type="file" name="file" required></label><br><br>
        <button type="submit">Отправить</button>
    </form>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        file = request.files['file']

        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            success = send_email(name, email, filepath)
            return 'Форма успешно отправлена!' if success else 'Ошибка отправки письма.'
        else:
            return 'Файл не был прикреплён.'
    return render_template_string(HTML_FORM)

def send_email(name, email, filepath):
    msg = EmailMessage()
    msg['Subject'] = f'Новая заявка от {name}'
    msg['From'] = SMTP_USER
    msg['To'] = EMAIL_TO
    msg.set_content(f'Имя: {name}\nEmail: {email}')

    with open(filepath, 'rb') as f:
        file_data = f.read()
        file_name = os.path.basename(filepath)
        msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)

try:
    print(f"📡 Подключение к SMTP: {SMTP_SERVER}:{SMTP_PORT}")
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        print("🔐 Авторизация...")
        server.login(SMTP_USER, SMTP_PASSWORD)
        print("✉️ Отправка письма...")
        server.send_message(msg)
    print("✅ Email успешно отправлен!")
    return True
except Exception as e:
    print(f"❌ Ошибка при подключении или отправке SMTP: {e}")
    return False

if __name__ == '__main__':
    app.run(debug=True)