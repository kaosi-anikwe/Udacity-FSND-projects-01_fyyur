# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

from curses.ascii import NUL
import json
from os import abort
import re
from unicodedata import name
from urllib import response
import dateutil.parser
import babel
from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    Response,
    flash,
    redirect,
    url_for,
    abort,
)
import sys
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
from models import *


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    if isinstance(value, str):
        date = dateutil.parser.parse(value)
    else:
        date = value
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale="en")


app.jinja_env.filters["datetime"] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    # Show recently listed artists
    artists = []
    get_artists = Artist.query.order_by(Artist.id.desc()).limit(10).all()
    for artist in get_artists:
        artists.append({"id": artist.id, "name": artist.name})
    # Show recently listed venues
    venues = []
    get_venues = Venue.query.order_by(Venue.id.desc()).limit(10).all()
    for venue in get_venues:
        venues.append({"id": venue.id, "name": venue.name})
    return render_template("pages/home.html", artists=artists, venues=venues)


#  Venues
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():
    # TODO: replace with real venues data.
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    real_data = []
    distinct = Venue.query.distinct(Venue.city, Venue.state).all()
    for i in range(len(distinct)):
        real_data.append(
            {
                "city": distinct[i].city,
                "state": distinct[i].state,
                "venues": [],
            }
        )
        venues = Venue.query.filter_by(
            city=real_data[i]["city"], state=real_data[i]["state"]
        ).all()
        for venue in venues:
            upcoming = Shows.query.filter(
                Shows.venue_id == venue.id, Shows.start_time > datetime.now()
            ).all()
            real_data[i]["venues"].append(
                {
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": len(upcoming),
                }
            )

    return render_template("pages/venues.html", areas=real_data)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get("search_term")
    search = "%{}%".format(search_term)
    results = Venue.query.filter(Venue.name.ilike(search)).all()
    dbresponse = {"count": len(results), "data": []}
    for result in results:
        upcoming = Shows.query.filter(
            Shows.venue_id == result.id, Shows.start_time > datetime.now()
        ).all()
        dbresponse["data"].append(
            {
                "id": result.id,
                "name": result.name,
                "num_upcoming_shows": len(upcoming),
            }
        )

    return render_template(
        "pages/search_venues.html",
        results=dbresponse,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/venues/search/city_state", methods=["POST"])
def search_venue_city_state():
    # Search venue by city and state
    response = {"count": 0, "data": []}
    search_term = request.form.get("search_term")
    search = search_term.split(", ")
    if len(search) < 2:
        flash("Invalid input. Format: city, state")
        abort(500)
    venues = Venue.query.filter(
        Venue.city.ilike(search[0]), Venue.state.ilike(search[1])
    ).all()
    if venues == []:
        return render_template(
            "pages/cs_search_artists.html", results=response
        )
    else:
        for venue in venues:
            response["data"].append({"id": venue.id, "name": venue.name})
        response["count"] = response["count"] + len(venues)
    return render_template(
        "pages/cs_search_artists.html",
        results=response,
        search_term=request.form.get("search_term"),
    )


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id

    dbvenue = Venue.query.get(venue_id)
    genres = VenueGenres.query.filter(VenueGenres.venue_id == venue_id).all()
    past_shows = (
        Shows.query.filter(
            Shows.venue_id == venue_id, Shows.start_time < datetime.now()
        )
        .order_by(Shows.start_time.desc())
        .all()
    )
    upcoming_shows = Shows.query.filter(
        Shows.venue_id == venue_id, Shows.start_time > datetime.now()
    ).all()

    real_data = {
        "id": dbvenue.id,
        "name": dbvenue.name,
        "genres": [],
        "address": dbvenue.address,
        "city": dbvenue.city,
        "state": dbvenue.state,
        "phone": dbvenue.phone,
        "website": dbvenue.website,
        "facebook_link": dbvenue.facebook_link,
        "seeking_talent": dbvenue.seeking_talent,
        "seeking_description": dbvenue.seeking_description,
        "image_link": dbvenue.image_link,
        "past_shows": [],
        "upcoming_shows": [],
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    # Append list of venue genres
    for genre in genres:
        real_data["genres"].append(genre.genres)
    # Append list of past shows
    for past_show in past_shows:
        artist = Artist.query.get(past_show.artist_id)
        real_data["past_shows"].append(
            {
                "artist_id": past_show.artist_id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": past_show.start_time,
            }
        )
    # Append list of upcoming shows
    for show in upcoming_shows:
        artist = Artist.query.get(show.artist_id)
        real_data["upcoming_shows"].append(
            {
                "artist_id": show.artist_id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": show.start_time,
            }
        )
    return render_template("pages/show_venue.html", venue=real_data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = VenueForm(request.form)
    if form.validate():
      try:
          name=request.form.get('name')
          genres = request.form.getlist("genres")
          seeking_talent = False
          if request.form.get("seeking_talent"):
              seeking_talent = True
          new_venue = Venue(
              name=request.form.get("name"),
              city=request.form.get("city"),
              state=request.form.get("state"),
              address=request.form.get("address"),
              phone=request.form.get("phone"),
              image_link=request.form.get("image_link"),
              facebook_link=request.form.get("facebook_link"),
              website=request.form.get("website_link"),
              seeking_talent=seeking_talent,
              seeking_description=request.form.get("seeking_description"),
          )
          db.session.add(new_venue)
          db.session.commit()
          # on successful db insert, flash success
          flash(
              'Venue: "'
              + request.form["name"]
              + '" was successfully listed!'
          )
      except:
          print(sys.exc_info())
          db.session.rollback()
          flash(
              'Something went wrong. Venue: "'
              + request.form["name"]
              + '" could not be listed.'
          )
          abort(500)
      # Add genres to VenueGenres table
      venue = Venue.query.filter_by(name=name).first()
      for genre in genres:
        try:
            new_genre = VenueGenres(venue_id=venue.id, genres=genre)
            db.session.add(new_genre)
            db.session.commit()
        except:
            print(sys.exc_info())
            db.session.rollback()
            abort(500)
      db.session.close()
      return redirect(url_for("index"))
    return render_template("forms/new_venue.html", form=form)
    
        


# Delete Venue
# ---------------------------------------------------------------


@app.route("/venues/delete/<venue_id>")
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    error = False
    try:
        venue = Venue.query.get(venue_id)
        venue_name = venue.name
        db.session.delete(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()
        if error:
            flash(
                'Venue: "'
                + venue_name
                + '" could not be deleted. Please try again.'
            )
            abort(500)
        else:
            flash('Venue: "' + venue_name + '" was deleted successfully!')
    return redirect(url_for("venues"))


# BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
# clicking that button delete it from the db then redirect the user to the homepage
@app.route("/venues/<venue_id>/delete/")
def delete_home_venue(venue_id):
    error = False
    try:
        venue = Venue.query.get(venue_id)
        venue_name = venue.name
        db.session.delete(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()
        if error:
            flash(
                'Venue: "'
                + venue_name
                + '" could not be deleted. Please try again.'
            )
            abort(500)
        else:
            flash('Venue: "' + venue_name + '" was deleted successfully!')
    return redirect(url_for("index"))


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    # TODO: replace with real data returned from querying the database
    real_data = []
    artists = Artist.query.all()
    for artist in artists:
        real_data.append({"id": artist.id, "name": artist.name})

    return render_template("pages/artists.html", artists=real_data)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get("search_term")
    search = "%{}%".format(search_term)
    results = Artist.query.filter(Artist.name.ilike(search)).all()
    dbresponse = {"count": len(results), "data": []}
    for result in results:
        upcoming = Shows.query.filter(
            Shows.artist_id == result.id, Shows.start_time > datetime.now()
        ).all()
        dbresponse["data"].append(
            {
                "id": result.id,
                "name": result.name,
                "num_upcoming_shows": len(upcoming),
            }
        )

    return render_template(
        "pages/search_artists.html",
        results=dbresponse,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/artists/search/city_state", methods=["POST"])
def search_artist_city_state():
    # Search artist by city and state
    response = {"count": 0, "data": []}
    search_term = request.form.get("search_term")
    search = search_term.split(", ")
    if len(search) < 2:
        flash("Invalid input. Format: city, state")
        abort(500)
    artists = Artist.query.filter(
        Artist.city.ilike(search[0]), Artist.state.ilike(search[1])
    ).all()
    if artists == []:
        return render_template(
            "pages/cs_search_artists.html", results=response
        )
    else:
        for artist in artists:
            response["data"].append({"id": artist.id, "name": artist.name})
        response["count"] = response["count"] + len(artists)
    return render_template(
        "pages/cs_search_artists.html",
        results=response,
        search_term=request.form.get("search_term"),
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    artist = Artist.query.get(artist_id)
    genres = ArtistGenres.query.filter_by(artist_id=artist_id).all()
    past_shows = (
        Shows.query.filter(
            Shows.artist_id == artist_id, Shows.start_time < datetime.now()
        )
        .order_by(Shows.start_time.desc())
        .all()
    )
    upcoming_shows = Shows.query.filter(
        Shows.artist_id == artist_id, Shows.start_time > datetime.now()
    ).all()
    real_data = {
        "id": artist.id,
        "name": artist.name,
        "genres": [],
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "available_start": artist.available_start,
        "available_stop": artist.available_stop,
        "past_shows": [],
        "upcoming_shows": [],
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    # Append list of artist genres
    for genre in genres:
        real_data["genres"].append(genre.genres)
    # Append list of past shows
    for past_show in past_shows:
        venue = Venue.query.get(past_show.venue_id)
        real_data["past_shows"].append(
            {
                "venue_id": past_show.venue_id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": past_show.start_time,
            }
        )
    # Append list of upcoming showws
    for show in upcoming_shows:
        venue = Venue.query.get(show.venue_id)
        real_data["upcoming_shows"].append(
            {
                "venue_id": show.venue_id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": show.start_time,
            }
        )
    return render_template("pages/show_artist.html", artist=real_data)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = {
        "id": 4,
        "name": "Guns N Petals",
        "genres": ["Rock n Roll"],
        "city": "San Francisco",
        "state": "CA",
        "phone": "326-123-5000",
        "website": "https://www.gunsnpetalsband.com",
        "facebook_link": "https://www.facebook.com/GunsNPetals",
        "seeking_venue": True,
        "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
        "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    }
    # TODO: populate form with fields from artist with ID <artist_id>
    # Get data from db by querying with <artist_id>
    artist = Artist.query.get(artist_id)
    genres = ArtistGenres.query.filter_by(artist_id=artist_id).all()
    # Create artist object from db data
    dbartist = {
        "id": artist.id,
        "name": artist.name,
        "genres": [],
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "available_start": artist.available_start,
        "available_stop": artist.available_stop,
    }
    for genre in genres:
        dbartist["genres"].append(genre.genres)
    # Pre populate form fields with db data
    myform = ArtistForm(obj=artist)
    myform.genres.data = dbartist["genres"]
    return render_template(
        "forms/edit_artist.html", form=myform, artist=dbartist
    )


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    # Check if avavilability is properly set
    available_start = request.form.get("available_start")
    available_stop = request.form.get("available_stop")
    # If availability improperly set
    if available_start and available_stop == "":
        flash("Availability not properly set")
        return redirect(url_for("edit_artist", artist_id=artist_id))
    if available_start == "" and available_stop:
        flash("Availability not properly set!")
        return redirect(url_for("create_artist_form"))

    # If availability properly set
    # Without availability-------------------
    artist = Artist.query.get(artist_id)
    artist.name = request.form.get("name")
    artist.city = request.form.get("city")
    artist.state = request.form.get("state")
    artist.phone = request.form.get("phone")
    artist.image_link = request.form.get("image_link")
    artist.facebook_link = request.form.get("facebook_link")
    artist.website = request.form.get("website_link")
    artist.seeking_description = request.form.get("seeking_description")
    # With availability-------------------
    if available_start and available_stop:
        artist.available_start = request.form.get("available_start")
        artist.available_stop = request.form.get("available_stop")

    if request.form.get("seeking_venue") == "y":
        artist.seeking_venue = True
    elif request.form.get("seeking_venue") != "y":
        artist.seeking_venue = False
    # Delete previous genres
    genres = ArtistGenres.query.filter_by(artist_id=artist_id).all()
    for genre in genres:
        db.session.delete(genre)
    # Add new genres
    new_genres = request.form.getlist("genres")
    for genre in new_genres:
        new_genre = ArtistGenres(artist_id=artist_id, genres=genre)
        db.session.add(new_genre)

    db.session.commit()
    return redirect(url_for("show_artist", artist_id=artist_id))


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    form = VenueForm()

    # TODO: populate form with values from venue with ID <venue_id>
    # Get data from db by querying with <venue_id>
    venue = Venue.query.get(venue_id)
    genres = VenueGenres.query.filter_by(venue_id=venue_id).all()
    # Create venue object with data from db
    dbvenue = {
        "id": venue.id,
        "name": venue.name,
        "genres": [],
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
    }
    for genre in genres:
        dbvenue["genres"].append(genre.genres)
    # Pre populate form fields with data from db
    myform = VenueForm(obj=venue)
    myform.genres.data = dbvenue["genres"]
    return render_template("forms/edit_venue.html", form=myform, venue=dbvenue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    venue = Venue.query.get(venue_id)
    venue.name = request.form.get("name")
    venue.city = request.form.get("city")
    venue.state = request.form.get("state")
    venue.phone = request.form.get("phone")
    venue.image_link = request.form.get("image_link")
    venue.facebook_link = request.form.get("facebook_link")
    venue.website = request.form.get("website_link")
    venue.seeking_description = request.form.get("seeking_description")

    if request.form.get("seeking_talent") == "y":
        venue.seeking_talent = True
    elif request.form.get("seeking_talent") != "y":
        venue.seeking_talent = False
    # Delete previous genres
    genres = VenueGenres.query.filter_by(venue_id=venue_id).all()
    for genre in genres:
        db.session.delete(genre)
    # Add new genres
    new_genres = request.form.getlist("genres")
    for genre in new_genres:
        new_genre = VenueGenres(venue_id=venue_id, genres=genre)
        db.session.add(new_genre)

    db.session.commit()
    return redirect(url_for("show_venue", venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    error = False
    name = request.form.get("name")
    city = request.form.get("city")
    state = request.form.get("state")
    phone = request.form.get("phone")
    image_link = request.form.get("image_link")
    genres = request.form.getlist("genres")
    facebook_link = request.form.get("facebook_link")
    website_link = request.form.get("website_link")
    seeking_venue = False
    seeking_description = request.form.get("seeking_description")
    available_start = request.form.get("available_start")
    available_stop = request.form.get("available_stop")

    if request.form.get("seeking_venue") == "y":
        seeking_venue = True

    # Check if availability is properly set
    # If availability improperly set--------------------
    if available_start and available_stop == "":
        flash("Availability not properly set!")
        return redirect(url_for("create_artist_form"))
    if available_start == "" and available_stop:
        flash("Availability not properly set!")
        return redirect(url_for("create_artist_form"))

    # If availability properly set
    # With availability-----------------------
    if available_start and available_stop:
        try:
            new_artist = Artist(
                name=name,
                city=city,
                state=state,
                phone=phone,
                image_link=image_link,
                facebook_link=facebook_link,
                website=website_link,
                seeking_venue=seeking_venue,
                seeking_description=seeking_description,
                available_start=available_start,
                available_stop=available_stop,
            )
            db.session.add(new_artist)
            db.session.commit()
        except:
            error = True
            db.session.rollback()
        finally:
            if error:
                # TODO: on unsuccessful db insert, flash an error instead.
                # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
                flash(
                    'Something went wrong. Artist: "'
                    + request.form["name"]
                    + '" could not be listed.'
                )
                abort(500)
            else:
                # on successful db insert, flash success
                flash(
                    'Artist: "'
                    + request.form["name"]
                    + '" was successfully listed!'
                )
            # Add genres to ArtistGenres table
            artist = Artist.query.filter_by(name=name, city=city).first()
            for genre in genres:
                try:
                    new_genre = ArtistGenres(artist_id=artist.id, genres=genre)
                    db.session.add(new_genre)
                    db.session.commit()
                except:
                    db.session.rollback()
                    abort(500)
            db.session.close()
    # Without availability---------------
    if available_start == "" and available_stop == "":
        try:
            new_artist = Artist(
                name=name,
                city=city,
                state=state,
                phone=phone,
                image_link=image_link,
                facebook_link=facebook_link,
                website=website_link,
                seeking_venue=seeking_venue,
                seeking_description=seeking_description,
            )
            db.session.add(new_artist)
            db.session.commit()
        except:
            error = True
            db.session.rollback()
        finally:
            # db.session.close()
            if error:
                # TODO: on unsuccessful db insert, flash an error instead.
                # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
                flash(
                    'Something went wrong. Artist: "'
                    + request.form["name"]
                    + '" could not be listed.'
                )
                abort(500)
            else:
                # on successful db insert, flash success
                flash(
                    'Artist: "'
                    + request.form["name"]
                    + '" was successfully listed!'
                )
            # Add genres to ArtistGenres table
            artist = Artist.query.filter_by(name=name, city=city).first()
            for genre in genres:
                try:
                    new_genre = ArtistGenres(artist_id=artist.id, genres=genre)
                    db.session.add(new_genre)
                    db.session.commit()
                except:
                    db.session.rollback()
                    abort(500)
            db.session.close()
    return render_template("pages/home.html")


# Delete Artist
# ---------------------------------------------------------------


@app.route("/artists/delete/<artist_id>")
def delete_artist(artist_id):
    error = False
    try:
        artist = Artist.query.get(artist_id)
        artist_name = artist.name
        db.session.delete(artist)
        db.session.commit()
    except:
        error = True
        abort(500)
    finally:
        db.session.close()
        if error:
            flash(
                'Artist: "'
                + artist_name
                + '" could not be deleted. Please try again.'
            )
        else:
            flash('Artist "' + artist_name + '" was deleted successfully!')
    return redirect(url_for("artists"))


# Delete button on artist page, redirects to home page
@app.route("/artists/<artist_id>/delete")
def delete_home_artist(artist_id):
    error = False
    try:
        artist = Artist.query.get(artist_id)
        artist_name = artist.name
        db.session.delete(artist)
        db.session.commit()
    except:
        error = True
        abort(500)
    finally:
        db.session.close()
        if error:
            flash(
                'Artist: "'
                + artist_name
                + '" could not be deleted. Please try again.'
            )
        else:
            flash('Artist "' + artist_name + '" was deleted successfully!')
    return redirect(url_for("index"))


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    real_data = []
    shows = Shows.query.order_by(Shows.start_time.desc()).all()
    for show in shows:
        venue = Venue.query.get(show.venue_id)
        artist = Artist.query.get(show.artist_id)
        real_data.append(
            {
                "venue_id": show.venue_id,
                "venue_name": venue.name,
                "artist_id": show.artist_id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": show.start_time,
            }
        )

    return render_template("pages/shows.html", shows=real_data)


@app.route("/shows/search", methods=["POST"])
def search_shows():
    # Search show by artist name or venue name
    search_term = request.form.get("search_term")
    search = "%{}%".format(search_term)
    venues = Venue.query.filter(Venue.name.ilike(search)).all()
    artists = Artist.query.filter(Artist.name.ilike(search)).all()

    response = {"count": 0, "data": []}
    # Use each result from querying venue table for search term to query shows table and append results to response object
    if venues != []:
        show_counter = 0
        for venue in venues:
            show_count = Shows.query.filter(Shows.venue_id == venue.id).all()
            show_counter = show_counter + len(show_count)
            for show in show_count:
                venue = Venue.query.get(show.venue_id)
                artist = Artist.query.get(show.artist_id)
                response["data"].append(
                    {
                        "venue_id": venue.id,
                        "venue_name": venue.name,
                        "artist_id": artist.id,
                        "artist_name": artist.name,
                        "artist_image_link": artist.image_link,
                        "start_time": show.start_time,
                    }
                )
        response["count"] = response["count"] + show_counter
    # Use each result from querying artist table for search term to query shows table and append results to response object
    elif artists != []:
        show_counter = 0
        for artist in artists:
            show_count = Shows.query.filter(Shows.artist_id == artist.id).all()
            show_counter = show_counter + len(show_count)
            for show in show_count:
                venue = Venue.query.get(show.venue_id)
                artist = Artist.query.get(show.artist_id)
                response["data"].append(
                    {
                        "venue_id": venue.id,
                        "venue_name": venue.name,
                        "artist_id": artist.id,
                        "artist_name": artist.name,
                        "artist_image_link": artist.image_link,
                        "start_time": show.start_time,
                    }
                )
        response["count"] = response["count"] + show_counter
    return render_template(
        "pages/search_shows.html",
        results=response,
        search_term=request.form.get("search_term"),
    )


@app.route("/shows/create", methods=["GET"])
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    # Artist name Venue name is drop down of all Artists and Venues in database
    form.artist_name.choices = [
        (artist.id, artist.name)
        for artist in Artist.query.order_by(Artist.name).all()
    ]
    form.venue_name.choices = [
        (venue.id, venue.name)
        for venue in Venue.query.order_by(Venue.name).all()
    ]

    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    error = False
    artist = request.form.get("artist_name")
    venue = request.form.get("venue_name")
    start_time = request.form.get("start_time")
    # Check availability------------
    check = Artist.query.get(artist)
    if check.available_start:
        check_start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        if (
            check_start_time <= check.available_start
            or check_start_time >= check.available_stop
        ):
            flash(
                "Sorry, "
                + check.name
                + " is not availble at that time. Check artist availablity and try again."
            )
            return redirect(url_for("create_shows"))
    try:
        new_show = Shows(
            artist_id=artist, venue_id=venue, start_time=start_time
        )
        db.session.add(new_show)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
        abort(500)
    finally:
        db.session.close()
        if error:
            # TODO: on unsuccessful db insert, flash an error instead.
            # e.g., flash('An error occurred. Show could not be listed.')
            # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
            flash("Something went wrong. Show could not be added.")
        else:
            # on successful db insert, flash success
            flash("Show was successfully listed!")
    return redirect(url_for("index"))
    # return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
