import sqlite3

def get_connection():
    conn = sqlite3.connect("nfl_data.db")
    return conn
