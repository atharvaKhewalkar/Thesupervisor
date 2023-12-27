from flask import Blueprint, render_template, session, request, redirect, url_for,send_from_directory
from flask_mail import Message
import secrets
from bson import ObjectId
import os
from werkzeug.utils import secure_filename
from . import app 
from . import mongo, mail 

bp = Blueprint('main', __name__)

@bp.route("/")
def index():
    return render_template('html/login.html')

@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@bp.app_errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500


# @bp.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploads/<path:filename>')
def download_file(filename):
    return send_from_directory("uploads", filename)


@bp.route('/logout')
def logout():
    if 'user' in session:
        session.pop('user')  # Clear the user session if 'user' exists
    return redirect(url_for('main.index'))


@bp.route('/profile')
def profile():
    # Check if the user is logged in
    if 'user' in session:
        # Get the email of the logged-in user
        email = session['user']['email']

        # Fetch student details from the users collection based on the email
        student_details = mongo.db.users.find_one({'email': email})

        # Fetch scores for attempted tests
        mcq_scores = list(mongo.db.result.find())
        mcq_scores_para=list(mongo.db.student_score_para.find())
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
                test_details.append(mongo.db.test.find_one({'test_id':test_id}))
                test_scores.append(stu_score)
                
        for score in mcq_scores_para:
            stud_data = score.get('student_data', {})
            test_id = score.get('test_id', '')

            # Check if the logged-in user has attempted the test
            if email in stud_data:
                stu_score = stud_data[email]
                test_details.append(mongo.db.test_paragraph.find_one({'test_id':test_id}))
                test_scores.append(stu_score)

        if student_details:
            # Pass student details, test IDs, and test scores to the template
            return render_template('html/stud_profile.html', student_details=student_details, test_details=test_details, test_scores=test_scores)
        else:
            return 'Student details not found'
    else:
        return redirect(url_for('main.index'))


    
@bp.route('/edit_profile', methods=['POST'])
def edit_profile():
    if 'user' in session:
        email = session['user']['email']
        users_collection = mongo.db.users

        # Fetch user details from the collection based on email
        user_details = users_collection.find_one({'email': email})

        if user_details:
            # Update user details based on the submitted form
            user_details['name'] = request.form.get('name')
            # Repeat similar lines for other details like email, year, department, etc.

            # Update the document in the collection
            users_collection.update_one({'email': email}, {'$set': user_details})

            # Redirect to the profile page after updating
            return redirect(url_for('main.profile'))
        else:
            return 'User details not found'
    else:
        return redirect(url_for('main.index'))
    


@bp.route('/home')
def home():
        upcoming_test = list(mongo.db.test.find())
        submitted_answers = list(mongo.db.submitted_answers_collection.find({}, {'answers': 1,'test_id':1, '_id': 0}))
        upcoming_test_ids = list(mongo.db.test.find({},{'test_id':1,'_id':0}))

        upcoming_test_para = list(mongo.db.test_paragraph.find())
        submitted_answers_para = list(mongo.db.submitted_answers_collection_para.find({}, {'answers': 1,'test_id':1, '_id': 0}))
        upcoming_test_ids_para = list(mongo.db.test_paragraph.find({},{'test_id':1,'_id':0}))
        
        ids_toremove=[]
        for test in upcoming_test_ids:
            id=test['test_id']
            keys_from_answers = []
            for i in submitted_answers:
                res=i['test_id']
                if(id==res):
                    ans=i['answers']
                    keys_from_answers.extend(ans.keys())
                    temp=keys_from_answers
                    for j in temp:
                        if(j==session.get('user').get('email')):
                            ids_toremove.append(res)
        
        ids_toremove_para=[]
        for test in upcoming_test_ids_para:
            id_para=test['test_id']
            keys_from_answers_para = []
            for i in submitted_answers_para:
                res_para=i['test_id']
                if(id_para==res_para):
                    ans_para=i['answers']
                    keys_from_answers_para.extend(ans_para.keys())
                    temp_para=keys_from_answers_para
                    for j in temp_para:
                        if(j==session.get('user').get('email')):
                            ids_toremove_para.append(res_para)
    
        upcoming_test = [test for test in upcoming_test if test.get('test_id') not in ids_toremove]
        upcoming_test_para = [test for test in upcoming_test_para if test.get('test_id') not in ids_toremove_para]

        return render_template('html/index.html', upcoming_tests=upcoming_test,upcoming_test_para=upcoming_test_para)


