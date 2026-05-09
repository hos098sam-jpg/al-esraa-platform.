import os, random, string
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
# تحديث مفتاح الأمان ليكون خاص بالمنصة
app.secret_key = "al_esraa_ultimate_v14_2026"

# إعداد قاعدة البيانات
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'al_esraa_pro.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- الجداول المطورة ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    username = db.Column(db.String(50), unique=True) # رقم الهاتف
    parent_phone = db.Column(db.String(50))
    password = db.Column(db.String(50))
    role = db.Column(db.String(10), default='student')
    enrolled_courses = db.Column(db.Text, default="")
    results = db.relationship('ExamResult', backref='student', lazy=True)

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
    exam = db.relationship('Exam', backref='lesson', uselist=False, cascade="all, delete-orphan")

class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    duration = db.Column(db.Integer, default=30)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))
    questions = db.relationship('Question', backref='exam', lazy=True, cascade="all, delete-orphan")

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    option_a = db.Column(db.String(200))
    option_b = db.Column(db.String(200))
    option_c = db.Column(db.String(200))
    option_d = db.Column(db.String(200))
    correct_answer = db.Column(db.String(1))
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'))

class ExamResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer)
    total = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    lesson_title = db.Column(db.String(100))

class SubscriptionCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True)
    is_used = db.Column(db.Boolean, default=False)

# إنشاء قاعدة البيانات وتعيين الإدمن (مس إسراء فرج)
with app.app_context():
    db.create_all()
    # تم تغيير الرقم والاسم هنا كما طلبت
    if not User.query.filter_by(username="01063839943").first():
        db.session.add(User(
            full_name="إسراء فرج",
            username="01063839943",
            parent_phone="Admin",
            password="123",
            role="admin"
        ))
        db.session.commit()

# --- المسارات (Routes) ---
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
                           codes=SubscriptionCode.query.filter_by(is_used=False).all(),
                           students=User.query.filter_by(role='student').all())

@app.route('/add_course', methods=['POST'])
def add_course():
    if session.get('role') == 'admin':
        db.session.add(Course(title=request.form.get('title'), price=request.form.get('price')))
        db.session.commit()
    return redirect(url_for('admin_pro'))

@app.route('/add_lesson_full', methods=['POST'])
def add_lesson_full():
    if session.get('role') == 'admin':
        raw_url = request.form.get('video_url')
        v_id = ""
        if "shorts/" in raw_url: v_id = raw_url.split("shorts/")[1].split("?")[0]
        elif "v=" in raw_url: v_id = raw_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in raw_url: v_id = raw_url.split("youtu.be/")[1].split("?")[0]
        final_video = f"https://www.youtube.com/embed/{v_id}" if v_id else raw_url

        new_l = Lesson(title=request.form.get('lesson_title'), video_url=final_video,
                        pdf_url=request.form.get('pdf_url'), course_id=request.form.get('course_id'))
        db.session.add(new_l); db.session.flush()

        new_exam = Exam(duration=int(request.form.get('duration') or 30), lesson_id=new_l.id)
        db.session.add(new_exam); db.session.flush()

        for i in range(1, 6): # يدعم حتى 5 أسئلة لكل درس
            txt = request.form.get(f'q{i}_text')
            if txt:
                q = Question(text=txt, option_a=request.form.get(f'q{i}_a'), option_b=request.form.get(f'q{i}_b'),
                             option_c=request.form.get(f'q{i}_c'), option_d=request.form.get(f'q{i}_d'),
                             correct_answer=request.form.get(f'q{i}_correct'), exam_id=new_exam.id)
                db.session.add(q)
        db.session.commit()
    return redirect(url_for('admin_pro'))

@app.route('/delete_course/<int:id>')
def delete_course(id):
    if session.get('role') == 'admin':
        c = Course.query.get(id)
        db.session.delete(c); db.session.commit()
    return redirect(url_for('admin_pro'))

@app.route('/student_dashboard')
def student_dashboard():
    if 'u_id' not in session: return redirect(url_for('login'))
    u = User.query.get(session['u_id'])
    enrolled = u.enrolled_courses.split(',') if u.enrolled_courses else []
    return render_template('student_dashboard.html', user=u, courses=Course.query.all(), enrolled_ids=enrolled)

@app.route('/get_exam/<int:lesson_id>')
def get_exam(lesson_id):
    lesson = Lesson.query.get(lesson_id)
    if not lesson or not lesson.exam: return jsonify({'error': 'no exam'})
    qs = [{'id': q.id, 'text': q.text, 'a': q.option_a, 'b': q.option_b, 'c': q.option_c, 'd': q.option_d} for q in lesson.exam.questions]
    return jsonify({'duration': lesson.exam.duration, 'questions': qs, 'exam_id': lesson.exam.id})

@app.route('/submit_exam', methods=['POST'])
def submit_exam():
    data = request.json
    exam = Exam.query.get(data['exam_id'])
    score = 0
    for q in exam.questions:
        if data['answers'].get(str(q.id)) == q.correct_answer: score += 1
    new_res = ExamResult(score=score, total=len(exam.questions), user_id=session['u_id'], lesson_title=exam.lesson.title)
    db.session.add(new_res); db.session.commit()
    return jsonify({'score': score, 'total': len(exam.questions)})

@app.route('/unlock_course', methods=['POST'])
def unlock_course():
    code_val = request.form.get('code')
    course_id = request.form.get('course_id')
    code_entry = SubscriptionCode.query.filter_by(code=code_val, is_used=False).first()
    if code_entry:
        u = User.query.get(session['u_id'])
        current = u.enrolled_courses.split(',') if u.enrolled_courses else []
        if course_id not in current:
            current.append(course_id)
            u.enrolled_courses = ",".join(current)
            code_entry.is_used = True
            db.session.commit()
    return redirect(url_for('student_dashboard'))

@app.route('/generate_codes', methods=['POST'])
def generate_codes():
    if session.get('role') == 'admin':
        for _ in range(int(request.form.get('count') or 5)):
            c = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            db.session.add(SubscriptionCode(code=c))
        db.session.commit()
    return redirect(url_for('admin_pro'))

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)