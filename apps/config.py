import os, random, string

class Config(object):

    basedir = os.path.abspath(os.path.dirname(__file__))

    # Set up the App SECRET_KEY
    SECRET_KEY  = os.getenv('SECRET_KEY', None)
    if not SECRET_KEY:
        SECRET_KEY = ''.join(random.choice( string.ascii_lowercase  ) for i in range( 32 ))

    MONGO_URI = os.getenv('MONGO_URI', None)

    CELERY_SCRIPTS_DIR        = os.path.join(basedir, "tasks_scripts")
    CELERY_LOGS_URL           = "/tasks_logs/"
    CELERY_LOGS_DIR           = os.path.join(basedir, "tasks_logs")

    MEDIA_FOLDER = os.path.join(basedir, "media")
    PROFILE_FOLDER = os.path.join(basedir, "static", "dist", "img") #! New Change : Note This is placeholder as this folder will be not included in git track. Need new central pic folder.

    if not MONGO_URI:
        print('> Error: MongoDB URI is not set')

class ProductionConfig(Config):
    DEBUG = False

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600

class DebugConfig(Config):
    DEBUG = True

# Load all possible configurations
config_dict = {
    'Production': ProductionConfig,
    'Debug'     : DebugConfig
}