@bp.route('/test')
def test():
    return render_template('html/test.html')


@bp.route('/login', methods=['POST'])
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
                # Store user data in the session
                session['user'] = {
                    'name': login_user['name'],
                    'email': login_user['email'],
                    'rollno': login_user['rollno'],
                    'department': login_user['department'],
                }

                if user_type == 'student':
                    upcoming_test = list(mongo.db.test.find())
                    submitted_answers = list(mongo.db.submitted_answers_collection.find({}, {'answers': 1,'test_id':1, '_id': 0}))
                    upcoming_test_ids = list(mongo.db.test.find({},{'test_id':1,'_id':0}))

                    upcoming_test_para = list(mongo.db.test_paragraph.find())
                    submitted_answers_para = list(mongo.db.submitted_answers_collection_para.find({}, {'answers': 1,'test_id':1, '_id': 0}))
                    upcoming_test_ids_para = list(mongo.db.test_paragraph.find({},{'test_id':1,'_id':0}))
                    
                    ids_toremove=[]
                    for test in upcoming_test_ids:
                        id=test['test_id']
                        keys_from_answers = []
                        for i in submitted_answers:
                            res=i['test_id']
                            if(id==res):
                                ans=i['answers']
                                keys_from_answers.extend(ans.keys())
                                temp=keys_from_answers
                                for j in temp:
                                    if(j==session.get('user').get('email')):
                                        ids_toremove.append(res)
                    
                    ids_toremove_para=[]
                    for test in upcoming_test_ids_para:
                        id_para=test['test_id']
                        keys_from_answers_para = []
                        for i in submitted_answers_para:
                            res_para=i['test_id']
                            if(id_para==res_para):
                                ans_para=i['answers']
                                keys_from_answers_para.extend(ans_para.keys())
                                temp_para=keys_from_answers_para
                                for j in temp_para:
                                    if(j==session.get('user').get('email')):
                                        ids_toremove_para.append(res_para)
                
                    upcoming_test = [test for test in upcoming_test if test.get('test_id') not in ids_toremove]
                    upcoming_test_para = [test for test in upcoming_test_para if test.get('test_id') not in ids_toremove_para]

                    return render_template('html/index.html', upcoming_tests=upcoming_test,upcoming_test_para=upcoming_test_para)

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
                        return redirect(url_for('main.teacherDashboard'))
                        
                return 'Invalid email or password combination'
            else:
                return 'Your email is not verified. Please check your email for a verification link.'

    return 'Invalid email or password combination'

@bp.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'email': request.form['email']})

        if existing_user is None:
            # Handle file upload
            file = request.files['file']
            if file and allowed_file(file.filename):
                # Generate a secure filename based on the student name
                filename = secure_filename(request.form['username'] + '.jpg')
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

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
                'profile_image': filename  # Save the filename in the database
            }
            users.insert_one(new_user)

            msg = Message('Email Verification', sender='riteshphadtare32@gmail.com',
                          recipients=[request.form['email']])
            msg.body = f"Please click on the following link to verify your email: {url_for('main.verify_email', token=token, _external=True)}"
            mail.send(msg)

            return 'Please check your email to verify your account.'

    return 'User with this email already exists.'



@bp.route('/verify_email/<token>', methods=['GET'])
def verify_email(token):
    users = mongo.db.users
    user = users.find_one({'token': token})

    if user:
        # Mark the user as verified and remove the token
        users.update_one({'_id': user['_id']}, {
                         '$set': {'verified': True}, '$unset': {'token': 1}})
        return 'Email verification successful. You can now log in.'

    return 'Invalid token or user not found.'


@bp.route('/signUpTeacher', methods=['POST', 'GET'])
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
            return render_template('html/login.html')

    return 'User with this email already exists.'


@bp.route("/teacherLogin")
def teacherLogin():
    return render_template('html/teacherlogin.html')


