from flask import Flask, render_template, url_for, request, session, redirect, jsonify, send_from_directory
from flask_pymongo import PyMongo
import os
import secrets
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename




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
app.config['UPLOAD_FOLDER'] = 'uploads'


mail = Mail(app)
mongo = PyMongo(app)
std = mongo.db.studentsData


@app.route("/")
def index():
    return render_template('login.html')


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


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


@app.route('/score')
def score():
    return render_template('scores.html')


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
            token = secrets.token_urlsafe(16)
            new_user = {
                'name': request.form['username'],
                'year': request.form['year'],
                'department': request.form['department'],
                'rollno': request.form['rollno'],
                'email': request.form['email'],
                'password': request.form['password'],
                'token': token,
                'verified': False
            }
            users.insert_one(new_user)

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


@app.route('/teacherDashboard')
def teacherDashboard():
    upcoming_test = list(mongo.db.test.find())
    QUESTION_COUNT = 10  # Set the value according to your requirements
    return render_template('teacherDashboard.html', upcoming_tests=upcoming_test, QUESTION_COUNT=QUESTION_COUNT)


@app.route('/questionCount', methods=['GET', 'POST'])
def questionCount():
    qCount = 0  # Provide a default value
    if request.method == 'POST':
        qCount = int(request.form.get('count', 0))
    return render_template('question_addition.html', qCount=qCount)





# @app.route('/createTest')
# def createTest():
#     return render_template('question_addition.html')

@app.route('/create_test', methods=['GET', 'POST'])
def create_test():
    if request.method == 'POST':
        # Create a list to store multiple questions
        questions = []
        c = int(request.form['que_count'])
        # Loop through the form data to get all questions
        for i in range(1, c+1):  # Assuming you want to handle 3 questions, adjust as needed
            question_key = f'question_{i}'
            option1_key = f'option1_{i}'
            option2_key = f'option2_{i}'
            option3_key = f'option3_{i}'
            option4_key = f'option4_{i}'
            correct_option_key = f'correct_option_{i}'

            # Check if the question exists in the form data
            if question_key in request.form:
                # Create a dictionary for each question
                question = {
                    'question': request.form[question_key],
                    'option1': request.form[option1_key],
                    'option2': request.form[option2_key],
                    'option3': request.form[option3_key],
                    'option4': request.form[option4_key],
                    'answer': request.form[correct_option_key]
                }
                # Append the question dictionary to the list
                questions.append(question)

        # Create the new_test dictionary with the list of questions
        new_test = {
            'subject': request.form['test_sub_name'],
            'description': request.form['test_description'],
            'marks': request.form['test_marks'],
            'time': request.form['test_time'],
            'test_date': request.form['test_date'],
            'questions': questions  # Use 'questions' instead of 'question'
        }

        # Insert the new_test document into the database
        mongo.db.test.insert_one(new_test)

        return render_template('teacherDashboard.html')
        


# def save_image(file):
#     if file:
#         filename = secure_filename(file.filename)
#         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         file.save(filepath)
#         return url_for('uploaded_file', filename=filename)
#     return None


if __name__ == "__main__":
    app.run(debug=True)
