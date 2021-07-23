from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_socketio import SocketIO, emit
from game import Game, DBModels, Deck


app = Flask(__name__)
app.config["SECRET_KEY"] = b'Y\xbe\xbf7\xd7\x16\xcf\xee2z$\xae1\xca\x84\x890\x84=~@\xae\xabP'

socketio = SocketIO(app)

models_instance = DBModels()
deck = Deck()

@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        username = request.form["join-username-text"]
        game_id = request.form["join-id-text"]
        if models_instance.game_exists(game_id):
            session["user"] = username
            return redirect(url_for("game", game_id=game_id))

        flash("Game not found.")
        return render_template("index.html")

    return render_template("index.html")

@app.route("/game/<game_id>")
def game(game_id):
    if "user" in session:
        if models_instance.game_exists(game_id):
            game = Game(game_id)
            creator = game.game_creator()
            all_user_cards = {}
            try:
                cards = game.get_user_cards(session["user"])
            except:
                cards = []
            
            connected_users = game.usernames()
            for user in connected_users:
                try:
                    all_user_cards[user] = game.get_user_cards(user)
                except:
                    all_user_cards[user] = []
            
            try:
                has_ended = game.everybody_has_played()
            except:
                has_ended = False

            return render_template("game.html", logged_user=session["user"], is_creator=creator==session["user"], has_started=game.has_been_started(),
            cards=cards, connected=connected_users, all_cards=all_user_cards, has_ended=has_ended)

        
        return "Game could not be found"

    flash("You have to enter a username in order to join a game.")
    return redirect(url_for("index"))


@socketio.on("create_new_game")
def create_game(msg):
    user = msg["user"]
    if user != "" and not user.isspace():
        models_instance.create_game(user)
        emit("created_game_response", {"id": models_instance.latest_game()}, room=request.sid)


@socketio.on("connected_to_game")
def connected(msg):
    if "user" in session:
        game_id = msg["id"]
        game = Game(game_id)
        if not game.has_been_started():
            game.connect(session["user"], request.sid)
            data = {"connected_users": game.connected_users(), "logged": session["user"], 
            "creator": game.game_creator(), "game_id": game_id}
            for sid in game.connected_sids():
                emit("new_user_connected", data, room=sid)
        
        elif game.has_been_started() and session["user"] in game.usernames():
            # user has reloaded page with started game
            game.connect(session["user"], request.sid)
            data = {"connected_users": game.connected_users(), "lost": game.fetch_lost(), "logged": session["user"], "creator": game.game_creator(),
            "game_id": game_id}
            for sid in game.connected_sids():
                emit("ready_game", data, room=sid)

            if not game.everybody_has_played():
                emit("user_turn", {"card": deck.held_card(session["user"])}, room=game.fetch_user_sid(game.current_turn()))


@socketio.on("leave_game")
def leave(msg):
    if "user" in session:
        user = msg["user"]
        game_id = msg["id"]
        game = Game(game_id)
        connected_users = game.connected_users()
        if user in list(map(lambda x: x[1], connected_users)):
            current_sid = game.fetch_user_sid(user)
            for sid in game.connected_sids():
                emit("user_left", {"to_remove": current_sid}, room=sid)

            game.disconnect(user)

@socketio.on("start_game")
def start_game(msg):
    if "user" in session:
        game_id = msg["id"]
        sid = request.sid
        game = Game(game_id)
        commiter = game.fetch_user_by_sid(sid)
        creator = game.game_creator()
        if commiter == creator and not game.has_been_started():
            if len(game.connected_users()) > 1:
                game.start()
                sids = game.connected_sids()
                for sid in sids:
                    emit("started_game", room=sid)
                
                emit("user_turn", {"card": deck.get_card(game.current_turn())}, room=game.fetch_user_sid(game.current_turn()))
            else:
                emit("not_enough_users", room=request.sid)


@socketio.on("replay_game")
def replay_game(msg):
    if "user" in session:
        game_id = msg["id"]
        sid = request.sid
        game = Game(game_id)
        commiter = game.fetch_user_by_sid(sid)
        creator = game.game_creator()
        if commiter == creator and game.everybody_has_played():
            game.reset()
            for sid in game.connected_sids():
                emit("reload", room=sid)


@socketio.on("continue")
def add_card(msg):
    if "user" in session:
        game_id = msg["id"]
        game = Game(game_id)
        game.add_card(session["user"], deck.held_card(session["user"]))
        emit("new_card", {"card": deck.held_card(session["user"]), "user": session["user"]}, room=game.fetch_user_sid(game.current_turn()))
        for user in list(filter(lambda x: x != game.current_turn(), game.usernames())):
            emit("new_other_card", {"user": user}, room=game.fetch_user_sid(user))

        deck.remove_card_from_deck(deck.held_card(session["user"]))
        if not game.has_lost(session["user"]):
            emit("user_turn", {"card": deck.get_card(game.current_turn())}, room=game.fetch_user_sid(game.current_turn()))
        else:
            game.end_turn()
            emit("lost", {"user": session["user"]}, room=game.fetch_user_sid(game.current_turn()))
            for user in list(filter(lambda x: x != game.current_turn(), game.usernames())):
                emit("other_user_lost", {"user": session["user"]}, room=game.fetch_user_sid(user))

            if not game.everybody_has_played():
                game.next_turn()
            else:
                for sid in game.connected_sids():
                    emit("end_game", {"winner": game.winner()}, room=sid)
                emit("add_replay_button", room=game.fetch_user_sid(game.game_creator()))
            
            game.user_lost(session["user"])

@socketio.on("decline")
def decline_new_card(msg):
    if "user" in session:
        game_id = msg["id"]
        game = Game(game_id)
        try:
            game.get_user_cards(session["user"])
            game.end_turn()
            emit("end_turn", room=game.fetch_user_sid(game.current_turn()))
            if not game.everybody_has_played():
                game.next_turn()
                for sid in game.connected_sids():
                    emit("next_turn", {"user": game.current_turn()}, room=sid)

                emit("user_turn", {"card": deck.get_card(game.current_turn())}, room=game.fetch_user_sid(game.current_turn()))
            else:
                for sid in game.connected_sids():
                    emit("end_game", {"winner": game.winner()}, room=sid)
                emit("add_replay_button", room=game.fetch_user_sid(game.game_creator()))
        except:
            emit("no_card_picked", room=game.fetch_user_sid(game.current_turn()))


if __name__ == "__main__":
    socketio.run(app, debug=True)
