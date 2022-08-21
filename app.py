from flask import Flask, session, request, render_template, redirect, url_for, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from constants import SQLITE_DB_URI, SESSION_SECRET

# create application and configure session.
app = Flask(__name__)

# configure application session
app.secret_key = SESSION_SECRET

# Set up database
engine = create_engine(SQLITE_DB_URI)
db = scoped_session(sessionmaker(bind=engine))


# ==============================
#       Helper Functions
# ==============================

def checkUserAuthStatus():
    """Checks if a user is authenticated."""
    try:
        username = session['username']
        return True if len(username) >= 4 else False
    except KeyError:
        return False


def getBooksByTitle(title):
    """Searches for books by title."""

    books = db.execute("SELECT books.id as id, isbn, name AS author, title, \
                published FROM books JOIN authors ON \
                books.author_id = authors.id \
                WHERE title LIKE :query LIMIT 20;", {
        "query": title
    })

    return list(books)


def getBooksByIsbn(isbn):
    books = db.execute("SELECT books.id as id, isbn, name AS author, title, \
                published FROM books JOIN authors ON \
                books.author_id = authors.id \
                WHERE isbn LIKE :query LIMIT 20;", {
        "query": isbn
    })

    return list(books)


def getBooksByAuthor(author):
    books = db.execute("SELECT books.id as id, isbn, name AS author, title, \
                published FROM books JOIN authors ON \
                books.author_id = authors.id \
                WHERE authors.name LIKE :query LIMIT 20;", {
        "query": author
    })

    return list(books)


def getBookById(id):
    """Returns a book by its id."""
    book = db.execute("""
                        SELECT 
                            books.id as id,
                            books.title as title,
                            books.isbn as isbn,
                            books.published as published,
                            authors.name as author
                        FROM books
                        JOIN authors
                        ON
                            books.author_id = authors.id
                        WHERE books.id = :id;""", {"id": id})
    try:
        # Convert the book to dictionary
        book = list(book)[0]
        return {
            "id": book[0],
            "title": book[1],
            "isbn": book[2],
            "published": book[3],
            "author": book[4]
        }
    except IndexError:
        return None


def getBookReviewsByUser(book_id, username):
    """Returns reviews of a book by username """

    review = db.execute("""
                        SELECT
                            reviews.review as text,
                            reviews.created_on as created_on,
                            reviews.rating as rating
                        FROM users
                        INNER JOIN reviews ON
                        users.id = reviews.user_id
                        WHERE 
                            reviews.book_id = :book_id
                        AND
                            users.username = :username
                    """, {"book_id": book_id, "username": username})
    try:
        review = list(review)[0]

        # Convert rating to 0 to 100%

        return {
            "text": review[0],
            "created_on": review[1],
            "rating": int(review[2]) * 20
        }

    except IndexError:
        return None


def addReviewByBookId(book_id, rating, review):
    try:
        # Find the user id via username
        user_id = db.execute("SELECT id FROM users WHERE username=:username;", {
            "username": session["username"]
        })

        user_id = list(user_id)[0][0]

        # Insert the review
        db.execute("INSERT INTO reviews (book_id, user_id, rating, review) VALUES (:book, :user, :rating, :review)", {
            "book": book_id,
            "user": user_id,
            "rating": rating,
            "review": review
        })

        # Commit the changes
        db.commit()

        # Return the success
        return True

    except Exception as ex:
        return False


# ==============================
#       Logged in routes
# ==============================

@app.route("/", methods=['GET', 'POST'])
def index():
    # Check if user is logged in
    if checkUserAuthStatus():
        if (request.method == 'GET'):
            return render_template('index.html', books=None)

        if (request.method == "POST"):
            query = request.form.get('query')
            criteria = request.form.get('search-criteria')
            query = "%" + query + "%"

            # Store the books
            books = []

            # Get Results based on criteria
            if (criteria == 'title'):
                books = getBooksByTitle(query)
            elif criteria == 'isbn':
                books = getBooksByIsbn(query)
            elif criteria == 'author':
                books = getBooksByAuthor(query)
            else:
                books = None

            # Display the list of books.
            return render_template('index.html', books=books)

    return redirect('/login')


