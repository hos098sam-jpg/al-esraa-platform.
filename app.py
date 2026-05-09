import os
import random
import string
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__, template_folder='.', static_folder='.')
app.secret_key = "al_esraa_ultimate_v15_2026"

# إعدادات رفع الصور
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# قاعدة البيانات
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
    option_a = db.Column(db.String(200)); option_b = db.Column(db.String(200))
    option_c = db.Column(db.String(200)); option_d = db.Column(db.String(200))
    correct_answer = db.Column(db.String(1))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))

class SubscriptionCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True)
    is_used = db.Column(db.Boolean, default=False)

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="01063839943").first():
        db.session.add(User(full_name="إسراء فرج", username="01063839943", password="esraa2026", role="admin"))
        db.session.commit()

def save_image(file):
    if file and file.filename != '':
        filename = secure_filename(str(random.randint(1000, 9999)) + "_" + file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return f"static/uploads/{filename}"
    return None

# --- المسارات ---
@app.route('/admin_pro')
def admin_pro():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    return render_template('admin_dashboard.html', 
                           courses=Course.query.all(), 
                           students=User.query.filter_by(role='student').all(),
                           codes=SubscriptionCode.query.filter_by(is_used=False).all())

@app.route('/add_course', methods=['POST'])
def add_course():
    if session.get('role') == 'admin':
        price = int(request.form.get('price', 0))
        img = save_image(request.files.get('course_image'))
        db.session.add(Course(title=request.form.get('title'), price=price, image_path=img))
        db.session.commit()
    return redirect(url_for('admin_pro'))

@app.route('/generate_codes', methods=['POST'])
def generate_codes():
    if session.get('role') == 'admin':
        count = int(request.form.get('count', 0))
        for _ in range(count):
            c = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            db.session.add(SubscriptionCode(code=c))
        db.session.commit()
    return redirect(url_for('admin_pro'))

@app.route('/enroll/<int:course_id>', methods=['POST'])
def enroll(course_id):
    if not session.get('u_id'): return redirect(url_for('login'))
    user = User.query.get(session['u_id'])
    course = Course.query.get(course_id)
    
    # ميزة الكورس المجاني
    if course.price == 0:
        if str(course_id) not in user.enrolled_courses.split(','):
            user.enrolled_courses += f"{course_id},"
            db.session.commit()
        return redirect(url_for('student_dashboard'))
    
    # الاشتراك بكود
    code_txt = request.form.get('sub_code')
    code_obj = SubscriptionCode.query.filter_by(code=code_txt, is_used=False).first()
    if code_obj:
        code_obj.is_used = True
        user.enrolled_courses += f"{course_id},"
        db.session.commit()
    return redirect(url_for('student_dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
