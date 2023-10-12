from flask import Flask, render_template, url_for, request, session, redirect
from flask_pymongo import PyMongo

app = Flask(__name__)

# Set a secret key
app.secret_key = 'IT2023@'  # Replace with a unique and secret key

# Rest of your code
app.config['MONGO_DBNAME'] = 'IT'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/IT'

mongo = PyMongo(app)

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
            if user_type == 'student':
                return redirect(url_for('home'))
            elif user_type == 'teacher':
                return redirect(url_for('teacherDashoard'))
    
    return 'Invalid email or password combination'


@app.route('/signUp', methods=['POST', 'GET'])
def signUp():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'email': request.form['email']})
        
        if existing_user is None:
            new_user = {
                'name': request.form['username'],
                'email': request.form['email'],
                'password': request.form['password'],
                'year': request.form['year'],
                'department': request.form['department'],
                'rollno': request.form['rollno']
            }
            users.insert_one(new_user)
            return redirect(url_for('index'))
    
    return 'User with this email already exists.'

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

if __name__ == "__main__":
    app.run(debug=True)
