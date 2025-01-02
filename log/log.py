import logging


# basic configuration
logging.basicConfig(
    level=logging.INFO,
    filename='log/logs/main.log',
    filemode= 'w',
    format='%(asctime)s - %(name)s - %(message)s',
    encoding= 'utf-8'
)

logFiles = ['log/logs/' + files for files in ['chat.log', 'callbacks.log', 'createBot.log', 'send.log', 'upload.log', 'db.log', 'model.log']]

logging.info('setting up custom logs')
# creating custom loggers
# help = logging.getLogger('help')
# help.setLevel(logging.INFO)
# logging.info('help log created')

chat = logging.getLogger('chat')
chat.setLevel(level=logging.INFO)
logging.info('chat log created')

callbacks = logging.getLogger('callbacks')
callbacks.setLevel(level=logging.INFO)
logging.info('callbacks log created')

botCreate = logging.getLogger('create bot')
botCreate.setLevel(level=logging.INFO)
logging.info('botCreate log created')

send = logging.getLogger('send')
send.setLevel(level=logging.INFO)
logging.info('send log created')

upload = logging.getLogger('upload')
upload.setLevel(level= logging.INFO)
logging.info('upload log created')

db = logging.getLogger('db')
db.setLevel(level=logging.INFO)
logging.info('db log created')

model = logging.getLogger('model')
model.setLevel(level= logging.INFO)
logging.info('model log created')

customLoggers = [chat, callbacks, botCreate, send, upload, db, model]

# some basic configuration of each custom logger


for index, file in enumerate(logFiles):
    handler = logging.FileHandler(file, mode= 'w')
    formatter = logging.Formatter(
        '%(levelname)s - %(asctime)s - %(name)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    
    customLoggers[index].addHandler(handler)
    logging.info(f'handler added of {file[9: -4]}')
    
logging.info('all set for custom loggers.')