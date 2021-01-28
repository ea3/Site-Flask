from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from data import articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
import os
from dotenv import load_dotenv
from functools import wraps


app = Flask(__name__)
mysql = MySQL(app)

# Config mySQL
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')
app.config['MYSQL_CURSORCLASS'] = os.environ.get('MYSQL_CURSORCLASS')
app.secret_key = os.environ.get('SECRET_KEY')

# some_articles = articles()


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/articles')
def articles():
    # Create cursor
    cur = mysql.connection.cursor()
    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles1 = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles1=articles1)
    else:
        msg = 'No Articles Found'
        cur.close()
        return render_template('articles.html', msg=msg)



@app.route('/article/<string:article_id>/')
def article(article_id):
    return render_template('article.html', id=article_id)


class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match'),
    ])
    confirm = PasswordField('Confirm Password')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)",
                    (name, email, username, password))

        # Commit to db
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and ready to go', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

# User login


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form fields
        username = request.form['username']
        password_candidate = request.form['password']

        # create a cursor
        cur = mysql.connection.cursor()

        # Get user by username

        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare the passwords

            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))

            else:
                error = 'Invalid Login'
                return render_template('login.html', error=error)

        # cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)
    return render_template('login.html')


# Check if user is logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap


# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles1 = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles1=articles1)
    else:
        msg = 'No Articles Found'
        cur.close()
        return render_template('dashboard.html', msg=msg)









# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('home'))


# Article form
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=20)])


# Add an article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create cursor

        cur = mysql.connection.cursor()

        # Execute

        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))

        # Commit to db
        mysql.connection.commit()

        # Close
        cur.close()

        flash('Article created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
