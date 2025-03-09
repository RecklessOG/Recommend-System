import pickle
import requests
import urllib.request
import bs4 as bs
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify
from flask_mysqldb import MySQL
from flask import flash  # ✅ Import flash for alerts
from werkzeug.security import generate_password_hash  # ✅ Import this to fix error
import hashlib
import MySQLdb.cursors

from flask import current_app


from flask import Flask, render_template, request, session, redirect, url_for
from datetime import timedelta


from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load NLP model and TF-IDF vectorizer
filename = 'nlp_model.pkl'
clf = pickle.load(open(filename, 'rb'))
vectorizer = pickle.load(open('tranform.pkl', 'rb'))

# Global Variables for Data & Similarity Matrix
data = None
similarity_matrix = None

# Create similarity matrix
def create_similarity():
    global data, similarity_matrix

    print("Loading dataset and generating similarity matrix...")

    # Load dataset
    data = pd.read_csv('main_data.csv')

    # Vectorizing 'comb' column
    cv = CountVectorizer()
    count_matrix = cv.fit_transform(data['comb'])

    # Compute similarity matrix
    similarity_matrix = cosine_similarity(count_matrix)

    print(f"Similarity Matrix Created: Shape {similarity_matrix.shape}")

# Movie recommendation function
def rcmd(m):
    global data, similarity_matrix

    # Ensure data & similarity_matrix are loaded
    if data is None or similarity_matrix is None:
        create_similarity()

    m = m.lower()
    print(f"Searching recommendations for: {m}")

    # Check if movie exists
    if m not in data['movie_title'].str.lower().unique():
        print("Movie not found in dataset!")
        return ['Sorry! Try another movie name.']

    # Find index of the movie
    i = data[data['movie_title'].str.lower() == m].index[0]
    print(f"Movie index: {i}")

    # Get similarity scores
    lst = list(enumerate(similarity_matrix[i]))
    lst = sorted(lst, key=lambda x: x[1], reverse=True)[1:11]  # Top 10 recommendations

    recommendations = [data['movie_title'][item[0]] for item in lst]
    print(f"Recommendations: {recommendations}")

    return recommendations

# Get movie suggestions
def get_suggestions():
    global data
    if data is None:
        data = pd.read_csv('main_data.csv')
    return list(data['movie_title'].str.capitalize())

# Flask App
app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # 🔑 Add this line
app.permanent_session_lifetime = timedelta(days=1)
# MySQL Configuration (ADD THIS)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'  # Change if needed
app.config['MYSQL_PASSWORD'] = ''  # Set your MySQL password
app.config['MYSQL_DB'] = 'login'  # Change this to your DB name
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'  # Returns results as dictionaries

# Initialize MySQL
mysql = MySQL(app)


@app.before_request
def make_session_permanent():
    session.permanent = True  # Ensure the session persists

    if 'email' in session:  # If a user is logged in
        try:
            # Step 1: Connect to MySQL
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

            # Step 2: Check if the user exists in the database
            cursor.execute("SELECT * FROM users WHERE email = %s", (session['email'],))
            user = cursor.fetchone()  # Fetch user data

            # Step 3: Close the database connection
            cursor.close()

            # Step 4: If user is not found, clear the session
            if not user:
                session.clear()

        except Exception as e:
            print("Database error:", e)  # Print any errors


@app.route("/")
@app.route("/")
@app.route("/home")
def home():
    user = request.args.get('user')  # Get username from PHP redirect
    email = request.args.get('email')  # Get email from PHP redirect

    if user:
        session['user'] = user  # Store full name
    if email:
        session['email'] = email  # Store email for watchlist

    print("Stored in Session:", session.get('user'), session.get('email'))  # Debugging line

    return render_template('home.html', user=session.get('user'))


