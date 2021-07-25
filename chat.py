import sqlite3
from datetime import date


class DBConnection:
    def __init__(self):
        self.con = sqlite3.connect("chat.db", check_same_thread=False)
        self.cur = self.con.cursor()

        self.cur.execute("""CREATE TABLE IF NOT EXISTS messages (
            content text not null,
            sender text not null,
            sent_date text not null,
            game_id text not null
        )""")


class Chatroom(DBConnection):
    def __init__(self, game_id):
        super().__init__()
        self.id = game_id
    
    def fetch_messages(self):
        self.cur.execute("SELECT * FROM messages WHERE game_id = (?)", (self.id,))
        return self.cur.fetchall()


class Message(DBConnection):
    def __init__(self, content, sender, game_id):
        super().__init__()
        self.content = content
        self.id = game_id
        self.sender = sender
    
    def add(self):
        self.cur.execute("INSERT INTO messages VALUES (?, ?, ?, ?)", (self.content, self.sender, date.today(), self.id))
        self.con.commit()
