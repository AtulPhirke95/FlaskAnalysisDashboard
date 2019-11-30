from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo,ValidationError
from flaskblog import mongo
from flask_login import LoginManager, current_user

class RegistrationForm(FlaskForm):
    #username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        if mongo.db.regUser.find({"email_id":email.data}).count()>0:
            raise ValidationError('Email ID is already exists')

class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    #remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class ForgotPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                        validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset')


class UpdateAccountForm(FlaskForm):
    #username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Update')

##    def validate_email(self, email):
##        if email.data == current_user.username:
##            if mongo.db.regUser.find({"email_id":email.data}).count()>0:
##                raise ValidationError('Email ID is already exists')
            
class AdminAccountForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

##    def validate_email(self, email):
##        if email.data != "admin":
##            raise ValidationError('Enter valild credential for email id field to log in to admin dashboard')


class UpdateUserEmailFormByAdmin(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Update')

    def validate_email(self, email):
        if mongo.db.regUser.find({"email_id":email.data}).count()>0:
            raise ValidationError('Email ID is already exists')

class UpdateUserPasswordFormByAdmin(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Update')

    def validate_password(self, password):
        if mongo.db.regUser.find({"password":password.data}).count()>0:
            raise ValidationError('Enter different password')
