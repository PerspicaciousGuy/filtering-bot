import os


class temp(object):
    BANNED_USERS = []
    ME = None
    BOT = None
    CURRENT=int(os.environ.get("SKIP", 2))
    CANCEL = False
    U_NAME = None
    B_NAME = None
    GETALL = {}
    SHORT = {}
    LIB_COUNT = "0"
