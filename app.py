import os
from flask import Flask, redirect, render_template, request, jsonify, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from werkzeug.utils import secure_filename
import logging
import bcrypt
from sqlalchemy import func  # Для нечутливого до регістру пошуку

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Створюємо новий додаток Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'секретный_ключ'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newflask.db'
app.config['UPLOAD_FOLDER'] = 'upload'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#app.secret_key = 'your-secret-key'
db = SQLAlchemy(app)
login_manager = LoginManager(app)                                   # Ініціалізується менеджер авторизації Flask-Login, підключений до цього Flask-додатку.
login_manager.login_view = 'login'                                  # Вказується ім'я маршруту ('login'), куди Flask-Login перенаправлятиметься неавторизованим користувачам

#Цей блок коду — модель користувача, яка описує, як виглядає таблиця User у базі даних.
# Модель користувача
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login =  db.Column(db.String(150), unique=True)
    name = db.Column(db.String(150))
    surname = db.Column(db.String(150))
    tel = db.Column(db.String(150))
    clas = db.Column(db.Integer)
    password = db.Column(db.String(150))
    role = db.Column(db.String(50))  # 'teacher', 'student', 'parent'

# Моделі
#class Post(db.Model):
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

# Регистрація
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login = request.form['login']
        name = request.form['name']
        surname = request.form['surname']
        tel = request.form['tel']
        clas = int(request.form['clas'])  # Преобразуем строку в целое число
        password = request.form['password']
        role = request.form['role']

        # Перевірка, чи існує
        if User.query.filter_by(login=login).first():
            flash('Такий користувач вже існує')
            return redirect(url_for('register'))

        # Створення нового користувача
        new_user = User(login=login, name=name, surname=surname, tel=tel, clas=clas, password=password, role=role)
        
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

# Авторизація
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

# Вихід
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), nullable=False, unique=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), nullable=False, unique=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)

# Декоратор головної сторінки
@app.route("/index")
def index():
    return render_template('Index.html')

@app.route("/teacher")
def teacher():
    return render_template('teacher.html')

@app.route("/parents")
def parent():
    return render_template('parents.html')

@app.route("/student")
def student():
    return render_template('student.html')

@app.route("/calendar")
def calendar():
    return render_template('calendar.html')

