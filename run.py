import telebot
import json
# import time
# from datetime import date
# import pycountry
import requests as rq
from dotenv import load_dotenv
import threading as th
import time
from concurrent.futures import ThreadPoolExecutor
import os
# import re
from google import generativeai as genai

from telebot.types import InlineKeyboardButton , InlineKeyboardMarkup
from db import connection_pool

# Load environment variables from the .env.local file
load_dotenv('.env.local')
AI_preText = None

 


# initializing the TeleBot class
bot = telebot.TeleBot(os.getenv('bot_apiAdhi'), parse_mode=None)

# object for threads pooling
threads = ThreadPoolExecutor(max_workers= 50)

# decorator for showing the database initialization
def decorator(func):
  def wrapper():
    print('\n ================== \n')
    print(func())
    print('\n ================== \n')
    
  return wrapper


# this method will create the schema of the database
@decorator
def create_schema(db_file = os.getenv('db_script')):
  print('=> initiallizing database...')
  try:
    with open(db_file , 'r') as file:
      queries = file.read()
    
    # execute each query
    connection = connection_pool.get_connection()
    cursor = connection.cursor()
    print('---connection established for init')
    for i in cursor.execute(queries , multi = True):
      pass
    
    connection.commit()
    
    
    print('---connection closed for init')
    return '=> database initialized successfully...'
  
  except Exception as e:
    print(f'=> database initialization failed...')
    return exit()
  
  finally:
    # closing the connection
    cursor.close()
    connection.close()
  

def set_AI():
  '''
  this is setting up the google's gemini // you can try with different models as well
  '''
  
  # some pre-instructions to the AI model
  global AI_preText
  
  with open('geminiMsg.txt') as file:
    AI_preText = file.read()
  
  # setting up configuration
  genai.configure(api_key=os.getenv('gemini_apiKey'))
  
  # getting the model object
  model = genai.GenerativeModel("gemini-2.0-flash-exp")
  
  # print('----')
  return model
    
model = set_AI()

# create the database schema
create_schema()
# totalThreads = 0



def handle_files(file):
    '''
    get the file along with its caption and find out details(name, quality, is movie or series , year , season number etc) and save it to the database
    '''
    
    # get the file id
    try:
      # print('video')
      file_id = file.video.file_id
    except:
      # print('document')
      file_id = file.document.file_id
    
    while True:
      # there are some limitations of api requests per minute(and also sometimes for a day) to the server. If the number of requests overpass the limit, then we have to wait to about 60s.
      try:
        # getting response from the model
        response = model.generate_content(AI_preText + file.caption)
        # global ai_req
        # ai_req += 1
        # print('AI requests: ', ai_req)
        # if we have got a response means the api request was successfull, so now get out of the loop
        break
      except:
        # print('AI requests: ', ai_req)
        # print('sleeping')
        time.sleep(15)
        
    # preprocessing the response got from the model converting it the python dictionary using json module
    data = response.text.replace('```json', '').replace('```', '')
    data = json.loads(data)
    # print(data)
    
    # getting connection from the connection pool
    connection = connection_pool.get_connection()
    cursor = connection.cursor()
    print('\n ===========')
    print('connection established for movies/series upload')
    print('=========== \n')
    
    # saving the data to the database
    
    # saving the data to the 'all_records' table
    try:
        # this will run if no other movie with the same name is found in 'all_records' table
        query = '''
        INSERT INTO all_records
        (name , isMovie)
        VALUES (%s , %s)
        '''
        
        
        cursor.execute(query , (data['movie']['name'] if data['ismovie'] == 1 else data['series']['name'], data['ismovie']))
        # print('all records')
        
      
    except Exception as e:
        # means movie / series was already in the all_records table
        pass
    
    # saving the data to seriesdata or moviesdata table
    try:
      if data['ismovie'] == 0:
            # means its a series
            
            # now fetching details from the data variable and inserting into the database
            sData = data['series']
            
            query = '''
            INSERT INTO seriesdata
            (name , year , season , quality , episode , ref, language, subtitle)
            VALUES
            (%s , %s , %s , %s , %s , %s, %s, %s)
            '''
            

            cursor.execute(query , (sData['name'] , sData['year'] , sData['season'] , sData['quality'] , sData['episode'] , file_id, sData['language'], sData['subtitle']))

      else:
          # if its a movie
          
          # getting data from the data variable and inserting into the database
          sData = data['movie']
          
          query = '''
          INSERT INTO moviesdata
          (name , year , quality , ref, language , subtitle)
          VALUES (%s , %s , %s , %s , %s, %s)
          '''
          
          cursor.execute(query , (sData['name'] , sData['year'] , sData['quality'], file_id, sData['language'] , sData['subtitle']))

    
    
    except Exception as e:
      # means the data or movie/series was already in the database
      print(f"Already in the {'seriesdata' if data['ismovie'] == 0 else 'moviesdata'}  database")
    
    
    finally:
      # commiting and closing the connection
      connection.commit()
      cursor.close()
      connection.close()
      

