$(document).ready(function(){
	$('button').click(function(){
        var machine = window.location.toString().split('_')[1];
        var recipe = {}
        if (machine == 'pico')
            recipe.rfid = document.getElementById('import_recipe').elements['rfid'].value;
        else
            recipe.guid = document.getElementById('import_recipe').elements['guid'].value;
		$.ajax({
			url: 'import_' + machine + '_recipe',
			type: 'POST',
            data: JSON.stringify(recipe),
            dataType: "json",
            processData: false,
            contentType: "application/json; charset=UTF-8",
            success: function(data) {
                showAlert("Success!", "success");
                setTimeout(function () { window.location.href = machine + '_recipes';}, 2000);
            },
            error: function(request, status, error) {
                showAlert("Error: " + request.responseText, "danger");
                //setTimeout(function () { window.location.href = machine + '_recipes';}, 2000);
            },
		});
    });
    function showAlert(msg, type){
        $('#alert').html("<div class='w-50 alert text-center alert-" + type + "'>" + msg + "</div>");
        $('#alert').show();
    }
});
