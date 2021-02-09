function showAlert(msg, type) {
    $('#alert').html("<div class='w-100 alert text-center alert-" + type + "'>" + msg + "</div>");
    $('#alert').show();
}

function delete_device(machine_type, uid){
    if (confirm("Are you sure?")){
        var fd = new FormData();    
        fd.append( 'machine_type', machine_type );

		$.ajax({
			url: '/devices/' + uid,
			type: 'DELETE',
            data: fd,
            processData: false,
            contentType: false,
            success: function(data) {
                showAlert("Success!", "success");
                setTimeout(function () { window.location.href = '/devices';}, 2000);
            },
            error: function(request, status, error) {
                showAlert("Error: " + request.responseText, "danger");
                //setTimeout(function () { window.location.href = "zseries_recipes";}, 2000);
            },
		});
    }
};
