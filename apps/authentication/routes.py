
import os
from flask import render_template, redirect, request, url_for
from flask_login import (
    current_user,
    login_user,
    logout_user,
    login_required
)
from werkzeug.utils import secure_filename
from apps import mongo, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm, ChangePasswordForm
from apps.authentication.models import Users, Profile
from apps.config import Config
from pymongo import MongoClient
from apps.authentication.util import verify_pass, hash_pass
from bson import ObjectId

# @blueprint.route('/')
# def route_default():
#     return redirect(url_for('authentication_blueprint.login'))


# Login & Registration

client = MongoClient("mongodb://localhost:27017/FYP")
db = client["FYP"]

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    if request.method == 'POST' and 'login' in request.form:
        # Read form data
        username = request.form['username']
        password = request.form['password']

        # Locate user
        user = Users.get_by_username(username)

        # Check the password
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('home_blueprint.index'))

        # Something (user or pass) is not ok
        return render_template('accounts/login.html',
                               msg='Wrong user or password',
                               form=login_form)

    if not current_user.is_authenticated:
        return render_template('accounts/login.html',
                               form=login_form)
    return redirect(url_for('home_blueprint.index'))


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    create_account_form = CreateAccountForm(request.form)
    if request.method == 'POST' and 'register' in request.form:
        username = request.form['username']
        name = request.form['name']

        # Check if username or email already exists
        if Users.get_by_username(username):
            return render_template('accounts/register.html',
                                   msg='Username',
                                   success=False,
                                   form=create_account_form)

        # Create a new user
        user = Users(
            username=username,
            name=name,
            password_hash=None
        )
        user.set_password(request.form['password'])
        user.save()
        # Log out the current user (if any)
        logout_user()

        # Log in the new user
        login_user(user)

        return redirect(url_for('home_blueprint.index'))

    return render_template('accounts/register.html', form=create_account_form)

@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('authentication_blueprint.login'))


@blueprint.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    context = {}
    profile = Users.get_by_id(current_user._id)
    if request.method == 'POST':
        update_fields = {f"{attribute}": value for attribute, value in request.form.items()}
        db.users.update_one({"_id": ObjectId(current_user._id)}, {"$set": update_fields})
        
    context['segment'] = 'profile'
    context['profile'] = profile
    return render_template('accounts/profile.html', **context)


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@blueprint.route('/profile-image/', methods=['POST'])
@login_required
def update_profile_image():
    profile = Profile.find_by_user_id(current_user.id)

    if 'avatar' not in request.files:
        return redirect(url_for('authentication_blueprint.profile'))

    file = request.files['avatar']

    if file.filename == '':
        return redirect(url_for('authentication_blueprint.profile'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(Config.MEDIA_FOLDER, filename))

        profile.avatar = filename
        db.session.commit()

        return redirect(url_for('authentication_blueprint.profile'))

    return redirect(url_for('authentication_blueprint.profile'))



@blueprint.route('/change-password', methods=['POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']

        user = Users.query.filter_by(username=current_user.username).first()

        if user and verify_pass(current_password, user.password):
            current_user.password = hash_pass(new_password)
            db.session.commit()
            return redirect(url_for('authentication_blueprint.profile'))
        else:
            return redirect(url_for('authentication_blueprint.profile'))
    else:
        return redirect(url_for('authentication_blueprint.profile'))

# Errors

@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for('authentication_blueprint.login'))
    # return render_template('pages/page-403.html'), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return redirect(url_for('authentication_blueprint.login'))
    # return render_template('pages/page-403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return redirect(url_for('authentication_blueprint.login'))
    # return render_template('pages/page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return redirect(url_for('authentication_blueprint.login'))
    # return render_template('pages/page-500.html'), 500


# custom filter
@blueprint.app_template_filter('default_if_none')
def default_if_none(value):
    return value if value else ""