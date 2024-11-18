from flask_login import UserMixin
from apps import login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson import ObjectId
client = MongoClient("mongodb://localhost:27017/FYP")
db = client["FYP"]
class Users(UserMixin):
    def __init__(self, **kwargs):
        self.username = kwargs.get('username')
        self.name = kwargs.get('name')
        self.password_hash = kwargs.get('password_hash')
        self._id = kwargs.get('_id')
        self.perm = "Admin"

    def save(self):
        user_data = {
            'username': self.username,
            'name': self.name,
            'password_hash': self.password_hash,
            "perm": self.perm
        }
        db.users.insert_one(user_data)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @classmethod
    def get_by_username(cls, username):
        user_data = db.users.find_one({'username': username})
        if user_data:
            return cls(**user_data)
        return None

    @classmethod
    def get_by_id(cls, user_id):
        user_data = db.users.find_one({'_id': ObjectId(user_id)})
        if user_data:
            return cls(**user_data)
        return None
    
    def get_id(self):
        return str(self._id) if self._id else None
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = Users.get_by_username(username)
    return user if user else None

@login_manager.user_loader
def user_loader(user_id):
    return Users.get_by_id(user_id)

class Role():
    ADMIN = 1
    USER = 2

    def __str__(self):
        return str(self.value)


class Profile:

    @staticmethod
    def find_by_id(_id):
        profile = db.profiles.find_one({'_id': _id})
        if profile:
            return Profile(**profile)
        return None

    @staticmethod
    def find_by_user_id(user_id):
        profile = db.profiles.find_one({'user_id': user_id})
        if profile:
            return Profile(**profile)
        return None

    @staticmethod
    def create_profile_for_user(user_id): 
        return db.profiles.insert_one({'user_id': user_id})

