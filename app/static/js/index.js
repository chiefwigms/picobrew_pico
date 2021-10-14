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

function add_integration(id) {
    var parentId = `f_${id}`;
    var new_chq_no = parseInt($(`#${parentId}> .total_integrations`).val()) + 1;
    var new_input = `
    <div class="form-row mb-2 integration" id="integration_${id}_${new_chq_no}">
        <div class="col-auto col-sm-8">
            <label class="sr-only" for="inlineFormInput">Integration URL</label>
            <input type="text" class="form-control form-control-sm webhook_url" id="url_${id}_${new_chq_no}" placeholder="crafter.pilotbatchbrewing.com/logsessions/<uuid>">
        </div>
        <div class="col-auto">
            <div class="form-check">
            <input class="form-check-input" type="checkbox" id="enabled_${id}_${new_chq_no}">
            <label class="form-check-label" for="autoSizingCheck">
                Enabled
            </label>
            </div>
        </div>
        <div class="col-auto">
            <!-- secondary=disabled, info=enabled, success=success, danger=error -->
            <span class="badge badge-secondary" id="status_${id}_${new_chq_no}">disabled</span>
        </div>
        <div class="col-auto"></div>
        <div class="col-auto">
            <button class="btn btn-sm btn-danger" type="button" id="bdelete_${id}_${new_chq_no}"
                onclick="event.stopPropagation();event.preventDefault();delete_integration('${parentId}', 'integration_${id}_${new_chq_no}');">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    </div>
    `;
    
    // var new_input = "<input type='text' id='new_" + new_chq_no + "'>";

    $(`#${parentId}> .new_integrations`).append(new_input);
    $(`#${parentId}> .total_integrations`).val(new_chq_no);

    display_unsaved_state(id);
}

function delete_integration(parentId, id) {
    var last_chq_no = $(`#${parentId}> .total_integrations`).val();

    $(`#${id}`).remove();
    $(`#${parentId}> .total_integrations`).val(last_chq_no - 1);

    display_unsaved_state(id);
}

function display_unsaved_state(chart_id) {
    $(`#bsave_${chart_id}`).show();
}

$(document).ready(function () {
    $('.save_integrations').click(function (event) {
        var chart_id = event.currentTarget.id.replace("bsave_", "");
        
        var integrations = {}
        integrations.chart_id = chart_id;
        integrations.device_id = document.getElementById(`${chart_id}_device_uid`).value;
        integrations.session_type = document.getElementById(`${chart_id}_session_type`).value;
        integrations.total_integrations = document.getElementById(`${chart_id}_total_integrations`).value;
        integrations.webhooks = []

        var $webhook_rows = $("#f_" + chart_id).find('.integration')
        for (var i=0; i<$webhook_rows.length; i++) {
            const $row = $webhook_rows[i];
            const change_num = $row.id.substring($row.id.lastIndexOf("_")+1) // id="integration_${parentId}_${new_chq_no}"
            
            var webhook = {}
            webhook.url = document.getElementById(`url_${chart_id}_${change_num}`).value;
            webhook.enabled = document.getElementById(`enabled_${chart_id}_${change_num}`).checked;
            integrations.webhooks.push(webhook);
        }

        $.ajax({
            url: `/device/${integrations.device_id}/sessions/${integrations.session_type}/webhooks`,
            type: 'POST',
            data: JSON.stringify(integrations),
            processData: false,
            contentType: "application/json; charset=UTF-8",
            success: function (data) {
                showAlert("Success!", "success")
            },
            error: function (request, status, error) {
                showAlert("Error: " + request.responseText, "danger")
                window.scrollTo({top: 0, behavior: 'smooth'});
            },
        });
    });

    // webhook url or enabled changes toggle unsaved state
    $('.new_integrations').find('input[type=text]').bind('input propertychange', function(event) {
        var chart_id = $(event.currentTarget).data('chartId')
        display_unsaved_state(chart_id)
    });
    $('.new_integrations').find('input[type=checkbox').change(function() {
        var chart_id = $(this).data('chartId')
        display_unsaved_state(chart_id)
    })
});