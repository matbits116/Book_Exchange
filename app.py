

from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'book-exchange-demo'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookexchange.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ------------------ MODELS ------------------
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    author = db.Column(db.String(120), nullable=False)
    cover_url = db.Column(db.String(300), nullable=False)
    rating_sum = db.Column(db.Integer, default=0)
    rating_count = db.Column(db.Integer, default=0)

    @property
    def average_rating(self):
        return round(self.rating_sum / self.rating_count, 1) if self.rating_count else 0

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)

# ------------------ ROUTES ------------------
@app.before_request
def setup():
    db.create_all()
    if Book.query.count() == 0:
        demo_books = [
            Book(title="The Great Gatsby", author="F. Scott Fitzgerald",
                 cover_url="https://covers.openlibrary.org/b/id/8675325-L.jpg", rating_sum=9, rating_count=2),
            Book(title="To Kill a Mockingbird", author="Harper Lee",
                 cover_url="https://covers.openlibrary.org/b/id/8228691-L.jpg", rating_sum=5, rating_count=1),
            Book(title="1984", author="George Orwell",
                 cover_url="https://covers.openlibrary.org/b/id/7222246-L.jpg", rating_sum=4, rating_count=1),
            Book(title="Pride and Prejudice", author="Jane Austen",
                 cover_url="https://covers.openlibrary.org/b/id/8091016-L.jpg", rating_sum=9, rating_count=2),
        ]
        db.session.bulk_save_objects(demo_books)
        db.session.commit()

@app.route('/', methods=['GET', 'POST'])
def home():
    search_term = ''
    books = Book.query.all()
    if request.method == 'POST' and 'search' in request.form:
        search_term = request.form['search']
        books = Book.query.filter(
            (Book.title.ilike(f'%{search_term}%')) | (Book.author.ilike(f'%{search_term}%'))
        ).all()
        if not books:
            flash(f"No books found for '{search_term}'.", 'info')

    book_of_the_day = Book.query.first()
    messages = Message.query.all()
    return render_template('index.html',
                           title='Book Exchange Platform',
                           books=books,
                           search_term=search_term,
                           user=session.get('user'),
                           book_of_the_day=book_of_the_day,
                           messages=messages)


from werkzeug.security import generate_password_hash, check_password_hash

# ------------------ AUTH ROUTES ------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm']

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            # Save both username and user_id in session
            session['user'] = user.username
            session['user_id'] = user.id  

            flash(f'Welcome, {user.username}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')



@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('user_id', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))



@app.route('/list', methods=['POST'])
def list_book():
    title = request.form['title']
    author = request.form['author']
    cover_url = request.form.get('coverUrl') or 'https://via.placeholder.com/120x180?text=No+Cover'
    new_book = Book(title=title, author=author, cover_url=cover_url)
    db.session.add(new_book)
    db.session.commit()
    flash('Book listed successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/rate', methods=['POST'])
def rate_book():
    title = request.form['title']
    stars = int(request.form['stars'])
    book = Book.query.filter_by(title=title).first()
    if book:
        book.rating_sum += stars
        book.rating_count += 1
        db.session.commit()
        flash('Thank you for rating!', 'success')
    return redirect(url_for('home'))

@app.route('/browse')
def browse():
    books = Book.query.all()
    return render_template('browse.html', title='Book Exchange Platform', books=books)

@app.route('/contact', methods=['POST'])
def contact():
    email = request.form['email']
    message = request.form['message']
    new_message = Message(email=email, message=message)
    db.session.add(new_message)
    db.session.commit()
    flash('Message sent!', 'success')
    return redirect(url_for('thankyou'))

@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')

# ------------------ MAIN ------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
