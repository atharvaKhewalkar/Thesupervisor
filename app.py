from flask import Flask
from pymongo import MongoClient
from flask import Blueprint, render_template, session, request, redirect, url_for, send_from_directory, jsonify
from flask_mail import Message
from flask_mail import Mail
import secrets
from bson import ObjectId
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import request, jsonify 
import cv2 #pip install opencv-contrib-python
import numpy as np
from PIL import Image
import pygetwindow as gw
import pyautogui
import time
import webbrowser
from selenium import webdriver
import sys
from tkinter import messagebox  # Import the messagebox module
import tkinter as tk
from tkinter import messagebox
import dlib

from flask import redirect, url_for, render_template
from selenium.common.exceptions import NoSuchWindowException



cam = cv2.VideoCapture(0)
detector=cv2.CascadeClassifier('haarcascade.xml')
# Replace with your email server details


app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587  # Replace with your email server port
app.config['MAIL_USE_TLS'] = True
# Replace with your email username
app.config['MAIL_USERNAME'] = 'riteshphadtare32@gmail.com'
# Replace with your email password
app.config['MAIL_PASSWORD'] = 'owyu hneq arko ocsq'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key='IT2023'
mail = Mail(app)
# MongoDB Atlas connection URI
MONGODB_URI = "mongodb+srv://itstudiodpu:43zB1ftcqLIBioLh@thesupervisor.lilvxlg.mongodb.net/"

# Create a MongoClient instance
client = MongoClient(MONGODB_URI)

# Access your database (replace 'your_database_name' with your actual database name)
db = client.IT

# Access a specific collection within the database (replace 'your_collection_name' with your actual collection name)

@app.route("/")
def index():
    return render_template('html/login.html')


# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/static/uploads/<path:filename>')
def download_file(filename):
    return send_from_directory("static/uploads", filename)


@app.route('/logout')
def logout():
    if 'user' in session:
        session.pop('user')  # Clear the user session if 'user' exists
    return redirect(url_for('index'))


@app.route('/teacher_profile')
def teacher_profile():
    temail = session.get('user').get('email')
    teacher_details = db.teachers.find_one({'email': temail})
    return render_template('html/teacher_profile.html', teacher_details=teacher_details)


@app.route('/t_edit_profile', methods=['POST'])
def t_edit_profile():
    if 'user' in session:
        email = session['user']['email']
        users_collection = db.teachers

        teacher_details = users_collection.find_one({'email': email})
        if teacher_details:
            # Update user details based on the submitted form
            teacher_details['name'] = request.form.get('name')
            teacher_details['department'] = request.form.get('department')
            # Update other details similarly based on your form fields

            # Handling profile photo upload
            if 'profile_photo' in request.files:
                profile_photo = request.files['profile_photo']
                if profile_photo.filename != '':
                    # Save the uploaded file to a specific folder
                    uploads_dir = 'static/uploads/profilePhotos'
                    if not os.path.exists(uploads_dir):
                        os.makedirs(uploads_dir)

                    # Use secure_filename to prevent malicious file names
                    filename = secure_filename(f"{email}.jpg")
                    databse_path = os.path.join("/profilePhotos/profile_photo_" + filename)
                    photo_path = os.path.join(uploads_dir, "profile_photo_" + filename)
                    profile_photo.save(photo_path)

                    # Update the user details with the profile photo path
                    teacher_details['profile_photo'] = databse_path

            # Update specific fields in the document
            users_collection.update_one({'email': email}, {'$set': {
                'name': teacher_details['name'],
                'department': teacher_details['department'],
                'profile_photo': teacher_details.get('profile_photo', '')
            }})

            return redirect(url_for('teacher_profile'))
        else:
            return 'User details not found'
    else:
        return redirect(url_for('index'))


@app.route('/profile')
def profile():
    # Check if the user is logged in
    if 'user' in session:
        # Get the email of the logged-in user
        email = session['user']['email']

        # Fetch student details from the users collection based on the email
        student_details = db.users.find_one({'email': email})

        # Fetch scores for attempted tests
        mcq_scores = list(db.result.find())
        mcq_scores_para = list(db.student_score_para.find())
        # Initialize lists to store test IDs and corresponding scores
        test_details = []
        test_scores = []

        # Iterate through the scores to find relevant data for the logged-in user
        for score in mcq_scores:
            stud_data = score.get('student_data', {})
            test_id = score.get('test_id', '')

            # Check if the logged-in user has attempted the test
            if email in stud_data:
                stu_score = stud_data[email]
                test_details.append(
                    db.test.find_one({'test_id': test_id}))
                test_scores.append(stu_score)

        for score in mcq_scores_para:
            stud_data = score.get('student_data', {})
            test_id = score.get('test_id', '')

            # Check if the logged-in user has attempted the test
            if email in stud_data:
                stu_score = stud_data[email]
                test_details.append(
                    db.test_paragraph.find_one({'test_id': test_id}))
                test_scores.append(stu_score)

        if student_details:
            # Pass student details, test IDs, and test scores to the template
            return render_template('html/stud_profile.html', student_details=student_details, test_details=test_details,
                                   test_scores=test_scores)
        else:
            return 'Student details not found'
    else:
        return redirect(url_for('index'))


