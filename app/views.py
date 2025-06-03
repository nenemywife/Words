from app import app
from flask import render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
from bs4 import BeautifulSoup

from flask_bcrypt import Bcrypt

from config import Config

app.config.from_object(Config)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
    
class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    describe = db.Column(db.Text)
    
    def __init__(self, username, password, describe):
        self.username = username
        self.password = bcrypt.generate_password_hash(password.encode('utf-8')).decode('utf-8')
        self.describe = describe
        
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password.encode("utf-8"), password)
    
class Lesson(db.Model):
    __tablename__ = "lesson"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(80), unique=True, nullable=False)
    describe = db.Column(db.Text, nullable=True, unique=False)
    
    user = db.relationship('User', backref=db.backref('lesson', lazy=True))
    
    def __init__(self, title, describe, user_id):
        self.title = title
        self.describe = describe
        self.user_id = user_id
        
class Word(db.Model):
    __tablename__ = "word"
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    word = db.Column(db.String(80), unique=False, nullable=False)
    typ = db.Column(db.String(15), unique=False, nullable=True)
    definition = db.Column(db.Text, nullable=True, unique=False)
    
    lesson = db.relationship('Lesson', backref=db.backref('word', lazy=True))
    
    def __init__(self, word, typ, definition, lesson_id):
        self.word = word
        self.typ = typ
        self.definition = definition
        self.lesson_id = lesson_id
    
with app.app_context():
    db.create_all()

isLogin = False

@app.route("/")
def index():
    return render_template("index.html", isLogin=isLogin)

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        check_user = User.query.filter_by(username=username).first()
        
        if check_user:
            check_password = check_user.check_password(password)
            if check_password:
                global isLogin
                isLogin = True
                session['username'] = username
                session['password'] = password
                return redirect("/")
            else:
                return render_template("user/login.html", isLogin=isLogin, error="NotCorrect")
        else:
            return render_template("user/login.html", isLogin=isLogin, error="NotExist")
    else:
        return render_template("user/login.html", isLogin=isLogin)
    
@app.route("/sign-up", methods=["POST", "GET"])
def sign_up():
    isUnique = True
    isAuthorize = True
    
    if request.method == "POST":
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        describe = ''
        if len(username) == 0 or len(password) == 0:
            isAuthorize = False
            return render_template("user/sign-up.html", isLogin=isLogin, isUnique=isUnique, isAuthorize=isAuthorize)
        else:
            check_exist = User.query.filter_by(username=username).first()
            if check_exist == None:
                isUnique = True
                new_user = User(username=username, password=password, describe=describe)
                db.session.add(new_user)
                db.session.commit()
                return redirect("/login")
            else:
                isUnique = False
                return render_template("user/sign-up.html", isLogin=isLogin, isUnique=isUnique, isAuthorize=isAuthorize)
    else:
        return render_template("user/sign-up.html", isLogin=isLogin, isUnique=isUnique, isAuthorize=isAuthorize)
    
@app.errorhandler(404)
def page_404(error):
    return render_template("404.html", error=error)

@app.route("/word-card", methods=["POST", "GET"])
def word_card():
    if isLogin:
        if request.method == "POST":
            lesson = request.form.get("choose_lesson", None)
            lesson_submit = request.form.get("lesson_submit", None)
            if lesson == None or lesson == "" or lesson_submit == None:
                return redirect("/word-card")
            elif lesson_submit == "edit":
                return redirect(f"/word-card/{lesson}/edit")
            elif lesson_submit == "delete":
                return redirect(f"/word-card/{lesson}/delete")
            elif lesson_submit == "learn":
                return redirect(f"/word-card/{lesson}/learn")
            else:
                return redirect(f"/word-card/{lesson}/list")
        else:
            lessons = []
            user = User.query.filter_by(username=session['username']).first()
            if user:
                user_id = user.id
            else:
                return redirect("/")
            lesson = Lesson.query.filter_by(user_id=user_id)
            if lesson:
                for l in lesson:
                    lessons.append(l.title)
            return render_template("word-card/home.html", isLogin=isLogin, lessons=lessons)
    else:
        return redirect("/")