@app.route("/logout")
def logout():
    # Clear Flask session data
    session.clear()

    # Redirect to home page
    response = redirect(url_for('home'))

    # Delete Flask session cookie
    response.delete_cookie('session')

    # Delete PHP session cookie (assuming it's named 'PHPSESSID')
    response.delete_cookie('PHPSESSID')  # This ensures PHP session is truly destroyed

    return response

@app.route("/similarity", methods=["POST"])
def similarity():
    movie = request.form['name']
    recommendations = rcmd(movie)

    if isinstance(recommendations, list):
        return jsonify({"status": "success", "recommendations": recommendations})
    else:
        return jsonify({"status": "error", "message": recommendations})

# IMDb Review Scraper
@app.route("/recommend", methods=["POST"])
def recommend():
    print("Fetching IMDb reviews...")
    imdb_id = request.form['imdb_id']
    url = f"https://www.imdb.com/title/{imdb_id}/reviews?ref_=tt_ov_rt"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"IMDb Response Status: {response.status_code}")

        if response.status_code != 200:
            return jsonify({"status": "error", "message": "IMDb did not return a valid response."})

        soup = BeautifulSoup(response.text, "html.parser")

        # Try different class names for review extraction
        review_containers = soup.find_all("div", class_="text show-more__control")  # Old Class
        if not review_containers:
            review_containers = soup.find_all("span", class_="sc-16ede01-2")  # Alternative Class
        if not review_containers:
            review_containers = soup.find_all("div", class_="text")  # Another possible class

        # Extract and filter reviews
        reviews_list = [r.get_text().strip() for r in review_containers if len(r.get_text().strip()) > 30]

        print(f"Extracted {len(reviews_list)} reviews.")
        if reviews_list:
            print("Sample Review:", reviews_list[0])
        else:
            # Fix: Return default message if no reviews are found
            reviews_list = ["No reviews available."]

    except requests.exceptions.RequestException as e:
        print(f"Error fetching reviews: {e}")
        return jsonify({"status": "error", "message": "Error fetching reviews."})

    return jsonify({"status": "success", "reviews": reviews_list})

# **Fix Autocomplete Data API** (Fixes films error)
@app.route("/autocomplete", methods=["GET"])
def autocomplete():
    suggestions = get_suggestions()
    return jsonify({"films": suggestions})


@app.route('/watchlist')
def watchlist():
    if 'email' not in session:
        return redirect(url_for('home'))  # Redirect if not logged in

    user_email = session.get('email')

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT movie_id, movie_title FROM watchlist WHERE user_email = %s", (user_email,))
    watchlist_movies = cursor.fetchall()
    cursor.close()

    print("Watchlist Movies from DB:", watchlist_movies)  # Debugging

    watchlist = [{"movie_id": movie["movie_id"], "movie_title": movie["movie_title"]} for movie in watchlist_movies]
    print("Processed Watchlist Data:", watchlist)  # Debugging

    return render_template('watchlist.html', watchlist=watchlist, user=session.get('user'))




