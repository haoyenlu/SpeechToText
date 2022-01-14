import sqlite3

connection = sqlite3.connect('database.db')

with open("schema.sql") as f:
    connection.executescript(f.read())

cur = connection.cursor()

cur.execute("INSERT INTO puzzle (content,question,useable) VALUES(?,?,?)",
            ('Example Puzzle','No Question','FALSE'))

connection.commit()

connection.close()