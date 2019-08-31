from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
#from data import Articles
from flask_sqlalchemy import SQLAlchemy
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import datetime

app = Flask(__name__)

#Articles = Articles()

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
    register_date = db.Column(db.DateTime())

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


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/articles')
def articles():
    result = db.session.query(Article).all()
    if len(result) == 0:
        msg = 'No Article Found'
        return render_template('articles.html', msg=msg)
    else:
        return render_template('articles.html', articles=result)


@app.route('/article/<string:id>')
def article(id):
    article = db.session.query(Article).filter(Article.id==id).first()
    return render_template('article.html', article=article)


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
        else:
            flash('You are already registered', 'warning')
            return redirect(url_for('register'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        user = db.session.query(User).filter(User.username == username).first()
        if user is None:
            error = 'Invalid login'
            app.logger.info('NO USER')
            return render_template('login.html', error = error)
        else:
            password = user.password
            if sha256_crypt.verify(password_candidate, password):
                app.logger.info('PASSWORD MATCHED')
                session['logged_in'] = True
                session['username'] = username
                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                app.logger.info('PASSWORD NOT MATCHED')
                error = 'Invalid login'
                return render_template('login.html', error = error)
    return render_template('login.html')

## Check user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@is_logged_in
def dashboard():
    result = db.session.query(Article).all()
    if len(result) == 0:
        msg = 'No Article Found'
        return render_template('dashboard.html', msg=msg)
    else:
        return render_template('dashboard.html', articles=result)


class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    author = db.Column(db.String(100))
    body = db.Column(db.Text())
    create_date = db.Column(db.DateTime())

    def __init__(self, title, author, body, create_date):
        self.title = title
        self.author = author
        self.body = body
        self.create_date = create_date


class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])


@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        data = Article(title, session['username'], body, datetime.datetime.now())
        db.session.add(data)
        db.session.commit()
        flash('Article created', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form = form)


@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    article = db.session.query(Article).filter(Article.id == id).one()

    form = ArticleForm(request.form)

    form.title.data = article.title
    form.body.data = article.body

    if request.method == 'POST' and form.validate():
        article.title = request.form['title']
        article.body = request.form['body']

        db.session.commit()
        flash('Article updated', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_article.html', form = form)


if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'secret123'
    app.run()