@app.route('/add_to_watchlist', methods=['POST'])
def add_to_watchlist():
    if 'user' not in session:
        return jsonify({"error": "User not logged in"}), 401

    session_user = session.get('user')  # Get session value
    print("Session user value:", session_user)  # Debugging

    cursor = mysql.connection.cursor()

    # Debugging: Print all users to check if `firstname` exists
    cursor.execute("SELECT firstname, email FROM users")
    all_users = cursor.fetchall()
    print("Database Users:", all_users)  # Debugging

    # Extract first name from session['user']
    first_name = session_user.split()[0] if session_user else None
    print("Extracted First Name:", first_name)  # Debugging

    cursor.execute("SELECT email FROM users WHERE firstname = %s", (first_name,))
    result = cursor.fetchone()
    cursor.close()

    print("Query Result:", result)  # Debugging

    if not result:
        return jsonify({"error": "User email not found in database"}), 500

    # FIX: Access email correctly from dictionary
    user_email = result['email']
    print("Resolved User Email:", user_email)  # Debugging

    user_email = result["email"]  # ✅ Correct (accessing by key)
    print("Resolved User Email:", user_email)  # Debugging

    movie_id = request.form.get('movie_id')
    movie_title = request.form.get('movie_title')

    if not movie_id or not movie_title:
        return jsonify({"error": "Invalid movie data"}), 400

    cursor = mysql.connection.cursor()

    # Check if movie already exists in watchlist
    cursor.execute("SELECT * FROM watchlist WHERE user_email = %s AND movie_id = %s", (user_email, movie_id))
    existing_movie = cursor.fetchone()

    if existing_movie:
        cursor.close()
        return jsonify({"message": "Movie already in watchlist"}), 409

    # Insert into watchlist
    cursor.execute("INSERT INTO watchlist (user_email, movie_id, movie_title) VALUES (%s, %s, %s)",
                   (user_email, movie_id, movie_title))
    mysql.connection.commit()
    cursor.close()

    return jsonify({"message": "Movie added to watchlist successfully"}), 200


@app.route('/trailer/<int:movie_id>')
def trailer(movie_id):
    TMDB_API_KEY = "64e7a74b2de23c092d569c61618303f9"  # 🔑 Your API Key directly here
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={TMDB_API_KEY}&language=en-US"

    print("Fetching trailer for Movie ID:", movie_id)  # Debugging
    trailer_url = None

    try:
        response = requests.get(url).json()
        print("TMDb API Response:", response)  # Debugging

        if 'results' in response and response['results']:
            for video in response['results']:
                if video['type'] == 'Trailer' and video['site'] == 'YouTube':
                    trailer_url = f"https://www.youtube.com/embed/{video['key']}"
                    print("Trailer Found:", trailer_url)  # Debugging
                    break
        else:
            print("No Trailer Found")
            trailer_url = None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching trailer: {e}")
        trailer_url = None

    return render_template('trailer.html', trailer_url=trailer_url)



@app.route('/trailer')
def trailer_page_manual():
    return render_template('trailer.html', trailer_url=None)

@app.route('/check_session')
def check_session():
    return jsonify(dict(session))

@app.route('/remove_from_watchlist', methods=['POST'])
def remove_from_watchlist():
    # Debugging: Print session data
    print("Session data:", session)

    if 'email' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'})

    user_email = session['email']
    movie_id = request.json.get('movie_id')

    if not movie_id:
        return jsonify({'success': False, 'message': 'No movie ID provided'})

    try:
        # Use the flask_mysqldb connection to the database
        conn = mysql.connection
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM watchlist WHERE user_email = %s AND movie_id = %s", (user_email, movie_id))
        result = cursor.fetchone()

        if result:
            cursor.execute("DELETE FROM watchlist WHERE user_email = %s AND movie_id = %s", (user_email, movie_id))
            conn.commit()
            message = "Movie removed successfully."
        else:
            message = "Movie not found in the watchlist."

        cursor.close()

        return jsonify({'success': True, 'message': message})

    except Exception as err:
        print("Error:", err)
        return jsonify({'success': False, 'message': 'Database error'})