@app.route('/edit_profile', methods=['POST'])
def edit_profile():
    if 'user' in session:
        email = session['user']['email']
        users_collection = db.users

        user_details = users_collection.find_one({'email': email})

        if user_details:
            # Update user details based on the submitted form
            user_details['name'] = request.form.get('name')
            user_details['year'] = request.form.get('year')
            user_details['department'] = request.form.get('department')
            # Update other details similarly based on your form fields

            # Handling profile photo upload
            if 'profile_photo' in request.files:
                profile_photo = request.files['profile_photo']
                if profile_photo.filename != '':
                    # Save the uploaded file to a specific folder
                    uploads_dir = 'static/uploads/profilePhotos'
                    if not os.path.exists(uploads_dir):
                        os.makedirs(uploads_dir)

                    # Use secure_filename to prevent malicious file names
                    filename = secure_filename(f"{email}.jpg")
                    databse_path = os.path.join("/profilePhotos/profile_photo_" + filename)
                    photo_path = os.path.join(uploads_dir, "profile_photo_" + filename)
                    profile_photo.save(photo_path)

                    # Update the user details with the profile photo path
                    user_details['profile_photo'] = databse_path

            # Update specific fields in the document
            users_collection.update_one({'email': email}, {'$set': {
                'name': user_details['name'],
                'year': user_details['year'],
                'department': user_details['department'],
                'profile_photo': user_details.get('profile_photo', '')
            }})

            return redirect(url_for('profile'))
        else:
            return 'User details not found'
    else:
        return redirect(url_for('index'))


@app.route('/home')
def home():
    upcoming_test = list(db.test.find())
    submitted_answers = list(db.submitted_answers_collection.find(
        {}, {'answers': 1, 'test_id': 1, '_id': 0}))
    upcoming_test_ids = list(db.test.find({}, {'test_id': 1, '_id': 0}))

    upcoming_test_para = list(db.test_paragraph.find())
    submitted_answers_para = list(db.submitted_answers_collection_para.find(
        {}, {'answers': 1, 'test_id': 1, '_id': 0}))
    upcoming_test_ids_para = list(
        db.test_paragraph.find({}, {'test_id': 1, '_id': 0}))

    ids_toremove = []
    for test in upcoming_test_ids:
        id = test['test_id']
        keys_from_answers = []
        for i in submitted_answers:
            res = i['test_id']
            if (id == res):
                ans = i['answers']
                keys_from_answers.extend(ans.keys())
                temp = keys_from_answers
                for j in temp:
                    if (j == session.get('user').get('email')):
                        ids_toremove.append(res)

    ids_toremove_para = []
    for test in upcoming_test_ids_para:
        id_para = test['test_id']
        keys_from_answers_para = []
        for i in submitted_answers_para:
            res_para = i['test_id']
            if (id_para == res_para):
                ans_para = i['answers']
                keys_from_answers_para.extend(ans_para.keys())
                temp_para = keys_from_answers_para
                for j in temp_para:
                    if (j == session.get('user').get('email')):
                        ids_toremove_para.append(res_para)

    upcoming_test = [test for test in upcoming_test if test.get(
        'test_id') not in ids_toremove]
    upcoming_test_para = [test for test in upcoming_test_para if test.get(
        'test_id') not in ids_toremove_para]

    return render_template('html/index.html', upcoming_tests=upcoming_test, upcoming_test_para=upcoming_test_para)


@app.route('/test')
def test():
    return render_template('html/test.html')


@app.route('/login', methods=['POST'])
def login():
    user_type = request.form.get('user_type')  # Get the selected user type

    jsonify_message = None 

    if user_type == 'student':
        collection = db.users
    elif user_type == 'teacher':
        collection = db.teachers
    else:
        return 'Invalid user type selected'

    login_user = collection.find_one({'email': request.form['email']})

    if login_user:
        if request.form['password'] == login_user['password']:
            if login_user.get('verified', False):
                # Store user data in the session
                session['user'] = {
                    'name': login_user['name'],
                    'email': login_user['email'],
                    'rollno': login_user['rollno'],
                    'department': login_user['department'],
                }

                if user_type == 'student':
                    upcoming_test = list(db.test.find())
                    submitted_answers = list(db.submitted_answers_collection.find(
                        {}, {'answers': 1, 'test_id': 1, '_id': 0}))
                    upcoming_test_ids = list(
                        db.test.find({}, {'test_id': 1, '_id': 0}))

                    upcoming_test_para = list(db.test_paragraph.find())
                    submitted_answers_para = list(db.submitted_answers_collection_para.find(
                        {}, {'answers': 1, 'test_id': 1, '_id': 0}))
                    upcoming_test_ids_para = list(
                        db.test_paragraph.find({}, {'test_id': 1, '_id': 0}))

                    ids_toremove = []
                    for test in upcoming_test_ids:
                        id = test['test_id']
                        keys_from_answers = []
                        for i in submitted_answers:
                            res = i['test_id']
                            if (id == res):
                                ans = i['answers']
                                keys_from_answers.extend(ans.keys())
                                temp = keys_from_answers
                                for j in temp:
                                    if (j == session.get('user').get('email')):
                                        ids_toremove.append(res)

                    ids_toremove_para = []
                    for test in upcoming_test_ids_para:
                        id_para = test['test_id']
                        keys_from_answers_para = []
                        for i in submitted_answers_para:
                            res_para = i['test_id']
                            if (id_para == res_para):
                                ans_para = i['answers']
                                keys_from_answers_para.extend(ans_para.keys())
                                temp_para = keys_from_answers_para
                                for j in temp_para:
                                    if (j == session.get('user').get('email')):
                                        ids_toremove_para.append(res_para)

                    upcoming_test = [test for test in upcoming_test if test.get(
                        'test_id') not in ids_toremove]
                    upcoming_test_para = [test for test in upcoming_test_para if test.get(
                        'test_id') not in ids_toremove_para]

                    return render_template('html/index.html', upcoming_tests=upcoming_test,
                                           upcoming_test_para=upcoming_test_para,
                                           jsonify_message=jsonify_message, Studemail = login_user['email'])

            elif user_type == 'teacher':
                if login_user:
                    if request.form['password'] == login_user['password']:
                        # Store teacher data in the session
                        session['user'] = {
                            'name': login_user['name'],
                            'email': login_user['email'],
                            'department': login_user['department'],
                            # Add other teacher-related information as needed
                        }

                        return redirect(url_for('teacherDashboard'))

                    jsonify_message = 'Invalid email or password combination'
                    return render_template('html/login.html', jsonify_message=jsonify_message)

                else:
                    jsonify_message = 'Your email is not verified. Please check your email for a verification link.'
                    return render_template('html/login.html', jsonify_message=jsonify_message)

        jsonify_message = 'Invalid email or password combination'
        return render_template('html/login.html', jsonify_message=jsonify_message)

    jsonify_message = 'Invalid user type selected'
    return render_template('html/login.html', jsonify_message=jsonify_message)


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = db.users
        existing_user = users.find_one({'email': request.form['email']})

        if existing_user is None:
            # Handle file upload
            file = request.files['file']
            if file and allowed_file(file.filename):
                # Generate a secure filename based on the student name
                filename = secure_filename(request.form['email'] + '.jpg')
                file_name = f"profile_photo_{filename}"
                databse_path = os.path.join("/profilePhotos/profile_photo_" + filename)
                file.save(os.path.join('static/uploads/profilePhotos/', file_name))
            count = users.count_documents({})
            unique_id = count + 1
            
            token = secrets.token_urlsafe(16)
            new_user = {
                'name': request.form['username'],
                'year': request.form['year'],
                'department': request.form['department'],
                'rollno': request.form['rollno'],
                'email': request.form['email'],
                'password': request.form['password'],
                'token': token,
                'verified': False,
                'profile_photo': databse_path,  # Save the filename in the database
                'unique_id':unique_id
            }
            users.insert_one(new_user)

            msg = Message('Email Verification', sender='riteshphadtare32@gmail.com',
                          recipients=[request.form['email']])
            msg.body = f"Please click on the following link to verify your email: {url_for('verify_email', token=token, _external=True)}"
            mail.send(msg)

            jsonify_message = 'Please check your email to verify your account.'
            return render_template('html/login.html', jsonify_message=jsonify_message)

    jsonify_message = 'User with this email already exists.'
    return render_template('html/login.html', jsonify_message=jsonify_message)