@app.route("/word-card/add-lesson", methods=["POST", "GET"])
def add_lesson():
    if isLogin:
        if request.method == "POST":
            title = request.form.get("title", "")
            describe = request.form.get("describe", "")
            if len(title) <= 0:
                return render_template("word-card/add_lesson.html", error="Empty", isLogin=isLogin)
            elif Lesson.query.filter_by(title=title).first() != None:
                return render_template("word-card/add_lesson.html", error="Exist", isLogin=isLogin)
            user = User.query.filter_by(username=session['username']).first()
            if user:
                user_id = user.id
            else:
                return redirect("/")
            lesson = Lesson(title=title, describe=describe, user_id=user_id)
            try:
                db.session.add(lesson)
                db.session.commit()
                return redirect(f"/word-card/{title}/add-word")
            except Exception as e:
                print(f"Error: {e}")
                return f"Error: {e}"
        else:
            return render_template("word-card/add_lesson.html", isLogin=isLogin)
    else:
        return redirect("/")
    
@app.route("/word-card/<title>/add-word", methods=["POST", "GET"])
def add_word(title):
    if isLogin:
        if request.method == "POST":
            word = request.form.get("word", "")
            typ = request.form.getlist("choose_typ")
            definition = request.form.get("def", "")
            types = ""
            for t in typ:
                types += (t+" ")
            print(types)
            if len(word) <= 0:
                return render_template("word-card/add_word.html", title=title, isLogin=isLogin, error="Empty")
            lesson = Lesson.query.filter_by(title=title).first()
            if lesson:
                lesson_id = lesson.id
            else:
                return redirect("/")
            words = Word(word=word, typ=types, definition=definition, lesson_id=lesson_id)
            try:
                db.session.add(words)
                db.session.commit()
                return redirect(f"/word-card/{title}/add-word")
            except Exception as e:
                print(f"Error: {e}")
                return f"Error: {e}"
        else:
            return render_template("word-card/add_word.html", title=title, isLogin=isLogin)
    else:
        return redirect("/")
    
@app.route("/word-card/<title>/list", methods=["POST", "GET"])
def word_list(title):
    if isLogin:
        if request.method == "POST":
            word = request.form.get("search", "")
            return redirect(f"/word-card/{title}/list/{word}")
        else:
            lesson = Lesson.query.filter_by(title=title).first()
            describe = lesson.describe
            words = Word.query.filter_by(lesson_id=lesson.id)
            length = words.count()
            return render_template("word-card/word_list.html", isLogin=isLogin, words=words, title=title, search=False, length=length, describe=describe)  
    else:
        return redirect("/")  

@app.route("/word-card/<title>/list/<qoo>")
def list_search(title, qoo):
    if isLogin:
        lesson = Lesson.query.filter_by(title=title).first()
        words = Word.query.filter_by(lesson_id=lesson.id)
        l = []
        for w in words:
            if qoo.lower() in w.word.lower():
                l.append(w)
        length = len(l)
        return render_template("word-card/word_list.html", isLogin=isLogin, words=l, title=title, search=True, length=length)
    else:
        return redirect("/")

@app.route("/word-card/<title>/learn", methods=["POST", "GET"])
def learn(title):
    if isLogin:
        if request.method == "POST":
            submit = request.form.get("learn_submit", "")
            if submit == "card":
                global first
                first = True
                return redirect(f"/word-card/{title}/learn/card")
            elif submit == "fill":
                return redirect(f"/word-card/{title}/learn/fill")
            else:
                return redirect("/word-card")
        else:
            return render_template("word-card/learn_choose.html", title=title, isLogin=isLogin)
    else:
        return redirect("/")

@app.route("/word-card/<title>/learn/fill")
def fills(title):
    lesson = Lesson.query.filter_by(title=title).first()
    words = Word.query.filter_by(lesson_id=lesson.id).first()
    global dic
    dic = {}
    global ind
    ind = 0
    return redirect(f"/word-card/{title}/learn/fill/{words.id}")

