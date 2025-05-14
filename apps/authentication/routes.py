
import os
from flask import render_template, redirect, request, url_for, flash, jsonify
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

    #! New Change : Load images from the profile pictures folder
    image_folder = os.path.join(Config.PROFILE_FOLDER)
    if os.path.exists(image_folder):
        images = [f'dist/img/{file}' for file in os.listdir(image_folder) if file.endswith(('png', 'jpg', 'jpeg', 'gif'))]
    else:
        images = []

    if request.method == 'POST':
        update_fields = {f"{attribute}": value for attribute, value in request.form.items()}
        db.users.update_one({"_id": ObjectId(current_user._id)}, {"$set": update_fields})
        
    context['segment'] = 'profile'
    context['profile'] = profile

    context['images'] = images  #! New Change : Pass images to the template

    return render_template('accounts/profile.html', **context)

#! Can use this function if want to add the ability to upload profile image from outside
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@blueprint.route('/update_profile_picture', methods=['POST'])
@login_required
def update_profile_picture():
    """Update the user's profile picture in MongoDB."""

    try:
        data = request.get_json()
        selected_image = data.get('image')  # Image path sent via AJAX

        if not selected_image:
            return jsonify({'error': 'No image provided'}), 400

        if selected_image:
            # Extract just the filename from the image path
            image_name = os.path.basename(selected_image)

            # Update MongoDB with the selected image name
            db.users.update_one(
                {"_id": ObjectId(current_user._id)},
                {"$set": {"avatar": image_name}}
            )
            return jsonify({"status": "success", "message": "Profile picture updated successfully"}), 200

        return jsonify({"status": "error", "message": "No image selected"}), 400
    except Exception as e:
        return jsonify ({'error': str(e)}), 500

### Change here for account permission
@blueprint.route('/change-account-permission', methods=['POST', 'GET'])
@login_required
def change_account_permission():
    """Handles changes to account permissions for the logged-in user."""
    current_user_id = current_user._id
    current_user_perm = current_user.get_user_perm()

    # Ensure the current user has a valid ID
    if not current_user_id:
        flash("Unable to identify the user. Please try again.", "danger")
        return redirect(url_for('authentication_blueprint.profile'))

    if request.method == 'POST':
        # Fetch form data
        new_permission = request.form.get('perm')

        # Check if the permission level has changed
        if new_permission == current_user_perm:
            flash("No changes made. Permission level remains the same.", "info")
            return redirect(url_for('authentication_blueprint.profile'))

        # Validation: Ensure new permission level is provided
        if not new_permission:
            flash("Permission level is required.", "danger")
            return redirect(url_for('authentication_blueprint.profile'))

        # Fetch the current user from the database
        user = Users.get_by_id(current_user_id)
        if not user:
            flash("User not found.", "danger")
            return redirect(url_for('authentication_blueprint.profile'))

        # Update and save the user's permission
        user.perm = new_permission
        user.save()

        flash(f"Permission updated to '{new_permission}' for user '{user.username}'.", "success")
        return redirect(url_for('authentication_blueprint.profile'))

    # Redirect for non-POST requests
    return redirect(url_for('authentication_blueprint.profile'))

### Change here for password error
@blueprint.route('/change-password', methods=['POST', 'GET']) #! New Change
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']

        if not current_password or not new_password: #! New Change
            flash('Please fill in all fields.', 'danger')
            return redirect(url_for('authentication_blueprint.profile'))

        user = Users.get_by_username(current_user.username) #! New Change

        if user and user.check_password(current_password):
            # Update the password using set_password
            user.set_password(new_password)
        
            # Save the updated user data
            user.save()

            flash('Password updated successfully!', 'success')
            return redirect(url_for('authentication_blueprint.profile'))
        else:
            flash('Incorrect current password. Please try again.', 'danger')
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