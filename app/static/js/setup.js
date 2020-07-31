$(document).ready(function(){
	$('#b_save_wireless_setup').click(function(){
        var wireless = {}
        wireless.bssid = document.getElementById('f_wireless_setup').elements['wifi_bssid'].value;
        wireless.ssid = document.getElementById('f_wireless_setup').elements['wifi_ssid'].value;
        wireless.password = document.getElementById('f_wireless_setup').elements['wifi_credentials'].value;
        
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
    function showAlert(msg, type){
        $('#alert').html("<div class='w-75 alert text-center alert-" + type + "'>" + msg + "</div>");
        $('#alert').show();
    }
});
function showPassword() {
    var x = document.getElementById("wifi_credentials");
    if (x.type === "password") {
        x.type = "text";
    } else {
        x.type = "password";
    }
}