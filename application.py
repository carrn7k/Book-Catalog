
from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
from flask import session as login_session

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Genre, Author, Books

import db_updates

import random, string
import json
import httplib2
import os
import requests

from oauth2client import client
from apiclient.discovery import build

# G_CLIENT_SECRET_FILE = json.loads(open('g_client_secrets.json', 'r').read())
FB_CLIENT_SECRET_FILE = json.loads(open('fb_client_secrets.json', 'r').read())

engine = create_engine('sqlite:///bookcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)

## utility functions #######
##def get_genres():
##    return session.query(Genre).all()

def make_response_error(error_msg):
    response = make_response(json.dumps(error_msg), 401)
    response.headers['content-type'] = 'application/json'
    return response

def create_user(name, email, photo):
    new_user = User(name=name, email=email, picture=photo)
    session.add(new_user)
    session.commit()
    return new_user.id

def get_user_id(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

############################
    
@app.route('/login')
def login():
    genres = db_updates.get_genres()
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, genres=genres)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    
    if not request.args.get('state') == login_session['state']:
        return make_response_error('Invalid state parameter.')

    auth_code = request.data

    # initiate flow using client secrets file
    flow = client.flow_from_clientsecrets(
        'g_client_secrets.json',
        scope='openid email',
        redirect_uri='http://localhost:5000')

    # use the flow object and auth_code to obtain
    # credentials
    credentials = flow.step2_exchange(auth_code)
    
    http_auth = credentials.authorize(httplib2.Http())

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    login_session['access_token'] = credentials.access_token

    data = answer.json()

    login_session['provider'] = 'Google'
    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['google_id'] = data['id']
    login_session['picture'] = data['picture']

    # check if the user exists and if not add
    # them to the database
    user_id = get_user_id(login_session['email'])
    if not user_id:
        user_id = create_user(login_session['username'],
                              login_session['email'],
                              login_session['picture'])

    return "SUCCESS!!!"

@app.route('/fbconnect', methods=['POST'])
def fbConnect():

    # validate the login_session 
    if not request.args.get('state') == login_session['state']:
        return make_response_error('Invalid State Paramenter')

    access_token = request.data

    app_id = FB_CLIENT_SECRET_FILE["web"]["app_id"]
    app_secret = FB_CLIENT_SECRET_FILE["web"]["app_secret"]

    # get client credentials to verify users
    url = "https://graph.facebook.com/oauth/access_token?client_id=%s&client_secret=%s&grant_type=client_credentials" % (
        app_id, app_secret)
    h = httplib2.Http()
    user_acess_data = h.request(url, 'GET')
    app_access_token = user_acess_data[1].split('=')[1]

    # use client credentials (app_token) and the access
    # token from the AJAX request to verify the user
    url = "https://graph.facebook.com/debug_token?input_token=%s&access_token=%s" % (
        access_token, app_access_token)
    h = httplib2.Http()
    inspection_data = h.request(url, 'GET')

    # if the user is validated, proceed to token exchange
    if json.loads(inspection_data[1])['data']['is_valid']:
        
        url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
            app_id, app_secret, access_token)
        h = httplib2.Http()
        result = h.request(url, 'GET')[1]

        # if the exchange was successful, use the access
        # token to make api calls on behalf of the user
        if result:

            token = result.split('&')[0]
            login_session['token'] = token

            # user info api call
            url = "https://graph.facebook.com/v2.4/me?%s&fields=name,id,email" % token
            user_info_response = h.request(url, 'GET')
            user_data = json.loads(user_info_response[1])

            user_id = get_user_id(user_data["email"])
            if not user_id:
                user_id = create_user(user_name, user_email, user_photo)
                
            login_session['id'] = user_id
            login_session['name'] = user_data["name"]
            login_session['email'] = user_data["email"]

            # user photo api call
            url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
            h = httplib2.Http()
            photo = h.request(url, 'GET')

            user_photo = json.loads(photo[1])["data"]["url"]
            login_session['photo'] = user_photo
            
        else:
            make_response_error("User Authorization Error")

        return str(user_id)
        
    else:
        make_response_error("Invalid User Token")

# JSON endpoints ##########

@app.route('/catalog/genre/<int:genre_id>/json')
def showGenresJSON(genre_id):
    genres = db_updates.get_genres()
    genre = db_updates.get_one('genre', genre_id)
    return jsonify(genre=genre.serialize)

@app.route('/catalog/<int:book_id>/book/json')
def showBookJSON(book_id):
    book = db_updates.get_one('book', book_id)
    return jsonify(book=book.serialize)

##@app.route('/catalog/authors/json')
## # ADD FUNCTIONALITY TO ADD AN AUTHOR
##def showAuthorsJSON():
##    authors = session.query(Author).all()
##    return jsonify(authors=authors.serialize)

