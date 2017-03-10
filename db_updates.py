# module for updating the DB

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Genre, Author, Books

engine = create_engine('sqlite:///bookcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# return all columns in a specified table
def get_all(category):
    if category == 'genres':
        return session.query(Genre).all()
    elif category == 'books':
        return session.query(Books).all()
    elif category == 'authors':
        return session.query(Author).all()
    elif category == 'users':
        return session.query(User).all()
    else:
        print('Incorrect parameter input')

# return a single column in a specified table
def get_one(category, category_id):
    if category == 'genre':
        return session.query(Genre).filter_by(id = category_id).one()
    elif category == 'book':
        return session.query(Books).filter_by(id = category_id).one()
    elif category == 'author':
        return session.query(Author).filter_by(id = category_id).one()

def add_author(name):
    author = Author(name=name)
    session.add(author)
    session.commit()
    return author.id

def add_genre(genre):
    genre = Genre(genre=genre)
    session.add(genre)
    session.commit()
    return genre.id

# add a book column to the Books table
def add_book(title, summary, current_genre_id,
             author_input, user_id, photo):

    new_book = Books(title=title,
                     summary=summary,
                     genre_id=current_genre_id,
                     user_id=user_id, photo=photo)
    session.add(new_book)
    
    # check if author exists in the DB
    try:
        author = session.query(Author).filter_by(name = author_input).one()
        new_book.author_id = author.id
    # add author to DB if not 
    except:
        new_author = Author(name=author_input)
        session.add(new_author)
        session.commit()
        
        new_book.author_id = new_author.id

    session.commit()
    return new_book

def delete_book(book):
    session.delete(book)
    session.commit()

## User Functions ############

def get_user_id(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

def create_user(name, email, photo):
    new_user = User(name=name, email=email, picture=photo)
    session.add(new_user)
    session.commit()
    return new_user.id
    
    
    
    
    