@app.route('/book/details/<int:id>')
def details(id):
    # Retrieve book via provided id
    book = getBookById(id)

    # Get book reviews
    review = getBookReviewsByUser(id, session.get('username'))

    # Render the details page
    return render_template('details.html', data={
        "book": book,
        "review": review,
    })


@app.route('/book/reviews/add', methods=["POST"])
def addReview():
    book_id = request.form.get('book-id')
    rating = request.form.get('rating')
    review = request.form.get('review')

    # Add review to database
    status = addReviewByBookId(book_id, rating, review)

    # Redirect the user to book detail page
    if status:
        return redirect(f"/book/details/{book_id}")

    return render_template("error.html", error="Something went wrong. We could not add review at this time. Please try again.")


@app.route('/instuctions')
def instructions():
    return render_template('instructions.html')


@app.route('/api/<string:isbn>')
def apiReview(isbn):
    # Get Book details by ISBN
    books = db.execute("""
                        SELECT 
                            books.title as title,
                            authors.name as author,
                            books.published as year,
                            books.isbn as isbn
                        FROM books
                        JOIN authors
                        ON books.author_id = authors.id
                        WHERE books.isbn = :isbn
                    """, {
        "isbn": isbn
    })

    try:
        books = list(books)[0]
    except:
        return jsonify({"error": "Book with given isbn not found in the database."}), 404

    # Create a result object
    result = {
        "title": books[0],
        "author": books[1],
        "year": books[2],
        "isbn": books[3],
    }

    return jsonify(result)


# ===========================
#    Authenticate Routes
# ===========================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """ Handles User Login """

    if (request.method == "GET"):
        if checkUserAuthStatus():
            return redirect('/')

        return render_template("login.html", error=None)

    if (request.method == "POST"):
        username = request.form.get('username')
        password = request.form.get('password')

        # check for the valid username and password
        if (len(username) <= 3):
            return render_template('login.html', error="Username should be of minimum 4 characters")

        if (len(password) <= 6):
            return render_template('login.html', error="Password should be of minimum 7 characters")

        # Get user from database
        user = db.execute('SELECT username, hash FROM users WHERE username=:username AND hash=:hash',
                          {"username": username, "hash": password})

        if len(list(user)) != 1:
            return render_template("login.html", error="User does not exists or Invalid Credentials provided.")
        else:
            session['username'] = username
            return redirect("/")


@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/signup', methods=["GET", 'POST'])
def signup():
    if (request.method == "GET"):
        # Check if user is logged in
        if checkUserAuthStatus():
            return redirect('/')

        return render_template("signup.html", error=None)

    if (request.method == "POST"):
        username = request.form.get('username')
        password = request.form.get('password')
        confirmPassword = request.form.get('confirm-password')

        # Make sure passwords match
        if (password != confirmPassword):
            return render_template("signup.html", error="Passwords do not match. please enter passwords again.")

        # check for the valid username and password
        if (len(username) <= 3):
            return render_template('signup.html', error="Username should be of minimum 4 characters")

        if (len(password) <= 6):
            return render_template('signup.html', error="Password should be of minimum 7 characters")

        # Check if user already exists with same username
        users = db.execute("SELECT username FROM users WHERE username=:username", {"username": username})

        if (len(list(users)) != 0):
            return render_template("signup.html", error="User already exists with same username.")

        # Insert the user in database
        try:
            db.execute('INSERT INTO users (username, hash) VALUES(:username, :hash)',
                       {"username": username, "hash": password})
            db.commit()

            # Update the session
            session['username'] = username

            # Redirect the user to home page
            return redirect("/")
        except Exception as ex:
            return render_template("signup.html", error="User cannot be created. Some error occured.")

        return render_template("signup.html", error=None)
