from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
import json
from datetime import datetime
from flask_mail import Mail
import os
from werkzeug.utils import secure_filename
import math

with open('config.json','r') as c:
    params=json.load(c)['params']

local_server=True
app = Flask(__name__)
app.secret_key='super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail=Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db=SQLAlchemy(app)


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20),  nullable=False)
    phone_num= db.Column(db.String(12),  nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    tagline = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(20),  nullable=False)
    content= db.Column(db.String(120),  nullable=False)
    img_file = db.Column(db.String(12), nullable=True)
    date = db.Column(db.String(12), nullable=True)



@app.route("/")
def home():

    posts = Posts.query.filter_by().all()
    last=math.ceil(len(posts)/int(params['no-of-post']))
    page=request.args.get('page')
    if(not str(page).isnumeric()):
        page=1
    page=int(page)
    posts = posts[(page-1)*int(params['no-of-post']):(page-1)*int(params['no-of-post'])+ int(params['no-of-post'])]
    if page==1:
        prev="#"
        next="/?page="+str(page+1)
    elif page==last:
        prev="/?page="+str(page-1)
        next="#"
    else:
        prev="/?page="+str(page-1)
        next="/?page="+str(page+1)

    return render_template("index.html",params=params,posts=posts,next=next,prev=prev)

@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post=Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params,post=post)


@app.route("/about")
def about():
    return render_template("about.html",params=params)

@app.route("/dashboard",methods=['GET','POST'])
def dashboard():

    if ('user' in session and session['user'] == params['admin_user']):
        post = Posts.query.all()
        return render_template("dashboard.html",params=params,post=post)

    if request.method=='POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if(username == params['admin_user'] and userpass==params['admin_password']):
            session['user'] = username
            post=Posts.query.all()
            return render_template('dashboard.html',params=params,post=post)
    return render_template('login.html',params=params)

@app.route("/edit/<string:sno>", methods=['GET','POST'])
def edit(sno):
    if('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            title=request.form.get('title')
            tline=request.form.get('tline')
            slug=request.form.get('slug')
            content=request.form.get('content')
            img_file=request.form.get('img_file')
            date=datetime.now()

            if sno == '0':
                post=Posts(title=title,tagline=tline,slug=slug,content=content,img_file=img_file,date=date)
                db.session.add(post)
                db.session.commit()

            else:
                post=Posts.query.filter_by(sno=sno).first()
                post.title=title
                post.tagline=tline
                post.slug=slug
                post.content=content
                post.date=date
                db.session.commit()
                return redirect('/edit/'+sno)

        post=Posts.query.filter_by(sno=sno).first()
        return  render_template('edit.html',params=params,post=post)
@app.route("/delete/<string:sno>", methods=['GET','POST'])
def delete(sno):
    if('user' in session and session['user'] == params['admin_user']):
        post=Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
        return redirect("/dashboard")


@app.route("/uploader",methods=['GET','POST'])
def uploader():
    if('user' in session and session['user']==params['admin_user']):
        if(request.method=='POST'):
            f=request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            return "Uploaded Successfully"


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/contact",methods= ['GET','POST'])
def contact():
    if(request.method=='POST'):
        "Add entry to the database"
        name=request.form.get('name')
        email = request.form.get('email')
        phone=request.form.get('phone')
        message = request.form.get('message')

        entry=Contacts(name=name,email=email,phone_num=phone,msg=message,date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients=[params['gmail-user']],
                          body=message+"\n"+phone
                          )
    return render_template("contact.html",params=params)

app.run(debug=True)