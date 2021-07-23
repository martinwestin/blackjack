# blackjack
An online blackjack web application using Flask in Python.
#
This is an online game where multiple users can connect to play a game of blackjack.
It is built using Flask in python together with SocketIO (flask-socketio) in order
to communicate from the server to connected clients. Every new created game gets
asserted a unique game id (using python's built in UUID library), and users can access
games using this key/id. Every game key also gets stored in a Sqlite3 database file.
