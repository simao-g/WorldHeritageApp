import warnings
warnings.filterwarnings('ignore', category=FutureWarning)
from flask import abort, render_template, Flask
import logging
import db

APP = Flask(__name__)

# Pagina Inicial
@APP.route('/')
def index():
    stats = {}
    stats = db.execute('''
        SELECT * FROM
          (SELECT COUNT(*) id_no FROM World_Heritage_Site)
        JOIN
          (SELECT COUNT(*) site_number FROM Location WHERE transboundary=1) #em vários países
        JOIN
          (SELECT COUNT(*) site_number FROM State_Of_Danger WHERE danger=1) #em perigo atualmente
        JOIN 
          (SELECT COUNT(*) site_number FROM Category WHERE category_short='C')
        JOIN 
          (SELECT COUNT(*) site_number FROM Category WHERE category_short='C/N')
        JOIN 
          (SELECT COUNT(*) site_number FROM Category WHERE category_short='N')
        ''').fetchone()
    logging.info(stats)
    return render_template('index.html', stats=stats)


# World Heritage Sites
@APP.route('/sites/')
def list_sites():
    sites = db.execute(
      '''
      SELECT id_no,name_en,short_description_en 
      FROM World_Heritage_Site
      ORDER BY id_no
      ''').fetchall()
    return render_template('sites-list.html', sites=sites)



@APP.route('/sites/<int:id>/')
def get_site(id):
    site = db.execute(
        '''
        SELECT id_no,name_en,short_description_en 
        FROM World_Heritage_Site 
        WHERE id_no = ?
        ''', [id]).fetchone()

    if site is None:
        abort(404, 'Site id {} does not exist.'.format(id))

    genres = db.execute(
        '''
        SELECT GenreId, Label 
        FROM MOVIE_GENRE NATURAL JOIN GENRE 
        WHERE movieId = ? 
        ORDER BY Label
        ''', [id]).fetchall()

    actors = db.execute(
        '''
        SELECT ActorId, Name
        FROM MOVIE_ACTOR NATURAL JOIN ACTOR
        WHERE MovieId = ?
        ORDER BY Name
        ''', [id]).fetchall()

    streams = db.execute(
        ''' 
        SELECT StreamId, StreamDate
        FROM STREAM
        WHERE MovieId = ?
        ORDER BY StreamDate Desc
        ''', [id]).fetchall();
    return render_template('movie.html',
        movie=movie, genres=genres, actors=actors, streams=streams)