import os

from flask import Flask, send_from_directory
from flask_login import LoginManager
from flask_pymongo import PyMongo
from flask_pymongo import MongoClient
from importlib import import_module
from celery import Celery, Task
from dotenv import load_dotenv
from apps.config import Config

load_dotenv()

app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)
login_manager = LoginManager()

def register_extensions(app):
    mongo.init_app(app)
    login_manager.init_app(app)

def register_blueprints(app):
    for module_name in ('authentication', 'home', ):
        module = import_module('apps.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)

def configure_database(app):
    global mongo

    mongo = PyMongo(app)

    @app.before_first_request
    def initialize_database():
        try:
            mongo.db.command("ping")
        except Exception as e:
            print('> Error: DBMS Exception: ' + str(e))

    @app.teardown_request
    def shutdown_session(exception=None):
        pass 


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


def create_app(config):
    # Read debug flag
    DEBUG = (os.getenv('DEBUG', 'False') == 'True')

    # Contextual
    static_prefix = '/static' if DEBUG else '/'

    app = Flask(__name__,static_url_path=static_prefix)

    @app.route('/media/<path:filename>')
    def media_files(filename):
        return send_from_directory(Config.MEDIA_FOLDER, filename)

    app.config.from_mapping(
        CELERY=dict(
            broker_url="redis://localhost",
            result_backend="redis://localhost",
            task_ignore_result=True,
        ),
    )
    app.config['MONGO_URI'] = os.getenv("MONGO_URI")
    celery_init_app(app)

    app.config.from_object(config)
    register_extensions(app)
    register_blueprints(app)
    configure_database(app)

    return app
