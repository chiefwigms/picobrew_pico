$(document).ready(function(){
	$('button').click(function(){
        var import_data = {}

        var rfid_element = document.getElementById('import_recipe').elements['rfid']
        if (rfid_element != undefined)
            import_data.rfid = rfid_element.value;
        
        var uid_element = document.getElementById('import_recipe').elements['uid']
        if (uid_element != undefined)
            import_data.uid = uid_element.value;
        
        var guid_element = document.getElementById('import_recipe').elements['guid']
        if (guid_element != undefined)
            import_data.guid = guid_element.value;

		$.ajax({
			url: window.location.pathname,
			type: 'POST',
            data: JSON.stringify(import_data),
            dataType: "json",
            processData: false,
            contentType: "application/json; charset=UTF-8",
            success: function(data) {
                showAlert("Success!", "success");
                setTimeout(function () { 
                    var machine = window.location.toString().split('_')[1];
                    window.location.href = machine + '_recipes';
                }, 2000);
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
