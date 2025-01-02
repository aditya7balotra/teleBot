from . import bot, model
from log import logging
from auth import auth, authData


chatLog = logging.getLogger('chat')


@bot.message_handler(commands=['c'])
def chat(message):
    '''
    a feature to chat with the gemini bot using the telbot
    '''
    bot.send_chat_action(message.chat.id, 'typing')
    
    # authentification
    status= auth(message.chat.id)
    if status == True:
        pass
    elif status == False:
        bot.reply_to(message, 'You are not authorized to chat with me')
        return None
    
    userMsg = message.text[3: ]
    try:
        # sending the message to the model
        response = model.generate_content('hello, ' + userMsg + 'answer in less than 200 words').text
        bot.reply_to(message, response)
    except:
        chatLog.exception('Model reply is too long to send by the bot')
        bot.reply_to(message, 'I dont wanna reply... I its my rest time dude!')
