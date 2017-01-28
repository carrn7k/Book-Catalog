import random

from flask import Flask, render_template, request, redirect, url_for

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Genre, Author, Books

from flask import session as login_session
import random, string
import json

from apiclient import discovery
import httplib2
from oauth2client import client

# CLIENT_SECRET_FILE = json.loads(open('g_client_secrets.json', 'r').read())
CLIENT_SECRET_FILE = 'g_client_secrets.json'

engine = create_engine('sqlite:///bookcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)

#create a google sign in
@app.route('/login')
def login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    # login_session['state'] = state
    print(request.data)
    return render_template('login.html', state=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    auth_code = request.data
    # Exchange auth code for access token, refresh token, and ID token
    credentials = client.credentials_from_clientsecrets_and_code(
        CLIENT_SECRET_FILE,
        ['https://www.googleapis.com/auth/drive.appdata', 'profile', 'email'],
        auth_code)
    print(credentials)

    # Call Google API
    http_auth = credentials.authorize(httplib2.Http())
    drive_service = discovery.build('drive', 'v3', http=http_auth)
    appfolder = drive_service.files().get(fileId='appfolder').execute()

    # Get profile info from ID token
    userid = credentials.id_token['sub']
    email = credentials.id_token['email']


@app.route('/')
@app.route('/catalog/')
def showGenres():
    genres = session.query(Genre).all()
    feat_books = session.query(Books).order_by(desc(Books.created)).limit(4).all()
    authors = session.query(Author).all()

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
    genre = session.query(Genre).filter_by(id = genre_id).one()
    genre_books = genre.books
    #books = session.query(Books).filter_by(genre_id = genre_id).all()
    return render_template('genreList.html', genre=genre,
                           books=genre_books)

@app.route('/catalog/authors/')
def showAuthors():
    authors = session.query(Author).all()
    return render_template('authorlist.html', authors=authors)

@app.route('/catalog/<int:book_id>/book/')
def showBook(book_id):
    book = session.query(Books).filter_by(id = book_id).one()
    return render_template('bookDescription.html', book=book)

@app.route('/catalog/book/new/', methods=['GET', 'POST'])
def createBook():
    if request.method == 'POST':
        new_book = Books(title=request.form['title'],
                        summary=request.form['summary'])
        session.add(new_book)
        # if author is already in the DB, fetch the author
        # and create a relationship with the existin ID. If
        # not, create a new author and use the new ID.
        author_input = request.form['author']
        try:
            author = session.query(Author).filter_by(name = author_input).one()
            new_book.author_id = author.id
        except:
            new_author = Author(name=author_input)
            session.add(new_author)
            session.commit()
            new_book.author_id = new_author.id
        session.commit()
        return redirect(url_for('showBook', book_id=new_book.id))
    else:
        return render_template('addBook.html')

@app.route('/catalog/<int:book_id>/book/edit/', methods=['GET', 'POST'])
def editBook(book_id):
    edit_book = session.query(Books).filter_by(id = book_id).one()
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
        return render_template('edit.html', book=edit_book)

@app.route('/catalog/<int:book_id>/book/delete/', methods=['GET', 'POST'])
def deleteBook(book_id):
    delete_book = session.query(Books).filter_by(id = book_id).one()
    if request.method == 'POST':
        session.delete(delete_book)
        session.commit()
        return redirect(url_for('showGenres'))
    else:
        return render_template('delete.html', book=delete_book)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
