const fixedRows = 3;

var default_data = [
    { name: "Preparing To Brew", location: "Prime", temperature: 0, step_time: 3, drain_time: 0 },
    { name: "Heating", location: "PassThru", temperature: 110, step_time: 0, drain_time: 0 },
    { name: "Dough In", location: "Mash", temperature: 110, step_time: 7, drain_time: 0 },
    { name: "Mash 1", location: "Mash", temperature: 148, step_time: 45, drain_time: 0 },
    { name: "Mash 2", location: "Mash", temperature: 156, step_time: 0, drain_time: 0 },
    { name: "Mash Out", location: "Mash", temperature: 178, step_time: 7, drain_time: 2 },
    { name: "Hops 1", location: "Adjunct1", temperature: 202, step_time: 10, drain_time: 0 },
    { name: "Hops 2", location: "Adjunct2", temperature: 202, step_time: 8, drain_time: 0 },
    { name: "Hops 3", location: "Adjunct3", temperature: 202, step_time: 8, drain_time: 0 },
    { name: "Hops 4", location: "Adjunct4", temperature: 202, step_time: 8, drain_time: 5 },
];

var idMutator = function (value, data, type, params, component) {
	return isDataLoading ? component.getTable().getRows().length : data.id;
}

var recipe_table = {
    movableRows: true,
    layout: "fitDataFill",
    tooltipGenerationMode: "hover",
    columnDefaults:{
        headerSort: false,
        hozAlign: "center",
        resizable: false,
        headerTooltip: recipe_tooltips("Picobrew"),
        tooltip: recipe_tooltips("Picobrew"),
    },
    columns: [
        {
            rowHandle: true, field:"handle", formatter: "handle", frozen: true, width: 50,
        },
        {
			title: "ID", field:"id", visible: false, mutatorData: idMutator,
        },        
        {
            title: "Step #", field:"step_num", formatter: "rownum", width: 60,
        },
        {
            title: "Name", field: "name", width: 200,
            validator: ["required", "string", "minLength:1", "maxLength:19", "regex:^[a-zA-Z0-9_@\\-\\ ]*$"],
            editable: editCheck,
            editor: "input"
        },
        {
            title: "Location", field: "location", width: 120,
            validator: ["required", "string"],
            editable: editCheck,
            editor: "select",
            editorParams: {
                values: [
                    //"Prime",
                    "Mash",
                    "PassThru",
                    "Adjunct1",
                    "Adjunct2",
                    "Adjunct3",
                    "Adjunct4",
                ]
            }
        },
        {
            title: "Temp (°F)", field: "temperature", width: 100,
            validator: ["required", "min:0", "max:208", "numeric"],
            editable: editCheck,
            editorParams: {
                min: 0,     // -18 C
                max: 208,   // 98 C
            },
            editor: temperature_editor,
            formatter: format_temperature
        },
        {
            title: "Time (min)", field: "step_time", width: 100,
            validator: ["required", "min:0", "max:180", "numeric"],
            editable: editCheck,
            editor: "number",
            editorParams: {
                min: 0,
                max: 180,
            }
        },
        {
            title: "Drain (min)", field: "drain_time", width: 100,
            validator: ["required", "min:0", "max:10", "numeric"],
            editable: editCheck,
            editor: "number",
            editorParams: {
                min: 0,
                max: 10,
            }
        },
        {   // hop timings are cumulative (H1+H2+H3+H4 = H1 Hop Contact Time)
            title: "Hop (min)", field: "hop_time", width: 100,
            editable: false,
            mutator: (value, data, type, params, component) => {
                // type is always data (field isn't editable)
                if (data.location && data.location.indexOf("Adjunct") == 0)
                    return data.hop_time == undefined ? data.step_time : data.hop_time;
                else
                    return "";
            },
        },
        {
            title: "Total (min)", field: "total_time", width: 100,
            editable: false,
            mutator: (value, data, type, params, component) => {
                return data.step_time + data.drain_time;
            },
            bottomCalc: "sum"
        },
        {
            formatter: plusIcon, field: "add_step", width: 49,
            cellClick: function (e, cell) {
                if (rowIsEditable(cell,true)) {
                    var newRowData = Object.assign({}, cell.getRow().getData());
                    newRowData.name = "New Step";
                    newRowData.id = getMaxID(cell)+1;
                    cell.getTable().addRow(newRowData, false, cell.getRow());
                }
            }
        },
        {
            formatter: minusIcon, field: "remove_step", width: 49,
            cellClick: function (e, cell) {
                if (rowIsEditable(cell,false)) {
                    cell.getRow().delete();
                }
            }
        },
    ]
};

function getMaxID(component) {
    var maxID=0;
    var rows=component.getTable().getRows();

    rows.forEach(function (row) {
        rowData=row.getData();
		if (rowData.id > maxID)
			maxID=rowData.id;
    });

    return maxID;
}    

function isRowMoved(row){
	var pos = row.getPosition(true);
	var index = row.getIndex();
	var moved = true;

	if (pos < fixedRows) {
		row.move(fixedRows-1);
		row.getTable().redraw(true);
	}

	if (index < fixedRows) {
		if (index == 0) 
			row.move(1, true);
		else 
			row.move(index-1);
		moved = false;
		row.getTable().redraw(true);
	}

	return moved;
}

