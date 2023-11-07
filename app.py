from flask import Flask, render_template, url_for, request, session, redirect
from flask_pymongo import PyMongo
import os
import secrets
from flask_mail import Mail, Message

app = Flask(__name__)

# Set a secret key
app.secret_key = 'ADBMS2023'  # Replace with a unique and secret key

# Rest of your code
app.config['MONGO_DBNAME'] = 'ADBMS'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/ADBMS'

app.config['MAIL_SERVER'] = 'smtp.googlemail.com'  # Replace with your email server details
app.config['MAIL_PORT'] = 587  # Replace with your email server port
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'riteshphadtare32@gmail.com'  # Replace with your email username
app.config['MAIL_PASSWORD'] = 'pexc sczh kjik exbv'  # Replace with your email password

mail = Mail(app)
mongo = PyMongo(app)
std = mongo.db.studentsData

@app.route("/")
def index():
    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'user' in session:
        session.pop('user')  # Clear the user session if 'user' exists
    return redirect(url_for('index'))


@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/login', methods=['POST'])
def login():
    user_type = request.form.get('user_type')  # Get the selected user type

    if user_type == 'student':
        collection = mongo.db.users
    elif user_type == 'teacher':
        collection = mongo.db.teachers
    else:
        return 'Invalid user type selected'

    login_user = collection.find_one({'email': request.form['email']})

    if login_user:
        if request.form['password'] == login_user['password']:
            if login_user.get('verified', False):
                if user_type == 'student':
                    return redirect(url_for('home'))
                elif user_type == 'teacher':
                    return redirect(url_for('teacherDashboard'))
            else:
                return 'Your email is not verified. Please check your email for a verification link.'
    
    return 'Invalid email or password combination'



@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'email': request.form['email']})

        if existing_user is None:
            # Generate a unique token for email verification
            token = secrets.token_urlsafe(16)
            new_user = {
                'name': request.form['username'],
                'year': request.form['year'],
                'department': request.form['department'],
                'rollno': request.form['rollno'],
                'email': request.form['email'],
                'password': request.form['password'],
                'token': token,  # Add a token field to store the verification token
                'verified': False  # Initialize as not verified
            }
            users.insert_one(new_user)

            # Send a verification email with a link containing the token
            msg = Message('Email Verification', sender='riteshphadtare32@gmail.com', recipients=[request.form['email']])
            msg.body = f"Please click on the following link to verify your email: {url_for('verify_email', token=token, _external=True)}"
            mail.send(msg)

            return 'Please check your email to verify your account.'

    return 'User with this email already exists.'

@app.route('/verify_email/<token>', methods=['GET'])
def verify_email(token):
    users = mongo.db.users
    user = users.find_one({'token': token})

    if user:
        # Mark the user as verified and remove the token
        users.update_one({'_id': user['_id']}, {'$set': {'verified': True}, '$unset': {'token': 1}})
        return 'Email verification successful. You can now log in.'

    return 'Invalid token or user not found.'

@app.route('/signUpTeacher', methods=['POST', 'GET'])
def signUpTeacher():
    if request.method == 'POST':
        teachers = mongo.db.teachers
        existing_user = teachers.find_one({'email': request.form['email']})
        
        if existing_user is None:
            new_teacher = {
                'name': request.form['username'],
                'email': request.form['email'],
                'password': request.form['password'],
                'department': request.form['department']
            }
            teachers.insert_one(new_teacher)
            return redirect(url_for('home'))
    
    return 'User with this email already exists.'

@app.route("/teacherLogin")
def teacherLogin():
    return render_template('teacherlogin.html')

@app.route("/teacherDashoard")
def teacherDashoard():
    return render_template('teacherDashboard.html')

@app.route('/add_Data')
def add_Data():
    return render_template('student_details_entry.html')

@app.route('/add_student', methods=['POST'])
def add_student():
    if request.method == 'POST':
        student = {
            'name': request.form['name'],
            'rollno': request.form['rollno'],
            'age': request.form['age'],
            'grade': request.form['grade']
        }
        std.insert_one(student)
        return redirect(url_for('show_students'))

@app.route('/show_students')
def show_students():
    students = list(std.find())
    return render_template('show_student_details.html', students=students)

@app.route("/updateD")
def updateD():
    return render_template('update.html')

@app.route('/update_student', methods=['POST'])
def update_student():
    if request.method == 'POST':
        rollno = request.form['rollno']
        student = {
            'name': request.form['name'],
            'age': request.form['age'],
            'grade': request.form['grade']
        }
        
        # Use the updateOne command to update the student data based on the rollno
        std.update_one({'rollno': rollno}, {'$set': student})

        return redirect(url_for('show_students'))


@app.route("/deleteD")
def deleteD():
    return render_template('delete.html')

@app.route("/delete_student", methods=['POST'])
def delete_student():
    if request.method == 'POST':
        rollno = request.form['rollno']
        # Use the deleteOne command to delete the student data based on the rollno
        std.delete_one({'rollno': rollno})
        return redirect(url_for('show_students'))


if __name__ == "__main__":
    app.run(debug=True)
