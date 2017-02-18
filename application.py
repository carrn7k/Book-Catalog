
from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response, flash
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

from apiclient import discovery
from oauth2client import client
from oauth2client.client import FlowExchangeError

G_CLIENT_ID = json.loads(open('g_client_secrets.json', 'r').read())['web']['client_id']
FB_CLIENT_SECRET_FILE = json.loads(open('fb_client_secrets.json', 'r').read())

engine = create_engine('sqlite:///bookcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)

## utility functions #######

def make_response_error(error_msg, error_code):
    response = make_response(json.dumps(error_msg), error_code)
    response.headers['content-type'] = 'application/json'
    return response

def is_user():
    if 'name' not in login_session:
        return None
    else:
        return login_session['name']

############################
    
@app.route('/login')
def login():
    genres = db_updates.get_all('genres')
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, genres=genres)

@app.route('/logout')
def logout():

    current_provider = login_session['provider']
    if not current_provider:
        flash("Sorry, there was an error logging out")
        print('\n')
        print('USER IS NOT LOGGED OR NOT IN THE SESSION')
        print('\n')
        return redirect(url_for('showGenres'))
    elif current_provider == 'Google':
        try:
            g_disconnect()
            flash("You're now logged out")
            return redirect(url_for('showGenres'))
        except:
            make_response_error('Logout Failed', 401)
    elif current_provider == 'Facebook':
        try:
            fb_disconnect()
            flash("You're now logged out")
            return redirect(url_for('showGenres'))
        except:
            make_response_error('Logout Failed', 401)

# logout functions
def g_disconnect():
    if login_session['access_token'] is None:
        return make_response_error('Current User is Not Logged In', 401)
    else:
        access_token = login_session['access_token']
        login_session.clear()
        url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
        h = httplib2.Http()
        result = h.request(url, 'GET')
        if result[0]['status'] != '200':
            return make_response_error('Failed to Revoke Token', 400)

def fb_disconnect():
    facebook_id = login_session['fb_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    login_session.clear()
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]

@app.route('/gconnect', methods=['POST'])
def gconnect():
    
    if not request.args.get('state') == login_session['state']:
        return make_response_error('Invalid state parameter.', 401)

    auth_code = request.data
    
    # initiate flow and exchange auth_code
    # for access token
    try: 
        flow = client.flow_from_clientsecrets(
            'g_client_secrets.json',
            scope='openid email',
            redirect_uri='http://localhost:5000')
        credentials = flow.step2_exchange(auth_code)

    except FlowExchangeError:
        return make_response_error('Failed to Obtain Authorization Code.', 401)
    
    # request user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    # security and error checks
    if data.get('error') is not None:
        return make_response_error(data['error']['message'], 401)

    if credentials.id_token['sub'] != data['id']:
        return make_response_error("Token and User ID Don't Match", 401)

    if credentials.client_id != G_CLIENT_ID:
        return make_response_error("Token ID and App ID don't match", 401)

    # update the login_session
    login_session['provider'] = 'Google'
    login_session['access_token'] = credentials.access_token
    login_session['g_id'] = data['id']
    login_session['name'] = data['name']
    login_session['email'] = data['email']
    login_session['google_id'] = data['id']
    login_session['picture'] = data['picture']

    # check if user is already logged in
    if (login_session.get('access_token') != None and
        login_session.get('g_id') == credentials.id_token['sub']):
        
        response = make_response(json.dumps('Current User is Already Logged In.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        print(response)
        flash("It looks like you're already logged in" + login_session['name'])
        return redirect(url_for('showGenres'))

    # check if the user exists and if not add
    # them to the database
    user_id = db_updates.get_user_id(login_session['email'])
    if not user_id:
        user_id = db_updates.create_user(login_session['username'],
                                         login_session['email'],
                                         login_session['picture'])
        login_session['user_id'] = user_id

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
    app_access_data = h.request(url, 'GET')
    app_access_token = app_access_data[1].split('=')[1]

    # check that the response returned an access token
    if app_access_data[0]['status'] != '200':
        return make_response_error('Could Not Obtain Access Token', 401)

    # use client credentials (app_token) and the access
    # token from the AJAX request to verify the user
    url = "https://graph.facebook.com/debug_token?input_token=%s&access_token=%s" % (
        access_token, app_access_token)
    h = httplib2.Http()
    inspection_data = h.request(url, 'GET')

    # if the user is validated, proceed to token exchange
    if not json.loads(inspection_data[1])['data']['is_valid']:
        return make_response_error('User Could Not Be Validated', 401)
    else:
        url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
            app_id, app_secret, access_token)
        h = httplib2.Http()
        result = h.request(url, 'GET')

        # if the exchange was successful, use the access
        # token to make api calls on behalf of the user   
        if result[0]['status'] != '200':
            return make_response_error('Token Exchange Failed', 401)
        else:
            
            fb_token = result[1].split('&')[0]
            login_session['access_token'] = fb_token

            # user info api call
            url = "https://graph.facebook.com/v2.4/me?%s&fields=name,id,email" % fb_token
            user_info_response = h.request(url, 'GET')
            user_data = json.loads(user_info_response[1])

            # user photo api call
            url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % fb_token
            h = httplib2.Http()
            photo = h.request(url, 'GET')
            user_photo = json.loads(photo[1])["data"]["url"]

            # if the user does not exist in the DB add them
            user_id = db_updates.get_user_id(user_data["email"])
            if not user_id:
                user_id = db_updates.create_user(user_name, user_email, user_photo)

            login_session['provider'] = 'Facebook'
            login_session['fb_id'] = user_id
            login_session['name'] = user_data["name"]
            login_session['email'] = user_data["email"]
            login_session['photo'] = user_photo

            # check if user is already logged in
            if (login_session.get('access_token') != None and
                login_session.get('f_id') == user_id):
                response = make_response(json.dumps('Current User is Already Logged in.'),
                                 200)
                response.headers['Content-Type'] = 'application/json'
                print(response)
                flash("It looks like you're already logged in" + login_session['name'])
            else:
                return str(user_id)


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

    # login_session.clear()

    user = is_user()
        
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
                           books=feat_books, author=feat_author,
                           user=user)
    
