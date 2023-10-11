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
    users = mongo.db.users
    login_user = users.find_one({'email': request.form['email']})

    if login_user:
        if request.form['password'] == login_user['password']:
            return redirect(url_for('home'))
    
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
                'password': request.form['password']
            }
            users.insert_one(new_user)  # Use insert_one here
            return redirect(url_for('index'))

    return 'User with this email already exists.'

@app.route("/teacherLogin")
def teacherLogin():
    return render_template('teacherlogin.html')

if __name__ == "__main__":
    app.run(debug=True)