@app.route('/verify_email/<token>', methods=['GET'])
def verify_email(token):
    users = db.users
    user = users.find_one({'token': token})

    if user:
        # Mark the user as verified and remove the token
        users.update_one({'_id': user['_id']}, {
            '$set': {'verified': True}, '$unset': {'token': 1}})
        jsonify_message = 'Email verification successful. You can now log in.'
        return render_template('html/login.html', jsonify_message=jsonify_message)

    jsonify_message = 'Invalid token or user not found.'
    return render_template('html/login.html', jsonify_message=jsonify_message)


@app.route('/signUpTeacher', methods=['POST', 'GET'])
def signUpTeacher():
    if request.method == 'POST':
        teachers = db.teachers
        existing_user = teachers.find_one({'email': request.form['email']})

        if existing_user is None:
            new_teacher = {
                'name': request.form['username'],
                'email': request.form['email'],
                'password': request.form['password'],
                'department': request.form['department']
            }
            teachers.insert_one(new_teacher)
            return render_template('html/login.html')

    jsonify_message = 'User with this email already exists.'
    return render_template('html/teacherlogin.html', jsonify_message=jsonify_message)


@app.route("/teacherLogin")
def teacherLogin():
    return render_template('html/teacherlogin.html')


@app.route('/teacherDashboard')
def teacherDashboard():
    upcoming_test = list(db.test.find())
    start_time = []
    end_time = []
    if upcoming_test:
        for i in upcoming_test:
            st = i.get('start_time', [])
            et = i.get('end_time', [])
            start_time_obj = datetime.strptime(st, "%Y-%m-%dT%H:%M:%S")
            end_time_obj = datetime.strptime(et, "%Y-%m-%dT%H:%M:%S")

            stime = start_time_obj.strftime("%H:%M")
            etime = end_time_obj.strftime("%H:%M")
            start_time.append(stime)
            end_time.append(etime)

        upcoming_test_para = list(db.test_paragraph.find())
        if upcoming_test_para:
            start_time_para = []
            end_time_para = []
            for i in upcoming_test_para:
                st_para = i.get('start_time', [])
                et_para = i.get('end_time', [])
                start_time_obj_para = datetime.strptime(st_para, "%Y-%m-%dT%H:%M:%S")
                end_time_obj_para = datetime.strptime(et_para, "%Y-%m-%dT%H:%M:%S")

                stime_para = start_time_obj_para.strftime("%H:%M")
                etime_para = end_time_obj_para.strftime("%H:%M")
                start_time_para.append(stime_para)
                end_time_para.append(etime_para)
                return render_template('html/teacherDashboard.html', upcoming_tests=upcoming_test,
                                       start_time=start_time, end_time=end_time, upcoming_tests_para=upcoming_test_para,
                                       start_time_para=start_time_para, end_time_para=end_time_para)
    return render_template('html/teacherDashboard.html', upcoming_tests=upcoming_test, start_time=start_time,
                           end_time=end_time)


@app.route('/typeofque')
def typeofque():
    return render_template('html/typeOfQues.html')


@app.route('/questionCount', methods=['GET', 'POST'])
def questionCount():
    qCount = 0  # Provide a default value
    selected_option = request.form.get('que_type')
    if request.method == 'POST':
        qCount = int(request.form.get('count', 0))
        max_id = 1
        if selected_option == "mcq":
            test_ids = []
            test_details = list(db.test.find())
            for test in test_details:
                test_id = test.get('test_id')
                test_ids.append(int(test_id))
            if test_ids:
                max_id = max(test_ids)
                max_id += 1
            else:
                max_id = 1

            return render_template('html/question_addition.html', qCount=qCount, test_id=max_id)
        else:
            test_ids = []
            test_details = list(db.test_paragraph.find())
            for test in test_details:
                test_id = test.get('test_id')
                test_ids.append(int(test_id))
            if test_ids:
                max_id = max(test_ids)
                max_id += 1
            else:
                max_id = 1
            return render_template('html/paragraph.html', qCount=qCount, test_id=max_id)


