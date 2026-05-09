import os
import random
import string
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__, template_folder='.', static_folder='.')
app.secret_key = "al_esraa_ultimate_v14_2026"

# إعدادات رفع الصور
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# قاعدة البيانات
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///al_esraa_pro.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- الجداول المطورة ---
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
    image_path = db.Column(db.String(200)) # صورة الكورس
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
    image_path = db.Column(db.String(200)) # صورة السؤال
    option_a = db.Column(db.String(200))
    option_b = db.Column(db.String(200))
    option_c = db.Column(db.String(200))
    option_d = db.Column(db.String(200))
    correct_answer = db.Column(db.String(1))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))

class ExamResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer)
    total = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    lesson_title = db.Column(db.String(100))

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="01063839943").first():
        db.session.add(User(full_name="إسراء فرج", username="01063839943", parent_phone="Admin", password="esraa2026", role="admin"))
        db.session.commit()

# دالة مساعدة لرفع الصور
def save_image(file):
    if file and file.filename != '':
        filename = secure_filename(str(random.randint(1,1000)) + "_" + file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return f"static/uploads/{filename}"
    return None

# --- المسارات (Routes) ---
@app.route('/')
def index():
    return render_template('index.html', courses=Course.query.all())

@app.route('/add_course', methods=['POST'])
def add_course():
    if session.get('role') == 'admin':
        img = save_image(request.files.get('course_image'))
        new_c = Course(title=request.form.get('title'), price=request.form.get('price'), image_path=img)
        db.session.add(new_c); db.session.commit()
    return redirect(url_for('admin_pro'))

@app.route('/add_lesson_full', methods=['POST'])
def add_lesson_full():
    if session.get('role') == 'admin':
        new_l = Lesson(title=request.form.get('lesson_title'), video_url=request.form.get('video_url'),
                        pdf_url=request.form.get('pdf_url'), course_id=request.form.get('course_id'))
        db.session.add(new_l); db.session.commit()
        
        # إضافة الأسئلة (عدد غير محدود)
        q_texts = request.form.getlist('q_text[]')
        for i, text in enumerate(q_texts):
            if text:
                img = save_image(request.files.getlist('q_image[]')[i])
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

@app.route('/admin_pro')
def admin_pro():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    return render_template('admin_pro.html', courses=Course.query.all(), students=User.query.filter_by(role='student').all())

# (باقي مسارات تسجيل الدخول والحذف والنتائج كما هي...)
# [أكمل الكود بمسارات تسجيل الدخول السابقة]

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
