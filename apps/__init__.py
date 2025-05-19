# import os

# from flask import Flask, send_from_directory
# from flask_login import LoginManager
# from flask_pymongo import PyMongo
# from flask_pymongo import MongoClient
# from importlib import import_module
# from celery import Celery, Task
# from dotenv import load_dotenv
# from apps.config import Config
# from flask import Flask
# from flask_jwt_extended import JWTManager
# from apps.authentication.routes import blueprint as auth_blueprint
# from flask import Flask
# from .config import Config
# from .extensions import mongo, login_manager, jwt
# from .authentication.routes import blueprint as auth_blueprint

# load_dotenv()

# app = Flask(__name__)
# app.config["MONGO_URI"] = os.getenv("MONGO_URI")
# mongo = PyMongo(app)
# login_manager = LoginManager()

# def register_extensions(app):
#     mongo.init_app(app)
#     login_manager.init_app(app)

# def register_blueprints(app):
#     for module_name in ('authentication', 'home', ):
#         module = import_module('apps.{}.routes'.format(module_name))
#         app.register_blueprint(module.blueprint)

# def configure_database(app):
#     global mongo

#     mongo = PyMongo(app)

#     @app.before_first_request
#     def initialize_database():
#         try:
#             mongo.db.command("ping")
#         except Exception as e:
#             print('> Error: DBMS Exception: ' + str(e))

#     @app.teardown_request
#     def shutdown_session(exception=None):
#         pass 


# def celery_init_app(app: Flask) -> Celery:
#     class FlaskTask(Task):
#         def __call__(self, *args: object, **kwargs: object) -> object:
#             with app.app_context():
#                 return self.run(*args, **kwargs)

#     celery_app = Celery(app.name, task_cls=FlaskTask)
#     celery_app.config_from_object(app.config["CELERY"])
#     celery_app.set_default()
#     app.extensions["celery"] = celery_app
#     return celery_app


# def create_app(config):
#     # Read debug flag
#     DEBUG = (os.getenv('DEBUG', 'False') == 'True')

#     # Contextual
#     static_prefix = '/static' if DEBUG else '/'

#     app = Flask(__name__,static_url_path=static_prefix)
    
#     @app.route('/media/<path:filename>')
#     def media_files(filename):
#         return send_from_directory(Config.MEDIA_FOLDER, filename)

#     app.config.from_mapping(
#         CELERY=dict(
#             broker_url="redis://localhost",
#             result_backend="redis://localhost",
#             task_ignore_result=True,
#         ),
#     )
#     app.config['MONGO_URI'] = os.getenv("MONGO_URI")
#     celery_init_app(app)

#     app.config.from_object(config)
#     register_extensions(app)
#     register_blueprints(app)
#     configure_database(app)

#     return app
# def create_app():
#     app = Flask(__name__)
#     app.config.from_object(Config)

#     # Init extensions
#     mongo.init_app(app)
#     login_manager.init_app(app)
#     jwt.init_app(app)

#     # Register blueprints
#     app.register_blueprint(auth_blueprint)

#     return app

from flask import Flask, send_from_directory
from importlib import import_module
from .extensions import mongo, login_manager, jwt
from .config import Config
from .authentication.routes import blueprint as auth_blueprint
from dotenv import load_dotenv
from celery import Celery, Task

load_dotenv()

def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    app.extensions["celery"] = celery_app
    return celery_app

def register_extensions(app):
    mongo.init_app(app)
    print("Mongo DB object:", mongo.db)
    login_manager.init_app(app)
    jwt.init_app(app)

def register_blueprints(app):
    for module_name in ('authentication', 'home', ):
        module = import_module(f'apps.{module_name}.routes')
        app.register_blueprint(module.blueprint)

def configure_database(app):
    @app.before_first_request
    def initialize_database():
        try:
            mongo.db.command("ping")
        except Exception as e:
            print('> Error: DBMS Exception: ' + str(e))

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config.from_mapping(
        CELERY=dict(
            broker_url="redis://localhost",
            result_backend="redis://localhost",
            task_ignore_result=True,
        )
    )

    register_extensions(app)
    register_blueprints(app)
    configure_database(app)
    celery_init_app(app)

    return app