@app.route('/create_test_mcq', methods=['GET', 'POST'])
def create_test_mcq():
    if request.method == 'POST':
        test_id = request.form['test_id']
        check_id = db.test.find_one({'test_id': test_id})
        c = int(request.form['que_count'])
        if check_id is None:
            # Create a list to store multiple questions
            questions = []
            # questions.append("null")
            c = int(request.form['que_count'])

            # Loop through the form data to get all questions
            for i in range(1, c + 1):  # Assuming you want to handle 3 questions, adjust as needed
                question_key = f'question_{i}'
                option1_key = f'option1_{i}'
                option2_key = f'option2_{i}'
                option3_key = f'option3_{i}'
                option4_key = f'option4_{i}'
                correct_option_value = request.form.get(f'correct_option_{i}')

                # Check if the question exists in the form data
                if question_key in request.form:
                    # Create a dictionary for each question
                    question = {
                        'question': request.form[question_key],
                        'option1': request.form[option1_key],
                        'option2': request.form[option2_key],
                        'option3': request.form[option3_key],
                        'option4': request.form[option4_key],
                        'answer': correct_option_value  # Use correct_option_value directly
                    }

                    file_key = f'file_{i}'
                    if file_key in request.files:
                        file = request.files[file_key]
                        if file.filename != '':
                            uploads_dir = 'static/uploads/queImg'
                            if not os.path.exists(uploads_dir):
                                os.makedirs(uploads_dir)
                            # Save the file to the upload folder
                            file_path = '/queImg/' + f"{test_id}_{file_key}.jpg"
                            # Add the image path to the question dictionary
                            file_save_path = os.path.join(uploads_dir,f"{test_id}_{file_key}.jpg")
                            file.save(file_save_path)
                            question['image_path'] = file_path
                    # Append the question dictionary to the list
                    questions.append(question)

            start_time = request.form['test_date'] + \
                         'T' + request.form['start_time'] + ':00'
            end_time = request.form['test_date'] + \
                       'T' + request.form['end_time'] + ':00'

            start_time_dt = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S')
            end_time_dt = datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S')
            # Create the new_test dictionary with the list of questions
            new_test = {
                'test_id': test_id,
                'subject': request.form['test_sub_name'],
                'description': request.form['test_description'],
                'marks': request.form['test_marks'],
                'teacher_email': session.get('user').get('email'),
                'start_time': start_time_dt.strftime('%Y-%m-%dT%H:%M:%S'),
                'end_time': end_time_dt.strftime('%Y-%m-%dT%H:%M:%S'),
                'test_date': request.form['test_date'],
                'questions': questions  # Use 'questions' instead of 'question'
            }

            # Insert the new_test document into the database
            db.test.insert_one(new_test)

            return redirect(url_for('teacherDashboard'))
        else:
            return render_template('html/question_addition.html', qCount=c, test_id_exists=True)


@app.route('/create_test_paragraph', methods=['GET', 'POST'])
def create_test_paragraph():
    if request.method == 'POST':
        test_id = request.form['test_id']
        check_id = db.test_paragraph.find_one({'test_id': test_id})
        c = int(request.form['que_count'])
        if check_id is None:
            questions = []

            c = int(request.form['que_count'])
            test_id = request.form['test_id']
            for i in range(1, c + 1):  # Assuming you want to handle 3 questions, adjust as needed
                question_key = f'question_{i}'

                # Check if the question exists in the form data
                if question_key in request.form:
                    # Create a dictionary for each question
                    question = {
                        'question': request.form[question_key],
                    }
                    # Append the question dictionary to the list
                    file_key = f'file_{i}'
                    if file_key in request.files:
                        file = request.files[file_key]
                        if file.filename != '':
                            uploads_dir = 'static/uploads/queImg'
                            if not os.path.exists(uploads_dir):
                                os.makedirs(uploads_dir)
                            # Ensure secure filename to prevent security risks
                            filename = secure_filename(file.filename)
                            # Save the file to the upload folder
                            file_path = f"{test_id}_{file_key}.jpg"
                            # Add the image path to the question dictionary
                            file_save_path = os.path.join(uploads_dir, f"{test_id}_{file_key}.jpg")
                            file.save(file_save_path)
                            question['image_path'] = file_path
                    questions.append(question)

            start_time = request.form['test_date'] + \
                         'T' + request.form['start_time'] + ':00'
            end_time = request.form['test_date'] + \
                       'T' + request.form['end_time'] + ':00'

            start_time_dt = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S')
            end_time_dt = datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S')
            # Create the new_test dictionary with the list of questions
            new_test = {
                'test_id': request.form['test_id'],
                'subject': request.form['test_sub_name'],
                'description': request.form['test_description'],
                'marks': request.form['test_marks'],
                'start_time': start_time_dt.strftime('%Y-%m-%dT%H:%M:%S'),
                'end_time': end_time_dt.strftime('%Y-%m-%dT%H:%M:%S'),
                'test_date': request.form['test_date'],
                'teacher_email': session.get('user').get('email'),
                'questions': questions
            }

            # Insert the new_test document into the database
            db.test_paragraph.insert_one(new_test)

            return redirect(url_for('teacherDashboard'))
        else:
            return render_template('html/question_addition.html', qCount=c, test_id_exists=True)


@app.route('/view_test_mcq/<test_id>')
def view_test_mcq(test_id):
    test_details = db.test.find_one({'test_id': test_id})
    test_questions = test_details.get('questions', [])
    qCount = len(test_questions)
    start_time = test_details.get('start_time', [])
    end_time = test_details.get('end_time', [])

    start_time_obj = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
    end_time_obj = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S")

    start_time = start_time_obj.strftime("%H:%M")
    end_time = end_time_obj.strftime("%H:%M")
    return render_template('html/edit_test_mcq.html', test_details=test_details, test_questions=test_questions,
                           qCount=qCount, start_time=start_time, end_time=end_time)


