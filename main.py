from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from forms import LoginForm, RegisterForm, AddPostForm, Comment_form
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, Date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, current_user, UserMixin, logout_user
import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SEC_KEY")
bootstrap = Bootstrap5(app)
ckeditor = CKEditor(app)




class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI', 'sqlite:///blog.db')
db = SQLAlchemy(model_class=Base)
db.init_app(app)


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


class User(db.Model, UserMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    posts = relationship('Post', back_populates='author')
    comments = relationship('Comment', back_populates='author')


class Post(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('user.id'))
    title: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    subtitle: Mapped[str] = mapped_column(String)
    date: Mapped[str] = mapped_column(Date, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author = relationship('User', back_populates='posts')
    post_img: Mapped[str] = mapped_column(String)
    comments = relationship('Comment', back_populates='post')


class Comment(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('user.id'))
    post_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('post.id'))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    author = relationship('User', back_populates='comments')
    date: Mapped[str] = mapped_column(Date, nullable=False)
    post = relationship('Post', back_populates='comments')


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    posts = db.session.execute(db.select(Post)).scalars()
    return render_template("index.html", posts=posts, logged_in=current_user.is_authenticated, current_user=current_user)


@app.route("/login", methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        user = db.session.execute(db.select(User).where(User.username == form.username.data)).scalar()
        if not user:
            flash("user name does not exist")
            return redirect(url_for('login'))
        hash_password = user.password
        if check_password_hash(hash_password, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash("wrong password try again")
            return redirect(url_for('login'))


    return render_template("login.html", form=form, logged_in=current_user.is_authenticated)


@app.route("/register", methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            flash("password does not match")
        db_username = db.session.execute(db.select(User).where(User.username == form.username.data))
        if db_username:
            flash("user name is taken, please choose another one!")
        else:
            hashed_password = generate_password_hash(form.password.data, method='scrypt', salt_length=16)
            user = User(
                name=form.name.data,
                username=form.username.data,
                email=form.email.data,
                password=hashed_password
            )

            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('home'))
    return render_template("register.html", form=form, logged_in=current_user.is_authenticated)


@app.route('/add_post', methods=['POST', 'GET'])
@login_required
def add_post():
    form = AddPostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.data.get('post_title'),
            subtitle=form.data.get('post_subtitle'),
            date=form.data.get('date'),
            body=form.data.get('body'),
            post_img=form.post_img.data,
            author=current_user,
        )
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("add_post.html", form=form, logged_in = current_user.is_authenticated)


@app.route('/post/<int:id>', methods=["POST", "GET"])
def post_detail(id):
    form = Comment_form()
    post = db.session.execute(db.select(Post).where(Post.id == id)).scalar()
    if form.validate_on_submit():
        comment = Comment(
            text=form.text.data,
            author=current_user,
            date=datetime.datetime.now(),
            post=post
        )
        db.session.add(comment)
        db.session.commit()
        return redirect(url_for('post_detail', id=post.id))
    return render_template("post.html", post=post, form=form)


@app.route('/edit/<int:id>', methods=['POST', 'GET'])
@login_required
def edit_post(id):
    post = db.session.execute(db.select(Post).where(Post.id == id)).scalar()
    form = AddPostForm(
        post_title=post.title,
        post_subtitle=post.subtitle,
        date=post.date,
        body=post.body,
        post_img=post.post_img
    )
    if form.validate_on_submit():
        post.title = form.post_title.data
        post.subtitle = form.post_subtitle.data
        post.date = form.date.data
        post.body = form.body.data
        post.post_img = form.post_img.data
        db.session.commit()
        return redirect(url_for('post_detail', id=post.id))
    return render_template("edit.html", form=form)


@app.route('/logout')
def log_out():
    logout_user()
    return redirect(url_for('home'))


@app.route('/delete_post/<int:post_id>')
def delete_post(post_id):
    post = db.get_or_404(Post, post_id)
    db.session.execute(db.delete(Comment).where(Comment.post_id == post_id))
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True, port=8000)
