

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField,HiddenField
from wtforms.validators import DataRequired

# login and registration


class LoginForm(FlaskForm):
    username = StringField('Username', id='username_login', validators=[DataRequired()])
    password = PasswordField('Password', id='pwd_login', validators=[DataRequired()])


class CreateAccountForm(FlaskForm):
    username = StringField('Username', id='username_create', validators=[DataRequired()])
    firstname = StringField('Firstname', id='firstname_create', validators=[DataRequired()])
    lastname = StringField('Lastname', id='lastname_create', validators=[DataRequired()])
    password = PasswordField('Password', id='pwd_create', validators=[DataRequired()])
    role = HiddenField('Role', id='role_hidden', validators=[DataRequired()])


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', id='current_pwd', validators=[DataRequired()])
    new_password1 = PasswordField('New Password', id='new_pwd1', validators=[DataRequired()])
    new_password2 = PasswordField('Re-Type New Password', id='new_pwd2', validators=[DataRequired()])