@app.route('/view_test_para/<test_id>')
def view_test_para(test_id):
    test_details = db.test_paragraph.find_one({'test_id': test_id})
    test_questions = test_details.get('questions', [])
    qCount = len(test_questions)
    start_time = test_details.get('start_time', [])
    end_time = test_details.get('end_time', [])

    start_time_obj = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
    end_time_obj = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S")

    start_time = start_time_obj.strftime("%H:%M")
    end_time = end_time_obj.strftime("%H:%M")
    return render_template('html/edit_test_para.html', test_details=test_details, test_questions=test_questions,
                           qCount=qCount, start_time=start_time, end_time=end_time)


@app.route('/edit_test_mcq/<test_id>', methods=['GET', 'POST'])
def edit_test_mcq(test_id):
    if request.method == 'POST':
        start_time = request.form['test_date'] + \
                     'T' + request.form['start_time'] + ':00'
        end_time = request.form['test_date'] + \
                   'T' + request.form['end_time'] + ':00'

        start_time_dt = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S')
        end_time_dt = datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S')
        test_details = {
            "test_id": test_id,
            "subject": request.form['test_sub_name'],
            "description": request.form['test_description'],
            "marks": int(request.form['test_marks']),
            'start_time': start_time_dt.strftime('%Y-%m-%dT%H:%M:%S'),
            'end_time': end_time_dt.strftime('%Y-%m-%dT%H:%M:%S'),
            'test_date': request.form['test_date'],
            "questions": []
        }

        que_count = int(request.form['que_count'])

        for i in range(1, que_count + 1):
            question = {
                "question": request.form['question_' + str(i)],
                "option1": request.form['option1_' + str(i)],
                "option2": request.form['option2_' + str(i)],
                "option3": request.form['option3_' + str(i)],
                "option4": request.form['option4_' + str(i)],
                "answer": request.form['correct_option_' + str(i)],
                "file": request.files['file_' + str(i)].filename if 'file_' + str(i) in request.files else None
            }
            test_details["questions"].append(question)

        # Update the test details in the MongoDB collection
        db.test.update_one({'test_id': test_id}, {
            '$set': test_details})

        return redirect(url_for('teacherDashboard'))
    return render_template('html/error.html', error_message="Test not found")


@app.route('/edit_test_para/<test_id>', methods=['GET', 'POST'])
def edit_test_para(test_id):
    if request.method == 'POST':
        start_time = request.form['test_date'] + \
                     'T' + request.form['start_time'] + ':00'
        end_time = request.form['test_date'] + \
                   'T' + request.form['end_time'] + ':00'

        start_time_dt = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S')
        end_time_dt = datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S')
        test_details = {
            "test_id": test_id,
            "subject": request.form['test_sub_name'],
            "description": request.form['test_description'],
            "marks": int(request.form['test_marks']),
            'start_time': start_time_dt.strftime('%Y-%m-%dT%H:%M:%S'),
            'end_time': end_time_dt.strftime('%Y-%m-%dT%H:%M:%S'),
            'test_date': request.form['test_date'],
            "questions": []
        }

        que_count = int(request.form['que_count'])

        for i in range(1, que_count + 1):
            question = {
                "question": request.form['question_' + str(i)],
                "image_path": request.files['file_' + str(i)].filename if 'file_' + str(i) in request.files else None
            }
            test_details["questions"].append(question)

        # Update the test details in the MongoDB collection
        db.test_paragraph.update_one({'test_id': test_id}, {
            '$set': test_details})

        return redirect(url_for('teacherDashboard'))
    return render_template('html/error.html', error_message="Test not found")