@app.route("/admin")
def admin():
    return render_template('admin.html')

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
    if not data or 'title' not in data or 'date' not in data:
        return jsonify({'error': 'Некоректні дані'}), 400
    try:
        event = Event(
            title=data['title'],
            date=datetime.strptime(data['date'], '%Y-%m-%d %H:%M:%S')
        )
        db.session.add(event)
        db.session.commit()
        logger.info(f"Створено подію: ID={event.id}, Назва={event.title}, Дата={event.date}")
        return jsonify({
            'id': event.id,
            'title': event.title,
            'date': event.date.strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Помилка при створенні події: {str(e)}")
        return jsonify({'error': 'Помилка при створенні події'}), 500

@app.route("/api/events/<int:id>", methods=['PUT'])
def update_event(id):
    event = Event.query.get_or_404(id)
    data = request.json
    if not data or 'title' not in data or 'date' not in data:
        return jsonify({'error': 'Некоректні дані'}), 400
    try:
        event.title = data['title']
        event.date = datetime.strptime(data['date'], '%Y-%m-%d %H:%M:%S')
        db.session.commit()
        logger.info(f"Оновлено подію: ID={event.id}, Назва={event.title}, Дата={event.date}")
        return jsonify({
            'id': event.id,
            'title': event.title,
            'date': event.date.strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Помилка при оновленні події ID={id}: {str(e)}")
        return jsonify({'error': 'Помилка при оновленні події'}), 500

@app.route("/api/events/<int:event_id>", methods=['DELETE'])
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    try:
        logger.info(f"Видаляємо подію: ID={event.id}, Назва={event.title}, Дата={event.date}")
        db.session.delete(event)
        db.session.commit()
        logger.info(f"Подію успішно видалено: ID={event_id}")
        return '', 204
    except Exception as e:
        db.session.rollback()
        logger.error(f"Помилка при видаленні події ID={event_id}: {str(e)}")
        return jsonify({'error': 'Помилка при видаленні події'}), 500

# Маршрути для вчителів
@app.route('/api/teachers', methods=['GET'])
def get_teachers():
    logger.info("Отримано запит на отримання списку вчителів")
    try:
        teachers = Teacher.query.all()
        teachers_list = [{
            'id': teacher.id,
            'firstName': teacher.first_name,
            'lastName': teacher.last_name,
            'role': 'Вчитель'
        } for teacher in teachers]
        logger.info(f"Знайдено вчителів: {len(teachers_list)}")
        return jsonify(teachers_list), 200
    except Exception as e:
        logger.error(f"Помилка при отриманні списку вчителів: {str(e)}")
        return jsonify({'error': 'Помилка при отриманні списку вчителів'}), 500

@app.route('/api/teachers', methods=['POST'])
def add_teacher():
    logger.info(f"Отримано запит: headers={request.headers}")
    logger.info(f"Тіло запиту: {request.get_data(as_text=True)}")
    
    try:
        data = request.json
    except Exception as e:
        logger.error(f"Помилка при розпарсюванні JSON: {str(e)}")
        return jsonify({'error': 'Невалідний JSON у запиті'}), 400
    
    logger.info(f"Розпарсені JSON-дані: {data}")
    
    if not data:
        logger.error("Дані відсутні (data is None)")
        return jsonify({'error': 'Некоректні дані: дані відсутні'}), 400
    
    required_fields = ['login', 'firstName', 'lastName', 'class', 'password']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        logger.error(f"Відсутні обов’язкові поля: {missing_fields}")
        return jsonify({'error': f'Некоректні дані: відсутні поля {missing_fields}'}), 400

    login = data['login'].strip()
    first_name = data['firstName'].strip()
    last_name = data['lastName'].strip()
    class_name = data['class'].strip()
    password = data['password'].strip()

    allowed_classes = ["Комп'ютерний клас", "Танцювальний клас", "Кулінарія", "Англійська мова"]
    if class_name not in allowed_classes:
        logger.error(f"Невірний клас: {class_name}")
        return jsonify({'error': f'Невірний клас: {class_name}. Допустимі значення: {allowed_classes}'}), 400

    try:
        # Перевіряємо, чи логін уже зайнятий у таблиці вчителів або адміністраторів
        if Teacher.query.filter_by(login=login).first() or Admin.query.filter_by(login=login).first():
            logger.warning(f"Логін уже зайнятий: {login}")
            return jsonify({'error': 'Логін уже зайнятий'}), 400

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        teacher = Teacher(
            login=login,
            first_name=first_name,
            last_name=last_name,
            class_name=class_name,
            password=hashed_password
        )
        db.session.add(teacher)
        db.session.commit()
        logger.info(f"Створено вчителя: ID={teacher.id}, Логін={teacher.login}, Ім'я={teacher.first_name}, Прізвище={teacher.last_name}, Клас={teacher.class_name}")
        return jsonify({
            'id': teacher.id,
            'login': teacher.login,
            'firstName': teacher.first_name,
            'lastName': teacher.last_name,
            'class': teacher.class_name
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Помилка при створенні вчителя: {str(e)}")
        return jsonify({'error': 'Помилка при створенні вчителя'}), 500

@app.route('/api/teachers/search', methods=['POST'])
def search_teacher():
    logger.info(f"Отримано запит на пошук вчителя: headers={request.headers}")
    logger.info(f"Тіло запиту: {request.get_data(as_text=True)}")

    try:
        data = request.json
    except Exception as e:
        logger.error(f"Помилка при розпарсюванні JSON: {str(e)}")
        return jsonify({'error': 'Невалідний JSON у запиті'}), 400

    logger.info(f"Розпарсені JSON-дані: {data}")

    if not data or 'firstName' not in data or 'lastName' not in data:
        logger.error(f"Некоректні дані для пошуку вчителя: {data}")
        return jsonify({'error': 'Некоректні дані: відсутні поля firstName або lastName'}), 400

    first_name = data['firstName'].strip()
    last_name = data['lastName'].strip()

    try:
        # Точний збіг (нечутливий до регістру)
        teacher = Teacher.query.filter(
            func.lower(Teacher.first_name) == func.lower(first_name),
            func.lower(Teacher.last_name) == func.lower(last_name)
        ).first()
        
        if teacher:
            logger.info(f"Вчитель знайдений: Ім'я={teacher.first_name}, Прізвище={teacher.last_name}")
            return jsonify({
                'found': True,
                'id': teacher.id,
                'suggestions': []
            }), 200
        else:
            logger.info(f"Вчитель не знайдений: Ім'я={first_name}, Прізвище={last_name}")
            # Шукаємо схожих вчителів
            suggestions = Teacher.query.filter(
                (func.lower(Teacher.first_name).like(f'%{first_name.lower()}%')) |
                (func.lower(Teacher.last_name).like(f'%{last_name.lower()}%'))
            ).all()
            
            suggestions_list = [
                {'firstName': t.first_name, 'lastName': t.last_name}
                for t in suggestions
            ]
            logger.info(f"Знайдено схожих вчителів: {suggestions_list}")
            
            return jsonify({
                'found': False,
                'suggestions': suggestions_list
            }), 404
    except Exception as e:
        logger.error(f"Помилка при пошуку вчителя: {str(e)}")
        return jsonify({'error': 'Помилка при пошуку вчителя'}), 500

@app.route('/api/teachers/delete', methods=['DELETE'])
def delete_teacher():
    logger.info(f"Отримано запит на видалення вчителя: headers={request.headers}")
    logger.info(f"Тіло запиту: {request.get_data(as_text=True)}")

    try:
        data = request.json
    except Exception as e:
        logger.error(f"Помилка при розпарсюванні JSON: {str(e)}")
        return jsonify({'error': 'Невалідний JSON у запиті'}), 400

    logger.info(f"Розпарсені JSON-дані: {data}")

    if not data or 'firstName' not in data or 'lastName' not in data:
        logger.error(f"Некоректні дані для видалення вчителя: {data}")
        return jsonify({'error': 'Некоректні дані: відсутні поля firstName або lastName'}), 400

    first_name = data['firstName'].strip()
    last_name = data['lastName'].strip()

    try:
        teacher = Teacher.query.filter(
            func.lower(Teacher.first_name) == func.lower(first_name),
            func.lower(Teacher.last_name) == func.lower(last_name)
        ).first()
        if not teacher:
            logger.warning(f"Вчитель не знайдений для видалення: Ім'я={first_name}, Прізвище={last_name}")
            return jsonify({'error': 'Вчитель не знайдений'}), 404

        logger.info(f"Видаляємо вчителя: ID={teacher.id}, Ім'я={teacher.first_name}, Прізвище={teacher.last_name}")
        db.session.delete(teacher)
        db.session.commit()
        logger.info(f"Вчитель успішно видалений: Ім'я={first_name}, Прізвище={last_name}")
        return '', 204
    except Exception as e:
        db.session.rollback()
        logger.error(f"Помилка при видаленні вчителя: {str(e)}")
        return jsonify({'error': 'Помилка при видаленні вчителя'}), 500

# Маршрути для адміністраторів
@app.route('/api/admins', methods=['GET'])
def get_admins():
    logger.info("Отримано запит на отримання списку адміністраторів")
    try:
        admins = Admin.query.all()
        admins_list = [{
            'id': admin.id,
            'firstName': admin.first_name,
            'lastName': admin.last_name,
            'role': 'Адміністратор'
        } for admin in admins]
        logger.info(f"Знайдено адміністраторів: {len(admins_list)}")
        return jsonify(admins_list), 200
    except Exception as e:
        logger.error(f"Помилка при отриманні списку адміністраторів: {str(e)}")
        return jsonify({'error': 'Помилка при отриманні списку адміністраторів'}), 500

@app.route('/api/admins', methods=['POST'])
def add_admin():
    logger.info(f"Отримано запит на додавання адміністратора: headers={request.headers}")
    logger.info(f"Тіло запиту: {request.get_data(as_text=True)}")
    
    try:
        data = request.json
    except Exception as e:
        logger.error(f"Помилка при розпарсюванні JSON: {str(e)}")
        return jsonify({'error': 'Невалідний JSON у запиті'}), 400
    
    logger.info(f"Розпарсені JSON-дані: {data}")
    
    if not data:
        logger.error("Дані відсутні (data is None)")
        return jsonify({'error': 'Некоректні дані: дані відсутні'}), 400
    
    required_fields = ['login', 'firstName', 'lastName', 'password']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        logger.error(f"Відсутні обов’язкові поля: {missing_fields}")
        return jsonify({'error': f'Некоректні дані: відсутні поля {missing_fields}'}), 400

    login = data['login'].strip()
    first_name = data['firstName'].strip()
    last_name = data['lastName'].strip()
    password = data['password'].strip()

    try:
        # Перевіряємо, чи логін уже зайнятий у таблиці вчителів або адміністраторів
        if Teacher.query.filter_by(login=login).first() or Admin.query.filter_by(login=login).first():
            logger.warning(f"Логін уже зайнятий: {login}")
            return jsonify({'error': 'Логін уже зайнятий'}), 400

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        admin = Admin(
            login=login,
            first_name=first_name,
            last_name=last_name,
            password=hashed_password
        )
        db.session.add(admin)
        db.session.commit()
        logger.info(f"Створено адміністратора: ID={admin.id}, Логін={admin.login}, Ім'я={admin.first_name}, Прізвище={admin.last_name}")
        return jsonify({
            'id': admin.id,
            'login': admin.login,
            'firstName': admin.first_name,
            'lastName': admin.last_name
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Помилка при створенні адміністратора: {str(e)}")
        return jsonify({'error': 'Помилка при створенні адміністратора'}), 500

@app.route('/api/admins/search', methods=['POST'])
def search_admin():
    logger.info(f"Отримано запит на пошук адміністратора: headers={request.headers}")
    logger.info(f"Тіло запиту: {request.get_data(as_text=True)}")

    try:
        data = request.json
    except Exception as e:
        logger.error(f"Помилка при розпарсюванні JSON: {str(e)}")
        return jsonify({'error': 'Невалідний JSON у запиті'}), 400

    logger.info(f"Розпарсені JSON-дані: {data}")

    if not data or 'firstName' not in data or 'lastName' not in data:
        logger.error(f"Некоректні дані для пошуку адміністратора: {data}")
        return jsonify({'error': 'Некоректні дані: відсутні поля firstName або lastName'}), 400

    first_name = data['firstName'].strip()
    last_name = data['lastName'].strip()

    try:
        # Точний збіг (нечутливий до регістру)
        admin = Admin.query.filter(
            func.lower(Admin.first_name) == func.lower(first_name),
            func.lower(Admin.last_name) == func.lower(last_name)
        ).first()
        
        if admin:
            logger.info(f"Адміністратор знайдений: Ім'я={admin.first_name}, Прізвище={admin.last_name}")
            return jsonify({
                'found': True,
                'id': admin.id,
                'suggestions': []
            }), 200
        else:
            logger.info(f"Адміністратор не знайдений: Ім'я={first_name}, Прізвище={last_name}")
            # Шукаємо схожих адміністраторів
            suggestions = Admin.query.filter(
                (func.lower(Admin.first_name).like(f'%{first_name.lower()}%')) |
                (func.lower(Admin.last_name).like(f'%{last_name.lower()}%'))
            ).all()
            
            suggestions_list = [
                {'firstName': a.first_name, 'lastName': a.last_name}
                for a in suggestions
            ]
            logger.info(f"Знайдено схожих адміністраторів: {suggestions_list}")
            
            return jsonify({
                'found': False,
                'suggestions': suggestions_list
            }), 404
    except Exception as e:
        logger.error(f"Помилка при пошуку адміністратора: {str(e)}")
        return jsonify({'error': 'Помилка при пошуку адміністратора'}), 500

@app.route('/api/admins/delete', methods=['DELETE'])
def delete_admin():
    logger.info(f"Отримано запит на видалення адміністратора: headers={request.headers}")
    logger.info(f"Тіло запиту: {request.get_data(as_text=True)}")

    try:
        data = request.json
    except Exception as e:
        logger.error(f"Помилка при розпарсюванні JSON: {str(e)}")
        return jsonify({'error': 'Невалідний JSON у запиті'}), 400

    logger.info(f"Розпарсені JSON-дані: {data}")

    if not data or 'firstName' not in data or 'lastName' not in data:
        logger.error(f"Некоректні дані для видалення адміністратора: {data}")
        return jsonify({'error': 'Некоректні дані: відсутні поля firstName або lastName'}), 400

    first_name = data['firstName'].strip()
    last_name = data['lastName'].strip()

    try:
        admin = Admin.query.filter(
            func.lower(Admin.first_name) == func.lower(first_name),
            func.lower(Admin.last_name) == func.lower(last_name)
        ).first()
        if not admin:
            logger.warning(f"Адміністратор не знайдений для видалення: Ім'я={first_name}, Прізвище={last_name}")
            return jsonify({'error': 'Адміністратор не знайдений'}), 404

        logger.info(f"Видаляємо адміністратора: ID={admin.id}, Ім'я={admin.first_name}, Прізвище={admin.last_name}")
        db.session.delete(admin)
        db.session.commit()
        logger.info(f"Адміністратор успішно видалений: Ім'я={first_name}, Прізвище={last_name}")
        return '', 204
    except Exception as e:
        db.session.rollback()
        logger.error(f"Помилка при видаленні адміністратора: {str(e)}")
        return jsonify({'error': 'Помилка при видаленні адміністратора'}), 500

#@app.route('/register', methods=['POST'])
#def register():
#    return "Registered successfully"

#@app.route('/login', methods=['POST', 'GET'])
#def login():
#    if request.method == 'POST':
#        name = request.form['name']
#        password = request.form['password']
#        print(f"Login attempt: {name}")
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
        logger.info("База даних ініціалізована")
    app.run(host="0.0.0.0", port=5000, debug=True)
