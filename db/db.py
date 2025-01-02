import mysql.connector
from dotenv import load_dotenv
import os

import mysql.connector.logger
from log import logging



# loading environment variables
load_dotenv('env/.env')
dbLog = logging.getLogger('db')

database_name = os.getenv('db_name')

# Initialize connection pool
def createPool():
    cP = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="db_pool",
        pool_size=32,  # Define the number of connections in the pool
        pool_reset_session=True,  # Reset session after each transaction
        host=os.getenv('db_host'),
        user=os.getenv('db_username'),
        password=os.getenv('db_pswd'),
        database=database_name
    )
    
    return cP


# decorator for showing the database initialization
def decorator(func):
    def wrapper():
        print('initialising database...')
        func()
        
      
    return wrapper


# this method will create the schema of the database
@decorator
def create_schema(db_file = os.getenv('db_script')):
    
    connectionS = connection_pool.get_connection()
    cursorS = connectionS.cursor()
    dbLog.info('got connected with the database successfully')
    
    try:
        with open(db_file , 'r') as file:
            queries = file.read()
        
        # execute each query
        
        for i in cursorS.execute(queries , multi = True):
            pass
        
        connectionS.commit()
        
        dbLog.info('data schema initialised successfully')
        
    
    except Exception as e:

        dbLog.warning('database schema initialisation failed', exc_info= True)
        
        return exit()
        
        
    finally:
        # closing the connection
        cursorS.close()
        connectionS.close()
        dbLog.info('connection closed with the database successfully (schema)')
        
    
    
    
# ensuring the database is available
try:
    connection_pool = createPool()
    dbLog.info('database connection pool created successfully')
    # creating the schema
    create_schema()

    
except mysql.connector.Error as e:
    dbLog.warning('database connection failed', exc_info= True)
   
    try:
        # print('Creating database (', database_name, ')...')
        dbLog.info(f'creating database({database_name})')
        # possibly database is not created with the given name, let's create one
        connection = mysql.connector.connect(
            host=os.getenv('db_host'),
            user=os.getenv('db_username'),
            password=os.getenv('db_pswd'),
        )
        
        cursor = connection.cursor()
        query = f'CREATE DATABASE {database_name}'
        cursor.execute(query)
        connection.commit()

        dbLog.info('database created successfully')
        connection_pool = createPool()
        # creating the schema
        create_schema()
        dbLog.info('database schema created successfully')
        
        
        
    except Exception as e:
        connection_pool = None
        # print('Database creation failed')
        # print('Reason: ', e)
        dbLog.critical('cannot create database. ^_^')
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            dbLog.info('connections for database initialisation closed properly(db dont exist)')

            