@bot.message_handler(content_types=['document','video'])
def thread_handle_files(file):
  '''
  this function will create multiple threads for each file/video as we recieve so that the bot will work smoothly
  ''' 
  # global totalThreads
  threads.submit(handle_files, file)
  # totalThreads += 1
  # print('Threads: ', totalThreads)




@bot.message_handler(commands=['help'])
def send_welcome(message):
    '''
    give some instructions to the user
    '''
    bot.send_message(message.chat.id, 
                     '''
    <b>Bot Help</b>

    This Telegram bot helps you find movies and web series.

    <b>/send &lt;movie_name&gt;</b>
    Get a movie or web series.

    <b>/rcmd &lt;movie_name&gt;</b>
    Get recommendations for a movie or web series.

    <b>/help</b>
    View this help page with all available commands.

    <i>Made with &#10084;&#65039; by YourBot</i>
    '''
    , parse_mode = 'HTML')
	
    # print(MessageID)
    # print(message.chat.id)



@bot.message_handler(commands=['send'])
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
  connection = connection_pool.get_connection()
  cursor = connection.cursor()
  print('\n ===========')
  
  print('connection established for send')
  
  print('=========== \n')
  
  # also replacing most punctuation marks
  # mostly are already deleted from the movie/series names, as instructed to the model
  query = '''
  SELECT isMovie FROM all_records
  WHERE REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(name, ' ', ''), ':', ''), '-', ''), '.', ''), ',', ''), '_', ''), '"', ''), "'", ''), ';', ''), '?', '') = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(%s, ' ', ''), ':', ''), '-', ''), '.', ''), ',', ''), '_', ''), '"', ''), "'", ''), ';', ''), '?', '')
  '''
  
  # print(name)
  # print('----')
  cursor.execute(query , (name, ))
  
  # execution result
  result = cursor.fetchone()
  # print(result)

  # 1 => movie , 0 => series, None => not found
  
  if result == (1,):
    # this will execute if the reauested one is the movie
    # so we have to use moviesdata table
    
    # sending typing... gesture to the user
    bot.send_chat_action(message.chat.id , 'typing')
    
    query = '''
    SELECT * FROM moviesdata 
    WHERE REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(name, ' ', ''), ':', ''), '-', ''), '.', ''), ',', ''), '_', ''), '"', ''), "'", ''), ';', ''), '?', '') = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(%s, ' ', ''), ':', ''), '-', ''), '.', ''), ',', ''), '_', ''), '"', ''), "'", ''), ';', ''), '?', '')
    '''
    # print(name)
    cursor.execute(query , (name , ))
    
    # get the execution result
    result = cursor.fetchall()
    
    # print(result)
    
    
    # if the movie is found in the database then send the movie to the user in GUI format
    # creating the Inline keyboard markup for some GUI interaction
    
    # inline keyboard for quality selection
    moviesMarkup = InlineKeyboardMarkup(row_width= 2)
    # Create a row of buttons
    row_buttons = []
    for i in range(0, len(result), 2):  # Step by 2 to create rows of 2 buttons
      
      for j in range(i, min(i + 2, len(result))):  # Add up to 2 buttons
          row_buttons.append(InlineKeyboardButton(text=f'{result[j][3]}', callback_data= f'moviesdata-{result[j][0]}')) # text = quality , callback_data = movie_sno
      
    moviesMarkup.add(*row_buttons)
      
    bot.reply_to(message , f'Select the desired quality for <strong><u>{name}</u> ({result[0][2]})</strong> ' , reply_markup = moviesMarkup , parse_mode = 'HTML')
    
    cursor.close()
    connection.close()
    print('\n ===========')
    
    print('connection closed for send')
    
    print('=========== \n')
    
    
  elif result == (0 , ):
    # this will execute if the requested one is the series
    # so we have to use seriesdata table

    # sending typing... gesture
    bot.send_chat_action(message.chat.id , 'typing')
    
    
    query = '''
    SELECT season , year , sno FROM seriesdata 
    WHERE REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(name, ' ', ''), ':', ''), '-', ''), '.', ''), ',', ''), '_', ''), '"', ''), "'", ''), ';', ''), '?', '') = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(%s, ' ', ''), ':', ''), '-', ''), '.', ''), ',', ''), '_', ''), '"', ''), "'", ''), ';', ''), '?', '')
    '''
    
    cursor.execute(query , (name , ))
    
    # fetching query execution result
    result = cursor.fetchall()
    
    # GUI phases:
      # we are going to send the seasons first , then after selecting the season the user have to select the episodes they want to get
      
    # preparing seasons
    seasons = [(season[2] , season[0] , season[1]) for season in result] # {(sno , seasonName , year)}

    n_seasons = []
    sns = []
    for i in seasons:
      if i[1] not in sns:
        sns.append(i[1])
        n_seasons.append(i)
      
        
    # print(sns)
    # print(seasons)
    seriesMarkup = InlineKeyboardMarkup()
    
    button_seasons = []
    for i in n_seasons:
      # type : sereis-season , series-season-episode

      button_seasons.append(InlineKeyboardButton(text = f'{i[1]} ({i[2]})', callback_data= f's-s:>{i[0]}')) # i[0] => sno
      
    seriesMarkup.add(
      *button_seasons
    )
      
    bot.reply_to(message , f'Select the season for <strong><u>{name}</u></strong> ' , reply_markup = seriesMarkup , parse_mode = 'HTML')
    
    cursor.close()
    connection.close()
    print('\n ===========')
    print('connection close for send')
    print('=========== \n')
    
  else:
    if is_rcmd == False:
      bot.reply_to(message , f'Not found , make sure that you enter the correct spelling @{message.chat.username}')
    else:
      bot.reply_to(is_rcmd.message , f'Not uploaded by the channel @{message.chat.username}')
    cursor.close()
    connection.close()
    print('\n ===========')
    print('connection close for send')
    print('=========== \n')

      