@app.route("/word-card/<title>/learn/fill/<id>", methods=["POST", "GET"])
def fill(title, id):
    if isLogin:
        lesson_id = Lesson.query.filter_by(title=title).first().id
        words = Word.query.filter_by(lesson_id=lesson_id)
        if request.method == "POST":
            form_word = request.form.get('text', ' ')
            global ind
            string = words[ind].word
            spell = string[0] + form_word + string[-1]
            # global dic
            if form_word == string[1:-1]:
                dic[spell] = True
            else:
                dic[spell] = False
            ind += 1
            if ind >= words.count():
                return redirect(f"/word-card/{title}/learn/fill/score")
            return redirect(f"/word-card/{title}/learn/fill/{words[ind].id}")
        else:
            return render_template("word-card/learn_fill.html", w=words[ind], title=title, isLogin=isLogin)
    else:
        return redirect("/")
    
@app.route("/word-card/<title>/learn/fill/score")
def fill_score(title):
    if isLogin:
        lesson_id = Lesson.query.filter_by(title=title).first().id
        words = Word.query.filter_by(lesson_id=lesson_id)
        acc = 0
        all = words.count()
        for i in dic:
            if dic[i] == True:
                acc += 1
        acc = round((acc/all)*100, 1)
        return render_template("word-card/learn_fill_score.html", isLogin=isLogin, dic=dic, words=words, acc=acc, title=title)
    else:
        return redirect("/")
    
@app.route("/word-card/<title>/learn/card")
def cards(title):
    lesson = Lesson.query.filter_by(title=title).first()
    words = Word.query.filter_by(lesson_id=lesson.id)
    global dic_card
    global length
    length = words.count()
    global ind_card
    ind_card = 0
    global first
    id = 0
    if first == True:
        length = words.count()
        ind_card = 0
        dic_card = {}
        for w in words:
            dic_card[w.word] = False
        first = False
    else:
        d = dic_card
        dic_card = {}
        for i in d:
            if d[i] == False:
                dic_card[i] = False
        if len(dic_card) == 0:
            first = True
            return redirect(f"/word-card/{title}/learn")
        ind_card = 0
        length = len(dic_card)
    print(list(dic_card))
    id = Word.query.filter_by(word=list(dic_card)[ind_card]).first().id
    print(f"id: {id}")
    return redirect(f"/word-card/{title}/learn/card/{id}")
    # return redirect(f"/word-card/{title}/learn/card/{words.first().id}")

@app.route("/word-card/<title>/learn/card/<id>", methods=["POST", "GET"])
def card(title, id):
    if isLogin:
        lesson_id = Lesson.query.filter_by(title=title).first().id
        words = Word.query.filter_by(lesson_id=lesson_id)
        if request.method == "POST":
            global ind_card
            global dic_card
            # string = words[ind_card].word
            string = list(dic_card)[ind_card]
            radio = request.form.get('check', ' ')
            if radio == 'know':
                dic_card[string] = True
            else:
                dic_card[string] = False
            print(dic_card)
            ind_card += 1
            if ind_card >= length:
                return redirect(f"/word-card/{title}/learn/card/score")
            # id = words[ind_card].id
            id = Word.query.filter_by(word=list(dic_card)[ind_card]).first().id
            return redirect(f"/word-card/{title}/learn/card/{id}")
        else:
            w = Word.query.filter_by(id=id).first()
            print(w)
            return render_template("word-card/learn_card.html", w=w, title=title, isLogin=isLogin)
            # return render_template("word-card/learn_card.html", w=words[ind_card], title=title, isLogin=isLogin)
    else:
        return redirect("/")
    
@app.route("/word-card/<title>/learn/card/score")
def card_score(title):
    if isLogin:
        lesson_id = Lesson.query.filter_by(title=title).first().id
        words = Word.query.filter_by(lesson_id=lesson_id)
        acc = 0
        global dic_card
        all = len(dic_card)
        for i in dic_card:
            if dic_card[i] == True:
                acc += 1
        acc = round((acc/all)*100, 1)
        print(dic_card)
        return render_template("word-card/learn_card_score.html", isLogin=isLogin, dic=list(dic_card.items()), words=words, acc=acc, title=title)
    else:
        return redirect("/")
    
