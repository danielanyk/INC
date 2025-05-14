from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_jwt_extended import JWTManager

mongo = PyMongo()
login_manager = LoginManager()
jwt = JWTManager()
# authentication.py
