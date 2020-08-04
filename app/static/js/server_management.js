function delete_server_file(filename, type, redirectHref){
    if (confirm("Are you sure?")){
		$.ajax({
			url: 'delete_file',
			type: 'POST',
            data: JSON.stringify({
                filename: filename,
                type: type
            }),
            dataType: "json",
            processData: false,
            contentType: "application/json; charset=UTF-8",
            success: function(data) {
                //showAlert("Success!", "success");
                setTimeout(function () { window.location.href = redirectHref;}, 2000);
            },
            error: function(request, status, error) {
                //showAlert("Error: " + request.responseText, "danger");
                //setTimeout(function () { window.location.href = "zseries_recipes";}, 2000);
            },
		});
    }
};