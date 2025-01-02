from . import bot
from auth import auth, authData


@bot.message_handler(commands=['help'])
def send_welcome(message):
    '''
    give some instructions to the user
    '''
    # sending typing... gesture
    bot.send_chat_action(message.chat.id, 'typing')
    
    print(message)
    
    # authentification
    status = auth(message.chat.id)
    if status == True:
        pass
    elif status == False:
        bot.send_message(message.chat.id, "You are not authenticated")
        return None
    
    bot.send_message(message.chat.id, 
                     '''
    <b>🎬 Movie & Series Assistant Bot 🎥</b>

This Telegram bot helps you find movies and web series directly from our database.

<b>✨ Features:</b>
<b>1. 📂 /send &lt;movie/series name&gt;</b>: Instantly get the movie or series if available.
<b>2. 🤖 /help</b>: Get guidance on how to use the bot.
<b>3. 💬 /c &lt;text&gt;</b>: Chat with the bot powered by advanced AI (Gemini).

<i>Made with &#10084;&#65039; by ABC Team</i>

    '''
    , parse_mode = 'HTML')
    
    