@app.route("/word-card/<title>/edit")
def edit(title):
    if isLogin:
        user = User.query.filter_by(username=session['username']).first()
        lesson = Lesson.query.filter_by(title=title, user_id=user.id).first()
        if lesson:
            words = Word.query.filter_by(lesson_id=lesson.id)
            return render_template("word-card/edit.html", title=title, describe=lesson.describe, words=words, isLogin=isLogin)
        else:
            return redirect("/word-card")
    else:
        return redirect("/")
    
@app.route("/word-card/<title>/edit/<id>", methods=["POST"])
def edit_passway(title, id):
    if isLogin:
        user = User.query.filter_by(username=session['username']).first()
        lesson = Lesson.query.filter_by(title=title, user_id=user.id).first()
        if lesson:
            word_submit = request.form.get("word_submit", None)
            words = Word.query.filter_by(id=id).first()
            if word_submit == "edit":
                return render_template("word-card/edit_word.html", title=title, words=words, isLogin=isLogin)
            elif word_submit == "delete":
                try:
                    db.session.delete(words)
                    db.session.commit()
                    return redirect(f"/word-card/{title}/edit")
                except Exception as e:
                    print(f"Error: {e}")
                    return f"Error: {e}"
            else:
                return redirect(f"/word-card/{title}/edit")
        else:
            return redirect("/word-card")
    else:
        return redirect("/")

@app.route("/word-card/<title>/delete")
def delete(title):
    if isLogin:
        user = User.query.filter_by(username=session['username']).first()
        lesson = Lesson.query.filter_by(title=title, user_id=user.id).first()
        words = Word.query.filter_by(lesson_id=lesson.id)
        if lesson:
            for w in words:
                try:
                    db.session.delete(w)
                    db.session.commit()
                except Exception as e:
                    print(f"Error: {e}")
                    return f"Error: {e}"
            try:
                db.session.delete(lesson)
                db.session.commit()
                return redirect("/word-card")
            except Exception as e:
                print(f"Error: {e}")
                return f"Error: {e}"
        else:
            return redirect("/word-card")
    else:
        return redirect("/")
    
@app.route("/word-card/<title>/edit/<id>/edit", methods=["POST"])
def edit_word(title, id):
    if isLogin:
        words = Word.query.filter_by(id=id).first()
        word = request.form.get("word", "")
        typ = request.form.getlist("choose_typ")
        definition = request.form.get("def", "")
        types = ""
        for t in typ:
            types += (t+" ")
        if len(word) <= 0:
            return render_template("word-card/edit_word.html", title=title, isLogin=isLogin, words=words, error="Empty")
        words.word = word
        words.typ = types
        words.definition = definition
        try:
            db.session.commit()
            return redirect(f"/word-card/{title}/edit")
        except Exception as e:
            print(f"Error: {e}")
            return f"Error: {e}"
    else:
        return redirect("/")    

@app.route("/word-card/<title>/edit/title", methods=["POST", "GET"])
def edit_title(title):
    if isLogin:
        lesson = Lesson.query.filter_by(title=title).first()
        if request.method == "POST":
            lesson_title = request.form.get("title", "")
            describe = request.form.get("describe", "")
            exist = Lesson.query.filter_by(title=lesson_title).first()
            if len(lesson_title) <= 0:
                return render_template("word-card/edit_title.html", error="Empty", isLogin=isLogin, lesson=lesson)
            elif exist != None and exist.id != id:
                return render_template("word-card/edit_title.html", error="Exist", isLogin=isLogin, lesson=lesson)
            lesson.title = lesson_title
            lesson.describe = describe
            print(lesson.title)
            try:
                db.session.commit()
                return redirect(f"/word-card/{lesson.title}/edit")
            except Exception as e:
                print(f"Error: {e}")
                return f"Error: {e}"
        else:
            return render_template("word-card/edit_title.html", isLogin=isLogin, lesson=lesson)
    else:
        return redirect("/")
    
@app.route("/dashboard")
def profile():
    if isLogin:
        username = session.get('username')
        user = User.query.filter_by(username=username).first()
        lessons = Lesson.query.filter_by(user_id=user.id)
        return render_template("user/dashboard.html", isLogin=isLogin, username=username, lessons=lessons)
    else:
        return redirect("/")