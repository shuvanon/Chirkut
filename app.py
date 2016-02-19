from flask import (Flask, g,render_template, flash, redirect, url_for)
from flask.ext.login import LoginManager

import forms
import models



DEBUG =True
PORT=8000
HOST = '127.0.0.1'

app = Flask(__name__)
app.secret_key = 'abcd.1234.xyz'

login_manager =LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(userid):
    try:
        return models.User.get(models.User.id==userid)
    except models.DoesNotExist:
        return None

@app.before_request
def before_request():
    """Connect to the database before each request."""
    g.db = models.DATABASE
    g.db.connect()


@app.after_request
def after_request(response):
    """Close the database connection after each request."""
    g.db.close()
    return response

@app.route('/register', methods=('GET', 'POST'))
def register():
        form = forms.RegisterForm()
        if form.validate_on_submit():
            flash("Yay, you registered", "success")
            models.User.create_user(
                user_name=form.username.data,
                email=form.email.data,
                password=form.password.data
            )
            return redirect(url_for('index'))
        return render_template('register.html', form=form)
        
        
@app.route('/index')
def index():
    return 'Hey'

if __name__ == '__main__':
    models.initialize()
    try:
        models.User.create_user(
            user_name='shuvanon',
            email='razik666@gmail.com',
            password='123456',
            admin=True
        )
    except ValueError:
        pass
    
    app.run(debug=DEBUG, host=HOST,port=PORT)
