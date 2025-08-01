import os
import smtplib
from email.message import EmailMessage
from flask import Flask, render_template, request
from dotenv import load_dotenv

load_dotenv()  #________________ Загружаем переменные из .env

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
        file = request.files.get('file')

        # Проверка файла id.txt
        if not file or file.filename != 'id.txt':
            return render_template("form.html",
                                   status="error",
                                   message="Неверное имя файла. Ожидается id.txt.",
                                   recommendation="Проверьте, что вы выбрали файл <code>id.txt</code> и попробуйте снова.")

        content = file.read().decode(errors='ignore').replace('\r', '')
        lines = content.split('\n')

        required_lines = [
            ("UserName=", 9),
            ("ComputerName=", 13),
            ("Domain=", 7),
            ("DiskSerial=", 11)
        ]

        for i, (prefix, length) in enumerate(required_lines):
            if i >= len(lines) or not lines[i].startswith(prefix):
                return render_template("form.html",
                                       status="error",
                                       message="Ошибка в id.txt: нарушена структура файла.",
                                       recommendation='''Рекомендация:<br>
Удалить файл <code>id.txt</code>.<br>
Запустить <code>test.vbe</code>.<br>
Дождаться завершения работы.<br>
Повторить заказ с новым <code>id.txt</code>.''')

        computer_name = lines[1][13:].strip()
        disk_serial = lines[3][11:].strip()

        if not computer_name or ' ' in computer_name:
            return render_template("form.html",
                                   status="error",
                                   message="Ошибка в id.txt: не определено имя компьютера.",
                                   recommendation="Проверьте, чтобы строка <code>ComputerName=</code> не была пустой и не содержала пробелов.")

        if not disk_serial or ' ' in disk_serial:
            return render_template("form.html",
                                   status="error",
                                   message="Ошибка в id.txt: не определён серийный номер диска.",
                                   recommendation="Убедитесь, что строка <code>DiskSerial=</code> корректна и не содержит пробелов.")

        # После всех проверок — шлём письмо
        msg = EmailMessage()
        msg['Subject'] = 'Новая заявка с формы'
        msg['From'] = SMTP_USER
        msg['To'] = EMAIL_TO
        msg.set_content(f"Имя: {name}\nEmail: {email}\nСообщение: {message}")

        # ПРИМЕЧАНИЕ: файл уже прочитан, надо отправить то же содержимое
        msg.add_attachment(content.encode(),
                           maintype='application',
                           subtype='octet-stream',
                           filename=file.filename)

        try:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)

            return render_template("form.html",
                                   status="success",
                                   message="Заявка успешно отправлена!",
                                   recommendation="Скоро вы получите письмо с инструкциями.")

        except Exception as e:
            return render_template("form.html",
                                   status="error",
                                   message="Ошибка отправки заявки",
                                   recommendation="Проверьте подключение к интернету или попробуйте позже.")

    
    # При первом заходе на страницу (GET)
    return render_template("form.html")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

