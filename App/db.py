import logging
import sqlite3
import re


global DB
DB = dict()

#Establishes a connection to the 'world_heritage_sites.db' SQLite database and sets up the global DB dictionary with the connection and cursor objects.
def connect():
    global DB
    c = sqlite3.connect('world_heritage_sites.db', check_same_thread=False)
    c.row_factory = sqlite3.Row
    DB['conn'] = c
    DB['cursor'] = c.cursor()
    logging.info('Connected to database')

#Executes a given SQL statement with optional arguments.
def execute(sql,args=None):
    global DB
    sql = re.sub('\s+',' ', sql)
    logging.info('SQL: {} Args: {}'.format(sql,args))
    return DB['cursor'].execute(sql, args) \
        if args != None else DB['cursor'].execute(sql)

#Closes the database connection.
def close():
    global DB
    DB['conn'].close()