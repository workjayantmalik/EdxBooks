import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from constants import SQLITE_DB_URI

engine = create_engine(SQLITE_DB_URI)
db = scoped_session(sessionmaker(bind=engine))    

def get_data():
	"""Returns each row as a python dictionary"""

	with open('books.csv', mode='r') as file:
			reader = csv.reader(file)

			for row in reader:

				if(row[0] == "isbn"):
					continue;

				yield {
					'isbn': row[0], 
					'title': row[1],
					'author': row[2],
					'published': row[3]
					};

authors = set([])

def insert_authors():
	"""Generated data for authors"""

	# Set helps to remove duplicate records
	for row in get_data():
		authors.add(row['author'])

	# Prepare the query
	query = "INSERT INTO authors (name) VALUES "
	for author in authors:
		# Check for special characters :, '
		author = author.replace(",", " ")
		author = author.replace("'", "''")

		# Add to query
		query += f"('{author}'),"

	# Replace last comma with semicolon
	query = query[0:-1] + ';'

	# Execute the query
	db.execute(query)
	db.commit()
	print("Authors inserted successfully...")

def get_author_id(name):
	if(len(authors) <= 0):
		for row in get_data():
			authors.add(row['author'])


	# Find the author in authors set
	return list(authors).index(name) + 1


def insert_books():
	"""Generate data for books"""
	query = "INSERT INTO books (isbn, title, published, author_id) VALUES "

	count = 1
	for row in get_data():
		# Extract the data
		isbn = row["isbn"]
		title = row["title"]
		published = row["published"]
		author = get_author_id(row["author"])

		# Check for special characters :, '
		isbn = isbn.replace(",", " ")
		isbn = isbn.replace("'", "''")
		title = title.replace(",", ' ')
		title = title.replace("'", "''")

		query += f"('{isbn}', '{title}', {published}, {author}),"

	# Replace the last character with ;
	query = query[0:-1] + ';'

	# Execute the query
	db.execute(query)
	db.commit()

	print("Books inserted successfully...")

def main():
	# Alert the user
	print("="*10)
	print("Process Started: Please wait until it finishes.")
	print("You will be provided status messages during the process.")
	print("="*10)

	# Create users table
	db.execute("CREATE TABLE IF NOT EXISTS users(\
			id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
			username TEXT NOT NULL,\
			hash TEXT NOT NULL\
			)");

	# Create authors table
	db.execute("CREATE TABLE IF NOT EXISTS authors(\
		id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
		name TEXT NOT NULL\
		)");

	# Create books table
	db.execute('CREATE TABLE IF NOT EXISTS books(\
		id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
		isbn TEXT NOT NULL, \
		title TEXT NOT NULL, \
		published INTEGER NOT NULL DEFAULT 0, \
		author_id INTEGER REFERENCES authors)')

    # create reviews table
	db.execute('CREATE TABLE IF NOT EXISTS reviews(\
			id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
			book_id INTEGER NOT NULL, \
			user_id INTEGER NOT NULL, \
			rating INTEGER NOT NULL DEFAULT 0, \
			review TEXT NOT NULL DEFAULT "", \
			created_on DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)')

	db.commit()

	print("tables created successfully...")

	# Insert Authors
	insert_authors()

	# Insert Books
	insert_books()

if __name__ == "__main__":
	main()
