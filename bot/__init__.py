from concurrent.futures import ThreadPoolExecutor
from .createBotObject import bot
from model import model, AI_preText
from db import connection_pool
from .chat import chat
from .callbacks import handle_all_callbacks
from .help import send_welcome
from .send import send_movie_series
from log import logging


# object for threads pooling
threads = ThreadPoolExecutor(max_workers= 8)
dbLog = logging.getLogger('db')

from .upload import thread_handle_files, handle_files
