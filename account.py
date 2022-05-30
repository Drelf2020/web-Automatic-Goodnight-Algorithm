from database import userDB
from pywebio.session import eval_js, run_js
from tornado.web import create_signed_value, decode_signed_value
from logging import DEBUG, Formatter, Logger
from WebHandler import WebHandler


logger = Logger('USER', DEBUG)
handler = WebHandler()
handler.setFormatter(Formatter("`%(asctime)s` `%(levelname)s` `User`: %(message)s", '%Y-%m-%d %H:%M:%S'))
logger.addHandler(handler)


SECRET = "encryption salt value"

async def get():
    token = await eval_js("localStorage.getItem(key)", key='token')  # get token from user's web browser
    username = decode_signed_value(SECRET, 'token', token, max_age_days=7)  # try to decrypt the username from the token
    logger.debug(f'eval_js: {username}')
    if username:
        username = username.decode('utf-8')
        pwd = userDB.query('PASSWORD', USERNAME=username)
        if not pwd:
            return
    return username

def save(username):
    logger.debug(f'save: {username}')
    signed = create_signed_value(SECRET, 'token', username).decode("utf-8")  # encrypt username to token
    run_js("localStorage.setItem(key, value)", key='token', value=signed)  # set token to user's web browser

def clear():
    save('')