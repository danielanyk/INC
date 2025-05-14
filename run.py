
# import logging
# import os
# from flask_migrate import Migrate
# from flask_minify import Minify
# from apps.config import Config
# from sys import exit
# from flask import jsonify, request
# from apps.config import config_dict
# from apps import create_app, mongo
# from celery import Celery, Task
# from flask_restful import Resource, Api
# from apps.home.models import Product
# import json
# from apps import create_app

# # logging.basicConfig(level=logging.DEBUG,
# #                     format='%(asctime)s %(levelname)s %(message)s',
# #                     handlers=[
# #                         logging.FileHandler("app.log"),
# #                         logging.StreamHandler()
# #                     ])

# logger = logging.getLogger(__name__)


# app = create_app()

# if __name__ == "__main__":
#     app.run(debug=True)
# try:
#     db = mongo.db
#     DEBUG = (os.getenv('DEBUG', 'False') == 'True')
#     get_config_mode = 'Debug' if DEBUG else 'Production'

#     try:
#         app_config = config_dict[get_config_mode.capitalize()]
#     except KeyError:
#         logger.error('Invalid <config_mode>. Expected values [Debug, Production]')
#         exit('Error: Invalid <config_mode>. Expected values [Debug, Production] ')

#     app = create_app(app_config)
#     celery_app = app.extensions["celery"]
#     api = Api(app)


#     class ProductAPI(Resource):
#         def get(self):
#             products = Product.get_json_list()
#             return products

#     api.add_resource(ProductAPI, '/api/product/')

#     if not DEBUG:
#         Minify(app=app, html=True, js=False, cssless=False)

#     if DEBUG:
#         app.logger.setLevel(logging.DEBUG)
#         app.logger.debug('DEBUG            = ' + str(DEBUG))
#         app.logger.debug('Page Compression = ' + ('FALSE' if DEBUG else 'TRUE'))
#         app.logger.debug('DBMS             = ' + app_config.MONGO_URI)

#     # class RequestFilter(logging.Filter):
#     #     def filter(self, record):
#     #         return "GET /batchStatus/" not in record.getMessage() and "GET /update_image_table/" not in record.getMessage()

#     # app.logger.addFilter(RequestFilter())

#     @app.route('/shutdown', methods=['POST'])
#     def shutdown():
#         func = request.environ.get('werkzeug.server.shutdown')
#         if func is None:
#             raise RuntimeError('Not running with the Werkzeug Server')
#         func()
#         return 'Server shutting down...'

#     def clear_processed_videos():
#         with open(Config.BLACK_PROCESSED_VIDEOS, "w") as file:
#             json.dump([], file, indent=4)

#     if __name__ == "__main__":
#         logger.debug('Starting the Flask application...')
#         clear_processed_videos()
#         app.run(host='0.0.0.0', port=5000)

# except ImportError as e:
#     logger.error('ImportError encountered', exc_info=True)
#     exit(1)
# except Exception as e:
#     logger.error('Unhandled exception', exc_info=True)
#     exit(1)


import logging
import os
import json
from flask import request
from flask_minify import Minify
from flask_restful import Resource, Api
from apps.config import config_dict, Config
from apps import create_app
from apps.home.models import Product

logger = logging.getLogger(__name__)

DEBUG = (os.getenv('DEBUG', 'False') == 'True')
get_config_mode = 'Debug' if DEBUG else 'Production'

try:
    app_config = config_dict[get_config_mode.capitalize()]
except KeyError:
    logger.error('Invalid <config_mode>. Expected values [Debug, Production]')
    exit(1)
app = create_app(app_config)



api = Api(app)


class ProductAPI(Resource):
    def get(self):
        products = Product.get_json_list()
        return products

api.add_resource(ProductAPI, '/api/product/')

if not DEBUG:
    Minify(app=app, html=True, js=False, cssless=False)

if DEBUG:
    app.logger.setLevel(logging.DEBUG)
    app.logger.debug('DEBUG            = ' + str(DEBUG))
    app.logger.debug('Page Compression = ' + ('FALSE' if DEBUG else 'TRUE'))
    app.logger.debug('DBMS             = ' + app_config.MONGO_URI)

@app.route('/shutdown', methods=['POST'])
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'

def clear_processed_videos():
    with open(Config.BLACK_PROCESSED_VIDEOS, "w") as file:
        json.dump([], file, indent=4)

if __name__ == "__main__":
    logger.debug('Starting the Flask application...')
    clear_processed_videos()
    app.run(host='0.0.0.0', port=5000)
