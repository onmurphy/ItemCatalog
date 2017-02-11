from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
 
from database_setup import Category, Base, Item
 
engine = create_engine('sqlite:///itemcatalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine
 
DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()



category1 = Category(name = "Soccer")

session.add(category1)
session.commit()


item1 = Item(name = "Soccer ball", description = "fun stuff", category = category1)

session.add(item1)
session.commit()

item2 = Item(name = "Soccer cleats", description = "shoes!", category = category1)

session.add(item2)
session.commit()





category2 = Category(name = "Baseball")

session.add(category2)
session.commit()

item1 = Item(name = "baseball glove", description = "helps you catch a ball!", category = category2)

session.add(item1)
session.commit()

item2 = Item(name = "baseball bat", description = "hit it out of the park!", category = category2)

session.add(item2)
session.commit()


category3 = Category(name = "Basketball")

session.add(category3)
session.commit()

item1 = Item(name = "net", description = "hoop sold separately", category = category3)

session.add(item1)
session.commit()


category4 = Category(name = "Football")

session.add(category4)
session.commit()


item1 = Item(name = "pads", description = "protect yourself from injury", category = category4)

session.add(item1)
session.commit()




print "added categories"
