from bot import bot

#Bot keeps Running 24/7
def startBot():
  print('bot is listening...')
  while True:
    try:
      bot.infinity_polling()
    except:
      print('error----')
      

if __name__ == '__main__':
  startBot()