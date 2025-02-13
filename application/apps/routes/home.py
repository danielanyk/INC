from flask import Blueprint, render_template

# Create a Blueprint for organizing routes
home_blueprint = Blueprint('home', __name__)

@home_blueprint.route('/home')
def home():
    return render_template('home.html')