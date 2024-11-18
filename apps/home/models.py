from apps import mongo
from bson.objectid import ObjectId
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db=mongo.db
class Product:

    @staticmethod
    def find_by_id(_id):
        return db.products.find_one({'_id': _id})

    @staticmethod
    def get_list():
        return list(db.products.find())

    @staticmethod
    def to_dict(product):
        return {
            'id': str(product['_id']),
            'name': product['name'],
            'info': product['info'],
            'price': product['price']
        }

    @staticmethod
    def get_json_list():
        products = Product.get_list()
        return [Product.to_dict(product) for product in products]


class StatusChoices:
    PENDING = 'PENDING'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'
    RUNNING = 'RUNNING'

class User(UserMixin):
    def __init__(self, user_id, username, password_hash=None):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash

    @staticmethod
    def validate_login(password_hash, password):
        return check_password_hash(password_hash, password)

    @classmethod
    def get(cls, user_id):
        user_data = db.users.find_one({"_id": ObjectId(user_id)})
        if not user_data:
            return None
        return cls(str(user_data["_id"]), user_data["username"], user_data["password"])

    @classmethod
    def find_by_username(cls, username):
        user_data = db.users.find_one({"username": username})
        if not user_data:
            return None
        return cls(str(user_data["_id"]), user_data["username"], user_data["password"])

    def get_id(self):
        return self.user_id

    @staticmethod
    def hash_password(password):
        return generate_password_hash(password)

    def save_to_mongo(self):
        if not self.password_hash:
            raise ValueError("Password hash missing")
        db.users.insert_one({
            "username": self.username,
            "password": self.password_hash
        })


class TaskResult:

    @staticmethod
    def find_by_id(_id):
        return db.task_results.find_one({'_id': ObjectId(_id)})

    @staticmethod
    def get_list():
        return list(db.task_results.find())

    @staticmethod
    def to_dict(task_result):
        return {
            'id': str(task_result['_id']),
            'task_name': task_result['task_name'],
            'periodic_task_name': task_result['periodic_task_name'],
            'status': task_result['status'],
            'result': task_result['result'],
            'date_created': task_result['date_created'],
            'date_done': task_result['date_done']
        }

    @staticmethod
    def get_json_list():
        task_results = TaskResult.get_list()
        return [TaskResult.to_dict(task_result) for task_result in task_results]

    @staticmethod
    def get_latest():
        try:
            # Attempt to retrieve the first document from the cursor; use `next` to avoid IndexError
            latest_task_result = next(db.task_results.find().sort('_id', -1).limit(1), None)
            if latest_task_result:
                return TaskResult.to_dict(latest_task_result)
            else:
                return None  # Return None or an appropriate response if no document is found
        except Exception as e:
            # Log the exception or handle it as needed
            print(f"An error occurred: {e}")
            return None

    @staticmethod
    def get_all():
        return list(db.task_results.find())