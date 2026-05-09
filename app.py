import os
import random
import string
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__, template_folder='.', static_folder='.')
app.secret_key = "al_esraa_ultimate_v14_2026"

# 1. إعدادات المجلدات ورفع الصور
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 2. إعدادات قاعدة البيانات
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///al_esraa_pro.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 3. الجداول (Database Models) ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    username = db.Column(db.String(50), unique=True)
    parent_phone = db.Column(db.String(50))
    password = db.Column(db.String(50))
    role = db.Column(db.String(10), default='student')
    enrolled_courses = db.Column(db.Text, default="")
    results = db.relationship('ExamResult', backref='student', lazy=True)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    price = db.Column(db.Integer, default=0)
    image_path = db.Column(db.String(200))
    lessons = db.relationship('Lesson', backref='course', lazy=True, cascade="all, delete-orphan")

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    video_url = db.Column(db.String(500))
    pdf_url = db.Column(db.String(500))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    questions = db.relationship('Question', backref='lesson', lazy=True, cascade="all, delete-orphan")

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    image_path = db.Column(db.String(200))
    option_a = db.Column(db.String(200))
    option_b = db.Column(db.String(200))
    option_c = db.Column(db.String(200))
    option_d = db.Column(db.String(200))
    correct_answer = db.Column(db.String(1))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))

class SubscriptionCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True)
    is_used = db.Column(db.Boolean, default=False)

class ExamResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer)
    total = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    lesson_title = db.Column(db.String(100))

# إنشاء الجداول والإدمن
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="01063839943").first():
        db.session.add(User(full_name="إسراء فرج", username="01063839943", parent_phone="Admin", password="esraa2026", role="admin"))
        db.session.commit()

# دالة حفظ الصور
def save_image(file):
    if file and file.filename != '':
        filename = secure_filename(str(random.randint(1000, 9999)) + "_" + file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return f"static/uploads/{filename}"
    return None

# --- 4. المسارات (Routes) ---

@app.route('/')
def index():
    return render_template('index.html', courses=Course.query.all())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form.get('phone'), password=request.form.get('password')).first()
        if u:
            session.update({'u_id': u.id, 'role': u.role, 'username': u.full_name})
            return redirect(url_for('admin_pro' if u.role == 'admin' else 'student_dashboard'))
    return render_template('login.html')

@app.route('/admin_pro')
def admin_pro():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    return render_template('admin_dashboard.html', 
                           courses=Course.query.all(), 
                           students=User.query.filter_by(role='student').all(),
                           codes=SubscriptionCode.query.all())

@app.route('/add_course', methods=['POST'])
def add_course():
    if session.get('role') == 'admin':
        img = save_image(request.files.get('course_image'))
        db.session.add(Course(title=request.form.get('title'), price=request.form.get('price'), image_path=img))
        db.session.commit()
    return redirect(url_for('admin_pro'))

@app.route('/add_lesson_full', methods=['POST'])
def add_lesson_full():
    if session.get('role') == 'admin':
        new_l = Lesson(title=request.form.get('lesson_title'), video_url=request.form.get('video_url'),
                        pdf_url=request.form.get('pdf_url'), course_id=request.form.get('course_id'))
        db.session.add(new_l); db.session.commit()
        
        q_texts = request.form.getlist('q_text[]')
        q_images = request.files.getlist('q_image[]')
        for i, text in enumerate(q_texts):
            if text:
                img = save_image(q_images[i]) if i < len(q_images) else None
                q = Question(text=text, image_path=img,
                             option_a=request.form.getlist('q_a[]')[i],
                             option_b=request.form.getlist('q_b[]')[i],
                             option_c=request.form.getlist('q_c[]')[i],
                             option_d=request.form.getlist('q_d[]')[i],
                             correct_answer=request.form.getlist('q_correct[]')[i],
                             lesson_id=new_l.id)
                db.session.add(q)
        db.session.commit()
    return redirect(url_for('admin_pro'))

@app.route('/generate_codes', methods=['POST'])
def generate_codes():
    if session.get('role') == 'admin':
        count = int(request.form.get('count', 0))
        for _ in range(count):
            random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            db.session.add(SubscriptionCode(code=random_code))
        db.session.commit()
    return redirect(url_for('admin_pro'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
