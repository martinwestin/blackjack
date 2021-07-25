String.prototype.format = function() {
    a = this;
    for (k in arguments) {
        a = a.replace("{" + k + "}", arguments[k]);
    }
    return a;
}

class PopupWindow {
    constructor(content=null, color=null) {
        this.content = content;
        this.color = color;
        this.div = document.getElementById("popup-window");
    }

    config(content, color) {
        this.content = content;
        this.color = color;
    }

    show() {
        this.div.style.backgroundColor = this.color;
        this.div.innerHTML = "<h2>{0}</h2>".format(this.content);
        this.div.innerHTML += "<button id='close-popup' onclick='popup.hide()'>Ok</button>";
        this.div.style.visibility = "visible";
    }

    hide() {
        this.div.style.visibility = "hidden";
    }
}

let popup = new PopupWindow();

var socket;

const url = window.location.href;
const game_id = url.split("/").pop().split("?")[0];
$(document).ready(function() {
    socket = io.connect("/");

    const chat = $(".chat-container-inner")
    chat.scrollTop(chat.prop("scrollHeight"));

    $("#message-input").bind('keyup', function(event) {
        if (event.keyCode === 13) {
            socket.emit("new_chat", {
                id: game_id,
                content: $("#message-input").val()
            });

            $("#message-input").val("");
        }
    });

    socket.on("new_chat_response", function(msg) {
        const user = msg["sender"];
        const sent = msg["sent"];
        const content = msg["content"];

        let newInnerHTML = chat.html();
        newInnerHTML += "<div class='chat'><div class='chat-top-container'><p>{0} | {1}</div><div class='chat-content-container'>{2}</div></div>".format(user, sent, content);
        chat.html(newInnerHTML);
        chat.scrollTop(chat.prop("scrollHeight"));
    });

    socket.on("connect", function() {
        socket.emit("connected_to_game", {
            id: game_id
        });
    });

    socket.on("reload", function() {
        location.reload();
    });

    socket.on("no_card_picked", function() {
        alert("You have to take at least one card.");
    });

    socket.on("new_user_connected", function(msg) {
        const users_div = $("#connected-users");
        const users = msg["connected_users"];
        const logged = msg["logged"];
        const creator = msg["creator"];

        let newInnerHTML = "<div class='title-container'><div class='title-container-inner'><h1>Connected users</h1></div>";
        newInnerHTML += "<div class='game-id-container'><strong>Game key: {0}</strong></div></div>".format(msg["game_id"]);
        for (const element in users) {
            const option = users[element];
            if (option[1] == logged) {
                newInnerHTML += "<div class='user-div' id={0}><div class='name-container'><p>{1}</p></div>".format(option[2], option[1]);
                if (option[1] != creator) {
                    newInnerHTML += "<div class='leave-container'><button class='leave-button' onclick='leave_game(\"{0}\")'>Leave</button></div>".format(option[1]);
                }
                newInnerHTML += "</div>";
            } else {
                newInnerHTML += "<div class='user-div' id={0}><div class='name-container'><p>{1}</p></div></div>".format(option[2], option[1]);
            }
        }
        users_div.html(newInnerHTML);
    });

    socket.on("ready_game", function(msg) {
        const users_div = $("#connected-users");
        const users = msg["connected_users"];
        const logged = msg["logged"];
        const creator = msg["creator"];

        let newInnerHTML = "<div class='title-container'><div class='title-container-inner'><h1>Connected users</h1></div>";
        newInnerHTML += "<div class='game-id-container'><strong>Game key: {0}</strong></div></div>".format(msg["game_id"]);
        for (const element in users) {
            const option = users[element];
            newInnerHTML += "<div class='user-div' id={0}><div class='name-container'><p>{1}</p></div>".format(option[2], option[1]);

            if (option[1] == logged && option[1] != creator) {
                newInnerHTML += "<div class='leave-container'><button class='leave-button' onclick='leave_game(\"{0}\")'>Leave</button></div>".format(option[1]);
            }
            newInnerHTML += "</div>";

        }
        users_div.html(newInnerHTML);
        const game_board = document.getElementById("main-game-board");
        game_board.style.visibility = "visible";
        const lost = msg["lost"];
        for (const element in lost) {
            const div = document.getElementById("{0}-section".format(lost[element]));
            div.style.backgroundColor = "grey";
        }

    });

    socket.on("user_left", function(msg) {
        const users_div = $("#connected-users");
        let newInnerHTML = users_div.html();
        location.href = "/";

    });

    socket.on("started_game", function() {
        const game_board = document.getElementById("main-game-board");
        game_board.style.visibility = "visible";
        $(".start-game-container").remove();
    });

    socket.on("user_turn", function(msg) {
        const newCardDiv = $("#new-card-container-inner");
        let newInnerHTML = "<div class='new-card'>";
        newInnerHTML += "<div class='add-container'><button onclick='add_card()'>Contiune</button></div>".format(msg["card"]);
        newInnerHTML += "<div class='decline-container'><button onclick='decline_card()'>Stay</button></div>";
        newInnerHTML += "</div>";
        newCardDiv.html(newInnerHTML);
    });

    socket.on("lost", function(msg) {
        popup.config("You lost because of a to high score.", "red")
        popup.show();
        $("#new-card-container-inner").html("");
        const cardsDiv = document.getElementById("{0}-section".format(msg["user"]));
        cardsDiv.style.backgroundColor = "grey";
    });

    socket.on("other_user_lost", function(msg) {
        popup.config("{0} lost the game!".format(msg["user"]), "red");
        popup.show();
        const cardsDiv = document.getElementById("{0}-cards".format(msg["user"]));
        cardsDiv.style.backgroundColor = "grey";
    });

    socket.on("end_turn", function(msg) {
        const newCardDiv = $("#new-card-container-inner");
        newCardDiv.html("");
    });

    socket.on("new_card", function(msg) {
        const card = msg["card"];
        const cardDiv = $(".user-cards");
        const topCardDiv = $("#{0}-cards".format(msg["user"]));
        let newInnerHTML = cardDiv.html();
        newInnerHTML += "<img src='/static/images/cards/{0}.jpg' alt='card' height='70'>".format(card);
        cardDiv.html(newInnerHTML);

        let newTopDivInnerHTML = topCardDiv.html();
        newTopDivInnerHTML += "<div class='card-container'><img src='/static/images/cards/{0}.jpg' alt='card' height='50'></div>".format(card);
        topCardDiv.html(newTopDivInnerHTML);
    });

    socket.on("new_other_card", function(msg) {
        const user = msg["user"];
        const cardDiv = $("#{0}-cards".format(user));
        let newInnerHTML = cardDiv.html();
        newInnerHTML += "<div class='card-container'><img src='/static/images/card.png' alt='deck' height='50'></div>";
    });

    socket.on("not_enough_users", function() {
        popup.config("There are not enough waiting users in order to play (there needs to be at least 2).", "red");
        popup.show();
    });

    socket.on("end_game", function(msg) {
        const winner = msg["winner"];
        if (winner != "Tie") {
            popup.config("{0} won the game!".format(winner), "lightgreen");
        } else {
            popup.config("Tie!", "lightgreen");
        }

        popup.show();
    });

    socket.on("add_replay_button", function() {
        let newInnerHTML = $(".left-container").html();
        newInnerHTML += "<div class='replay-game-container'><div class='button-container'>";
        newInnerHTML += "<button id='replay-button' onclick='replay()'>Replay</button></div></div>";
        $(".left-container").html(newInnerHTML);
    });

    socket.on("next_turn", function(msg) {
        popup.config("{0}'s turn!".format(msg["user"]), "lightgreen");
        popup.show();
    });

    $("#start-button").click(function() {
        socket.emit("start_game", {
            id: game_id
        });
    });

});

function leave_game(user) {
    socket.emit("leave_game", {
        user: user,
        id: game_id
    });
}

function add_card() {

    socket.emit("continue", {
        id: game_id
    });
}

function decline_card() {
    socket.emit("decline", {
        id: game_id
    });
}

function replay() {
    socket.emit("replay_game", {
        id: game_id
    });
}
