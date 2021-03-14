function showAlert(msg, type) {
    $('#alert').html("<div class='w-75 alert text-center alert-" + type + "'>" + msg + "</div>");
    $('#alert').show();
}

function start_fermentation(uid) {
    var session = {}
    session.active = true
    $.ajax({
        url: '/device/' + uid + '/sessions/ferm',
        type: 'PUT',
        data: JSON.stringify(session),
        dataType: "json",
        processData: false,
        contentType: "application/json; charset=UTF-8",
        success: function (data) {
            showAlert("Success!", "success");

            $("#bstart_" + uid).toggleClass('d-block d-none')
            $("#bstop_" + uid).toggleClass('d-block d-none')
            // setTimeout(function () { window.location.href = "/"; }, 2000);
        },
        error: function (request, status, error) {
            showAlert("Error: " + request.responseText, "danger");
            //setTimeout(function () { window.location.href = "pico_recipes";}, 2000);
        },
    });

};

 function stop_fermentation(uid) {
    var session = {}
    session.active = false
    $.ajax({
        url: '/device/' + uid + '/sessions/ferm',
        type: 'PUT',
        data: JSON.stringify(session),
        dataType: "json",
        processData: false,
        contentType: "application/json; charset=UTF-8",
        success: function (data) {
            showAlert("Success!", "success");
            $("#bstart_" + uid).toggleClass('d-block d-none')
            $("#bstop_" + uid).toggleClass('d-block d-none')

            // until socketio publishes a new "empty" state just force a refresh (which will clear the graphs)
            setTimeout(function () { window.location.href = "/"; }, 2000);
        },
        error: function (request, status, error) {
            showAlert("Error: " + request.responseText, "danger");
            //setTimeout(function () { window.location.href = "pico_recipes";}, 2000);
        },
    });
}

function start_iSpindel_fermentation(uid) {
    var session = {}
    session.active = true
    $.ajax({
        url: '/device/' + uid + '/sessions/iSpindel',
        type: 'PUT',
        data: JSON.stringify(session),
        dataType: "json",
        processData: false,
        contentType: "application/json; charset=UTF-8",
        success: function (data) {
            showAlert("Success!", "success");

            $("#bstart_" + uid).toggleClass('d-block d-none')
            $("#bstop_" + uid).toggleClass('d-block d-none')
            // setTimeout(function () { window.location.href = "/"; }, 2000);
        },
        error: function (request, status, error) {
            showAlert("Error: " + request.responseText, "danger");
            //setTimeout(function () { window.location.href = "pico_recipes";}, 2000);
        },
    });

};

 function stop_iSpindel_fermentation(uid) {
    var session = {}
    session.active = false
    $.ajax({
        url: '/device/' + uid + '/sessions/iSpindel',
        type: 'PUT',
        data: JSON.stringify(session),
        dataType: "json",
        processData: false,
        contentType: "application/json; charset=UTF-8",
        success: function (data) {
            showAlert("Success!", "success");
            $("#bstart_" + uid).toggleClass('d-block d-none')
            $("#bstop_" + uid).toggleClass('d-block d-none')

            // until socketio publishes a new "empty" state just force a refresh (which will clear the graphs)
            setTimeout(function () { window.location.href = "/"; }, 2000);
        },
        error: function (request, status, error) {
            showAlert("Error: " + request.responseText, "danger");
            //setTimeout(function () { window.location.href = "pico_recipes";}, 2000);
        },
    });
}

function start_tilt_fermentation(uid) {
    var session = {}
    session.active = true
    $.ajax({
        url: '/device/' + uid + '/sessions/tilt',
        type: 'PUT',
        data: JSON.stringify(session),
        dataType: "json",
        processData: false,
        contentType: "application/json; charset=UTF-8",
        success: function (data) {
            showAlert("Success!", "success");

            $("#bstart_" + uid).toggleClass('d-block d-none')
            $("#bstop_" + uid).toggleClass('d-block d-none')
            // setTimeout(function () { window.location.href = "/"; }, 2000);
        },
        error: function (request, status, error) {
            showAlert("Error: " + request.responseText, "danger");
            //setTimeout(function () { window.location.href = "pico_recipes";}, 2000);
        },
    });

}

function stop_tilt_fermentation(uid) {
    var session = {}
    session.active = false
    $.ajax({
        url: '/device/' + uid + '/sessions/tilt',
        type: 'PUT',
        data: JSON.stringify(session),
        dataType: "json",
        processData: false,
        contentType: "application/json; charset=UTF-8",
        success: function (data) {
            showAlert("Success!", "success");
            $("#bstart_" + uid).toggleClass('d-block d-none')
            $("#bstop_" + uid).toggleClass('d-block d-none')

            // until socketio publishes a new "empty" state just force a refresh (which will clear the graphs)
            setTimeout(function () { window.location.href = "/"; }, 2000);
        },
        error: function (request, status, error) {
            showAlert("Error: " + request.responseText, "danger");
            //setTimeout(function () { window.location.href = "pico_recipes";}, 2000);
        },
    });
}