@bp.route('/teacherDashboard')
def teacherDashboard():
    upcoming_test = list(mongo.db.test.find())
    QUESTION_COUNT = 10  # Set the value according to your requirements
    return render_template('html/teacherDashboard.html', upcoming_tests=upcoming_test, QUESTION_COUNT=QUESTION_COUNT)

@bp.route('/typeofque')
def typeofque():
    return render_template('html/typeOfQues.html')

@bp.route('/questionCount', methods=['GET', 'POST'])
def questionCount():
    qCount = 0  # Provide a default value
    selected_option = request.form.get('que_type')
    
    if request.method == 'POST':    
        qCount = int(request.form.get('count', 0))
        
        if selected_option=="mcq":
            return render_template('html/question_addition.html', qCount=qCount)
        else:
            return render_template('html/paragraph.html', qCount=qCount)


@bp.route('/create_test_mcq', methods=['GET', 'POST'])
def create_test_mcq():
    if request.method == 'POST':
        test_id= request.form['test_id']
        check_id = mongo.db.test.find_one({'test_id': test_id})
        c = int(request.form['que_count'])
        if check_id is None:
            # Create a list to store multiple questions
            questions = []
            # questions.append("null")
            c = int(request.form['que_count'])
            
            # Loop through the form data to get all questions
            for i in range(1, c+1):  # Assuming you want to handle 3 questions, adjust as needed
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
                                # Ensure secure filename to prevent security risks
                                filename = secure_filename(file.filename)
                                # Save the file to the upload folder
                                file_path = f"{test_id}_{file_key}.jpg"
                                # Add the image path to the question dictionary
                                file_save_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{test_id}_{file_key}.jpg")
                                file.save(file_save_path)
                                question['image_path'] = file_path
                        # Append the question dictionary to the list
                        questions.append(question)

            # Create the new_test dictionary with the list of questions
            new_test = {
                'test_id': test_id,
                'subject': request.form['test_sub_name'],
                'description': request.form['test_description'],
                'marks': request.form['test_marks'],
                'time': request.form['test_time'],
                'test_date': request.form['test_date'],
                'questions': questions  # Use 'questions' instead of 'question'
            }

            # Insert the new_test document into the database
            mongo.db.test.insert_one(new_test)

            return redirect(url_for('main.teacherDashboard'))
        else:
            return render_template('html/question_addition.html', qCount=c, test_id_exists=True)
    
@bp.route('/create_test_paragraph', methods=['GET', 'POST'])
def create_test_paragraph():
    if request.method == 'POST':
        test_id= request.form['test_id']
        check_id = mongo.db.test_paragraph.find_one({'test_id': test_id})
        c = int(request.form['que_count'])
        if check_id is None:
            questions = []

            c = int(request.form['que_count'])
            test_id=request.form['test_id']
            for i in range(1, c+1):  # Assuming you want to handle 3 questions, adjust as needed
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
                                # Ensure secure filename to prevent security risks
                                filename = secure_filename(file.filename)
                                # Save the file to the upload folder
                                file_path = f"{test_id}_{file_key}.jpg"
                                # Add the image path to the question dictionary
                                file_save_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{test_id}_{file_key}.jpg")
                                file.save(file_save_path)
                                question['image_path'] = file_path
                        questions.append(question)

            # Create the new_test dictionary with the list of questions
            new_test = {
                'test_id': request.form['test_id'],
                'subject': request.form['test_sub_name'],
                'description': request.form['test_description'],
                'marks': request.form['test_marks'],
                'time': request.form['test_time'],
                'test_date': request.form['test_date'],
                'teacher_email':session.get('user').get('email'),
                'questions': questions
            }

            # Insert the new_test document into the database
            mongo.db.test_paragraph.insert_one(new_test)

            return redirect(url_for('main.teacherDashboard'))
        else:
            return render_template('html/question_addition.html', qCount=c, test_id_exists=True)
    

@bp.route('/attempt_test/<test_id>')
def attempt_test(test_id):
    test = mongo.db.test.find_one(
        {
            'test_id': test_id
        }
    )
    if test:
        test_questions = test.get('questions', [])
        return render_template('html/attempt_test.html', test=test, questions=test_questions)
    return 'Test not found'


