
from flask import Blueprint

blueprint = Blueprint(
    'authentication_blueprint',
    __name__,
    url_prefix=''
)

# from flask import Flask
# from flask_jwt_extended import JWTManager
# # from apps.authentication.routes import blueprint as auth_blueprint

# app = Flask(__name__)
# app.config['JWT_SECRET_KEY'] = 'Ireallyreallyreallywannasleepsleepahhhhh'

# # Initialize JWT with the app
# jwt = JWTManager(app)

# # Register your blueprint
# app.register_blueprint(blueprint)