@app.route('/catalog/genre/<int:genre_id>/')
def showGenreList(genre_id):

    user = is_user()
    
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
                           books=genre_books, j_books=j_books, user=user)

@app.route('/catalog/authors/')
# ADD FUNCTIONALITY TO ADD AN AUTHOR
def showAuthors():
    
    user = is_user()
    
    genres = db_updates.get_all('genres')
    authors = db_updates.get_all('authors')
    return render_template('authorlist.html', authors=authors,
                           genres=genres, user=user)

@app.route('/catalog/<int:book_id>/book/')
def showBook(book_id):

    user = is_user()
        
    users = db_updates.get_all('users')
    genres = db_updates.get_all('genres')
    book = db_updates.get_one('book', book_id)
    return render_template('bookDescription.html', book=book,
                           genres=genres, user=user)

@app.route('/catalog/book/new/', methods=['GET', 'POST'])
def createBook():

    user = is_user()

    # set user_id to 1 (Me) during production
    user_id = 1
    
    new_book = None
    genres = db_updates.get_all('genres')

    if 'email' not in login_session:
        # add redirect to login page
        print('\n')
        print('THE USER IS NOT LOGGED IN')
        print('\n')

    if request.method == 'POST':
        title = request.form['title']
        summary = request.form['summary']
        author_input = request.form['author']
        genre = request.form['genres']

        current_genre = filter(lambda g: g.genre == genre, genres)
        current_genre_id = current_genre[0].id

        if title and summary and author_input and genre:
            
            # check if the book already exists in the 
            try:
                added_book = session.query(Books).filter_by(title = title).one()
                error = "Sorry, " + added_book.title + " has already been added!"
                return render_template('addBook.html', genres=genres, user=user,
                                   error=error)
            except:
                try:
                    new_book = db_updates.add_book(title, summary,
                                                   current_genre_id,
                                                   author_input,
                                                   user_id)
                except:
                    flash('Sorry, something went wrong...')
                    redirect(url_for('createBook'))

                # if successfull, redirect to the book description
                flash(new_book.title + 'Successfully Added!')
                return redirect(url_for('showBook', book_id=new_book.id))
        else:
            error = "Please enter all fields"
            return render_template('addBook.html', genres=genres, user=user,
                                   error=error)
    else:
        return render_template('addBook.html', genres=genres, user=user)

@app.route('/catalog/<int:book_id>/book/edit/', methods=['GET', 'POST'])
def editBook(book_id):

    user = is_user()
        
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
                author_id = db_updates.add_author(request.form['newAuthor'])
                edit_book.author_id = author_id
        session.commit()
        return redirect(url_for('showBook', book_id=edit_book.id))
    else:
        return render_template('edit.html', book=edit_book,
                               genres=genres, user=user)

@app.route('/catalog/<int:book_id>/book/delete/', methods=['GET', 'POST'])
def deleteBook(book_id):

    user = is_user()
        
    genres = db_updates.get_all('genres')
    delete_book = db_updates.get_one('book', book_id)
    if request.method == 'POST':
        session.delete(delete_book)
        session.commit()
        return redirect(url_for('showGenres'))
    else:
        return render_template('delete.html', book=delete_book,
                               genres=genres, user=user)

if __name__ == '__main__':
    app.debug = True
    app.secret_key = "super_secret_key"
    app.run(host='0.0.0.0', port=5000)