@bp.route('/attempt_test_para/<test_id>')
def attempt_test_para(test_id):
    test = mongo.db.test_paragraph.find_one(
        {
            'test_id': test_id
        }
    )
    if test:
        test_questions = test.get('questions', [])
        return render_template('html/attempt_test_paragraph.html', test=test, questions=test_questions)
    return 'Test not found'


@bp.route('/successfull_submition', methods=['GET', 'POST'])
def successfull_submition():
    # Retrieve values from URL parameters
    test_details = request.args.getlist('test_details')
    test_details_str = test_details[0]
    test_details_dict = eval(test_details_str)
    test_id = test_details_dict.get('test_id')
    
    check_id=mongo.db.result.find_one({'test_id':test_id})


    student_id = request.args.get('student_id')
    submitted_answers = request.args.getlist('submitted_answers')
    correct_answer = request.args.getlist('correct_answer')
    l = len(submitted_answers)
    score = set(submitted_answers).intersection(correct_answer)
    if check_id is None:
        res={}
        
        res[student_id]=len(score)
        
        mongo.db.result.insert_one({
            'test_id': test_id,
            'student_data': res
        })
    else:
        res = check_id.get('student_data', {})  # Retrieve 'student_data' from the found document or initialize as an empty dictionary if not present
        res[student_id] = len(score)

        # Update the existing document in the collection with the modified 'student_data'
        mongo.db.result.update_one(
        {'test_id': test_id},
        {'$set': {'student_data': res}}
        )
        

    return redirect(url_for('main.result',test_id=test_id,student_id=student_id,test_details=test_details))


@bp.route('/submit_test/<test_id>', methods=['GET', 'POST'])
def submit_test(test_id):
    if request.method == 'POST':
        # Retrieve the submitted test details from the database based on specified fields
        test_details = mongo.db.test.find_one({'test_id': test_id})

        if test_details is None:
            return 'Test details not found'  # Handle case when no matching document is found

        # Ensure 'questions' field exists in test_details or assign an empty list as a default value
        questions = test_details.get('questions', [])
        n = len(questions)

        correct_answer = []
        for i in range(0, n):
            single_question=questions[i]
            ans=single_question.get('answer')
            correct_answer.append(ans)
            
        
        selected_answers = []

        for i in range(1, n + 1):
            selected_option_key = f'correct_option_{i}'
            selected_option_value = request.form.get(selected_option_key)
            selected_answers.append(selected_option_value)

        # Retrieve the existing document from the collection based on test_id
        existing_submission = mongo.db.submitted_answers_collection.find_one({'test_id': test_id})

        if existing_submission is None:
            # If no existing document is found, create a new one
            new_submission = {
                'test_id': test_id,
                'answers': {
                    session.get('user').get('email'): selected_answers
                }
            }
            mongo.db.submitted_answers_collection.insert_one(new_submission)
        else:
            # If an existing document is found, update it
            existing_answers = existing_submission.get('answers', {})
            existing_answers[session.get('user').get('email')] = selected_answers

            mongo.db.submitted_answers_collection.update_one(
                {'test_id': test_id},
                {'$set': {'answers': existing_answers}}
            )

        return redirect(url_for('main.successfull_submition', test_details=test_details, student_id=session.get('user').get('email'), submitted_answers=selected_answers, correct_answer=correct_answer))

    return 'Invalid request method'

@bp.route('/submit_test_para/<test_id>', methods=['GET', 'POST'])
def submit_test_para(test_id):
    if request.method == 'POST':
        # Retrieve the submitted test details from the database based on specified fields
        test_details = mongo.db.test_paragraph.find_one({'test_id': test_id})

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
        existing_submission = mongo.db.submitted_answers_collection_para.find_one({'test_id': test_id})

        if existing_submission is None:
            # If no existing document is found, create a new one
            new_submission = {
                'test_id': test_id,
                'answers': {
                    session.get('user').get('email'): para_answers
                }
            }
            mongo.db.submitted_answers_collection_para.insert_one(new_submission)
        else:
            # If an existing document is found, update it
            existing_answers = existing_submission.get('answers', {})
            existing_answers[session.get('user').get('email')] = para_answers

            mongo.db.submitted_answers_collection_para.update_one(
                {'test_id': test_id},
                {'$set': {'answers': existing_answers}}
            )
        return redirect(url_for('main.home'))

    return 'Invalid request method'

