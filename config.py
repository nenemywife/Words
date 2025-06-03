class Config(object):
    DEBUG = True
    
    SECRET_KEY = "1a2b3c4d"
    
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
    SQLALCHEMY_BINDS = {'db_word': 'sqlite:///db_word.db'}
    
    DB_NAME = "production-db"
    DB_USERNAME = "root"
    DB_PASSWORD = "example"
    
    UPLOAD = "/home/username/myproject/app/static/images/uploads"
    
    SESSION_COOKIE_SECURE = True