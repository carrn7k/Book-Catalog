import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(500), nullable=False)
    picture = Column(String(500))

class Genre(Base):
    __tablename__ = 'genre'

    id = Column(Integer, primary_key=True)
    genre = Column(String(250), nullable=False)

class Author(Base):
    __tablename__ = 'author'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    created = Column(DateTime)

class Books(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    summary = Column(String(300), nullable=False)
    created = Column(DateTime)

    author_id = Column(Integer, ForeignKey('author.id'))
    author = relationship(Author, back_populates='books')
    
    genre_id = Column(Integer, ForeignKey('genre.id'))
    genre = relationship(Genre, back_populates='books')

    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

Genre.books = relationship(Books, back_populates='genre')
Author.books = relationship(Books, back_populates='author')


engine = create_engine('sqlite:///bookcatalog.db')
Base.metadata.create_all(engine)

