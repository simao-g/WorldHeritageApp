import warnings
warnings.filterwarnings('ignore', category=FutureWarning)
from flask import abort, render_template, Flask
import logging
import db

APP = Flask(__name__)

#Root page
@APP.route('/')
#Retrieves various statistics from the database.
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


@APP.route('/sites/')
# Lists all the World Heritage Sites
def list_sites():
    sites = db.execute(
      '''
      SELECT id_no,name_en,short_description_en
      FROM World_Heritage_Site
      ORDER BY id_no
      ''').fetchall()
    return render_template('sites-list.html', sites=sites)


@APP.route('/sites/<int:id>/')
#Route to retrieve information about a specific World Heritage Site by its ID.
#The function executes a SQL query to retrieve various details about the World Heritage Site.
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
#Retrieve and display the criteria for a specific World Heritage Site.
#Queries the database to fetch the criteria associated with the specified site.
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


@APP.route('/sites/search/<country>')
#Search for World Heritage Sites by country.
#Queries the database for sites located in the specified country and returns a list of sites.
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
#Search World Heritage Sites by the year they were inscribed.
#Queries the database for World Heritage Sites that were inscribed in the selected year.
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
      

@APP.route('/transboundary/')
#Display transboundary World Heritage Sites.
#Queries the database to retrieve information about transboundary World Heritage Sites.
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
#Search for transboundary World Heritage Sites by country.
#Queries the database for World Heritage Sites that are transboundary.
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
#Display World Heritage Sites by country.
#Queries the database for World Heritage Sites that are from the chosen country.
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
#Display World Heritage Sites by category.
#Queries the database for World Heritage Sites that are categorized by the selected category.
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
#Display World Heritage Sites that are in danger.
#Queries the database for World Heritage Sites that are marked as in danger.
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
#Display World Heritage Sites that are not in danger.
#Queries the database for World Heritage Sites that are not listed as being in danger.
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
#Handle site queries based on the query number provided.
#Queries the database for the information that the question requires
def site_queries(n_pergunta):
    if n_pergunta == 1:
        sql_code = '''
            SELECT states_name_en AS info_1, COUNT(*) AS info_2
            FROM Place
            NATURAL JOIN Location
            GROUP BY states_name_en
            HAVING transboundary=0
            ORDER BY info_2 DESC
            LIMIT 5;
            '''
        result = db.execute(sql_code).fetchall()
        title = "The 5 countries with the biggest amount of non-transboundary sites. Show the country name and the amount of sites, and order them (DESC) by  total."
        info_1 = "Country"
        info_2 = "Site Count"
        return render_template('queries-info1-info2.html', title=title, result=result, sql_code=sql_code, info_1=info_1, info_2=info_2)
    
    elif n_pergunta == 2:
        sql_code = '''
            SELECT id_no as site_number, name_en as site_name, l.latitude as info_1, l.longitude as info_2
            FROM location l
            JOIN world_heritage_site whs ON l.site_number = whs.id_no
            WHERE l.latitude < 0 AND longitude < 0
            ORDER BY l.latitude DESC;

            '''
        result = db.execute(sql_code).fetchall()
        title = "The names, latitude and longitude of the sites below the equator (latitude<0) and left to the Greenwich meridian (longitude<0)? Order them from North to South."
        info_1 = "Latitude"
        info_2 = "Longitude"
        return render_template('queries-site-id-name-info1-info2.html', title=title, result=result, info_1=info_1, info_2=info_2, sql_code=sql_code)
    elif n_pergunta == 3:
        sql_code = '''
            SELECT whs.id_no as site_number, whs.name_en as site_name
            FROM site_criteria st
            JOIN world_heritage_site whs ON whs.id_no = st.site_number
            WHERE criterion_code LIKE (
                SELECT cd.criterion_code
                FROM criterion_descriptions cd
                WHERE cd.cd_description LIKE "%To represent a masterpiece of human creative genius%")
            ORDER BY whs.name_en;
            '''
        result = db.execute(sql_code).fetchall()
        title = "Which sites, show the ID and the name, does Unesco consider representative of “a masterpiece of human creative genius”? Order them by name."
        return render_template('queries-site-id-name.html', title=title, result=result, sql_code=sql_code)
    
    elif n_pergunta == 4:
        sql_code = '''
            SELECT whs.id_no as site_number, whs.name_en as site_name
            FROM associated_dates ad 
            JOIN world_heritage_site whs ON ad.site_number = whs.id_no
            WHERE ad.date_inscribed = 2005
            ORDER BY site_name;
            '''
        result = db.execute(sql_code).fetchall()
        title = "Which sites became a part of the list in the year we were born(2005)? Order them by name."
        return render_template('queries-site-id-name.html', title=title, result=result, sql_code=sql_code)
    
    elif n_pergunta == 5:
        sql_code = '''
            SELECT id_no as site_number, name_en AS site_name, short_description_en AS Description
            FROM state_of_danger sd
            JOIN world_heritage_site whs ON sd.site_number = whs.id_no
            WHERE sd.date_end = 2024
            ORDER BY site_name;
            '''
        result = db.execute(sql_code).fetchall()
        title = "Has any site stopped being endangered this year (2024)? Show their ID's, names and descriptions, and order by name." 
        info_1 = "Description"
        return render_template('queries-site-id-name-info1.html', title=title, result=result, sql_code=sql_code)

    elif n_pergunta == 6:
        sql_code = '''
            WITH numb_criteria AS (SELECT site_number, count(site_number) AS cont_criteria
            FROM site_criteria sc
            GROUP BY sc.site_number
            ORDER BY sc.site_number)

            SELECT whs.id_no as site_number, whs.name_en AS site_name, cont_criteria as info_1
            FROM numb_criteria nc
            JOIN world_heritage_site whs ON nc.site_number = whs.id_no
            WHERE cont_criteria = (
                SELECT max(cont_criteria)
                FROM numb_criteria nc
                )
            ORDER BY site_name;
            '''
        result = db.execute(sql_code).fetchall()
        title = "Which site(s), ID and name, combine the biggest amount of criteria to be considered World Heritage and what is that amount as 'Number of criteria'? Order them by name."
        info_1 = "Number of criteria"
        return render_template('queries-site-id-name-info1.html', title=title, result=result, sql_code=sql_code, info_1=info_1)
    
    elif n_pergunta == 7:
        sql_code = '''
            SELECT cd.category as info_1, count(c.site_number) as info_2
            FROM category c
            JOIN category_description cd on c.category_short = cd.Category_short
            GROUP BY c.category_short;

            '''
        result = db.execute(sql_code).fetchall()
        title = "How many sites are there from each category? Show the category name and the amount of sites."
        info_1 = "Category"
        info_2 = "Amount of sites"
        return render_template('queries-category-info1-info2.html', title=title, result=result, sql_code=sql_code, info_1=info_1, info_2=info_2)

    
    elif n_pergunta == 8:
        sql_code = '''
            SELECT id_no as site_number, name_en as site_name, region_en as info_1, states_name_en as info_2
            FROM World_Heritage_Site
            JOIN Place ON World_Heritage_Site.id_no = Place.site_number
            WHERE states_name_en LIKE '%France%'
            ORDER BY site_name;
            '''
        result = db.execute(sql_code).fetchall()
        title = "What are the names, region and countries (transboundary sites) of the sites in France? Order them by name."
        info_1 = "Region"
        info_2 = "State"
        return render_template('queries-site-id-name-info1-info2.html', title=title, result=result, info_1=info_1, info_2=info_2, sql_code=sql_code)
    
    elif n_pergunta == 9:
        sql_code = '''
            SELECT whs.id_no as site_number, whs.name_en as site_name, p.states_name_en as info_1
            FROM World_Heritage_Site whs
            JOIN Place p ON whs.id_no = p.site_number
            WHERE p.states_name_en LIKE 'B%' OR p.states_name_en LIKE '%,B%' 
            ORDER BY whs.id_no;
            '''
        result = db.execute(sql_code).fetchall()
        title = "The sites associated with countries that start with the letter B and the name of their country/countries. Show their ID, name and the country or countries, and order them by ID."
        info_1 = "Country"
        return render_template('queries-site-id-name-info1.html', title=title, result=result, sql_code=sql_code, info_1=info_1)
    
    elif n_pergunta == 10:
        sql_code = '''
            SELECT category as info_1 , AVG(area_hectares) AS info_2
            FROM Location
            JOIN Category ON Location.site_number = Category.site_number
            JOIN Category_Description ON Category.category_short = Category_Description.category_short
            GROUP BY category;
            '''
        result = db.execute(sql_code).fetchall()
        title = "What is the average area of the sites of each category? Show the category name and the average area."
        info_1 = "Category"
        info_2 = "Average area"
        return render_template('queries-category-info1-info2.html', title=title, result=result, sql_code=sql_code, info_1=info_1, info_2=info_2)
    
    elif n_pergunta == 11:
        sql_code = '''
            SELECT CASE WHEN latitude >= 0 THEN 'North' ELSE 'South' END AS info_1, COUNT(*) AS info_2
            FROM Location
            GROUP BY info_1;
            '''
        result = db.execute(sql_code).fetchall()
        title = "What is the amount of sites in each hemisphere (North and South)?"
        info_1 = "Hemisphere"
        info_2 = "Site Count"
        return render_template('queries-info1-info2.html', title=title, result=result, sql_code=sql_code, info_1=info_1, info_2=info_2)
    
    elif n_pergunta == 12:
        sql_code = '''
            SELECT whs.id_no as site_number, whs.name_en as site_name, l.area_hectares as info_1, p.region_en as info_2
            FROM World_Heritage_Site whs
            JOIN Location l ON whs.id_no = l.site_number
            JOIN Place p ON whs.id_no = p.site_number
            ORDER BY l.area_hectares DESC
            LIMIT 10;
            '''
        result = db.execute(sql_code).fetchall()
        title = "List the 10 biggest sites in area and their regions. Show their ID, name, area and region, and order them by area (DESC)."
        info_1 = "Area (hectares)"
        info_2 = "Region"
        return render_template('queries-site-id-name-info1-info2.html', title=title, result=result, info_1=info_1, info_2=info_2, sql_code=sql_code)
    
    elif n_pergunta == 13:
        sql_code = '''
                SELECT id_no as site_number, name_en as site_name, latitude as info_1, longitude as info_2
                FROM Location as l
                JOIN World_Heritage_Site as whs ON l.site_number = whs.id_no
                JOIN State_Of_Danger as d ON whs.id_no=d.site_number
                WHERE danger=1 AND info_1 BETWEEN -23.5 AND 23.5
                ORDER BY site_number;
        '''

        result = db.execute(sql_code).fetchall()
        title = "List the sites in the torrid zone (between the tropics of cancer and capricorn) that are currently in danger. Show their ID, name, latitude, longitude, and order them by ID."
        info_1 = "Latitude"
        info_2 = "Longitude"
        return render_template('queries-site-id-name-info1-info2.html', title=title, result=result, info_1=info_1, info_2=info_2, sql_code=sql_code)
    
    elif n_pergunta == 14:
        sql_code = '''
            SELECT id_no as site_number, whs.name_en as site_name, p.region_en as info_1
            FROM World_Heritage_Site whs
            JOIN Place p ON whs.id_no = p.site_number
            WHERE info_1 = (
                SELECT region_en
                FROM Place
                GROUP BY region_en
                ORDER BY COUNT(*) DESC
                LIMIT 1)
            ORDER BY site_number;

            '''
        result = db.execute(sql_code).fetchall()
        title = "Find the sites that belong to the region with the biggest amount of sites. Show their ID, name and region, and order by ID."
        info_1 = "Region"
        return render_template('queries-site-id-name-info1.html', title=title, result=result, sql_code=sql_code, info_1=info_1)
    
    elif n_pergunta == 15:
        sql_code = '''
            WITH first_years as (
                SELECT DISTINCT date_inscribed
                FROM Associated_Dates
                ORDER BY date_inscribed
                LIMIT 10)

            SELECT whs.id_no as site_number, whs.name_en AS site_name, p.states_name_en as info_1, ad.date_inscribed as info_2
            FROM associated_dates ad
            JOIN world_heritage_site whs ON ad.site_number = whs.id_no
            JOIN place p ON whs.id_no=p.site_number
            WHERE ad.date_inscribed IN first_years
            ORDER BY ad.date_inscribed;

            '''
        result = db.execute(sql_code).fetchall()
        title = "What were the sites added during the first 10 years of the World Heritage sites list? Show their ID_no, name, the country or countries where it is located and the date of inscription, and order them by that date."
        info_1 = "States name"
        info_2 = "Date inscribed"
        return render_template('queries-site-id-name-info1-info2.html', title=title, result=result, sql_code=sql_code, info_1=info_1, info_2=info_2)
    
    else:
        abort(404, 'Query number {} does not exist.'.format(n_pergunta))




#
@APP.route('/authors/')
#Route handler for the authors page.
def authors():
    return render_template('authors.html')


# Run the app
if __name__ == '__main__':
    APP.run(debug=True)
