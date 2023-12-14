from flask import Flask, render_template, url_for, request, session, redirect
from flask_pymongo import PyMongo
import os
import secrets
from flask_mail import Mail, Message

app = Flask(__name__)

# Set a secret key
app.secret_key = 'IT2023'  # Replace with a unique and secret key

# Rest of your code
app.config['MONGO_DBNAME'] = 'IT'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/IT'

# Replace with your email server details
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587  # Replace with your email server port
app.config['MAIL_USE_TLS'] = True
# Replace with your email username
app.config['MAIL_USERNAME'] = 'riteshphadtare32@gmail.com'
# Replace with your email password
app.config['MAIL_PASSWORD'] = 'ahvq xbdz jrcw wfyc'

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
                    upcoming_test = list(mongo.db.test.find())
                    return render_template('index.html', upcoming_tests=upcoming_test)
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
            msg = Message('Email Verification', sender='riteshphadtare32@gmail.com',
                          recipients=[request.form['email']])
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
        users.update_one({'_id': user['_id']}, {
                         '$set': {'verified': True}, '$unset': {'token': 1}})
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
            return render_template('login.html')

    return 'User with this email already exists.'


@app.route("/teacherLogin")
def teacherLogin():
    return render_template('teacherlogin.html')


@app.route("/teacherDashboard")
def teacherDashboard():
        upcoming_test = list(mongo.db.test.find())
        return render_template('teacherDashboard.html',upcoming_tests=upcoming_test)


@app.route("/testCreation", methods=['GET', 'POST'])
def testCreation():
    if request.method == 'POST':
        test = mongo.db.test

        new_test = {
            'subject': request.form['test_sub_name'],
            'description': request.form['test_description'],
            'marks': request.form['test_marks'],
            'time': request.form['test_time'],
            'test_date': request.form['test_date']
        }
        test.insert_one(new_test)

        return render_template('teacherDashboard.html', message='Created')


if __name__ == "__main__":
    app.run(debug=True)
