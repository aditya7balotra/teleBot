from . import bot, threads, model, AI_preText, connection_pool
import json
import time
from log import logging
from auth import auth, authData

# these variables were defined for debugging purpose
# duplicates = 0
# movies = 0
# series = 0


uploadLog = logging.getLogger('upload')


def handle_files(file):
    '''
    get the file along with its caption and find out details(name, quality, is movie or series, year, season number etc) and save it to the database
    '''
    uploadLog.debug(f'Content type: {file.content_type}')
    
    # getting the file id
    file_id = file.video.file_id if file.content_type == 'video' else file.document.file_id
    
    # getting the caption
    if file.content_type == 'document':
        if file.caption is None and file.document.file_name != '':
            caption = file.document.file_name
        elif file.caption is not None and file.document.file_name == '':
            caption = file.caption
        elif file.caption is not None and file.document.file_name != '':
            caption = file.caption + ' ' + file.document.file_name
        else:
            bot.reply_to(file, 'at least give me some details')
            return None
    else:
        if file.caption == None:
            bot.reply_to(file, 'at least give me some details')
            caption = None
            return None
        else:
            caption = file.caption
    
    # requesting the model till i get a response
    while True:
        try:
            response = model.generate_content(AI_preText + caption)
            break
        except Exception as e:
            uploadLog.debug(f'Error in model: {e}')
            time.sleep(60)
    
    # extracting the main part from the response
    data = response.text.replace('```json', '').replace('```', '')
    data = json.loads(data)
    uploadLog.debug('got the data from the model')

    
    try:
        while True:
            # out of the total connections, sometimes it's possible that no one is available maybe because each one is already borrowed by threads
            connection = connection_pool.get_connection()
            time.sleep(5)
            break
    except:
        uploadLog.exception('database pool not giving connection')

    cursor = connection.cursor()
    uploadLog.debug(f'name: {data['movie']['name'] if data['ismovie'] == 1 else data['series']['name']}')

    try:
        # putting in all_records table
        query = '''
        INSERT INTO all_records
        (name, isMovie)
        VALUES (%s, %s)
        '''
        cursor.execute(query, (data['movie']['name'] if data['ismovie'] == 1 else data['series']['name'], data['ismovie']))

    except Exception as e:
        uploadLog.debug(f'{data['movie']['name'] if data['ismovie'] == 1 else data['series']['name']} -> all_records')
    
    
    # putting in moviesdata and seriesdata table
    try:
        if data['ismovie'] == 0:
            # means its a sereies
            
            sData = data['series']
            
            query = '''
            INSERT INTO seriesdata
            (name, year, season, quality, episode, ref, language, subtitle)
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.execute(query, (sData['name'], sData['year'], sData['season'], sData['quality'], sData['episode'], file_id, sData['language'], sData['subtitle']))
            uploadLog.debug(f'{sData['name']} -> series table')
            global series
            series += 1
            # print('total series added to the database: ', series)
        else:
            # if its a movie
            sData = data['movie']
            
            query = '''
            INSERT INTO moviesdata
            (name, year, quality, ref, language, subtitle)
            VALUES (%s, %s, %s, %s, %s, %s)
            '''
            cursor.execute(query, (sData['name'], sData['year'], sData['quality'], file_id, sData['language'], sData['subtitle']))
            uploadLog.debug(f'{sData['name']} -> movies table')
            global movies
            movies += 1
            # print('total movies added to the database: ', movies)
            
    except Exception as e:
        # uploadLog.exception('Exception: ')
        uploadLog.debug(f'{sData['name']} -> already in {'seriesdata' if data['ismovie'] == 0 else 'moviesdata'}: \n {e}')
        global duplicates
        duplicates += 1
        # print('total duplicates found: ', duplicates)
    finally:
        connection.commit()
        cursor.close()
        connection.close()


@bot.channel_post_handler(content_types=['document', 'video'])
@bot.message_handler(content_types=['document', 'video'])
def thread_handle_files(file):
    '''
    this function will create multiple threads for each file/video as we receive so that the bot will work smoothly
    '''
    # print(file)
    # authentification
    status = auth(file.chat.id)
    if status == True:
        pass
    elif status == False:
        # bot.send_message(file.chat.id, 'You are not authorized to use this bot')
        return None
    
    threads.submit(handle_files, file)
