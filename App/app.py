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
          (SELECT COUNT(*) site_number1 FROM Location WHERE transboundary=1)
        JOIN
          (SELECT COUNT(*) site_number2 FROM State_Of_Danger WHERE danger=1) 
        JOIN 
          (SELECT COUNT(*) site_number3 FROM Category WHERE category_short='C')
        JOIN 
          (SELECT COUNT(*) site_number4 FROM Category WHERE category_short='C/N')
        JOIN 
          (SELECT COUNT(*) site_number5 FROM Category WHERE category_short='N')
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
        SELECT id_no,name_en,short_description_en, GROUP_CONCAT(Place.states_name_en, ', ') as countries
        FROM World_Heritage_Site 
        JOIN Location ON World_Heritage_Site.id_no = Location.site_number
        JOIN place ON Location.site_number = place.site_number
        WHERE id_no = ?
        GROUP BY id_no, name_en, short_description_en
        ''', [id]).fetchone()

    if site is None:
        abort(404, 'Site id {} does not exist.'.format(id))

    return render_template('site.html', site=site)


# pesquisar por pais
@APP.route('/sites/search/<country>')
def search_sites(country):
    sites = db.execute(
        '''
        SELECT id_no,name_en,short_description_en
        FROM World_Heritage_Site
        JOIN Location ON World_Heritage_Site.id_no = Location.site_number
        JOIN place ON Location.site_number = place.site_number
        WHERE states_name_en LIKE ?
        GROUP BY id_no, name_en, short_description_en
        ''', ('%' + country + '%',)).fetchall()

    if not sites:
        abort(404, 'No sites found for country: {}'.format(country))

    return render_template('sites-list.html', sites=sites)


# Transboundary Sites
@APP.route('/transboundary/')
def transboundary_sites():
    try:
        transboundary_sites = db.execute('''
            SELECT id_no, name_en, short_description_en, states_name_en
            FROM World_Heritage_Site
            JOIN Location ON World_Heritage_Site.id_no = Location.site_number
            JOIN place ON Location.site_number = place.site_number
            WHERE transboundary = 1
            GROUP BY id_no, name_en, short_description_en, states_name_en
        ''').fetchall()

        if not transboundary_sites:
            abort(404, 'No transboundary sites found.')

        return render_template('transboundary.html', sites=transboundary_sites)
    except Exception as e:
        return str(e), 500


@APP.route('/transboundary/search/<country>')
def search_transboundary_sites(country):
    try:
        transboundary_sites = db.execute('''
            SELECT id_no, name_en, short_description_en, states_name_en
            FROM World_Heritage_Site
            JOIN Location ON World_Heritage_Site.id_no = Location.site_number
            JOIN place ON Location.site_number = place.site_number
            WHERE transboundary = 1 AND states_name_en LIKE ?
            GROUP BY id_no, name_en, short_description_en, states_name_en
        ''', ('%' + country + '%',)).fetchall()

        if not transboundary_sites:
            abort(404, 'No transboundary sites found for country: {}'.format(country))

        return render_template('transboundary.html', sites=transboundary_sites)
    except Exception as e:
        return str(e), 500


@APP.route('/sites/country/<country>')
def sites_by_country(country):
    sites = db.execute('''
        SELECT World_Heritage_Site.id_no, World_Heritage_Site.name_en, World_Heritage_Site.short_description_en
        FROM World_Heritage_Site
        JOIN Location ON World_Heritage_Site.id_no = Location.site_number
        JOIN Place ON Location.site_number = Place.site_number
        WHERE Place.states_name_en LIKE ?
        ORDER BY World_Heritage_Site.id_no
    ''', ('%' + country + '%',)).fetchall()

    if not sites:
        abort(404, 'No sites found for country: {}'.format(country))

    return render_template('sites-by-country.html', country=country, sites=sites)


# Run the app
if __name__ == '__main__':
    APP.run(debug=True)
