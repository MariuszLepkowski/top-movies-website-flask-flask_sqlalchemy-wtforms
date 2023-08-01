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


##CREATE DB
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///favorite-movies.db"
db = SQLAlchemy()
db.init_app(app)


##CREATE TABLE
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()

## After adding the new_movie the code needs to be commented out/deleted.
## So you are not trying to add the same movie twice. The db will reject non-unique movie titles.
# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
# with app.app_context():
#     db.session.add(new_movie)
#     db.session.commit()

# second_movie = Movie(
#     title="Avatar The Way of Water",
#     year=2022,
#     description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
#     rating=7.3,
#     ranking=9,
#     review="I liked the water.",
#     img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
# )
#
# with app.app_context():
#     db.session.add(second_movie)
#     db.session.commit()


# third_movie = Movie(
#     title="Drive",
#     year=2011,
#     description="A mysterious Hollywood stuntman and mechanic moonlights as a getaway driver and finds himself in trouble when he helps out his neighbor in this action drama.",
#     rating=7.5,
#     ranking=1,
#     review="Loved it!""I liked the water.",
#     img_url="https://www.shortlist.com/media/images/2019/05/the-30-coolest-alternative-movie-posters-ever-2-1556670563-K61a-column-width-inline.jpg"
# )

# with app.app_context():
#     db.session.add(third_movie)
#     db.session.commit()


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
                'release_date': movie['release_date']
            }
            movies_to_select.append(movie_to_select)
        return render_template("select.html", movies=movies_to_select)

    return render_template("add.html", form=form)


if __name__ == '__main__':
    app.run(debug=True)