@bot.callback_query_handler(func = lambda call : True)
def handle_all_callbacks(call):
  '''
  this will handle all the callbacks from the user
  '''
  
  # establish the connection
  connection = connection_pool.get_connection()
  cursor = connection.cursor()
  print('\n ===========')

  
  print('connection established for callback')
  
  print('=========== \n')
  
  
  if call.data.split('-')[0] == 'moviesdata':
    # this will run if the user selected a movie
    bot.send_chat_action(call.message.chat.id , 'upload_video')
    sno = call.data.split('-')[1]
    
    query = '''SELECT name , year , quality , ref FROM moviesdata
    WHERE sno = %s'''
    cursor.execute(query , (sno ,))
    
    result = cursor.fetchone()
    # print(result)
    name = result[0]
    yr = result[1]
    quality = result[2]
    ref = result[3]
    
    
    # sending the send_movie
    
    bot.send_video(
      chat_id=call.message.chat.id,
      video= ref,
      caption = f'''<strong>{name} {yr} {quality}\nEnjoy watching! @{call.message.chat.username}</strong>''',
      parse_mode= 'HTML'
    )

  
  
  # for series
  elif call.data.split(':>')[0] == 's-s':
    bot.send_chat_action(call.message.chat.id , 'typing')
    sno = call.data.split(':>')[1]
    cursor.execute('''
                   SELECT name , season , year FROM seriesdata
                   WHERE sno = %s
                   ''',
                   (sno ,)
                   )
    result = cursor.fetchone()
    name , season , yr = result[0] , result[1] , result[2]
    
    # now show all the buttons for episodes
    query = '''
    SELECT episode , sno FROM seriesdata
    WHERE REPLACE(name , ' ' , '') = REPLACE(%s , ' ' , '') AND season = %s
    ORDER BY episode
    '''
    # print(name , season)
    cursor.execute(query , (name , season))
    
    # print(name.split('(')[0][: -1])
    result = cursor.fetchall()
    n_epi = []
    epi = []
    for i in result:
      if i[0] not in epi:
        epi.append(i[0])
        n_epi.append(i)
      
    
    episodesMarkup = InlineKeyboardMarkup(row_width= 2)
    
    episodes_list = []
    for i in n_epi:
      episodes_list.append(InlineKeyboardButton(text = f'{i[0]}' , callback_data = f's-s-e:>{i[1]}')) #name season episode #i[0] => episode name , i[1] => sno
    
    episodesMarkup.add(
      *episodes_list
    )
    
    bot.reply_to(
      call.message , f'Select the episode for <strong> <u> {name} {season} {yr}</u></strong>' , parse_mode = 'HTML' , reply_markup = episodesMarkup
    )
    
  elif call.data.split(':>')[0] == 's-s-e':
    bot.send_chat_action(call.message.chat.id , 'typing')
    
    sno = call.data.split(':>')[1]
    
    # after this we are going to show the options for quality
    cursor.execute('''
                   SELECT name , season , episode , year , quality , sno FROM seriesdata
                   WHERE sno = %s
                   ''',
                   (sno, ))
    result = cursor.fetchall()
    
    name , season , episode , year = result[0][0] , result[0][1] , result[0][2] , result[0][3]
    cursor.execute('''
                   SELECT quality , sno FROM seriesdata
                   WHERE REPLACE(name , ' ' , '') = REPLACE(%s , ' ' , '') AND season = %s AND episode = %s
                   ''',
                   (name , season , episode ,))
    result = cursor.fetchall()
   
    
    qualityMarkup = InlineKeyboardMarkup(row_width= 2)
    
    # print('---')
    # print(result)
    quality_list = []
    for quality in result:
      # print(len(f's-s-e-q:>{name}:>{season}:>{episode}:>{quality[0]}'))
      quality_list.append(InlineKeyboardButton(text = f'{quality[0]}' , callback_data= f's-s-e-q:>{quality[-1]}'))
      
    # adding the buttons 
    qualityMarkup.add(
      *quality_list
    )
    # print('buttons added')
    # print(name , season , episode)
    
    bot.reply_to(
      call.message , f'Select the quality for<strong><u> {name} {season} {episode} {year}</u> </strong>' , parse_mode = 'HTML' , reply_markup = qualityMarkup
    )
    # print('reply send')
  elif call.data.split(':>')[0] == 's-s-e-q':
    # in this case the user has selected the quality they want for the episode and i will send this to the user
    bot.send_chat_action(call.message.chat.id , 'upload_video')
    
    # print(name , season , episode , quality)
    
    # let's new get the ref , so to send the file to the user
    sno = call.data.split(':>')[1]
    
    query = '''SELECT name, season , episode, quality, year , ref FROM seriesdata
    WHERE sno = %s'''
    cursor.execute(query , (sno ,))
    
    result = cursor.fetchone()
    # print('---')
    # print(result)
    
    bot.send_video(
      call.message.chat.id ,
      result[-1] ,
      caption= f'''<strong>{result[0]} {result[1]} {result[2]} {result[3]} {result[4]}\nEnjoy watching! @{call.message.chat.username}</strong>''',
      
      parse_mode= 'HTML'
      
    )
    
  elif call.data.split(':>')[0] == 'rcmd':
    # means this callback is from the /rcmd , so we need to fetch the movie/series and then work accordingly
    
    send_movie_series(call.message , is_rcmd = call)


  cursor.close()
  connection.close()
  print('\n ===========')
  
  print('connection closed for callback')
  
  print('=========== \n')
  



