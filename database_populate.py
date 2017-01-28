from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Genre, Author, Books

engine = create_engine('sqlite:///bookcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


genres = [Genre(genre="Science"), Genre(genre="History"),
          Genre(genre="Fiction")]

authors = [Author(name="Richard Dawkins"),
           Author(name="Jared Diamond"),
           Author(name="Kurt Vonnegut")]


for g in genres:
    session.add(g)
for a in authors:
    session.add(a)
    
session.commit()