@bp.route('/para_ans')
def para_ans():
    temail=session.get('user').get('email')
    res=list(mongo.db.test_paragraph.find({'teacher_email':temail}))
    return render_template('html/test_to_be_checked.html',tests=res)
    
    
@bp.route('/result', methods=['GET', 'POST'])
def result():
    test_details = request.args.getlist('test_details')
    test_details_str = test_details[0]
    test_details_dict = eval(test_details_str)
    test_id = test_details_dict.get('test_id')
    marks = test_details_dict.get('marks')  # Assuming 'marks' is a field in the 'test_details'
    subject = test_details_dict.get('subject')  # Assuming 'subject' is a field in the 'test_details'
    
    check_var = mongo.db.result.find_one({'test_id': test_id})
    if check_var is None:
        return "Test details not found"
    else:
        student_data = check_var.get('student_data', {})
        student_id = session.get('user').get('email')
        
        if student_id in student_data:
            value = student_data[student_id]
            return render_template('html/result.html', test_id=test_id, score=value, marks=marks, subject=subject, student_id=student_id)
        else:
            return "Test not given"
        
@bp.route('/stu_attempted_tests/<test_id>', methods=['GET', 'POST'])
def stu_attempted_tests(test_id):
    check=mongo.db.submitted_answers_collection_para.find_one({'test_id':test_id})
    
    if check is None:
            return 'No one has given the test'
    ans = check.get('answers', [])
    stud_email = []
    for i in ans:
        stud_email.append(i)
    
    answer_details=mongo.db.student_score_para.find_one({'test_id':test_id})
    if answer_details is None:
        return render_template('html/answer_checking.html', test_id=test_id, stud_email=stud_email)
    else:
        submitted_answer_student_id=answer_details.get('student_data',[])
        email_to_rem=submitted_answer_student_id.keys()
        stud_email = [email for email in stud_email if email not in email_to_rem]
    return render_template('html/answer_checking.html', test_id=test_id, stud_email=stud_email)


@bp.route('/check_answer/<test_id>/<student_email>', methods=['GET', 'POST'])
def check_answer(test_id, student_email):
    # Retrieve the submitted answers for the specified test and student
    submission = mongo.db.submitted_answers_collection_para.find_one({'test_id': test_id})
    
    if submission:
        answers = submission.get('answers', {})
        student_answers = answers.get(student_email, [])

        # Retrieve the questions for the specified test from the test_paragraph collection
        test_paragraph = mongo.db.test_paragraph.find_one({'test_id': test_id})

        if test_paragraph:
            questions = test_paragraph.get('questions', [])
            # Add logic here to render a page with the student's answers and questions for the teacher to check
            return render_template('html/teacher_check_answer.html', test_id=test_id, student_email=student_email, student_answers=student_answers, questions=questions)
        
    return 'No submission found for the specified test and student.'


@bp.route('/submit_scores/<test_id>/<student_email>', methods=['POST'])
def submit_scores(test_id, student_email):
    if request.method == 'POST':
        try:
            # Retrieve scores from the form submission
            scores = [int(score) for score in request.form.getlist('scores') if score is not None]

            # Calculate total score
            total_score = sum(scores)

            check_id = mongo.db.student_score_para.find_one({'test_id': test_id})

            if check_id is None:
                res = {student_email: total_score}

                mongo.db.student_score_para.insert_one({
                    'test_id': test_id,
                    'student_data': res
                })
            else:
                res = check_id.get('student_data', {})
                res[student_email] = total_score

                mongo.db.student_score_para.update_one(
                    {'test_id': test_id},
                    {'$set': {'student_data': res}}
                )
                
            flash('Scores submitted successfully', 'success')
            return redirect(url_for('main.stu_attempted_tests', test_id=test_id))
        except ValueError:
            flash('Invalid score input. Please enter numeric values only.', 'error')
            return redirect(url_for('main.stu_attempted_tests', test_id=test_id))

    return 'Invalid request method'