def get_current_user():
    if 'email' not in session:
        return None

    email = session['email']
    print(f"🟢 Fetching user from DB using email: {email}")

    try:
        conn = mysql.connection
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)  # Correct cursor type

        query = "SELECT id, firstname, lastname, email, password FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()  # Fetch user data from DB

        cursor.close()

        if user:
            print(f"✅ User found: {user}")  # Should now show real data
            return user
        else:
            print("❌ User not found in database")
            return None

    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return None

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    user = get_current_user()
    if not user:
        flash("User not found", "danger")  # Use flash for error message
        return render_template('edit_profile.html', user=None)

    if request.method == 'POST':
        try:
            new_firstname = request.form.get('firstname', '').strip()
            new_lastname = request.form.get('lastname', '').strip()
            new_email = request.form.get('email', '').strip()
            new_password = request.form.get('password', '').strip()

            conn = mysql.connection
            cursor = conn.cursor()

            if new_password:
                hashed_password = hashlib.md5(new_password.encode()).hexdigest()
                query = """
                    UPDATE users
                    SET firstname = %s, lastname = %s, email = %s, password = %s
                    WHERE id = %s
                """
                values = (new_firstname, new_lastname, new_email, hashed_password, user['id'])
            else:
                query = """
                    UPDATE users
                    SET firstname = %s, lastname = %s, email = %s
                    WHERE id = %s
                """
                values = (new_firstname, new_lastname, new_email, user['id'])

            cursor.execute(query, values)
            conn.commit()
            cursor.close()

            # Update session email
            session['email'] = new_email

            flash("Profile updated successfully!", "success")  # ✅ Flash message added

        except Exception as e:
            flash("Error updating profile. Please try again.", "danger")  # Error flash message
            print(f"❌ Error updating profile: {str(e)}")

    return render_template('edit_profile.html', user=get_current_user())

@app.route('/test_db')
def test_db():
    try:
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE();")  # Check current database
        db_name = cursor.fetchone()

        cursor.execute("SHOW TABLES;")  # Check if tables exist
        tables = cursor.fetchall()

        cursor.close()
        return f"✅ Connected to DB: {db_name}<br>✅ Tables: {tables}"

    except Exception as e:
        return f"❌ Database connection failed: {e}"


@app.route('/submit_review', methods=['GET', 'POST'])
def submit_review():
    if 'email' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    if request.method == 'POST':
        review = request.form['review']

        # Get user_id from email
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT id FROM users WHERE email = %s", (session['email'],))
        user = cursor.fetchone()

        if user:
            user_id = user['id']

            # Insert review into database
            cursor.execute("INSERT INTO reviews (user_id, review_text) VALUES (%s, %s)", (user_id, review))
            mysql.connection.commit()
            cursor.close()

            flash("Review submitted successfully!", "success")  # ✅ Flash success message

    return render_template('submit_review.html')  # ✅ Stay on the same page


