
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



############################

# Helper function for outputting error messages
def make_response_error(error_msg, error_code):
    response = make_response(json.dumps(error_msg), error_code)
    response.headers['content-type'] = 'application/json'
    return response

# Function to check if a user is logged in to
# grant a user authorization to change the DB
def is_user():
    if 'name' not in login_session:
        return None
    else:
        return login_session['name'].split(' ')[0]

############################
    
@app.route('/login')
def login():
    genres = db_updates.get_all('genres')

    # Create a state variable to prevent forgery
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    
    return render_template('login.html', STATE=state, genres=genres)

@app.route('/logout')
def logout():

    current_provider = login_session['provider']
    if not current_provider:
        flash("Sorry, there was an error logging out")
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

# Logout functions
def g_disconnect():

    # Revoke the access token in the session
    
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

    # Revoke the access token using facebook is and
    # access token in the session.
    
    if login_session['access_token'] is None:
        return make_response_error('Current User is Not Logged In', 401)
    else:
        facebook_id = login_session['fb_id']
        access_token = login_session['access_token']
        login_session.clear()
        url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
        h = httplib2.Http()
        result = h.request(url, 'DELETE')[1]

@app.route('/gconnect', methods=['POST'])
def gconnect():      
     
    if not request.args.get('state') == login_session['state']:
        return make_response_error('Invalid state parameter.', 401)

    # Code to exchange for access token 
    auth_code = request.data
    
    # Initiate flow and exchange auth_code
    # for access token. If the exchange fails,
    # thorw an error
    try: 
        flow = client.flow_from_clientsecrets(
            'g_client_secrets.json',
            scope='openid email',
            redirect_uri='http://localhost:5000')
        credentials = flow.step2_exchange(auth_code)

    except FlowExchangeError:
        return make_response_error('Failed to Obtain Authorization Code.', 401)
    
    # Request user info with the access token and convert the
    # response to json.
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    # Security and error checks
    if data.get('error') is not None:
        return make_response_error(data['error']['message'], 401)

    if credentials.id_token['sub'] != data['id']:
        return make_response_error("Token and User ID Don't Match", 401)

    if credentials.client_id != G_CLIENT_ID:
        return make_response_error("Token ID and App ID don't match", 401)

    # Update the login_session (the access token and provider
    # are required for logout).
    login_session['provider'] = 'Google'
    login_session['access_token'] = credentials.access_token
    login_session['g_id'] = data['id']
    login_session['name'] = data['name']
    login_session['email'] = data['email']
    login_session['google_id'] = data['id']
    login_session['picture'] = data['picture']

    # Check if user is already logged in
    if (login_session.get('access_token') != None and
        login_session.get('g_id') == credentials.id_token['sub']):
        
        response = make_response(json.dumps('Current User is Already Logged In.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        flash("It looks like you're already logged in" + login_session['name'])
        return redirect(url_for('showGenres'))

    # Check if the user exists and if not add
    # them to the database.
    user_id = db_updates.get_user_id(login_session['email'])
    if not user_id:
        user_id = db_updates.create_user(login_session['username'],
                                         login_session['email'],
                                         login_session['picture'])
        login_session['user_id'] = user_id

    return "SUCCESS!!!"    

@app.route('/fbconnect', methods=['POST'])
def fbConnect():

    # Validate the login_session 
    if not request.args.get('state') == login_session['state']:
        return make_response_error('Invalid State Paramenter')

    access_token = request.data

    app_id = FB_CLIENT_SECRET_FILE["web"]["app_id"]
    app_secret = FB_CLIENT_SECRET_FILE["web"]["app_secret"]

    # Get client credentials to verify users
    url = "https://graph.facebook.com/oauth/access_token?client_id=%s&client_secret=%s&grant_type=client_credentials" % (
        app_id, app_secret)
    h = httplib2.Http()
    app_access_data = h.request(url, 'GET')
    app_access_token = app_access_data[1].split('=')[1]

    # Check that the response returned an access token
    if app_access_data[0]['status'] != '200':
        return make_response_error('Could Not Obtain Access Token', 401)

    # Use client credentials (app_token) and the access
    # token from the AJAX request to verify the user.
    url = "https://graph.facebook.com/debug_token?input_token=%s&access_token=%s" % (
        access_token, app_access_token)
    h = httplib2.Http()
    inspection_data = h.request(url, 'GET')

    # If the user is validated, proceed to token exchange
    if not json.loads(inspection_data[1])['data']['is_valid']:
        return make_response_error('User Could Not Be Validated', 401)
    else:
        url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
            app_id, app_secret, access_token)
        h = httplib2.Http()
        result = h.request(url, 'GET')

        # If the exchange was successful, use the access
        # token to make api calls on behalf of the user   
        if result[0]['status'] != '200':
            return make_response_error('Token Exchange Failed', 401)
        else:
            
            fb_token = result[1].split('&')[0]
            login_session['access_token'] = fb_token

            # User info api call
            url = "https://graph.facebook.com/v2.4/me?%s&fields=name,id,email" % fb_token
            user_info_response = h.request(url, 'GET')
            user_data = json.loads(user_info_response[1])

            # User photo api call
            url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % fb_token
            h = httplib2.Http()
            photo = h.request(url, 'GET')
            user_photo = json.loads(photo[1])["data"]["url"]

            # If the user does not exist in the DB add them
            user_id = db_updates.get_user_id(user_data["email"])
            if not user_id:
                user_id = db_updates.create_user(user_data["name"],
                                                 user_data["email"],
                                                 user_photo)
                
            # Update the session (the provider and id are required
            # for logout.
            login_session['provider'] = 'Facebook'
            login_session['fb_id'] = user_id
            login_session['name'] = user_data["name"]
            login_session['email'] = user_data["email"]
            login_session['photo'] = user_photo

            # Check if user is already logged in
            if (login_session.get('access_token') != None and
                login_session.get('f_id') == user_id):
                response = make_response(json.dumps('Current User is Already Logged in.'),
                                 200)
                response.headers['Content-Type'] = 'application/json'
                flash("It looks like you're already logged in" + login_session['name'])
            else:
                return str(user_id)


# JSON endpoints ##########

# json for all books in a single category
@app.route('/catalog/genre/<int:genre_id>/json')
def showGenresJSON(genre_id):
    genre = db_updates.get_one('genre', genre_id)
    books = session.query(Books).filter_by(genre_id = genre.id).all()
    j_books = [b.serialize for b in books]
    return json.dumps({genre.genre: j_books})

# json for a single book
@app.route('/catalog/<int:book_id>/book/json')
def showBookJSON(book_id):
    book = db_updates.get_one('book', book_id)
    return jsonify(book=book.serialize)

# Main page to display Genres
@app.route('/', methods=['GET', 'POST'])
@app.route('/catalog/', methods=['GET', 'POST'])
def showGenres():

    user = is_user()
    
    # Create json data for the jQuery search bar    
    books = db_updates.get_all('books')
    j_books = json.dumps([{'label': b.title,
                           'value': b.id,
                           }
                for b in books])

    genres = db_updates.get_all('genres')
    authors = db_updates.get_all('authors')
    feat_books = session.query(Books).order_by(desc(Books.created)).limit(4).all()

    # Get a random author and their books from
    # the DB to display on the main page.
    a_len = len(authors) - 1
    feat_author = authors[random.randint(0, a_len)]
    auth_books = session.query(Books).filter_by(author_id = feat_author.id).all()

    if request.method == 'POST':
        book_search = request.form['b-search']
    else:
        return render_template('catalog.html', genres=genres, j_books=j_books,
                               feat_books=feat_books, author=feat_author,
                               auth_books=auth_books, user=user)

# Single Genre Page    
@app.route('/catalog/genre/<int:genre_id>/')
def showGenreList(genre_id):

    user = is_user()
    c_user_id = 1

    # If a user is logged in, use their id authorize editing
    # and deleting for books they've added.
##    if user:
##        c_user_id = db_updates.get_user_id(login_session['email'])
    
    genres = db_updates.get_all('genres')
    genre = db_updates.get_one('genre', genre_id)
    genre_books = genre.books

    # Create a json object of the books for DOM manipulation
    j_books = json.dumps([{'title': b.title,
                           'summary': b.summary,
                           'author': b.author.name,
                           'book_id': b.id,
                           'book_photo': b.photo,
                           'user_id': b.user_id,
                           'c_user_id': c_user_id}
                for b in genre_books])
    
    return render_template('genreList.html', genre=genre, genres=genres,
                           books=genre_books, j_books=j_books, user=user)

# Page to Display Authors
@app.route('/catalog/authors/')
def showAuthors():
    
    user = is_user()
    
    genres = db_updates.get_all('genres')
    authors = db_updates.get_all('authors')
    return render_template('authorlist.html', authors=authors,
                           genres=genres, user=user)

# Page to Display a Single Book
@app.route('/catalog/<int:book_id>/book/')
def showBook(book_id):

    user = is_user()
        
    users = db_updates.get_all('users')
    genres = db_updates.get_all('genres')
    book = db_updates.get_one('book', book_id)
    return render_template('bookDescription.html', book=book,
                           genres=genres, user=user)

# Page for Creating Books. A link to this page is only
# displayed to logged in users
@app.route('/catalog/book/new/', methods=['GET', 'POST'])
def createBook():

    # If the addbook page is accessed by an unauthorized user
    # redirect them to the login page.
    if 'email' not in login_session:
        flash('Sorry, you must be logged in to add a book')
        return redirect(url_for('login'))

    user = is_user()

    user_id = db_updates.get_user_id(login_session['email'])
    
    new_book = None
    genres = db_updates.get_all('genres')

    if request.method == 'POST':
        title = request.form['title']
        summary = request.form['summary']
        author_input = request.form['author']
        genre = request.form['genres']
        photo = request.form['photo']

        current_genre = filter(lambda g: g.genre == genre, genres)
        current_genre_id = current_genre[0].id

        if title and summary and author_input and genre:
            
            # Check if the book already exists in the DB.
            try:
                added_book = session.query(Books).filter_by(title = title).one()
                error = "Sorry, " + added_book.title + " has already been added!"
                return render_template('addBook.html', genres=genres, user=user,
                                   error=error)
            # If the book doesn't exist add it to the DB.
            except:
                try:
                    new_book = db_updates.add_book(title, summary,
                                                   current_genre_id,
                                                   author_input,
                                                   user_id, photo)
                except:
                    flash('Sorry, something went wrong...')
                    redirect(url_for('createBook'))

                # If successfull, redirect to the book description page.
                flash(new_book.title + ' Successfully Added!')
                return redirect(url_for('showBook', book_id=new_book.id))
        else:
            error = "Please enter all required fields"
            return render_template('addBook.html', genres=genres, user=user,
                                   error=error)
    else:
        return render_template('addBook.html', genres=genres, user=user)

# Page to edit a book
@app.route('/catalog/<int:book_id>/book/edit/', methods=['GET', 'POST'])
def editBook(book_id):

    # If the editBook page is accessed by an unauthorized user
    # redirect them to the login page.
    if 'email' not in login_session:
        flash('Sorry, you must be logged in to add a book')
        return redirect(url_for('login'))

    user = is_user()
    user_id = db_updates.get_user_id(login_session['email'])
        
    genres = db_updates.get_all('genres')
    edit_book = db_updates.get_one('book', book_id)

    if edit_book.user_id != user_id:
        error = "Sorry, you're not authorized to edit this book"
        return render_template('edit.html', book=edit_book,
                               genres=genres, user=user, error=error)
        
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

    # If the deleteBook page is accessed by an unauthorized user
    # redirect them to the login page
    if 'email' not in login_session:
        flash('Sorry, you must be logged in to add a book')
        return redirect(url_for('login'))

    user = is_user()
    user_id = db_updates.get_user_id(login_session['email'])
        
    genres = db_updates.get_all('genres')
    delete_book = db_updates.get_one('book', book_id)

    if delete_book.user_id != user_id:
        error = "Sorry, you're not authorized to delete this book"
        return render_template('delete.html', book=delete_book,
                               genres=genres, user=user, error=error)
    if request.method == 'POST':
        db_updates.delete_book(delete_book)
        return redirect(url_for('showGenres'))
    else:
        return render_template('delete.html', book=delete_book,
                               genres=genres, user=user)

if __name__ == '__main__':
    app.debug = True
    app.secret_key = "super_secret_key"
    app.run(host='0.0.0.0', port=5000)
