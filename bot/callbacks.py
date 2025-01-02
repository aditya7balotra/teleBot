from . import bot, connection_pool
from telebot.types import InlineKeyboardButton , InlineKeyboardMarkup
import time
from .send import send_movie_series
from log import logging


callbackLog = logging.getLogger('callbacks')

@bot.callback_query_handler(func = lambda call : True)
def handle_all_callbacks(call):
  '''
  this will handle all the callbacks from the user
  '''
  separator = ':x@x:'
  splitData = call.data.split(separator)

  
  # establish the connection
  try:
      while True:
        connection = connection_pool.get_connection()
        time.sleep(5)
        break
  except:
      callbackLog.exception('Error in getting connection from the pool, maybe because of threading... so trying again')
      
  cursor = connection.cursor()
  # print('\n ===========')

  
  # print('connection established for callback')
  
  # print('=========== \n')

  if splitData[0] == 'movies':
    # this will run if the user selected a movie
    sno = int(splitData[1])
    quality = splitData[2]
    
    # sending upload_video gesture
    bot.send_chat_action(call.message.chat.id , 'upload_video')
    
    query = '''SELECT name, year, ref FROM moviesdata
    WHERE sno = %s'''
    cursor.execute(query , (sno, ))
    
    result = cursor.fetchone()

    yr = result[1]
    ref = result[2]
    name = result[0]
    
    if yr == None:
      yr = ''
    
    # sending the movie
    bot.send_video(
      chat_id=call.message.chat.id,
      video= ref,
      caption = f'''<strong>{name} {yr} {quality}\nEnjoy watching! @{call.from_user.username}</strong>''',
      parse_mode= 'HTML'
    )

  
  
  # for series
  elif splitData[0] == 'seriesSeason':
    bot.send_chat_action(call.message.chat.id , 'typing')
    sno = splitData[1]
    season = splitData[2]
    
    cursor.execute('''
                   SELECT name, year FROM seriesdata
                   WHERE sno = %s
                   ''',
                   (sno ,)
                   )
    result = cursor.fetchone()
    name= result[0]
    yr= result[1]
    if yr == None:
      yr = ''
    
    
    # now show all the buttons for episodes
    query = '''
    SELECT episode , sno FROM seriesdata
    WHERE name = %s AND season = %s
    '''
    # print(name , season)
    cursor.execute(query , (name , season))
    
    result = cursor.fetchall()
    
    # ensuring unique episodes
    def clean(data):
      finalData = []
      ep = []
      for i in data:
        if i[0] not in ep:
          finalData.append(i)
          ep.append(i[0])
      
      return finalData
    
    result = clean(result)

    
    episodesMarkup = InlineKeyboardMarkup(row_width= 2)

    
    episodesButton = []
    for data in result:
      # callback format = seriesEp :x@x: sno :x@x: episode
      # separator = :x@x:
      episodesButton.append(InlineKeyboardButton(text= data[0], callback_data= f'seriesEp:x@x:{data[1]}:x@x:{data[0]}'))
      
    for i in range(0, len(episodesButton), 2):
      row = episodesButton[i : i+2]
      episodesMarkup.row(*row)
    
    # bot.reply_to(
    #   call.message , f'Select the episode for <strong> <u> {name} Season: {season} {yr}</u></strong>' , parse_mode = 'HTML' , reply_markup = episodesMarkup
    # )
    bot.edit_message_text(
      chat_id= call.message.chat.id,
      message_id= call.message.message_id,
      text= f'Select the episode for <strong> <u> {name} Season: {season} {yr}</u></strong>',
      parse_mode='HTML',
      reply_markup= episodesMarkup
    )
    
  elif splitData[0] == 'seriesEp':
    # sending the typing... gesture
    sno = splitData[1]
    bot.send_chat_action(call.message.chat.id , 'typing')

    # after this we are going to show the options for quality
    cursor.execute('''
                   SELECT name , season , episode , year , quality , sno FROM seriesdata
                   WHERE sno = %s
                   ''',
                   (sno, ))
    result = cursor.fetchone()
    
    name , season , episode , year = result[0] , result[1] , result[2] , result[3]
    if year == None:
      year = ''
    cursor.execute('''
                   SELECT quality , sno FROM seriesdata
                   WHERE name = %s AND season = %s AND episode = %s
                   ''',
                   (name , season , episode ,))
    
    result = cursor.fetchall()
    # here each quality we will get is going to be unique because of database side constraints
    
    qualityMarkup = InlineKeyboardMarkup(row_width= 2)

    quality_list = []
    for data in result:

      quality_list.append(InlineKeyboardButton(text = f'{data[0]}' , callback_data= f'seriesQ:x@x:{data[1]}:x@x:{data[0]}'))
      
    # adding the buttons 
    qualityMarkup.add(
      *quality_list
    )
    
    # bot.reply_to(
    #   call.message , f'Select the quality for<strong><u> {name} Season: {season} Episode: {episode} {year}</u> </strong>' , parse_mode = 'HTML' , reply_markup = qualityMarkup
    # )
    bot.edit_message_text(
      chat_id= call.message.chat.id,
      message_id= call.message.message_id,
      text= f'Select the quality for<strong><u> {name} Season: {season} Episode: {episode} {year}</u> </strong>',
      parse_mode='HTML',
      reply_markup= qualityMarkup
    )

  elif splitData[0] == 'seriesQ':
    # in this case the user has selected the quality they want for the episode and i will send this to the user
    sno = splitData[1]
    quality = splitData[2]
    bot.send_chat_action(call.message.chat.id , 'upload_video')
    
    
    query = '''
    SELECT name, season , episode, quality, year , ref FROM seriesdata
    WHERE sno = %s
    '''
    cursor.execute(query , (sno ,))
    
    result = cursor.fetchone()

    
    bot.send_video(
      call.message.chat.id ,
      result[-1] ,
      caption= f'''<strong>{result[0]} Season: {result[1]} Episode: {result[2]} {result[3]} {'' if result[4] == None else result[4]}\nEnjoy watching! @{call.from_user.username}</strong>''',
      
      parse_mode= 'HTML'
      
    )
    
  elif call.data.split(':>')[0] == 'rcmd':
    # means this callback is from the /rcmd , so we need to fetch the movie/series and then work accordingly
    
    send_movie_series(call.message , is_rcmd = call)


  cursor.close()
  connection.close()
  # print('\n ===========')
  
  # print('connection closed for callback')
  
  # print('=========== \n')
  