#############################

@app.route('/')
@app.route('/catalog/')
def showGenres():
    genres = db_updates.get_all('genres')
    authors = db_updates.get_all('authors')
    
    feat_books = session.query(Books).order_by(desc(Books.created)).limit(4).all()

    a_len = len(authors) - 1
    feat_author = authors[random.randint(0, a_len)]
##    for i in range(6):
##        genres.append('test')
##    # split list into sublists with 3 items to render as
##    # 3 column tables in html
##    genre_table = [genres[i:i+3] for i in range(0, len(genres), 3)]
##    return render_template('catalog.html', genre_table=genre_table)
    return render_template('catalog.html', genres=genres,
                           books=feat_books, author=feat_author)
    
@app.route('/catalog/genre/<int:genre_id>/')
def showGenreList(genre_id):
    
    genres = db_updates.get_all('genres')
    genre = db_updates.get_one('genre', genre_id)
    genre_books = genre.books

    # create a json object of the books for DOM manipulation
    j_books = json.dumps([{'title': b.title,
                           'summary': b.summary,
                           'author': b.author.name,
                           'book_id': b.id}
                for b in genre_books])
    
    #books = session.query(Books).filter_by(genre_id = genre_id).all()
    return render_template('genreList.html', genre=genre, genres=genres,
                           books=genre_books, j_books=j_books)

@app.route('/catalog/authors/')
# ADD FUNCTIONALITY TO ADD AN AUTHOR
def showAuthors():
    genres = db_updates.get_all('genres')
    authors = db_updates.get_all('authors')
    return render_template('authorlist.html', authors=authors,
                           genres=genres)

@app.route('/catalog/<int:book_id>/book/')
def showBook(book_id):
    genres = db_updates.get_all('genres')
    book = db_updates.get_one('book', book_id)
    return render_template('bookDescription.html', book=book,
                           genres=genres)

@app.route('/catalog/book/new/', methods=['GET', 'POST'])
def createBook():
    genres = db_updates.get_all('genres')

    if request.method == 'POST':
        title = request.form['title']
        summary = request.form['summary']
        author_input = request.form['author']
        genre = request.form['genres']

        current_genre = filter(lambda g: g.genre == genre, genres)
        current_genre_id = current_genre[0].id

        if title and summary and author_input and genre:
            
            new_book = Books(title=request.form['title'],
                             summary=request.form['summary'])
            session.add(new_book)
            new_book.genre_id = current_genre_id
            # if author is already in the DB, fetch the author
            # and create a relationship with the existing ID. If
            # not, create a new author and use the new ID.
            try: 
                author = session.query(Author).filter_by(name = author_input).one()
                new_book.author_id = author.id
                print('\n')
                print('Author exists and book is linked to him/her')
                print('\n')
            except:
                new_author = Author(name=author_input)
                session.add(new_author)
                session.commit()
                new_book.author_id = new_author.id
                print('\n')
                print('New author has been created')
                print('\n')
            
            session.commit()
            return redirect(url_for('showBook', book_id=new_book.id))
        else:
            print('\n')
            print('CREATE MESSAGE FLASHING: PLEASE INPUT ALL FIELDS')
            print('\n')
            return render_template('addBook.html', genres=genres)
    else:
        return render_template('addBook.html', genres=genres)

@app.route('/catalog/<int:book_id>/book/edit/', methods=['GET', 'POST'])
def editBook(book_id):
    genres = db_updates.get_all('genres')
    edit_book = db_updates.get_one('book', book_id)
    if request.method == 'POST':
        if request.form['newTitle']:
            edit_book.title = request.form['newTitle']
        if request.form['newSummary']:
            edit_book.summary = request.form['newSummary']
        if request.form['newAuthor']:
            try:
                edit_book.author.name = request.form['newAuthor']
            except:
                author = Author(name=request.form['newAuthor'])
                session.add(author)
                session.commit()
                edit_book.author_id = author.id
        session.add(edit_book)
        session.commit()
        return redirect(url_for('showBook', book_id=edit_book.id))
    else:
        return render_template('edit.html', book=edit_book,
                               genres=genres)

@app.route('/catalog/<int:book_id>/book/delete/', methods=['GET', 'POST'])
def deleteBook(book_id):
    genres = db_updates.get_all('genres')
    delete_book = db_updates.get_one('book', book_id)
    if request.method == 'POST':
        session.delete(delete_book)
        session.commit()
        return redirect(url_for('showGenres'))
    else:
        return render_template('delete.html', book=delete_book,
                               genres=genres)

if __name__ == '__main__':
    app.debug = True
    app.secret_key = "super_secret_key"
    app.run(host='0.0.0.0', port=5000)