$(document).ready(function () {
    $('.recipe_image_loader').on('change', function(element) {
        load_new_image(element);
        // if on recipe list view, extract recipeId embedded in element id
        if (element.target.id.includes("recipe_image_loader_")) {
            var recipe_id = element.target.id.replace("recipe_image_loader_", "")    
            $("#bsave_" + recipe_id).show();
        }
    });


    $('#b_new_recipe').click(function () {
        var form = document.getElementById('f_new_recipe');
        if (!validate(form)) {
            return false;
        }

        var recipe = {}
        recipe.id = ''
        recipe.name = form.elements['recipe_name'].value;
        recipe.abv = form.elements['abv'].value;
        recipe.ibu = form.elements['ibu'].value;
        recipe.abv_tweak = -1
        recipe.ibu_tweak = -1
        recipe.image = recipe_images[recipe.id]
        recipe.notes = form.elements['notes'].value;
        recipe.steps = table.getData();
        $.ajax({
            url: 'new_pico_recipe',
            type: 'POST',
            data: JSON.stringify(recipe),
            dataType: "json",
            processData: false,
            contentType: "application/json; charset=UTF-8",
            success: function (data) {
                showAlert("Success!", "success");
                setTimeout(function () { window.location.href = "pico_recipes"; }, 2000);
            },
            error: function (request, status, error) {
                showAlert(`Error: ${request.responseText}`, "danger");
                //setTimeout(function () { window.location.href = "pico_recipes";}, 2000);
            },
        });
    });

    $('#upload_recipe_file').on('change', function () {
        upload_recipe_file('picobrew', $(this).prop('files')[0], 'pico_recipes');
    });

    for (element of document.getElementsByTagName("input")) {
        const $feedback = $(element).siblings(".invalid-tooltip");
        if (element.pattern && element.required && $feedback) {
            element.addEventListener('change', (event) => {
                $(element).closest("form").removeClass("was-validated");
                $feedback.hide();
          });
        }
    }
});

function validate(form) {
    let valid = true;
    for (element of form.getElementsByTagName('input')) {
        const $feedback = $(element).siblings(".invalid-tooltip");
        if (element.type == "text" && element.pattern) {
            const re = new RegExp(element.pattern)
            if (!re.test(element.value)) {
                $feedback.show();
                valid = false;
            }
        }

        if (element.type == "number" && (element.min || element.max)) {
            const min = parseFloat(element.min);
            const max = parseFloat(element.max);
            const value = parseFloat(element.value);
            if ((min && value <= min) || (max && value >= max)) {
                $feedback.show();
                valid = false;
            }
        }
    };

    $(form).addClass("was-validated");
    return valid;
}

function update_recipe(recipe_id) {
    var table = Tabulator.findTable("#t_" + recipe_id)[0];
    if (table) {
        var recipe = {};
        recipe.id = recipe_id
        recipe.name = $('#recipe_name_' + recipe_id).val()
        recipe.abv = $('#abv_' + recipe_id).val()
        recipe.ibu = $('#ibu_' + recipe_id).val()
        recipe.notes = $('#notes_' + recipe_id).val()
        recipe.steps = table.getData();
        recipe.image = recipe_images[recipe.id]
        $.ajax({
            url: 'update_pico_recipe',
            type: 'POST',
            data: JSON.stringify(recipe),
            dataType: "json",
            processData: false,
            contentType: "application/json; charset=UTF-8",
            success: function (data) {
                //showAlert("Success!", "success");
                setTimeout(function () { window.location.href = "pico_recipes"; }, 2000);
            },
            error: function (request, status, error) {
                showAlert("Error: " + request.responseText, "danger");
                //setTimeout(function () { window.location.href = "pico_recipes";}, 2000);
            },
        });
    }
};

function download_recipe(recipe_id, recipe_name) {
    var table = Tabulator.findTable("#t_" + recipe_id)[0];
    if (table) {
        window.location = `/recipes/picobrew/${recipe_id}/${unescapeHtml(recipe_name)}.json`;
    }
};

function clone_recipe(recipe) {
    recipe.id = ''
    recipe.name = `${recipe.name} (copy ${Math.floor((Math.random() * 100) + 1)})`;
    $.ajax({
        url: 'new_pico_recipe',
        type: 'POST',
        data: JSON.stringify(recipe),
        dataType: "json",
        processData: false,
        contentType: "application/json; charset=UTF-8",
        success: function (data) {
            showAlert("Success!", "success")
            setTimeout(function () { window.location.href = "pico_recipes"; }, 2000);
        },
        error: function (request, status, error) {
            showAlert(`Error: ${request.responseText}`, "danger")
            //setTimeout(function () { window.location.href = "pico_recipes";}, 2000);
        },
    });
}

function delete_recipe(recipe_id) {
    if (confirm("Are you sure?")) {
        $.ajax({
            url: 'delete_pico_recipe',
            type: 'POST',
            data: JSON.stringify(recipe_id),
            dataType: "json",
            processData: false,
            contentType: "application/json; charset=UTF-8",
            success: function (data) {
                //showAlert("Success!", "success");
                setTimeout(function () { window.location.href = "pico_recipes"; }, 2000);
            },
            error: function (request, status, error) {
                showAlert(`Error: ${request.responseText}`, "danger");
                //setTimeout(function () { window.location.href = "pico_recipes";}, 2000);
            },
        });
    }
};

function delete_file(filename) {
    delete_server_file(filename, 'recipe', 'pico_recipes');
};
