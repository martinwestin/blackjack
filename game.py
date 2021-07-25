import sqlite3
import uuid
import random

class DBModels:
    def __init__(self):
        self.con = sqlite3.connect("games.db", check_same_thread=False)
        self.cur = self.con.cursor()

        self.cur.execute("""CREATE TABLE IF NOT EXISTS games (
            creator text not null,
            game_id text not null
        )""")
    
    def create_game(self, user):
        game_id = uuid.uuid1().hex
        self.cur.execute("INSERT INTO games VALUES (?, ?)", (user, game_id))
        self.con.commit()
    
    def game_exists(self, game_id):
        self.cur.execute("SELECT * FROM games WHERE game_id = (?)", (game_id,))
        return len(self.cur.fetchall()) == 1
    
    def latest_game(self):
        self.cur.execute("SELECT game_id FROM games")
        return self.cur.fetchall()[-1][0]


class Game(DBModels):
    active_games = {}
    started_games = []
    current_turns = {}
    orders = {}
    holdings = {}
    lost = {}
    # played is a dictionary containing lists of every player that has took a turn in each game.
    played = {}

    def __init__(self, game_id):
        super().__init__()
        if self.game_exists(game_id):
            self.game_id = game_id
            
        else:
            raise Exception("The requested game could not be found")
    
    def connect(self, user, session_id):
        self.active_games[user] = [self.game_id, session_id]
    
    def disconnect(self, user):
        self.active_games.pop(user)
    
    def connected_users(self):
        return list(filter(lambda x: x[0] == self.game_id, 
        list(map(lambda x: [self.active_games[x][0], x, self.active_games[x][1]], self.active_games))))

    def usernames(self):
        return list(map(lambda x: x[1], self.connected_users()))

    def connected_sids(self):
        return list(map(lambda x: x[2], self.connected_users()))
    
    def fetch_user_by_sid(self, sid):
        return list(filter(lambda x: x[2] == sid, self.connected_users()))[0][1]
    
    def fetch_user_sid(self, user):
        return list(filter(lambda x: x[1] == user, self.connected_users()))[0][2]
    
    def game_creator(self):
        self.cur.execute("SELECT creator FROM games WHERE game_id = (?)", (self.game_id,))
        return self.cur.fetchone()[0]
    
    def start(self):
        self.orders[self.game_id] = self.usernames()
        self.current_turns[self.game_id] = self.orders[self.game_id][0]
        self.started_games.append(self.game_id)
        self.holdings[self.game_id] = {}
        self.lost[self.game_id] = []
        self.played[self.game_id] = []
    
    def reset(self):
        self.orders.pop(self.game_id)
        self.current_turns.pop(self.game_id)
        self.started_games.remove(self.game_id)
        self.holdings.pop(self.game_id)
        self.lost.pop(self.game_id)
        self.played.pop(self.game_id)
    
    def user_lost(self, user):
        self.orders[self.game_id].remove(user)
        self.lost[self.game_id].append(user)
    
    def end_turn(self):
        current_turn = self.current_turns[self.game_id]
        self.played[self.game_id].append(current_turn)

    def next_turn(self):
        current_turn = self.current_turns[self.game_id]
        self.current_turns[self.game_id] = self.orders[self.game_id][self.orders[self.game_id].index(current_turn) + 1]
    
    def everybody_has_played(self):
        return len(self.played[self.game_id]) == len(self.connected_users())
    
    def current_turn(self):
        return self.current_turns[self.game_id]
    
    def has_been_started(self):
        return self.game_id in self.started_games
    
    def add_card(self, user, card):
        try:
            self.holdings[self.game_id][user].append(card)
        except:
            self.holdings[self.game_id][user] = [card]

    def get_user_cards(self, user):
        return list(map(lambda x: self.holdings[self.game_id][x], list(filter(lambda x: x == user, self.holdings[self.game_id]))))[0]

    def hand_sum(self, user):
        return sum(list(map(lambda x: Deck().cards[x], self.get_user_cards(user))))
    
    def has_lost(self, user):
        return self.hand_sum(user) > 21
    
    def everybody_have_played(self):
        return len(self.played[self.game_id]) == len(self.connected_users())
    
    def winner(self):
        if self.everybody_has_played():
            scores = list(map(lambda x: (x, self.hand_sum(x)), self.usernames()))
            try:
                winner_list = sorted(list(filter(lambda x: x[1] < 22, scores)), key=lambda x: x[1])
                return winner_list[-1][0]

            except:
                return "Tie"

        raise Exception("Every player must have played before anybody can win.")
    
    def fetch_lost(self):
        return self.lost[self.game_id]


class Deck:
    current_cards = {}

    def __init__(self):
        self.cards = {
            "2C": 2, "2D": 2, "2H": 2, "2S": 2,
            "3C": 3, "3D": 3, "3H": 3, "3S": 3,
            "4C": 4, "4D": 4, "4H": 4, "4S": 4,
            "5C": 5, "5D": 5, "5H": 5, "5S": 5,
            "6C": 6, "6D": 6, "6H": 6, "6S": 6,
            "7C": 7, "7D": 7, "7H": 7, "7S": 7,
            "8C": 8, "8D": 8, "8H": 8, "8S": 8,
            "9C": 9, "9D": 9, "9H": 9, "9S": 9,
            "10C": 10, "10D": 10, "10H": 10, "10S": 10,
            "JC": 10, "JD": 10, "JH": 10, "JS": 10,
            "QC": 10, "QD": 10, "QH": 10, "QS": 10,
            "KC": 10, "KD": 10, "KH": 10, "KS": 10,
            "AC": 11, "AD": 11, "AH": 11, "AS": 11
        }
    
    def get_card(self, user):
        card = random.choice(list(self.cards.keys()))
        self.current_cards[user] = card
        return card
    
    def remove_card_from_deck(self, card):
        self.cards.pop(card)
    
    @classmethod
    def held_card(cls, user):
        try:
            return cls.current_cards[user]
        except:
            Deck().get_card(user)
            return cls.current_cards[user]
