from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, DateField, URLField
from wtforms.validators import DataRequired, length
from flask_ckeditor import CKEditor, CKEditorField


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), length(1, 20)])
    password = PasswordField('Password', validators=[DataRequired(), length(8, 150)])
    submit = SubmitField()


class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    email = EmailField('Email')
    password = PasswordField('Password', validators=[DataRequired(), length(8, 20)])
    password_again = PasswordField('Password Again', validators=[DataRequired(), length(8, 20)])
    submit = SubmitField()


class AddPostForm(FlaskForm):
    post_title = StringField(validators=[DataRequired()])
    post_subtitle = StringField(validators=[DataRequired()])
    date = DateField(validators=[DataRequired()])
    body = CKEditorField(validators=[DataRequired()])
    post_img = StringField(validators=[DataRequired()])
    submit = SubmitField()


class Comment_form(FlaskForm):
    text = CKEditorField('Comment', validators=[DataRequired()])
    submit = SubmitField()

