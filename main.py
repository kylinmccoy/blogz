from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:password@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'klcajpvpuoub89apd'


class Post(db.Model):

    post_keyid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    archived = db.Column(db.Boolean)
    post_heading = db.Column(db.String(50))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, name, heading, owner):
        self.name = name
        self.archived = False
        self.post_heading = heading
        self.owner = owner

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    posts = db.relationship('Post', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password

def is_integer(num):
    try: 
        int(num)
        return True
    except ValueError:
        return False

@app.before_request
def require_login():
    #allowed_routes = ['login', 'signup', 'blog', 'onepost', 'oneuser', 'allposts', 'index']
    disallowed_routes = ['logout', 'newpost']
    if((request.endpoint in disallowed_routes) and ('username' not in session)):
        return redirect('/login')

@app.route('/allposts', methods=['POST', 'GET'])
def postlist():

    if request.method == 'POST':
        post_name = request.form['blog_post']
        post_header = request.form['post_heading']
        new_post = Post(post_name, post_header)

        db.session.add(new_post)
        db.session.commit()

    posts = Post.query.filter_by(archived=False).all()
    archived_posts = Post.query.filter_by(archived=True).all()
    return render_template('blog.html', title="Build a Blog", 
        posts=posts, archived_posts=archived_posts)

@app.route('/', methods=['POST', 'GET'])
def index():

    users = User.query.all()
    return render_template('home.html', title="Blogz", 
        users=users)

@app.route('/blog', methods=['GET', 'POST'])
def blog_posts():
    posts = Post.query.filter_by(archived=False).all()
    archived_posts = Post.query.filter_by(archived=True).all()
    return render_template('blog.html', title="Build a Blog Posts", 
        posts=posts, archived_posts=archived_posts)

@app.route('/newpost', methods=['GET', 'POST'])
def newpost():
    warning = ""
    post_heading=""
    new_post=""
    if request.method == 'POST':
        post_name = request.form['blog_post']
        post_header = request.form['post_heading']
        owner = User.query.filter_by(username=session['username']).first()
        if post_name and post_header:
            new_post = Post(post_name, post_header, owner)
            db.session.add(new_post)
            db.session.commit()
            return redirect('/onepost?onepostid='+str(new_post.post_keyid))
        else:
            warning="Make sure to enter both post text and a header"
            new_post=post_name
            post_heading=post_header

    posts = Post.query.filter_by(archived=False).all()
    return render_template('newpost.html', title="New Post Submission",
        posts=posts, warning=warning, post_heading=post_heading, new_post=new_post)


@app.route("/archive-post", methods=['POST'])
def archive_post():
     
    post_keyid = int(request.form['post-id'])
    post = Post.query.get(post_keyid)
    post.archived = True
    db.session.add(post)
    db.session.commit()

    return redirect('/')

@app.route("/onepost", methods=['POST', 'GET'])
def show_a_post():
    post = Post.query.filter_by(post_keyid=request.args.get('onepostid')).first()
    return render_template('onepost.html', title="This Blog",
        post=post)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['username'] = username
            flash("Logged in")
            return redirect('/newpost')
        elif user:
            session['loginwarn'] = 'Invalid Password'
            return render_template('login.html', loginwarn="Incorrect Password")
        elif username and not user:
            session['loginwarn'] = 'Invalid Username'
            return render_template('login.html', loginwarn="Username does not exist")
        else:
            return render_template('login.html', loginwarn="Login Failed")

    return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    return render_template('signup.html')

@app.route('/signupsend', methods=['POST', 'GET'])
def signupsend():
    username = request.form['username']
    password = request.form['password']
    re_password = request.form['verify']

    username_error = ''
    password_error = ''
    re_password_error = ''
    email_error = ''

    if not username:
        username_error = 'Missing username'
        username = '' 
    else:
        username = username
        if len(username) > 20 or len(username) < 3:
            username_error = 'Username length out of range (3-20)'
            username = ''
         
    if not password:
        password_error = 'Missing password'
        password = '' 
    else:
        password = password
        if len(password) > 20 or len(password) < 3:
            password_error = 'Password length out of range (3-20)'
            password = ''

    if not password_error:
        if password != re_password:
            re_password_error = 'Passwords do not match'
            re_password = ''

    if request.method == 'POST':
        if not password_error and not username_error and not re_password_error:
            session['username']=username
            existing_user = User.query.filter_by(username=session['username']).first()
            if not existing_user:
                new_user = User(username, password)
                db.session.add(new_user)
                db.session.commit()
                session['username'] = username
                return redirect('/newpost')
            else:
                username_error="Existing username"
                return render_template("signup.html", 
                    username_error=username_error, 
                    password_error=password_error,
                    re_password_error=re_password_error,
                    username=username,
                    password='',
                    re_password='',
                    title = "User Signup")
        else:
            return render_template("signup.html", 
                username_error=username_error, 
                password_error=password_error,
                re_password_error=re_password_error,
                username=username,
                password='',
                re_password='',
                title = "User Signup")

    return render_template('signup.html')

@app.route('/logout', methods=['POST'])
def logout():
    del session['username']
    flash("Logged out")
    return redirect('/blog')

@app.route('/oneuser')
def show_a_blog():
    posts = Post.query.filter_by(owner_id=request.args.get('user_id')).all()
    return render_template('blog.html', title="This Blog",
        posts=posts)

if __name__ == '__main__':
    app.run()