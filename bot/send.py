from . import bot, connection_pool
import time
from telebot.types import InlineKeyboardButton , InlineKeyboardMarkup
from log import logging
from auth import auth, authData
from concurrent.futures import ThreadPoolExecutor


# setting up the thread pool
threadsSend = ThreadPoolExecutor(max_workers= 8)
# getting the logger
sendLog = logging.getLogger('send')

def isMovie(name, cursor):
    '''
    Returns:
        1: if name is a movies in all_records table
        0: if name is a series in all_records table
        -1: if name is not in all_records table
    cursor: connection cursor
    '''
    
    
    query = '''
    SELECT isMovie FROM all_records
    WHERE REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(name, ' ', ''), ':', ''), '-', ''), '.', ''), ',', ''), '_', ''), '"', ''), "'", ''), ';', ''), '?', '') = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(%s, ' ', ''), ':', ''), '-', ''), '.', ''), ',', ''), '_', ''), '"', ''), "'", ''), ';', ''), '?', '')
    '''
    
    cursor.execute(query , (name, ))

    
    # execution result
    result = cursor.fetchone()
    logging.debug(f'data fetched from the all_records table for {name}')

    if result != None:
        return result[0]
    
    else:
        return -1

def searchMovies(name, cursor):
    '''
    this function searches the movie in the database and returns the list of tuples containing movie data
    '''

    
    query = '''
        SELECT sno, quality FROM moviesdata 
        WHERE REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(name, ' ', ''), ':', ''), '-', ''), '.', ''), ',', ''), '_', ''), '"', ''), "'", ''), ';', ''), '?', '') = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(%s, ' ', ''), ':', ''), '-', ''), '.', ''), ',', ''), '_', ''), '"', ''), "'", ''), ';', ''), '?', '')
        '''
    # print(name)
    cursor.execute(query , (name , ))
    
    # get the execution result
    result = cursor.fetchall()
    logging.debug(f'data fetched from moviesData table for {name}')

    return result
    

def searchSeries(name, cursor):
    '''
    this function will search the series in the seriesData table and return the list of tuples containing the data
    '''
    
    query = '''
        SELECT sno, season FROM seriesdata 
        WHERE REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(name, ' ', ''), ':', ''), '-', ''), '.', ''), ',', ''), '_', ''), '"', ''), "'", ''), ';', ''), '?', '') = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(%s, ' ', ''), ':', ''), '-', ''), '.', ''), ',', ''), '_', ''), '"', ''), "'", ''), ';', ''), '?', '')
        '''
        
    cursor.execute(query , (name , ))
    
    # fetching query execution result
    result = cursor.fetchall()

    logging.debug('data fetched from seriesData table for {name}')
    
    return result


    
def send_movie_series(message , is_rcmd = False):
    '''
    this function will send the desired movie/series to the user
    is_rmcd: its for check. True means we are in this function for the recommendation purpose, False indicates we are here because of /send <movie_name> command from the user
    '''

    
    # sending typing... gester to the user
    bot.send_chat_action(message.chat.id , 'typing')
    
    
    
    if is_rcmd == False:
        # means not for the recommendation purpose
        name = message.text[6 : ] #fetch the movie/series name
      
    else:
        # here for the recommendation purpose
        name = is_rcmd.data.split(':>')[1]
    
    # get a connection
    try:
        while True:
            connection = connection_pool.get_connection()
            time.sleep(5)
            break
    except:
        print('sleeping because connection could not be made with sql server')
        
    cursor = connection.cursor()

    result = isMovie(name, cursor)
    
    if result == 1:
        
        
        moviesResult = searchMovies(name, cursor)

        moviesMarkup = InlineKeyboardMarkup(row_width= 2)
    
        buttonsText = []

        for data in moviesResult:
            # using :x@x: as separator in callbacks
            # callback_data fromat = movies/series :x@x: movieName :x@x: quality
            sno = data[0]
            buttonsText.append(InlineKeyboardButton(text = data[1], callback_data= f'movies:x@x:{sno}:x@x:{data[1]}'))
        
        # print(buttonsText)
        for i in range(0, len(moviesResult), 2):
            rowButtons = buttonsText[i: i+2]

            moviesMarkup.row(*rowButtons)
            
        bot.reply_to(message , f'Select the desired quality for <strong><u>{name}</u></strong> ' , reply_markup = moviesMarkup , parse_mode = 'HTML')
        
        cursor.close()
        connection.close()

      
      
    elif result == 0:
        def sortR(data):
            return int(data[1])
        
        def clean(data):
            # this function is to ensure that seasons shown in the GUI are in proper descending order
            finalData = []
            seasonsGot = []
            for i, detum in enumerate(data):
                if detum[1] not in seasonsGot:
                    finalData.append(detum)
                    seasonsGot.append(detum[1])
            return finalData
        
        seriesResult = sorted(searchSeries(name, cursor), key= sortR)
 
        seriesResult = clean(seriesResult)

        
        # sending typing... gesture
        bot.send_chat_action(message.chat.id , 'typing')
        
        seriesMarkup = InlineKeyboardMarkup()
        
        button_seasons = []

        for data in seriesResult:
            # using separator :x@x:
            # season callbacks format: seriesSeason/seriesEpisode/seriesQuality :x@x: sno in seriesData table :x@x: season/episode/quality
            button_seasons.append(InlineKeyboardButton(text = f'{data[1]}', callback_data= f'seriesSeason:x@x:{data[0]}:x@x:{data[1]}'))
            
        
            
        for i in range(0, len(button_seasons), 2):
            rowButtons = button_seasons[i: i+2]
            seriesMarkup.row(*rowButtons)
                            
          
        bot.reply_to(message , f'Select the season for <strong><u>{name}</u></strong> ' , reply_markup = seriesMarkup , parse_mode = 'HTML')
        
        cursor.close()
        connection.close()
      
    else:
        if is_rcmd == False:
            # print(message)
            bot.reply_to(message , f'Not found , make sure that you enter the correct spelling @{message.from_user.username}')
        else:
            bot.reply_to(is_rcmd.message , f'Not uploaded by the channel @{message.chat.username}')
        cursor.close()
        connection.close()



@bot.message_handler(commands=['send'])
def thread_movie_series(message):
    '''
    this function will create a new thread to send the movie/series to the user, thus improving performance
    '''
    
    # authentification
    status = auth(message.chat.id)
    if status == True:
        pass
    elif status == False:
        bot.send_message(message.chat.id, 'You are not authorized to use this bot')
        return None
    
    threadsSend.submit(send_movie_series, message)