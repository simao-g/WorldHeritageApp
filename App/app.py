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
        SELECT id_no,name_en,short_description_en, 
        place.states_name_en as countries,
        region_en, latitude, longitude, area_hectares,
        date_inscribed, justification_en, danger,category
        FROM World_Heritage_Site 
        JOIN Location ON World_Heritage_Site.id_no = Location.site_number
        JOIN place ON Location.site_number = place.site_number
        JOIN associated_dates ON World_Heritage_Site.id_no = associated_dates.site_number
        JOIN state_of_danger ON World_Heritage_Site.id_no = state_of_danger.site_number
        JOIN Category c ON World_Heritage_Site.id_no = c.site_number
        JOIN Category_Description cd ON c.category_short = cd.category_short
        JOIN site_criteria ON World_Heritage_Site.id_no = site_criteria.site_number
        JOIN Criterion_Descriptions cr ON site_criteria.criterion_code = cr.criterion_code
        WHERE id_no = ?
        GROUP BY id_no, name_en, short_description_en
        ''', [id]).fetchone()

    if site is None:
        abort(404, 'Site id {} does not exist.'.format(id))

    return render_template('site.html', site=site)

@APP.route('/sites/<int:id>/criteria/')
def get_criteria(id):
    criteria = db.execute(
        '''
        SELECT id_no, name_en,sc.criterion_code,cd.cd_description, wh.justification_en
        FROM World_Heritage_Site wh
        JOIN Category c ON wh.id_no = c.site_number
        JOIN site_criteria sc ON c.site_number = sc.site_number
        JOIN criterion_descriptions cd ON sc.criterion_code = cd.criterion_code
        WHERE id_no = ?
        GROUP BY wh.id_no, sc.criterion_code
        ORDER BY
            CASE 
                WHEN sc.criterion_code = 'N10' THEN 999
                ELSE 1                                 
            END,
            sc.criterion_code;
        ''', (id,)).fetchall()
    
    return render_template('site-criteria.html', criteria=criteria)

#pesquisar por pais
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

@APP.route('/sites/search/<int:year>')
def sites_by_year(year):
    sites = db.execute(
        '''
        SELECT id_no, name_en, short_description_en
        FROM World_Heritage_Site
        JOIN associated_dates ON World_Heritage_Site.id_no = associated_dates.site_number
        WHERE date_inscribed = ?
        ''', [year]).fetchall()

    if not sites:
        abort(404, 'No sites found for year: {}'.format(year))

    return render_template('sites-by-year.html', year=year, sites=sites)
      
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

@APP.route('/country/<country>')
def sites_by_country(country):
    sites = db.execute('''
        SELECT id_no, name_en
        FROM World_Heritage_Site
        JOIN Location ON World_Heritage_Site.id_no = Location.site_number
        JOIN Place ON Location.site_number = Place.site_number
        WHERE Place.states_name_en LIKE ?
        ORDER BY World_Heritage_Site.id_no
    ''', ('%' + country + '%',)).fetchall()

    if not sites:
        abort(404, 'No sites found for country: {}'.format(country))

    return render_template('sites-by-country.html', country=country, sites=sites)

@APP.route('/sites/category/<category>')
def sites_by_category(category):
    sites = db.execute(
        '''
        SELECT id_no, name_en, short_description_en
        FROM World_Heritage_Site
        JOIN Category c ON World_Heritage_Site.id_no = c.site_number
        JOIN Category_Description cd ON c.category_short = cd.category_short
        WHERE cd.category = ?
        ''', [category]).fetchall()

    if not sites:
        abort(404, 'No sites found for category: {}'.format(category))

    return render_template('sites-by-category.html', category=category, sites=sites)

@APP.route('/sites/danger')
def sites_in_danger():
    sites = db.execute(
        '''
        SELECT id_no, name_en, short_description_en
        FROM World_Heritage_Site
        JOIN state_of_danger ON World_Heritage_Site.id_no = state_of_danger.site_number
        WHERE danger = 1
        ''').fetchall()

    if not sites:
        abort(404, 'No sites found that are in danger.')

    return render_template('sites-in-danger.html', sites=sites)

@APP.route('/sites/not-in-danger')
def sites_not_in_danger():
    sites = db.execute(
        '''
        SELECT id_no, name_en, short_description_en
        FROM World_Heritage_Site
        JOIN state_of_danger ON World_Heritage_Site.id_no = state_of_danger.site_number
        WHERE danger = 0
        ''').fetchall()

    if not sites:
        abort(404, 'No sites found that are not in danger.')

    return render_template('sites-not-in-danger.html', sites=sites)

@APP.route('/queries/<int:n_pergunta>')
def site_queries(n_pergunta):
    if n_pergunta == 1:
        sql_code = '''
            SELECT whs.id_no as site_number, whs.name_en
            FROM associated_dates ad
            JOIN world_heritage_site whs ON ad.site_number = whs.id_no
            WHERE ad.date_end IS NOT Null
            ORDER BY whs.name_en
            '''
        result = db.execute(sql_code).fetchall()
        title = "Que locais deixaram de ser património? Ordenada-os pelo nome"
    
    else:
        abort(404, 'Query number {} does not exist.'.format(n_pergunta))

    return render_template('site-queries.html', title=title, result=result, sql_code=sql_code)


# Run the app
if __name__ == '__main__':
    APP.run(debug=True)
