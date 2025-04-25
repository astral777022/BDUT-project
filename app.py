import os                                                           #https://docs.python.org/uk/3.13/library/os.html
from flask import Flask, redirect, render_template, request, url_for, jsonify, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from werkzeug.utils import secure_filename

# Створюємо новий додаток Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'секретный_ключ'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newflask.db'     # Налаштовуємо підключення до БД
app.config['UPLOAD_FOLDER'] = 'upload'                              # Вказується папка (upload), куди зберігатимуться завантажені користувачами файли.
db = SQLAlchemy(app)                                                # Створюємо об'єкт БД SQLAlchemy
login_manager = LoginManager(app)                                   # Ініціалізується менеджер авторизації Flask-Login, підключений до цього Flask-додатку.
login_manager.login_view = 'login'                                  # Вказується ім'я маршруту ('login'), куди Flask-Login перенаправлятиметься неавторизованим користувачам

#Цей блок коду — модель користувача, яка описує, як виглядає таблиця User у базі даних.
# Модель користувача
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    role = db.Column(db.String(50))  # 'teacher', 'student', 'parent'

#class Post(db.Model):                                               # — Це визначення класу Post, який успадковується db.Model. Спадкування db.Modelозначає, що SQLAlchemy буде використовувати цей клас як таблицю в базі даних.
#    id = db.Column(db.Integer, primary_key=True)
#    title = db.Column(db.String(300), nullable=False)
#    text = db.Column(db.Text, nullable=False)

# Завантаження користувача
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))                             # SQLAlchemy метод, який шукає користувача з таким первинним ключем (id).

# Головна сторінка (тільки для авторизованих)
@app.route('/')
@login_required
def home():
    if current_user.role == 'teacher':
        greeting = "Доброго дня, вчитель!"
    elif current_user.role == 'student':
        greeting = "Раді тебе бачити, учень!"
    elif current_user.role == 'parent':
        greeting = "Доброго дня, батьки!"
    else:
        greeting = "WELCOME!"

    return f'{greeting} Ваш логин: {current_user.name}'

#class Register(db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#    login = db.Column(db.String(15), nullable=False)
#    name = db.Column(db.String(300), nullable=False)
#    text = db.Column(db.Text, nullable=False)

# Регистрація
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        role = request.form['role']

        # Перевірка, чи існує
        if User.query.filter_by(name=name).first():
            flash('Такий користувач вже існує')
            return redirect(url_for('register'))

        # Створення нового користувача
        new_user = User(name=name, password=password, role=role)
        
        try:
            db.session.add(new_user)
            db.session.commit()
             # Авторизація нового користувача
            login_user(new_user)
            return redirect(url_for('home'))
        except Exception as e:
            flash(f'Помилка при реєстрації: {str(e)}')
            return redirect(url_for('register'))
        
    # Для Get - запиту відображаємо сторінку реєстрації
    return render_template('student.html')

# Авторизация
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        user = User.query.filter_by(name=name, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('home'))
        flash('Невірні дані')
    return render_template('Index.html')

# Выход
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

class Event(db.Model):                                              # Події
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
                                                      
# Декоратор головної сторінки
@app.route("/index")
def index():
    return render_template('Index.html')

@app.route("/teacher")                                                  # Вчитель
def teacher():
    return render_template('teacher.html')

@app.route("/parents")                                                  # Батьки
def parent():
    return render_template('parents.html')

@app.route("/student")                                                  # Учні
def student():
    return render_template('student.html')

@app.route("/calendar")                                                 # Календар
def calendar():
    return render_template('calendar.html')

@app.route("/api/events", methods=['GET'])
def get_events():
    events = Event.query.all()
    return jsonify([{
        'id': event.id,
        'title': event.title,
        'date': event.date.strftime('%Y-%m-%d %H:%M:%S')
    } for event in events])

@app.route("/api/events", methods=['POST'])
def create_event():
    data = request.json
    event = Event(
        title=data['title'],
        date=datetime.strptime(data['date'], '%Y-%m-%d %H:%M:%S')
    )
    db.session.add(event)
    db.session.commit()
    return jsonify({
        'id': event.id,
        'title': event.title,
        'date': event.date.strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route("/api/events/<int:id>", methods=['PUT'])
def update_event(id):
    event = Event.query.get_or_404(id)
    data = request.json
    event.title = data['title']
    event.date = datetime.strptime(data['date'], '%Y-%m-%d %H:%M:%S')
    db.session.commit()
    return jsonify({
        'id': event.id,
        'title': event.title,
        'date': event.date.strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route("/api/events/<int:event_id>", methods=['DELETE'])
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return '', 204

#@app.route('/register', methods=['POST'])
#def register():
#    # Add your registration logic here
#    return "Registered successfully"

#@app.route('/login', methods=['POST', 'GET'])
#def login():
#    if request.method == 'POST':
#        name = request.form['name']
#        password = request.form['password']
#        # Add proper authentication logic here
#        print(f"Login attempt: {name}")  # For debugging only
#        return redirect('parents')
#    return render_template('login.html')

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/file", methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file')
            return redirect(request.url)
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new_file = File(
                file_name=filename
            )
            db.session.add(new_file)
            db.session.commit()
    return '''
        <!doctype html>
        <title>Upload new File</title>
        <h1>Upload new File</h1>
        <form method=post enctype=multipart/form-data>
          <input type=file name=file>
          <input type=submit value=Upload>
        </form>
    '''

@app.route('/file/download/<int:id>')
def download_file(id):
    file = File.query.get_or_404(id)
    return send_from_directory(app.config['UPLOAD_FOLDER'], file.file_name)

@app.route('/users')
def list_users():
    users = User.query.all()
    return '<br>'.join([f'ID: {user.id}, Name: {user.name}, Role: {user.role}' for user in users])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)