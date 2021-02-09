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

function download_server_session(filename, type){
    window.location = '/sessions/' + type + '/' + escape(filename);
};

function upload_recipe_file(machineType, file, redirectUrl) {
    // error due to unsupported file type
    if(!file.name.endsWith(".json")) {
        showAlert(`Error: ${file.name} is an unsupported filetype.`, "danger");
        return;
    }

    let formData = new FormData();
    formData.append("recipe", file);

    fetch(`/recipes/${machineType}`, {
        method: 'POST',
        body: formData
    })
    .then(result => {
        if (!result.ok) {
            // make the promise be rejected if we didn't get a 2xx response
            throw new Error(`Server Failed with ${result.status} response code`);
        }
        return result.text()
    })
    .then(result => {
        console.log('Success: ', result);
        showAlert("Success!", "success");
        setTimeout(function () { window.location.href = redirectUrl; }, 2000);
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert(`Error: upload of recipe failed<br/>${error}`, "danger");
    });
}