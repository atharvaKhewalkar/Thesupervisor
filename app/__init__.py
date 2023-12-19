# app/__init__.py
from flask import Flask
from flask_mail import Mail
from flask_pymongo import PyMongo

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

from app.views import bp  # Import the Blueprint

app.register_blueprint(bp, url_prefix='/')  # Register the Blueprint with a prefix

if __name__ == "__main__":
    app.run(debug=True)
