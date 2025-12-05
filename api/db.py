import pymysql

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="1619",
        database="magic",
        cursorclass=pymysql.cursors.DictCursor
    )