def check_user_opencv(test_id, Studemail):
    exclude_class = "person"
    min_faces = 1
    min_visibility_percentage = 0.50
    delay_before_opening_tab = 5
    popup_delay = 5
    global status
    status = True
    global popup_counter  # Declare popup_counter as a global variable
    popup_counter = 0

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read('trainingData.yml')
    dlib_detector = dlib.get_frontal_face_detector()
    face_cascade = cv2.CascadeClassifier('haarcascade.xml')

    driver = webdriver.Chrome()

    net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
    layer_names = net.getUnconnectedOutLayersNames()

    classes = []
    with open("coco.names", "r") as f:
        classes = [line.strip() for line in f]

    cap = cv2.VideoCapture(0)
    user_detected = False
    first_time_user = True
    exam_tab_opened = False
    start_time = 0
    start_time1 = 0
    exam_url = "http://127.0.0.1:5001/attempt_test/"+test_id+"/"+Studemail

    def open_exam_tab():
        global exam_tab_opened
        driver.get(exam_url)
        print('Exam tab opened successfully 1')
        exam_tab_opened = True

    def test_submitted():
        global status
        print('Exam tab closed successfully')
        status = False  # Set status to False to exit the loop


    max_popup_count = 10

    def show_popup(class_name):
        global popup_counter
        alert_message = f"Non-Person/Object Detected: {class_name}"
        script = f"alert('{alert_message}');"
        try:
            driver.execute_script(script)
            alert = driver.switch_to.alert
            # alert.accept()  # You can also use alert.dismiss() if needed
        except Exception as e:
            # Handle other exceptions or log them if needed
            print(f"Error handling alert: {e}")
        popup_counter += 1

    while status:
        ret, frame = cap.read()

        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            height, width, channels = frame.shape

            faces = dlib_detector(gray, 1)

            for face in faces:
                
                if not status:
                    cap.release()
                    cv2.destroyAllWindows()
                    break

                x, y, w, h = face.left(), face.top(), face.width(), face.height()

                if x >= 0 and y >= 0 and x + w <= width and y + h <= height:
                    id_, confidence = recognizer.predict(gray[y:y + h, x:x + w])

                    if confidence < 65:
                        name = f"User {id_}"
                        cv2.putText(frame, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                        if first_time_user and not exam_tab_opened:
                            start_time = time.time()
                            first_time_user = False

                        elif not exam_tab_opened and time.time() - start_time >= delay_before_opening_tab:
                            open_exam_tab()
                            exam_tab_opened = True
                            print('Exam tab opened successfully 2')

                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            if len(faces) > min_faces or len(faces) == 0:
                message1 = f"More than {min_faces} faces or no face detected. Trigger an action here."
                print(message1)
                if exam_tab_opened:
                    show_popup(message1)
                    if popup_counter < max_popup_count:
                        popup_counter += 1
                        time.sleep(popup_delay)
                    else:
                        test_submitted()
                        break

        blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        net.setInput(blob)
        outs = net.forward(layer_names)

        for out in outs:
            
            if not status:
                break
            for detection in out:
                
                if not status:
                    break
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]

                if confidence > 0.5 and classes[class_id] != exclude_class:
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)

                    visibility_percentage = (w * h) / (width * height) * 100

                    if visibility_percentage > min_visibility_percentage:
                        x = int(center_x - w / 2)
                        y = int(center_y - h / 2)

                        detected_object = {
                            'class': classes[class_id],
                            'confidence': confidence,
                            'visibility_percentage': visibility_percentage,
                            'bounding_box': (x, y, x + w, y + h)
                        }

                        if classes[class_id] == "cell phone":
                            message = f"{detected_object['class']} detected with confidence {detected_object['confidence']:.2f} {popup_counter}" 
                            show_popup(message)  

                            if popup_counter >= max_popup_count:
                                test_submitted()
                                break

                            time.sleep(popup_delay)

                        color = (0, 255, 0)
                        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                        cv2.putText(frame, f"{classes[class_id]} {confidence:.2f}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5, color, 2)

        cv2.imshow("Object Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()




@app.route('/check_user/<test_id>/<Studemail>')
def check_user(test_id, Studemail):
    try:
        check_user_opencv(test_id, Studemail)
    except NoSuchWindowException as e:
        # Handle NoSuchWindowException
        print(f"Error executing check_user_opencv: {e}")
    
    # Redirect to home page
    return redirect(url_for('home', Studemail=Studemail))

@app.route('/attempt_test/<test_id>/<Studemail>')
def attempt_test(test_id,Studemail):
    test = db.test.find_one(
        {
            'test_id': test_id
        }
    )
    if test:
        test_questions = test.get('questions', [])
        start_time = test.get('start_time', [])
        end_time = test.get('end_time', [])

        start_time_obj = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
        end_time_obj = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S")

        st = start_time_obj.strftime("%H:%M:%S")
        et = end_time_obj.strftime("%H:%M:%S")

        return render_template('html/attempt_test.html', test=test, questions=test_questions, start_time=start_time,
                               end_time=end_time, et=et, st=st, Studemail=Studemail)
    return 'Test not found'


@app.route('/attempt_test_para/<test_id>')
def attempt_test_para(test_id):
    test = db.test_paragraph.find_one(
        {
            'test_id': test_id
        }
    )
    if test:
        test_questions = test.get('questions', [])
        start_time = test.get('start_time', [])
        end_time = test.get('end_time', [])

        start_time_obj = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
        end_time_obj = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S")

        st = start_time_obj.strftime("%H:%M:%S")
        et = end_time_obj.strftime("%H:%M:%S")
        return render_template('html/attempt_test_paragraph.html', test=test, questions=test_questions, et=et, st=st,
                               start_time=start_time, end_time=end_time)
    return 'Test not found'


@app.route('/successfull_submition', methods=['GET', 'POST'])
def successfull_submition():
    # Retrieve values from URL parameters
    test_details = request.args.getlist('test_details')
    test_details_str = test_details[0]
    test_details_dict = eval(test_details_str)
    test_id = test_details_dict.get('test_id')

    check_id = db.result.find_one({'test_id': test_id})

    student_id = request.args.get('student_id')
    submitted_answers = request.args.getlist('submitted_answers')
    correct_answer = request.args.getlist('correct_answer')
    l = len(submitted_answers)
    score = set(submitted_answers).intersection(correct_answer)
    if check_id is None:
        res = {}

        res[student_id] = len(score)

        db.result.insert_one({
            'test_id': test_id,
            'student_data': res
        })
    else:
        # Retrieve 'student_data' from the found document or initialize as an empty dictionary if not present
        res = check_id.get('student_data', {})
        res[student_id] = len(score)

        # Update the existing document in the collection with the modified 'student_data'
        db.result.update_one(
            {'test_id': test_id},
            {'$set': {'student_data': res}}
        )

    return redirect(url_for('result', test_id=test_id, student_id=student_id, test_details=test_details))


@app.route('/submit_test/<test_id>/<Studemail>', methods=['GET', 'POST'])
def submit_test(test_id,Studemail):
    if request.method == 'POST':
        # Retrieve the submitted test details from the database based on specified fields
        test_details = db.test.find_one({'test_id': test_id})

        if test_details is None:
            return 'Test details not found'  # Handle case when no matching document is found

        # Ensure 'questions' field exists in test_details or assign an empty list as a default value
        questions = test_details.get('questions', [])
        n = len(questions)

        correct_answer = []
        for i in range(0, n):
            single_question = questions[i]
            ans = single_question.get('answer')
            correct_answer.append(ans)

        selected_answers = []

        for i in range(1, n + 1):
            selected_option_key = f'correct_option_{i}'
            selected_option_value = request.form.get(selected_option_key)
            selected_answers.append(selected_option_value)

        # Retrieve the existing document from the collection based on test_id
        existing_submission = db.submitted_answers_collection.find_one({
            'test_id': test_id})
        user_email = Studemail
        if existing_submission is None:
            # If no existing document is found, create a new one
            new_submission = {
                'test_id': test_id,
                'answers': {
                    user_email: selected_answers
                }
            }
            db.submitted_answers_collection.insert_one(new_submission)
        else:
            # If an existing document is found, update it
            existing_answers = existing_submission.get('answers', {})
            existing_answers[user_email] = selected_answers

            db.submitted_answers_collection.update_one(
                {'test_id': test_id},
                {'$set': {'answers': existing_answers}}
            )

        return redirect(url_for('successfull_submition', test_details=test_details,
                                student_id=Studemail, submitted_answers=selected_answers,
                                correct_answer=correct_answer))

    return 'Invalid request method'


@app.route('/submit_test_para/<test_id>', methods=['GET', 'POST'])
def submit_test_para(test_id):
    if request.method == 'POST':
        # Retrieve the submitted test details from the database based on specified fields
        test_details = db.test_paragraph.find_one({'test_id': test_id})

        if test_details is None:
            return 'Test details not found'  # Handle case when no matching document is found

        # Ensure 'questions' field exists in test_details or assign an empty list as a default value
        questions = test_details.get('questions', [])
        n = len(questions)

        para_answers = []

        for i in range(1, n + 1):
            para_answers_key = f'answer_{i}'
            para_answers_value = request.form.get(para_answers_key)
            para_answers.append(para_answers_value)

        # Retrieve the existing document from the collection based on test_id
        existing_submission = db.submitted_answers_collection_para.find_one({'test_id': test_id})

        if existing_submission is None:
            # If no existing document is found, create a new one
            new_submission = {
                'test_id': test_id,
                'answers': {
                    session.get('user').get('email'): para_answers
                }
            }
            db.submitted_answers_collection_para.insert_one(
                new_submission)
        else:
            # If an existing document is found, update it
            existing_answers = existing_submission.get('answers', {})
            existing_answers[session.get('user').get('email')] = para_answers

            db.submitted_answers_collection_para.update_one(
                {'test_id': test_id},
                {'$set': {'answers': existing_answers}}
            )
        return redirect(url_for('home'))

    return 'Invalid request method'


@app.route('/para_ans')
def para_ans():
    temail = session.get('user').get('email')
    res = list(db.test_paragraph.find({'teacher_email': temail}))
    return render_template('html/test_to_be_checked.html', tests=res)


@app.route('/result', methods=['GET', 'POST'])
def result():
    test_details = request.args.getlist('test_details')
    test_details_str = test_details[0]
    test_details_dict = eval(test_details_str)
    test_id = test_details_dict.get('test_id')
    Stud_email = request.args.getlist('student_id')
    # Assuming 'marks' is a field in the 'test_details'
    marks = test_details_dict.get('marks')
    # Assuming 'subject' is a field in the 'test_details'
    subject = test_details_dict.get('subject')

    check_var = db.result.find_one({'test_id': test_id})
    if check_var is None:
        jsonify_message = "Test details not found"
        return render_template('html/result.html', jsonify_message=jsonify_message)
    else:
        student_data = check_var.get('student_data', {})
        student_id = Stud_email[0]
        print(f"Student Email : {Stud_email}")
        if student_id in student_data:
            value = student_data[student_id]
            return render_template('html/result.html', test_id=test_id, score=value, marks=marks, subject=subject,
                                   student_id=student_id)
        else:
            jsonify_message = "Test not given"
            return render_template('html/result.html', jsonify_message=jsonify_message)


@app.route('/stu_attempted_tests/<test_id>', methods=['GET', 'POST'])
def stu_attempted_tests(test_id):
    check = db.submitted_answers_collection_para.find_one(
        {'test_id': test_id})

    if check is None:
        return 'No one has given the test'
    ans = check.get('answers', [])
    stud_email = []
    for i in ans:
        stud_email.append(i)

    answer_details = db.student_score_para.find_one({'test_id': test_id})
    if answer_details is None:
        return render_template('html/answer_checking.html', test_id=test_id, stud_email=stud_email)
    else:
        submitted_answer_student_id = answer_details.get('student_data', [])
        email_to_rem = submitted_answer_student_id.keys()
        stud_email = [
            email for email in stud_email if email not in email_to_rem]
    return render_template('html/answer_checking.html', test_id=test_id, stud_email=stud_email)


@app.route('/check_answer/<test_id>/<student_email>', methods=['GET', 'POST'])
def check_answer(test_id, student_email):
    # Retrieve the submitted answers for the specified test and student
    submission = db.submitted_answers_collection_para.find_one({
        'test_id': test_id})

    if submission:
        answers = submission.get('answers', {})
        student_answers = answers.get(student_email, [])

        # Retrieve the questions for the specified test from the test_paragraph collection
        test_paragraph = db.test_paragraph.find_one({'test_id': test_id})

        if test_paragraph:
            questions = test_paragraph.get('questions', [])
            # Add logic here to render a page with the student's answers and questions for the teacher to check
            return render_template('html/teacher_check_answer.html', test_id=test_id, student_email=student_email,
                                   student_answers=student_answers, questions=questions)

    return 'No submission found for the specified test and student.'


@app.route('/submit_scores/<test_id>/<student_email>', methods=['POST'])
def submit_scores(test_id, student_email):
    if request.method == 'POST':
        # Retrieve scores from the form submission
        scores = [int(score) for score in request.form.getlist(
            'scores') if score is not None]

        # Calculate total score
        total_score = sum(scores)

        check_id = db.student_score_para.find_one({'test_id': test_id})

        if check_id is None:
            res = {}

            res[student_email] = total_score

            db.student_score_para.insert_one({
                'test_id': test_id,
                'student_data': res
            })
        else:
            # Retrieve 'student_data' from the found document or initialize as an empty dictionary if not present
            res = check_id.get('student_data', {})
            res[student_email] = total_score

            # Update the existing document in the collection with the modified 'student_data'
            db.student_score_para.update_one(
                {'test_id': test_id},
                {'$set': {'student_data': res}}
            )
        return redirect(url_for('stu_attempted_tests', test_id=test_id))
    return 'Invalid request method'


@app.route('/score', methods=['GET', 'POST'])
def score():
    temail = session.get('user').get('email')
    mcq_test = list(db.test.find({'teacher_email': temail}))
    para_test = list(db.test_paragraph.find({'teacher_email': temail}))
    return render_template('html/scores.html', mcq_test=mcq_test, para_test=para_test)


@app.route('/mcq_stud_score/<test_id>', methods=['GET', 'POST'])
def mcq_stud_score(test_id):
    # Assuming you have already imported necessary modules and set up your Flask app

    # Fetch test details from the result collection
    test_details = db.result.find_one({'test_id': test_id})
    student_data = test_details.get('student_data', [])

    # Extract student email addresses and scores
    student_email = list(student_data.keys())

    # Fetch user details for each student using their email addresses
    students_details = []
    for email in student_email:
        user_details = db.users.find_one({'email': email})
        if user_details:
            student_details = {
                'name': user_details.get('name', ''),
                'rollno': user_details.get('rollno', ''),
                'email': email,
                'score': student_data[email]  # Assuming scores are stored as-is in the result
            }
            students_details.append(student_details)

    return render_template('html/stud_score.html', students_details=students_details,test_id=test_id)


@app.route('/get_student_data/<test_id>', methods=['POST'])
def get_student_data(test_id):
    try:
        rollno = request.form.get('rollno')

        # Fetch test details from the result collection
        test_details = db.result.find_one({'test_id': test_id})  # Replace '1' with the actual test_id
        if test_details is None:
            test_details = db.student_score_para.find_one({'test_id': test_id})
        student_data = test_details.get('student_data', {})

        # Fetch user details for the specified roll number
        user_details = db.users.find_one({'rollno': rollno})

        if user_details:
            student_data_for_rollno = student_data.get(user_details.get('email', ''), 0)
            student_data = {
                'name': user_details.get('name', ''),
                'rollno': rollno,
                'email': user_details.get('email', ''),
                'score': student_data_for_rollno
            }
            return jsonify(student_data)
        else:
            return jsonify({'error': 'Student not found'})
    except Exception as e:
        print(f"Error in get_student_data route: {str(e)}")
        return jsonify({'error': 'Internal Server Error'})


@app.route('/para_stud_score/<test_id>', methods=['GET', 'POST'])
def para_stud_score(test_id):
    test_details = db.student_score_para.find_one({'test_id': test_id})
    student_data = test_details.get('student_data', [])

    student_email = list(student_data.keys())

    students_details = []
    for email in student_email:
        user_details = db.users.find_one({'email': email})
        if user_details:
            student_details = {
                'name': user_details.get('name', ''),
                'rollno': user_details.get('rollno', ''),
                'email': email,
                'score': student_data[email]
            }
            students_details.append(student_details)

    return render_template('html/stud_score.html', students_details=students_details,test_id=test_id)

@app.route('/edit_stud_data',  methods=['GET', 'POST'])
def edit_stud_data():
    students = list(db.users.find().sort('department', 1))
    return render_template('html/edit_stud_data.html', students=students)


@app.route('/edit_student', methods=['POST'])
def edit_student():
    # Get data from the JSON request
    data = request.get_json()
    email = data.get('email')
    name = data.get('name')
    year = data.get('year')
    rollno = data.get('rollno')
    password = data.get('password')

    # Update the student data in the MongoDB collection
    db.users.update_one({'email': email}, {'$set': {'name': name, 'year': year, 'rollno': rollno, 'password': password}})

    return jsonify({"message": "Student data updated successfully!"})

@app.route('/delete_student', methods=['POST'])
def delete_student():
    # Get data from the JSON request
    data = request.get_json()
    email = data.get('email')

    # Delete the student data from the MongoDB collection
    db.users.delete_one({'email': email})

    return jsonify({"message": "Student data deleted successfully!"})

@app.route('/filter_by_department/<department>', methods=['GET'])
def filter_by_department(department):
    if department == 'all':
        students = list(db.users.find())
    else:
        students = list(db.users.find({'department': department}))

    return render_template('html/edit_stud_data.html', students=students)

@app.route('/clickPhotos',methods=['GET', 'POST'])
def clickPhotos():
    
    Id = db.users.find_one({'email': session.get('user').get('email')}, {'unique_id': 1})['unique_id'] if session.get('user') else None
    sampleNum=0
    while(True):
        ret, img = cam.read()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)
        for (x,y,w,h) in faces:
            cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2)
            
            #saving the captured face in the dataset folder
            cv2.imwrite("static/uploads/studImg/User."+ str(Id) +'.'+ str(sampleNum) + ".jpg", gray[y:y+h,x:x+w])
            sampleNum=sampleNum+1
            cv2.imshow('frame',img)
        # break if the sample number is morethan 20
        if sampleNum>60:
            break
    cam.release()
    cv2.destroyAllWindows()
    
    return redirect(url_for('profile'))

