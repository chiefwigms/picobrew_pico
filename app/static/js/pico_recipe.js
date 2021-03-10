const fixedRows = 3;
var isDataLoading;

function rowIsEditable(cell) {
    var pos = cell.getTable().getRowPosition(cell.getRow(),true);
    return (pos < fixedRows) ? false : true;
}
var editCheck = function (cell) {
    return rowIsEditable(cell);
}
var plusIcon = function (cell, formatterParams) {
    return rowIsEditable(cell) ? "<i class='far fa-plus-square fa-lg'></i>" : "";
}
var minusIcon = function (cell, formatterParams) {
    return rowIsEditable(cell) ? "<i class='far fa-minus-square fa-lg'></i>" : "";
}
function showAlert(msg, type) {
    $('#alert').html("<div class='w-100 alert text-center alert-" + type + "'>" + msg + "</div>");
    $('#alert').show();
}
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
var tables_loaded = [];
var idMutator = function (value, data, type, params, component) {
	return isDataLoading ? component.getTable().getRows().length : data.id;
}
var recipe_table = {
    movableRows: true,
    headerSort: false,
    layout: "fitDataFill",
    resizableColumns: false,
    tooltipGenerationMode: "hover",
    tooltipsHeader: tooltips_func,
    tooltips: tooltips_func,
    columns: [
        {
            rowHandle: true, formatter: "handle", headerSort: false, frozen: true, width: 50
        },
        {
			title: "ID", field:"id", visible: false, mutatorData: idMutator
        },        
        {
            title: "Step #", field:"step_num", formatter: "rownum", hozAlign: "center", width: 60
        },
        {
            title: "Name", field: "name", width: 200,
            validator: ["required", "string", "minLength:1", "maxLength:19", "regex:^[a-zA-Z0-9_@\\-\\ ]*$"],
            editable: editCheck,
            editor: "input"
        },
        {
            title: "Location", field: "location", width: 120, hozAlign: "center",
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
            },
            cellEdited: (cell) => {
                calculate_hop_timing(cell.getTable().getData(), cell.getTable())
            }
        },
        {
            title: "Temp (°F)", field: "temperature", width: 100, hozAlign: "center",
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
            title: "Time (min)", field: "step_time", width: 100, hozAlign: "center",
            validator: ["required", "min:0", "max:180", "numeric"],
            editable: editCheck,
            editor: "number",
            editorParams: {
                min: 0,
                max: 180,
            },
            cellEdited: (cell) => {
                total_time = cell.getValue() + cell.getData().drain_time;
                cell.getRow().getCell("total_time").setValue(total_time);
                calculate_hop_timing(cell.getTable().getData(), cell.getTable())
            }
        },
        {
            title: "Drain (min)", field: "drain_time", width: 100, hozAlign: "center",
            validator: ["required", "min:0", "max:10", "numeric"],
            editable: editCheck,
            editor: "number",
            editorParams: {
                min: 0,
                max: 10,
            },
            cellEdited: (cell) => {
                total_time = cell.getValue() + cell.getData().step_time;
                cell.getRow().getCell("total_time").setValue(total_time);
            }
        },
        {   // hop timings are cumulative (H1+H2+H3+H4 = H1 Hop Contact Time)
            title: "Hop (min)", field: "hop_time", width: 100, hozAlign: "center",
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
            title: "Total (min)", field: "total_time", width: 100, hozAlign: "center",
            editable: false,
            mutator: (value, data, type, params, component) => {
                return data.step_time + data.drain_time;
            },
            bottomCalc: "sum"
        },
        {
            formatter: plusIcon, field: "add_step", width: 49, hozAlign: "center",
            cellClick: function (e, cell) {
                if (rowIsEditable(cell)) {
                    var newRowData = Object.assign({}, cell.getRow().getData());
                    newRowData.name = "New Step";
                    newRowData.id = getMaxID(cell)+1;
                    cell.getTable().addRow(newRowData, false, cell.getRow());
                }
            }
        },
        {
            formatter: minusIcon, field: "remove_step", width: 49, hozAlign: "center",
            cellClick: function (e, cell) {
                if (rowIsEditable(cell)) {
                    cell.getRow().delete();
                    if (cell.getTable().getRows().length==fixedRows) {
                        cell.getTable().addRow(Object.assign({},default_data[fixedRows]));
                    }
                }
            }
        },
    ],
    dataLoading: function() {
        isDataLoading=true;
    },
    dataLoaded: data_loaded,
};

function data_loaded(data) {
    isDataLoading=false;
    calculate_hop_timing(data)
}

function calculate_hop_timing(data, provided_table = undefined) {
    //data - all data loaded into the table
    if (data.length == 0) {
        return;
    } else {
        // called outside cell edit
        if (provided_table == undefined) {
            recently_loaded = Object.keys(tables).filter(key => tables_loaded.indexOf(key) == -1)

            // type is always data (field isn't editable)
            // table data is being filled in and not completely available, build up global reference for each recipe
            if (recently_loaded.length != 0) {
                provided_table = tables[recently_loaded[0]]
                tables_loaded.push(recently_loaded[0])
            } else {
                // create experience
                provided_table = table;
            }
        }
        
        var rows = provided_table.getRows();
        var adjunctSteps = rows.filter(row => row.getData().location.indexOf("Adjunct") == 0);

        var cumulative_hop_time = {
            "Adjunct1": 0,
            "Adjunct2": 0,
            "Adjunct3": 0,
            "Adjunct4": 0
        };
        adjunctSteps.slice().reverse().forEach(adjunctRow => {
            var row_data = adjunctRow.getData();
            for (x in cumulative_hop_time) {
                if (row_data.location <= "Adjunct" + x) {
                    cumulative_hop_time[x] += row_data.step_time
                }
            }

            // cumulative_hop_time += row_data.step_time;
            adjunctRow.update({ "hop_time": cumulative_hop_time[row_data.location] });
        });
    }
}

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
        var recipe = {}
        recipe.id = ''
        recipe.name = document.getElementById('f_new_recipe').elements['recipe_name'].value;
        recipe.abv = document.getElementById('f_new_recipe').elements['abv'].value;
        recipe.ibu = document.getElementById('f_new_recipe').elements['ibu'].value;
        recipe.abv_tweak = -1
        recipe.ibu_tweak = -1
        recipe.image = recipe_images[recipe.id]
        recipe.notes = document.getElementById('f_new_recipe').elements['notes'].value;
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
});

function update_recipe(recipe_id) {
    var table = Tabulator.prototype.findTable("#t_" + recipe_id)[0];
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
                //showAlert("Error: " + request.responseText, "danger");
                //setTimeout(function () { window.location.href = "pico_recipes";}, 2000);
            },
        });
    }
};

function edit_recipe(recipe_id) {
    $('#view_' + recipe_id).toggleClass('d-none');
    $('#form_' + recipe_id).toggleClass('d-none');
};

function download_recipe(recipe_id, recipe_name) {
    var table = Tabulator.prototype.findTable("#t_" + recipe_id)[0];
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
                //showAlert(`Error: ${request.responseText}`, "danger");
                //setTimeout(function () { window.location.href = "pico_recipes";}, 2000);
            },
        });
    }
};

function delete_file(filename) {
    delete_server_file(filename, 'recipe', 'pico_recipes');
};
