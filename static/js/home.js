String.prototype.format = function() {
    a = this;
    for (k in arguments) {
        a = a.replace("{" + k + "}", arguments[k]);
    }
    return a;
}

if ( window.history.replaceState ) {
    window.history.replaceState( null, null, window.location.href );
}

let socket;
$(document).ready(function() {
    socket = io.connect("/");
    
    $("#create-button").click(function() {
        socket.emit("create_new_game", {
            "user": $("#username-text").val()
        });
    });

    socket.on("created_game_response", function(msg) {
        window.location.href = "/game/{0}".format(msg["id"]);
    });
})
