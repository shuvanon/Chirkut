from flask import (Flask, g,render_template, flash, redirect, url_for, abort,send_from_directory,request)
from flask.ext.bcrypt import check_password_hash
from flask.ext.login import LoginManager, login_user,logout_user,login_required,current_user
from werkzeug import secure_filename
import os

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
    g.user = current_user


@app.after_request
def after_request(response):
    """Close the database connection after each request."""
    g.db.close()
    return response


app.config['UPLOAD_FOLDER'] = 'uploads/'

app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']



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
        
        

@app.route('/login', methods=('GET','POST'))
def login():
    form =forms.LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.email ==form.email.data)
        except models.DoesNotExist:
            flash("Your email or password does not match!***", "error")
        else:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("You've been logged in!", "success")
                return redirect(url_for('index'))
            else:
                flash("Your email or password does not match!", "error")
    return    render_template('login.html', form=form)
        
 
@app.route('/logout')
@login_required
def logout():
   logout_user()
   flash ("You've been logged out! Come back soon!", "success")
   return redirect(url_for('index'))
 
 
@app.route('/new_post', methods=['GET', 'POST'])
@login_required
def post():
    form = forms.PostForm()
    if form.validate_on_submit():
        models.Post.create(user=g.user._get_current_object(),
                           content=form.content.data.strip())
        flash("Message posted: Thanks!", "success")
        return redirect(url_for('index'))
    return render_template('post.html', form=form)

@app.route('/new_upload/', methods=['GET', 'POST'])
@login_required
def upload_file():

    if request.method == 'POST':
        file = request.files['file']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            models.File.create(user=g.user._get_current_object(),
                           path=("/uploads/"+ filename))
            flash("File uploaded: Thanks!", "success")
            return redirect(url_for('filestream'))
    
    return render_template('upload.html')
        
@app.route('/index')
@login_required
def index():
    stream = models.Post.select().limit(100)
    return render_template('stream.html', stream=stream)

@app.route('/stream')
@app.route('/stream/<username>')
def stream(username=None):
    template = 'stream.html'
    if username and username != current_user.username:
        try:
            user = models.User.select().where(models.User.username**username).get() # the ** is the "like" operator (non-case sensitive comparison)
        except models.DoesNotExist:
            abort(404)
        else:    
            stream = user.posts.limit(100)
    else:
        stream = current_user.get_stream().limit(100)
        user = current_user
    if username:
        template = 'user_stream.html'
    return render_template(template, stream=stream, user=user)

@app.route('/allfile')
@login_required
def allfile():
    fileStream = models.File.select().limit(100)
    return render_template('filestream.html', filestream=fileStream)

@app.route('/filestream')
#@app.route('/filestream/<username>')
def filestream(username=None):
    template = 'fileStream.html'
    if username and username != current_user.username:
        try:
            user = models.User.select().where(models.User.username**username).get() # the ** is the "like" operator (non-case sensitive comparison)
        except models.DoesNotExist:
            abort(404)
        else:        
            filestream = user.files.limit(100)
    else:
        filestream = current_user.get_filestream().limit(100)
        user = current_user
    #if username:
        #template = 'user_stream.html'
    return render_template(template, filestream=filestream, user=user)


@app.route('/post/<int:post_id>')
def view_post(post_id):
    posts=models.Post.select().where(models.Post.id == post_id)
    if posts.count()==0:
        abort(404)
    return render_template('stream.html', stream=posts)

@app.route('/uploads/<int:file_id>')
def view_file(file_id):
    files=models.File.select().where(models.File.id == file_id)
    if files.count()==0:
        abort(404)
    return render_template('filestream1.html', stream=files)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    #render_template('filestream.html', filestream=send_from_directory(app.config['UPLOAD_FOLDER'],
      #                         filename))
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


@app.route('/follow/<username>')
@login_required
def follow(username):
    try:
        to_user=models.User.get(models.User.username**username)
    except models.DoesNotExist:
        abort(404)
    else:
        try:
            models.Relationship.create(
                from_user=g.user._get_current_object(),
                to_user=to_user
            )
        except models.IntegrityError:
            pass
        else:
            flash("You are now following {}!".format(to_user.username), "success")
    return redirect(url_for('stream', username=to_user.username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    try:
        to_user=models.User.get(models.User.username**username)
    except models.DoesNotExist:
        abort(404)
    else:
        try:
            models.Relationship.get(
                from_user=g.user._get_current_object(),
                to_user=to_user
            ).delete_instance()
        except models.IntegrityError:
            pass
        else:
            flash("you have unfollowed {}!".format(to_user.username), "success")
    return redirect(url_for('stream', username=to_user.username))



@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

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
