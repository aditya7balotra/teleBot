import mysql.connector
from dotenv import load_dotenv
import os

# loading environment variables
load_dotenv('.env.local')

database_name = os.getenv('db_name')

# Initialize connection pool
def createPool():
    cP = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="db_pool",
        pool_size=10,  # Define the number of connections in the pool
        pool_reset_session=True,  # Reset session after each transaction
        host=os.getenv('db_host'),
        user=os.getenv('db_username'),
        password=os.getenv('db_pswd'),
        database=database_name
    )
    
    return cP

try:
    connection_pool = createPool()
    
except mysql.connector.Error as e:

    print(f'database connection falided...\nPossibly database with the specified name({database_name}) is not created')
    try:
        print('Creating database ', database_name, ' ...')
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
        print('Database created successfully')
        
        connection_pool = createPool()
    except Exception as e:
        connection_pool = None
        print('Database creation failed')
        print('Reason: ', e)
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            
        
    
