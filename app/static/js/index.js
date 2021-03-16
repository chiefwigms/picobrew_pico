function showAlert(msg, type) {
    $('#alert').html("<div class='w-75 alert text-center alert-" + type + "'>" + msg + "</div>");
    $('#alert').show();
}

function start_monitoring(session_type, uid) {
    var session = {}
    session.active = true
    $.ajax({
        url: `/device/${uid}/sessions/${session_type}`,
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
            window.scrollTo({top: 0, behavior: 'smooth'});
            //setTimeout(function () { window.location.href = "pico_recipes";}, 2000);
        },
    });
}

function stop_monitoring(session_type, uid) {
    var session = {}
    session.active = false
    $.ajax({
        url: `/device/${uid}/sessions/${session_type}`,
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
            window.scrollTo({top: 0, behavior: 'smooth'});
            //setTimeout(function () { window.location.href = "pico_recipes";}, 2000);
        },
    });
}