from flask import Blueprint, render_template, session, request, redirect, url_for,send_from_directory
from flask_mail import Message
import secrets
from bson import ObjectId

from . import mongo, mail 

bp = Blueprint('main', __name__)

@bp.route("/")
def index():
    return render_template('html/login.html')


# @bp.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@bp.route('/logout')
def logout():
    if 'user' in session:
        session.pop('user')  # Clear the user session if 'user' exists
    return redirect(url_for('main.index'))


@bp.route('/home')
def home():
        upcoming_test = list(mongo.db.test.find())
        submitted_answers = list(mongo.db.submitted_answers_collection.find({}, {'answers': 1,'test_id':1, '_id': 0}))
        upcoming_test_ids = list(mongo.db.test.find({},{'test_id':1,'_id':0}))
        
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
    
        upcoming_test = [test for test in upcoming_test if test.get('test_id') not in ids_toremove]
        return render_template('html/index.html', upcoming_tests=upcoming_test)


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
                                    if(j==login_user['email']):
                                        ids_toremove.append(res)
                
                    upcoming_test = [test for test in upcoming_test if test.get('test_id') not in ids_toremove]
                    return render_template('html/index.html', upcoming_tests=upcoming_test)

            elif user_type == 'teacher':
                return redirect(url_for('main.teacherDashboard'))
            else:
                return 'Your email is not verified. Please check your email for a verification link.'

    return 'Invalid email or password combination'

@bp.route('/register', methods=['POST', 'GET'])
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
    selected_option = request.form.get('radiobutton_name')
    
    if request.method == 'POST':    
        qCount = int(request.form.get('count', 0))
        
        if selected_option=="mcq":
            return render_template('html/question_addition.html', qCount=qCount)
        else:
            return render_template('html/paragraph.html', qCount=qCount)


@bp.route('/create_test', methods=['GET', 'POST'])
def create_test():
    if request.method == 'POST':
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
                    # Append the question dictionary to the list
                    questions.append(question)

        # Create the new_test dictionary with the list of questions
        new_test = {
            'test_id': request.form['test_id'],
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

# @bp.route('/attempt_test')
# def attempt_test():
#     return render_template('html/attempt_test.html')

@bp.route('/attempt_test/<test_id>')
def attempt_test(test_id):
    # Fetch the specific test using the test_id from the database
    # test = mongo.db.test.find_one({'_id': ObjectId(test_subject)})  # Assuming '_id' is the ObjectId of the test

    test = mongo.db.test.find_one(
        {
            'test_id': test_id
        }
    )

    if test:
        # Assuming 'questions' is the key for the questions in the test document
        test_questions = test.get('questions', [])

        # Render the attempt test page with the test details and questions
        return render_template('html/attempt_test.html', test=test, questions=test_questions)

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

        for i in range(1, n + 1):
            answer_key = f'answer_{i}'
            correct_answer.append(request.form.get(answer_key))

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


@bp.route('/result', methods=['GET', 'POST'])
def result():
    test_details = request.args.getlist('test_details')
    test_details_str = test_details[0]
    test_details_dict = eval(test_details_str)
    print(test_details_dict)
    test_id = test_details_dict.get('test_id')
    print(test_id)
    marks = test_details_dict.get('marks')  # Assuming 'marks' is a field in the 'test_details'
    subject = test_details_dict.get('subject')  # Assuming 'subject' is a field in the 'test_details'
    
    check_var = mongo.db.result.find_one({'test_id': test_id})
    print(check_var)
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