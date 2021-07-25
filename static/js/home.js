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
