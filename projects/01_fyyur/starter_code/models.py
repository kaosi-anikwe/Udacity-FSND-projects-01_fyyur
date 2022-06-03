from flask import Flask, jsonify, render_template, request, Response, flash, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


app = Flask(__name__)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

class Shows(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
class Venue(db.Model):
    __tablename__ = 'Venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False)
    seeking_description = db.Column(db.String(200))
    genres = db.relationship('VenueGenres', cascade="all, delete-orphan", single_parent=True, backref=db.backref('venue'))
    shows = db.relationship('Shows', cascade="all, delete-orphan", backref=db.backref('venue'), lazy=True)

class VenueGenres(db.Model):
    __tablename__ = 'venue_genres'
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    genres = db.Column(db.String(), nullable=False)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False)
    seeking_description = db.Column(db.String(120))
    available_start = db.Column(db.DateTime)
    available_stop = db.Column(db.DateTime)
    genres = db.relationship('ArtistGenres', cascade="all, delete-orphan", single_parent=True, backref=db.backref('artist'))
    shows = db.relationship('Shows', cascade="all, delete-orphan", backref=db.backref('artist'), lazy=True)

class ArtistGenres(db.Model):
    __tablename__ = 'artist_genres'
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    genres = db.Column(db.String(), nullable=False)
    