from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os
from dotenv import load_dotenv


load_dotenv()

TOKEN = os.getenv('TOKEN')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
Bootstrap5(app)


# CREATE DB
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///favorite-movies.db"
db = SQLAlchemy()
db.init_app(app)


# CREATE TABLE
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True, default=0.0)
    ranking = db.Column(db.Integer, nullable=True, default=0.0)
    review = db.Column(db.String(250), nullable=True, default='')
    img_url = db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()


# CREATE A FORM
class RateMovieForm(FlaskForm):
    rating = StringField(
        label="Your rating out of 10 e. g. 7.5",
        validators=[DataRequired()],
    )

    review = StringField(
        label="Your review",
        validators=[DataRequired()],
    )

    submit = SubmitField(label="Done")


class AddMovie(FlaskForm):
    title = StringField(
        label="Movie Title",
        validators=[DataRequired()]
    )

    submit = SubmitField(label="Add Movie")


@app.route("/")
def home():
    movies = db.session.execute(db.select(Movie).order_by(Movie.rating)).scalars()
    return render_template("index.html", movies=movies)


@app.route("/edit", methods=['POST', 'GET'])
def edit_rating_review():
    movie_id = request.args.get('id')
    movie_selected = db.get_or_404(Movie, movie_id)
    form = RateMovieForm()

    if request.method == 'POST':
        movie_selected.rating = request.form["rating"]
        movie_selected.review = request.form["review"]
        db.session.commit()
        return redirect(url_for('home'))

    return render_template("edit.html", form=form, movie=movie_selected)


@app.route("/delete", methods=['GET'])
def delete_movie():
    movie_id = request.args.get('id')
    movie_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=['GET', 'POST'])
def add_movie():
    form = AddMovie()

    if request.method == 'POST' and form.validate_on_submit():

        headers = {
            "accept": "application/json",
            "Authorization": TOKEN,
        }

        parameters = {
            "query": form.title.data,
        }

        url = "https://api.themoviedb.org/3/search/movie"
        response = requests.get(url=url, params=parameters, headers=headers)
        search_results = response.json()

        movies_to_select = []

        for movie in search_results['results']:
            movie_to_select = {
                'title': movie['title'],
                'release_date': movie['release_date'],
                'id': movie['id']
            }

            movies_to_select.append(movie_to_select)
        return render_template("select.html", movies=movies_to_select)
    return render_template("add.html", form=form)


@app.route("/get_movie_details/<int:movie_id>", methods=['GET', 'POST'])
def add_selected_movie(movie_id):
    headers = {
        "accept": "application/json",
        "Authorization": TOKEN,
    }

    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    response = requests.get(url=url, headers=headers)
    movie_details = response.json()

    # Extract the required movie details from the API response
    title = movie_details['title']
    img_url = f"https://image.tmdb.org/t/p/w500/{movie_details['poster_path']}"
    year = movie_details['release_date']
    description = movie_details['overview']

    # Check if the movie with the same title already exists in the database
    existing_movie = Movie.query.filter_by(title=title).first()

    if existing_movie:
        # If the movie exists, redirect to the edit page for that movie
        return redirect(url_for('edit_rating_review', id=existing_movie.id))

    # Create a new Movie object with the extracted details

    new_movie = Movie(
        title=title,
        img_url=img_url,
        year=year,
        description=description,
    )

    with app.app_context():
        db.session.add(new_movie)
        db.session.commit()

    if new_movie.id is None:
        new_movie.id = generate_unique_id()

    return redirect(url_for('edit_rating_review', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
