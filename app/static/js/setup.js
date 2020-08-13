$(document).ready(function(){
    var select = document.querySelector('#wifi_selector'),
    wifi_bssid = document.querySelector('#wifi_bssid'),
    wifi_ssid = document.querySelector('#wifi_ssid'),
    wifi_credentials = document.querySelector('#wifi_credentials');
    select.addEventListener('change',function(){
        var selected = $(this).find('option:selected');
        wifi_bssid.value = selected.data('bssid')
        wifi_ssid.value = selected.data('ssid')
        wifi_credentials.value = ''
    });

    $('#b_save_wireless_setup').click(function(){
        var wireless = {}
        wireless.interface = 'wlan0';
        wireless.bssid = $('#f_wireless_setup').find('#wifi_bssid').val();
        wireless.ssid = $('#f_wireless_setup').find('#wifi_ssid').val();
        wireless.password = $('#f_wireless_setup').find('#wifi_credentials').val();

        $.ajax({
            url: 'setup',
            type: 'POST',
            data: JSON.stringify(wireless),
            dataType: "json",
            processData: false,
            contentType: "application/json; charset=UTF-8",
            success: function(data) {
                showAlert("Success!", "success");
                setTimeout(function () { window.location.href = "/";}, 2000);
            },
            error: function(request, status, error) {
                showAlert("Error: " + request.responseText, "danger");
                //setTimeout(function () { window.location.href = "pico_recipes";}, 2000);
            },
        });
    });

    $('#b_save_ap0_setup').click(function(){
        var ap0 = {}
        ap0.interface = 'ap0';
        ap0.ssid = $('#f_ap0_setup').find('#ap0_ssid').val();
        ap0.password = $('#f_ap0_setup').find('#ap0_credentials').val();

        $.ajax({
            url: 'setup',
            type: 'POST',
            data: JSON.stringify(ap0),
            dataType: "json",
            processData: false,
            contentType: "application/json; charset=UTF-8",
            success: function(data) {
                showAlert("Success!", "success");
                setTimeout(function () { window.location.href = "/";}, 2000);
            },
            error: function(request, status, error) {
                showAlert("Error: " + request.responseText, "danger");
                //setTimeout(function () { window.location.href = "pico_recipes";}, 2000);
            },
        });
    });
    function showAlert(msg, type){
        $('#alert').html("<div class='w-75 alert text-center alert-" + type + "'>" + msg + "</div>");
        $('#alert').show();
    }
});
function showPassword(elementId) {
    var x = document.getElementById(elementId);
    if (x.type === "password") {
        x.type = "text";
    } else {
        x.type = "password";
    }
}