@app.route('/trainModel',methods=['GET', 'POST'])
def trainModel():
    recognizer=cv2.face.LBPHFaceRecognizer_create()
    path='static/uploads/studImg/'
    def getImagesWithID(path):
        imagePaths=[os.path.join(path,f) for f in os.listdir(path)]
        faces=[]
        IDs=[]

        for imagepath in imagePaths:
            faceImg=Image.open(imagepath).convert('L')
            faceNp=np.array(faceImg,'uint8')
            print(imagepath)
            ID=int(os.path.split(imagepath)[-1].split(".")[1])
            #dataset/User.1.3
            faces.append(faceNp)
            IDs.append(ID)
            cv2.imshow("training",faceNp)
            cv2.waitKey(10)
        return np.array(IDs),faces

    Ids,faces=getImagesWithID(path)
    recognizer.train(faces,Ids)
    recognizer.save('trainingData.yml')
    cv2.destroyAllWindows()

    return redirect(url_for('teacherDashboard'))

@app.route('/close_tab',methods=['GET', 'POST'])
def close_tab():
    pyautogui.click(x=100, y=100)
    pyautogui.hotkey('ctrl', 'w')
    print('Exam tab closed successfully')
    return render_template('html/login.html')

if __name__ == '__main__':
    app.run(port=5001)
