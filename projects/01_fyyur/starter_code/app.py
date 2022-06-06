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
    get_artists = Artists.query.order_by(Artists.id.desc()).limit(10).all()
    for artist in get_artists:
        artists.append({"id": artist.id, "name": artist.name})
    # Show recently listed venues
    venues = []
    get_venues = Venues.query.order_by(Venues.id.desc()).limit(10).all()
    for venue in get_venues:
        venues.append({"id": venue.id, "name": venue.name})
    return render_template("pages/home.html", artists=artists, venues=venues)


#  Venues
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():
    # num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    real_data = []
    distinct = Venues.query.distinct(Venues.city, Venues.state).all()
    for i in range(len(distinct)):
        real_data.append(
            {
                "city": distinct[i].city,
                "state": distinct[i].state,
                "venues": [],
            }
        )
        venues = Venues.query.filter_by(
            city=real_data[i]["city"], state=real_data[i]["state"]
        ).all()
        for venue in venues:
            upcoming_shows = (
                db.session.query(Shows)
                .join(Venues)
                .filter(
                    Shows.venue_id == venue.id,
                    Shows.start_time > datetime.now(),
                )
                .all()
            )
            real_data[i]["venues"].append(
                {
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": len(upcoming_shows),
                }
            )
    return render_template("pages/venues.html", areas=real_data)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    search_term = request.form.get("search_term")
    search = "%{}%".format(search_term)
    results = Venues.query.filter(Venues.name.ilike(search)).all()
    dbresponse = {"count": len(results), "data": []}
    for result in results:
        upcoming_shows = (
            db.session.query(Shows)
            .join(Venues)
            .filter(
                Shows.venue_id == result.id, Shows.start_time > datetime.now()
            )
            .all()
        )
        dbresponse["data"].append(
            {
                "id": result.id,
                "name": result.name,
                "num_upcoming_shows": len(upcoming_shows),
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
        return redirect(url_for("venues"))
    search_1 = "%{}%".format(search[0])
    search_2 = "%{}%".format(search[1])
    venues = Venues.query.filter(
        Venues.city.ilike(search_1), Venues.state.ilike(search_2)
    ).all()
    if not venues:
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
    dbvenue = Venues.query.get(venue_id)
    genres = VenueGenres.query.filter(VenueGenres.venue_id == venue_id).all()

    past_shows = (
        db.session.query(Shows)
        .join(Venues)
        .join(Artists)
        .filter(Shows.venue_id == venue_id, Shows.start_time < datetime.now())
        .order_by(Shows.start_time.desc())
        .all()
    )

    upcoming_shows = (
        db.session.query(Shows)
        .join(Venues)
        .join(Artists)
        .filter(Shows.venue_id == venue_id, Shows.start_time > datetime.now())
        .all()
    )

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
        real_data["past_shows"].append(
            {
                "artist_id": past_show.artist_id,
                "artist_name": past_show.artist.name,
                "artist_image_link": past_show.artist.image_link,
                "start_time": past_show.start_time,
            }
        )
    # Append list of upcoming shows
    for show in upcoming_shows:
        real_data["upcoming_shows"].append(
            {
                "artist_id": show.artist_id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
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
    form = VenueForm(request.form)
    if form.validate():
        try:
            seeking_talent = False
            if request.form.get("seeking_talent"):
                seeking_talent = True
            new_venue = Venues(
                name=request.form.get("name"),
                city=request.form.get("city"),
                state=request.form.get("state"),
                address=request.form.get("address"),
                phone=request.form.get("phone"),
                image_link=request.form.get("image_link"),
                facebook_link=request.form.get("facebook_link"),
                website=request.form.get("website"),
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
        finally:
            venue = Venues.query.filter_by(
                name=request.form.get("name")
            ).first()
            genres = request.form.getlist("genres")
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
    try:
        venue = Venues.query.get(venue_id)
        venue_name = venue.name
        db.session.delete(venue)
        db.session.commit()
        flash('Venue: "' + venue_name + '" was deleted successfully!')
    except:
        print(sys.exc_info())
        db.session.rollback()
        flash(
            'Venue: "'
            + venue_name
            + '" could not be deleted. Please try again.'
        )
        abort(500)
    finally:
        db.session.close()
    return redirect(url_for("venues"))


@app.route("/venues/<venue_id>/delete/")
def delete_home_venue(venue_id):
    try:
        venue = Venues.query.get(venue_id)
        venue_name = venue.name
        db.session.delete(venue)
        db.session.commit()
        flash('Venue: "' + venue_name + '" was deleted successfully!')
    except:
        print(sys.exc_info())
        db.session.rollback()
        flash(
            'Venue: "'
            + venue_name
            + '" could not be deleted. Please try again.'
        )
        abort(500)
    finally:
        db.session.close()
    return redirect(url_for("index"))


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    real_data = []
    artists = Artists.query.all()
    for artist in artists:
        real_data.append({"id": artist.id, "name": artist.name})

    return render_template("pages/artists.html", artists=real_data)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    search_term = request.form.get("search_term")
    search = "%{}%".format(search_term)
    results = Artists.query.filter(Artists.name.ilike(search)).all()
    dbresponse = {"count": len(results), "data": []}
    for result in results:
        upcoming_shows = (
            db.session.query(Shows)
            .join(Artists)
            .filter(
                Shows.artist_id == result.id, Shows.start_time > datetime.now()
            )
            .all()
        )
        dbresponse["data"].append(
            {
                "id": result.id,
                "name": result.name,
                "num_upcoming_shows": len(upcoming_shows),
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
        return redirect(url_for("artists"))
    search_1 = "%{}%".format(search[0])
    search_2 = "%{}%".format(search[1])
    artists = Artists.query.filter(
        Artists.city.ilike(search_1), Artists.state.ilike(search_2)
    ).all()
    if not artists:
        return render_template(
            "pages/cs_search_artists.html",
            results=response,
            search_term=search_term,
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
    artist = Artists.query.get(artist_id)
    genres = ArtistGenres.query.filter_by(artist_id=artist_id).all()

    past_shows = (
        db.session.query(Shows)
        .join(Artists)
        .join(Venues)
        .filter(
            Shows.artist_id == artist_id, Shows.start_time < datetime.now()
        )
        .order_by(Shows.start_time.desc())
        .all()
    )

    upcoming_shows = (
        db.session.query(Shows)
        .join(Artists)
        .join(Venues)
        .filter(
            Shows.artist_id == artist_id, Shows.start_time > datetime.now()
        )
        .all()
    )
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
        real_data["past_shows"].append(
            {
                "venue_id": past_show.venue_id,
                "venue_name": past_show.venue.name,
                "venue_image_link": past_show.venue.image_link,
                "start_time": past_show.start_time,
            }
        )
    # Append list of upcoming showws
    for show in upcoming_shows:
        real_data["upcoming_shows"].append(
            {
                "venue_id": show.venue_id,
                "venue_name": show.venue.name,
                "venue_image_link": show.venue.image_link,
                "start_time": show.start_time,
            }
        )
    return render_template("pages/show_artist.html", artist=real_data)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    artist = Artists.query.get(artist_id)
    form = ArtistForm(obj=artist)

    genres = ArtistGenres.query.filter_by(artist_id=artist_id).all()
    dbartist = {"genres": []}
    for genre in genres:
        dbartist["genres"].append(genre.genres)
    form.genres.data = dbartist["genres"]
    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    form = ArtistForm(request.form)
    artist = Artists.query.get(artist_id)
    if form.validate():
        # Check if avavilability is properly set
        available_start = request.form.get("available_start")
        available_stop = request.form.get("available_stop")
        # If availability improperly set
        if available_start and not available_stop:
            flash("Availability not properly set")
            return render_template(
                "forms/edit_artist.html", form=form, artist=artist
            )
        if not available_start and available_stop:
            flash("Availability not properly set!")
            return render_template(
                "forms/edit_artist.html", form=form, artist=artist
            )

        # If availability properly set
        # Without availability-------------------
        artist.name = request.form.get("name")
        artist.city = request.form.get("city")
        artist.state = request.form.get("state")
        artist.phone = request.form.get("phone")
        artist.image_link = request.form.get("image_link")
        artist.facebook_link = request.form.get("facebook_link")
        artist.website = request.form.get("website")
        artist.seeking_description = request.form.get("seeking_description")
        artist.available_start = None
        artist.available_stop = None
        # With availability-------------------
        if available_start and available_stop:
            artist.available_start = request.form.get("available_start")
            artist.available_stop = request.form.get("available_stop")

        if request.form.get("seeking_venue"):
            artist.seeking_venue = True
        elif not request.form.get("seeking_venue"):
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
    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    venue = Venues.query.get(venue_id)
    form = VenueForm(obj=venue)

    genres = VenueGenres.query.filter_by(venue_id=venue_id).all()
    dbvenue = {"genres": []}
    for genre in genres:
        dbvenue["genres"].append(genre.genres)
    form.genres.data = dbvenue["genres"]
    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form)
    venue = Venues.query.get(venue_id)
    if form.validate():
        venue.name = request.form.get("name")
        venue.city = request.form.get("city")
        venue.state = request.form.get("state")
        venue.phone = request.form.get("phone")
        venue.image_link = request.form.get("image_link")
        venue.facebook_link = request.form.get("facebook_link")
        venue.website = request.form.get("website")
        venue.seeking_description = request.form.get("seeking_description")

        if request.form.get("seeking_talent"):
            venue.seeking_talent = True
        elif not request.form.get("seeking_talent"):
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
    return render_template("forms/edit_venue.html", form=form, venue=venue)


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    form = ArtistForm(request.form)
    if not form.validate():
        return render_template("forms/new_artist.html", form=form)
    name = request.form.get("name")
    city = request.form.get("city")
    state = request.form.get("state")
    phone = request.form.get("phone")
    image_link = request.form.get("image_link")
    genres = request.form.getlist("genres")
    facebook_link = request.form.get("facebook_link")
    website = request.form.get("website")
    seeking_venue = False
    seeking_description = request.form.get("seeking_description")
    available_start = request.form.get("available_start")
    available_stop = request.form.get("available_stop")

    if request.form.get("seeking_venue"):
        seeking_venue = True

    # Check if availability is properly set
    # If availability improperly set--------------------
    if available_start and not available_stop:
        flash("Availability not properly set!")
        return render_template("forms/new_artist.html", form=form)
    if not available_start and available_stop:
        flash("Availability not properly set!")
        return render_template("forms/new_artist.html", form=form)

    # If availability properly set
    # With availability-----------------------
    if available_start and available_stop:
        try:
            new_artist = Artists(
                name=name,
                city=city,
                state=state,
                phone=phone,
                image_link=image_link,
                facebook_link=facebook_link,
                website=website,
                seeking_venue=seeking_venue,
                seeking_description=seeking_description,
                available_start=available_start,
                available_stop=available_stop,
            )
            db.session.add(new_artist)
            db.session.commit()
            flash(
                'Artist: "'
                + request.form["name"]
                + '" was successfully listed!'
            )
        except:
            db.session.rollback()
            print(sys.exc_info())
            flash(
                'Something went wrong. Artist: "'
                + request.form["name"]
                + '" could not be listed.'
            )
            abort(500)
        finally:
            # Add genres to ArtistGenres table
            artist = Artists.query.filter_by(name=name, city=city).first()
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
    if not available_start and not available_stop:
        try:
            new_artist = Artists(
                name=name,
                city=city,
                state=state,
                phone=phone,
                image_link=image_link,
                facebook_link=facebook_link,
                website=website,
                seeking_venue=seeking_venue,
                seeking_description=seeking_description,
            )
            db.session.add(new_artist)
            db.session.commit()
            flash(
                'Artist: "'
                + request.form["name"]
                + '" was successfully listed!'
            )
        except:
            db.session.rollback()
            print(sys.exc_info())
            flash(
                'Something went wrong. Artist: "'
                + request.form["name"]
                + '" could not be listed.'
            )
            abort(500)
        finally:
            # Add genres to ArtistGenres table
            artist = Artists.query.filter_by(name=name, city=city).first()
            for genre in genres:
                try:
                    new_genre = ArtistGenres(artist_id=artist.id, genres=genre)
                    db.session.add(new_genre)
                    db.session.commit()
                except:
                    db.session.rollback()
                    abort(500)
            db.session.close()
        return redirect(url_for("index"))


# Delete Artist
# ---------------------------------------------------------------
@app.route("/artists/delete/<artist_id>")
def delete_artist(artist_id):
    try:
        artist = Artists.query.get(artist_id)
        artist_name = artist.name
        db.session.delete(artist)
        db.session.commit()
        flash('Artist "' + artist_name + '" was deleted successfully!')
    except:
        flash(
            'Artist: "'
            + artist_name
            + '" could not be deleted. Please try again.'
        )
        print(sys.exc_info())
        abort(500)
    finally:
        db.session.close()
    return redirect(url_for("artists"))


@app.route("/artists/<artist_id>/delete")
# Delete button on artist page, redirects to home page
def delete_home_artist(artist_id):
    try:
        artist = Artists.query.get(artist_id)
        artist_name = artist.name
        db.session.delete(artist)
        db.session.commit()
        flash('Artist "' + artist_name + '" was deleted successfully!')
    except:
        flash(
            'Artist: "'
            + artist_name
            + '" could not be deleted. Please try again.'
        )
        abort(500)
    finally:
        db.session.close()
    return redirect(url_for("index"))


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    # displays list of shows at /shows
    real_data = []
    shows = Shows.query.order_by(Shows.start_time.desc()).all()
    for show in shows:
        venue = Venues.query.get(show.venue_id)
        artist = Artists.query.get(show.artist_id)
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
    venue_search = (
        db.session.query(Shows)
        .join(Venues)
        .join(Artists)
        .filter(Venues.name.ilike(search))
        .order_by(Shows.start_time.desc())
        .all()
    )
    artist_search = (
        db.session.query(Shows)
        .join(Artists)
        .join(Venues)
        .filter(Artists.name.ilike(search))
        .order_by(Shows.start_time.desc())
        .all()
    )
    response = {"count": 0, "data": []}
    for show in venue_search:
        response["data"].append(
            {
                "venue_id": show.venue.id,
                "venue_name": show.venue.name,
                "artist_id": show.artist.id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                "start_time": show.start_time,
            }
        )
    for show in artist_search:
        if show not in venue_search:
            response["data"].append(
                {
                    "venue_id": show.venue.id,
                    "venue_name": show.venue.name,
                    "artist_id": show.artist.id,
                    "artist_name": show.artist.name,
                    "artist_image_link": show.artist.image_link,
                    "start_time": show.start_time,
                }
            )
    response["count"] = len(response["data"])
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
        for artist in Artists.query.order_by(Artists.name).all()
    ]
    form.venue_name.choices = [
        (venue.id, venue.name)
        for venue in Venues.query.order_by(Venues.name).all()
    ]
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    artist = request.form.get("artist_name")
    venue = request.form.get("venue_name")
    start_time = request.form.get("start_time")
    # Check availability------------
    check = Artists.query.get(artist)
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
        flash("Show was successfully listed!")
    except:
        db.session.rollback()
        flash("Something went wrong. Show could not be added.")
        print(sys.exc_info())
        abort(500)
    finally:
        db.session.close()
    return redirect(url_for("index"))


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
