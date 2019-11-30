from flask import Flask
from flask_pymongo import PyMongo
from flask_mongoengine import MongoEngine
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import os


from flaskwebgui import FlaskUI #get the FlaskUI class

app = Flask(__name__)

#ui = FlaskUI(app)

app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'

#app.config["MONGO_URI"] = "mongodb://localhost:27017/FailureDB"
app.config["MONGO_URI"] = os.environ['db_cred']

mongo = PyMongo(app)
bcrypt =  Bcrypt(app)
login_manager = LoginManager(app)

login_manager.login_view = 'login'  #function name of route
login_manager.login_message_category = 'info'


from flaskblog import routes
