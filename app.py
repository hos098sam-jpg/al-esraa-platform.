import os
import random
import string
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# التعديل السحري: خلينا المجلد الرئيسي هو مجلد القوالب عشان يقرأ الملفات وهي بره
app = Flask(__name__, template_folder='.', static_folder='.')

# مفتاح الأمان
app.secret_key = "al_esraa_ultimate_v14_2026"

# إعداد قاعدة البيانات - مسار مباشر وبسيط
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///al_esraa_pro.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- الجداول ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    username = db.Column(db.String(50), unique=True)
    parent_phone = db.Column(db.String(50))
    password = db.Column(db.String(50))
    role = db.Column(db.String(10), default='student')
    enrolled_courses = db.Column(db.Text, default="")

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    price = db.Column(db.Integer, default=0)
    lessons = db.relationship('Lesson', backref='course', lazy=True, cascade="all, delete-orphan")

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    video_url = db.Column(db.String(500))
    pdf_url = db.Column(db.String(500))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))

# إنشاء قاعدة البيانات وتعيين الإدمن (مس إسراء فرج)
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="01063839943").first():
        db.session.add(User(
            full_name="إسراء فرج",
            username="01063839943",
            parent_phone="Admin",
            password="123",
            role="admin"
        ))
        db.session.commit()

# --- المسارات ---
@app.route('/')
def index():
    return render_template('index.html', courses=Course.query.all())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form.get('phone'), password=request.form.get('password')).first()
        if u:
            session.update({'u_id': u.id, 'role': u.role, 'username': u.full_name, 'phone': u.username})
            return redirect(url_for('admin_pro' if u.role == 'admin' else 'student_dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        phone = request.form.get('phone')
        if not User.query.filter_by(username=phone).first():
            new_u = User(full_name=request.form.get('full_name'), username=phone,
                         parent_phone=request.form.get('parent_phone'), password=request.form.get('password'))
            db.session.add(new_u); db.session.commit()
            session.update({'u_id': new_u.id, 'role': 'student', 'username': new_u.full_name, 'phone': new_u.username})
            return redirect(url_for('student_dashboard'))
    return render_template('register.html')

@app.route('/admin_pro')
def admin_pro():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    return render_template('admin_pro.html', courses=Course.query.all(),
                           students=User.query.filter_by(role='student').all())

@app.route('/student_dashboard')
def student_dashboard():
    if 'u_id' not in session: return redirect(url_for('login'))
    u = User.query.get(session['u_id'])
    enrolled = u.enrolled_courses.split(',') if u.enrolled_courses else []
    return render_template('student_dashboard.html', user=u, courses=Course.query.all(), enrolled_ids=enrolled)

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
