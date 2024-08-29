import sqlite3

def connect():
    conn = sqlite3.connect("../detectApp.db")
    cur = conn.cursor()
    # check if connected successfully
    if conn:
        print("Connected to the database")
        # list all tables
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        print(cur.fetchall())
        # get the table named (camras_camra)
        cur.execute("SELECT * FROM main.camaras_camara")
        print(cur.fetchall())
        # close connection
        conn.close()
    else:
        print("Failed to connect to the database")


connect()