# ----- adhi's work start here

def filterRcmdMovies(dictData):
    '''
    This function will filter the dict data to get the list of similar movies provided by it
    '''
    # sno = 1
    try:
        similarData = dictData['similar']['results']
        similarMovies = []
        
        def workInListElements(elm):
            similarMovies.append(f"{elm['name']}")
            
            
        for elm in similarData:
            workInListElements(elm)
        #     sno += 1
    except:
        similarMovies = ['movie not found']
    
    # print(similarMovies)
    return similarMovies

    

@bot.message_handler(commands= ['rcmd'])
def recommend_movies(msg):
    '''
    This function will recommend movies based upon the given movie
    
    Expected command /rcmd movie_name
    '''
    # chat action
    bot.send_chat_action(msg.chat.id , 'typing')
    noRcmd = 10 #suggest 10 movies ===> you can change , also keep in mind that Telegram also restricts the max. number of texts your bot can send
    movie_name = msg.text[6 : ]
    # print(movie_name)
    
     
    base_url = 'https://tastedive.com/api/similar'
    api_key = os.getenv('api_key')
    
    parameters = {
    'q': f'movie:{movie_name}',  # Specify the query (you can include multiple items)
    'type': 'movie',            # Specify the type of content (movie, music, etc.)
    'info': 0,                  # Set to 1 to get additional information like description and YouTube links
    'limit': noRcmd,                 # Limit the number of recommendations
    'k': api_key    # Replace with your actual API access key
    }
    
    res = rq.get(base_url , params= parameters)
    print(res.json())
    # getting 10 similar movies
    similarMovies = filterRcmdMovies(res.json())
    # print(similarMovies)
    # print('---')
    # preparing the inline buttons
    # bot.send_message(msg.chat.id,'removing keyboard....' , reply_markup=ReplyKeyboardRemove())
    
    if similarMovies[0] == 'movie not found':
      bot.reply_to(msg , 
                  f'<strong>cannot found , make sure you typed correct spellings</strong> @{msg.chat.username}',
                  parse_mode = 'HTML')
    else:
      rcmd_markup = InlineKeyboardMarkup(row_width = 2)
      
      for i in range(0, len(similarMovies), 2):  # Step by 2 to create rows of 2 buttons
          # Create a row of buttons
          row_buttons = []
          for j in range(i, min(i + 2, len(similarMovies))):  # Add up to 2 buttons
              
              row_buttons.append(InlineKeyboardButton(text=similarMovies[j], callback_data=f'rcmd:>{similarMovies[j]}')) 
          
          rcmd_markup.row(*row_buttons)  # Unpack the list to add the buttons as a row
      
      # Sending the reply with the inline keyboard
      bot.reply_to(msg, f'@{msg.chat.username} Here are a few suggestions:', reply_markup=rcmd_markup)
      
@bot.message_handler(commands=['c'])
def chat(message):
  '''
  a feature to chat with the gemini bot using the telbot
  '''
  bot.send_chat_action(message.chat.id, 'typing')
  userMsg = message.text[3: ]
  try:
    # sending the message to the model
    response = model.generate_content(userMsg + 'please reply in short, less than 200 words')
    
    bot.reply_to(message, response.text)
  except:
    bot.reply_to(message, 'Sorry, message too long to send')



#Bot keeps Running 24/7
def startBot():
  while True:
    try:
      bot.infinity_polling()
    except:
      print('error----')
      
if __name__ == '__main__':
  startBot()