from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from data import Articles
from flask_sqlalchemy import SQLAlchemy
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
import datetime

app = Flask(__name__)

Articles = Articles()

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://ktsubaki:@localhost:5432/pythonflaskapp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    username = db.Column(db.String(30))
    password = db.Column(db.String(100))
    email = db.Column(db.String(100))
    register_date = db.Column(db.DateTime)

    def __init__(self, name, username, password, email):
        self.name = name
        self.username = username
        self.password = password
        self.email = email
        self.register_date = datetime.datetime.now()


class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message = 'Password do not match')])
    confirm = PasswordField('Confirm Password')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        email = form.email.data
        if db.session.query(User).filter(User.name == name or User.username == username).count() == 0:
            data = User(name, username, password, email)
            db.session.add(data)
            db.session.commit()
            flash('You are now registered and can login', 'success')
            return redirect(url_for('login'))
        else:
            flash('You are already registered', 'warning')
            return redirect(url_for('register'))

    return render_template('register.html', form=form)

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    return render_template('articles.html', articles = Articles)

@app.route('/article/<string:id>')
def article(id):
    return render_template('article.html', id = id)

if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'secret123'
    app.run()
