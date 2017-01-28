from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Genre, Author, Books

engine = create_engine('sqlite:///bookcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

book1 = Books(title="The Selfish Gene",
              summary="""According to the introduction to this book,
              The Selfish Gene changes the way that many scientists
              look at the process of natural selection. The author
              begins by suggesting that intelligent, thinking animals
              must ask questions about its origins, and that Darwin
              has supplied excellent answers. However, Darwin's
              thoughts have been misinterpreted over the years to
              suggest that animals work together to preserve their
              own species. This book will challenge that idea.""",
              author_id=1, genre_id=1)

book2 = Books(title="Guns, Germs, and Steel",
              summary="""The book attempts to explain why Eurasian
              civilizations (including North Africa) have survived
              and conquered others, while arguing against the idea
              that Eurasian hegemony is due to any form of Eurasian
              intellectual, moral, or inherent genetic superiority.""",
              author_id=2, genre_id=2)

book3 = Books(title="Slaughterhouse Five",
              summary="""a satirical novel by Kurt Vonnegut about
              World War II experiences and journeys through time
              of Billy Pilgrim, from his time as an American soldier
              and chaplain's assistant, to postwar and early years.
              It is generally recognized as Vonnegut's most influential
              and popular work. A central event is Pilgrim's surviving
              the Allies' firebombing of Dresden as a prisoner-of-war.
              This was an event in Vonnegut's own life, and the novel
              is considered semi-autobiographical.""",
              author_id=3, genre_id=3)

session.add(book1)
session.add(book2)
session.add(book3)
session.commit()