@app.route('/all_reviews')
def all_reviews():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT reviews.review_text, users.firstname, users.lastname
        FROM reviews
        JOIN users ON reviews.user_id = users.id
        ORDER BY reviews.id DESC
    """)
    reviews = cursor.fetchall()
    cursor.close()

    return render_template('all_reviews.html', reviews=reviews)


@app.route('/watchlist_recommendations')
def watchlist_recommendations():
    user = get_current_user()
    if not user:
        return redirect(url_for('home'))

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT movie_id FROM watchlist WHERE user_email = %s", (session['email'],))
    watchlist_movies = cursor.fetchall()
    cursor.close()

    if not watchlist_movies:
        return render_template("watchlist_recommend.html", recommendations=[])

    movie_ids = [movie['movie_id'] for movie in watchlist_movies]

    tmdb_api_key = "64e7a74b2de23c092d569c61618303f9"
    recommendations = []

    for movie_id in movie_ids:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}/recommendations"
        params = {"api_key": tmdb_api_key, "language": "en-US", "page": 1}  # Fetch only first page

        try:
            response = requests.get(url, params=params, timeout=5)  # Add timeout to prevent delays
            response.raise_for_status()  # Raise error if request fails
            data = response.json()

            movie_recommendations = data.get("results", [])[:10]  # Limit to 10 movies

            # Reduce image size for faster loading
            for movie in movie_recommendations:
                poster_path = movie.get('poster_path', '')
                movie[
                    'poster_url'] = f"https://image.tmdb.org/t/p/w300{poster_path}" if poster_path else "/static/default-image.jpg"

            recommendations.extend(movie_recommendations)
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Error fetching recommendations for {movie_id}: {e}")

    return render_template("watchlist_recommend.html", recommendations=recommendations)


@app.route('/submit_rating', methods=['POST'])
def submit_rating():
    if 'email' not in session:
        return jsonify({"alert": "Please log in to submit a rating."})  # Send an alert message instead of a 401 error

    data = request.get_json()
    if not data or 'movie_id' not in data or 'rating' not in data:
        return jsonify({"error": "Invalid data"}), 400

    movie_id = data['movie_id']
    rating = data['rating']

    try:
        conn = MySQLdb.connect(host="localhost", user="root", passwd="", db="login")
        cursor = conn.cursor()

        # Get user ID based on session email
        cursor.execute("SELECT id FROM users WHERE email = %s", (session['email'],))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        user_id = user[0]

        # Check if the user has already rated this movie
        cursor.execute("SELECT rating FROM ratings WHERE user_id = %s AND movie_id = %s", (user_id, movie_id))
        existing_rating = cursor.fetchone()

        if existing_rating:
            # If a rating exists, update it instead of inserting a new one
            cursor.execute("UPDATE ratings SET rating = %s WHERE user_id = %s AND movie_id = %s",
                           (rating, user_id, movie_id))
            message = "Rating updated successfully!"
        else:
            # Insert new rating
            cursor.execute("INSERT INTO ratings (user_id, movie_id, rating) VALUES (%s, %s, %s)",
                           (user_id, movie_id, rating))
            message = "Rating submitted successfully!"

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": message, "previous_rating": rating}), 200

    except MySQLdb.Error as e:
        print(f"❌ Database Error: {e}")
        return jsonify({"error": "Database error"}), 500


@app.route('/get_rating', methods=['GET'])
def get_rating():
    if 'email' not in session:
        return jsonify({"error": "User not logged in"}), 401  # Unauthorized

    movie_id = request.args.get('movie_id')
    if not movie_id:
        return jsonify({"error": "Movie ID missing"}), 400

    try:
        conn = MySQLdb.connect(host="localhost", user="root", passwd="", db="login")
        cursor = conn.cursor()

        # Get user ID
        cursor.execute("SELECT id FROM users WHERE email = %s", (session['email'],))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        user_id = user[0]

        # Fetch previous rating
        cursor.execute("SELECT rating FROM ratings WHERE user_id = %s AND movie_id = %s", (user_id, movie_id))
        existing_rating = cursor.fetchone()

        cursor.close()
        conn.close()

        if existing_rating:
            return jsonify({"rating": existing_rating[0]}), 200
        else:
            return jsonify({"rating": None}), 200

    except MySQLdb.Error as e:
        print(f"❌ Database Error: {e}")
        return jsonify({"error": "Database error"}), 500


@app.route('/ratings')
def ratings_page():
    conn = MySQLdb.connect(host="localhost", user="root", passwd="", db="login")
    cursor = conn.cursor()

    # Fetch average ratings per movie
    cursor.execute("""
        SELECT ratings.movie_id, ROUND(AVG(ratings.rating), 1) AS avg_rating
        FROM ratings
        GROUP BY ratings.movie_id
    """)
    avg_ratings = cursor.fetchall()
    cursor.close()
    conn.close()

    # TMDb API key
    TMDB_API_KEY = "64e7a74b2de23c092d569c61618303f9"

    # Fetch movie titles in one batch
    movie_titles = {}
    for movie_id, _ in avg_ratings:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            movie_titles[movie_id] = response.json().get("title", "Unknown Movie")
        else:
            movie_titles[movie_id] = "Unknown Movie"

    # Replace movie_id with movie titles
    avg_ratings = [(movie_titles.get(movie_id, "Unknown Movie"), avg_rating) for movie_id, avg_rating in avg_ratings]

    return render_template("ratings.html", avg_ratings=avg_ratings)







if __name__ == '__main__':
    create_similarity()  # Load similarity matrix at startup
    app.run(debug=True)
