var plusIcon = function (cell, formatterParams) {
    return "<i class='far fa-plus-square fa-lg'></i>";
}
var minusIcon = function (cell, formatterParams) {
    return "<i class='far fa-minus-square fa-lg'></i>";
}
function showAlert(msg, type) {
    $('#alert').html("<div class='w-100 alert text-center alert-" + type + "'>" + msg + "</div>");
    $('#alert').show();
}

var default_data = [
    { name: "Heat Mash", location: "PassThru", temperature: 152, step_time: 0, drain_time: 0 },
    { name: "Mash", location: "Mash", temperature: 152, step_time: 90, drain_time: 8 },
    { name: "Heat to Mash Out", location: "PassThru", temperature: 175, step_time: 0, drain_time: 0 },
    { name: "Mash Out", location: "Mash", temperature: 175, step_time: 15, drain_time: 8 },
    { name: "Heat to Boil", location: "PassThru", temperature: 207, step_time: 0, drain_time: 0 },
    { name: "Pre-hop Boil", location: "PassThru", temperature: 207, step_time: 45, drain_time: 0 },
    { name: "Hops 1", location: "Adjunct1", temperature: 207, step_time: 10, drain_time: 0 },
    { name: "Hops 2", location: "Adjunct2", temperature: 207, step_time: 5, drain_time: 0 },
    { name: "Hops 3", location: "Adjunct3", temperature: 207, step_time: 8, drain_time: 0 },
    { name: "Balance Temps", location: "PassThru", temperature: 0, step_time: 1, drain_time: 8 },
    { name: "Cool to Whirlpool", location: "PassThru", temperature: 175, step_time: 0, drain_time: 0 },
    { name: "Whirlpool", location: "Adjunct4", temperature: 175, step_time: 20, drain_time: 5 },
    { name: "Connect Chiller", location: "Pause", temperature: 0, step_time: 0, drain_time: 0 },
    { name: "Chill", location: "PassThru", temperature: 66, step_time: 10, drain_time: 10 },
];
var tables_loaded = [];
var recipe_table = {
    movableRows: true,
    headerSort: false,
    layout: "fitDataFill",
    resizableColumns: false,
    tooltipGenerationMode: "hover",
    columns: [
        {
            rowHandle: true, formatter: "handle", headerSort: false, frozen: true, width: 50
        },
        {
            title: "Step #", formatter: "rownum", hozAlign: "center", width: 60
        },
        {
            title: "Name", field: "name", width: 200,
            validator: ["required", "minLength:1", "maxLength:19", "string"],
            editor: "input"
        },
        {
            title: "Location", field: "location", width: 120, hozAlign: "center", tooltip: false,
            validator: ["required", "string"],
            editor: "select",
            editorParams: {
                values: [
                    "PassThru",
                    "Mash",
                    "Adjunct1",
                    "Adjunct2",
                    "Adjunct3",
                    "Adjunct4",
                    "Pause",
                ]
            },
            cellEdited: (cell) => {
                calculate_hop_timing(cell.getTable().getData(), cell.getTable())
            }
        },
        {
            title: "Temp (°F)", field: "temperature", width: 100, hozAlign: "center",
            validator: ["required", "min:0", "max:208", "numeric"],
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
            formatter: plusIcon, width: 49, hozAlign: "center",
            cellClick: function (e, cell) {
                cell.getTable().addRow(Object.assign({}, cell.getRow().getData()), false, cell.getRow()).then(function(row) {
                    row.update({name: "New Step"});
                });
            }
        },
        {
            formatter: minusIcon, width: 49, hozAlign: "center",
            cellClick: function (e, cell) {
                cell.getRow().delete();
            }
        },
    ],
    dataLoaded: data_loaded,
    tooltips: function (column) {
        var tip = ""
        switch (column.getField()) {
            case "name":
                tip = "19 Characters Max";
                break;
            case "temperature":
                tip = "[0 - 208]";
                break;
            case "step_time":
                tip = "[0 - 180]";
                break;
            case "drain_time":
                tip = "[0 - 10]";
                break;
            case "hop_time":
                tip = "Hop Contact Time";
                break;
            default:
                break;
        }
        return tip;
    },
};

function data_loaded(data) {
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

$(document).ready(function () {
    $('#b_new_recipe').click(function () {
        var recipe = {}
        recipe.id = ''
        recipe.name = document.getElementById('f_new_recipe').elements['recipe_name'].value;
        recipe.steps = table.getData();
        $.ajax({
            url: 'new_zymatic_recipe',
            type: 'POST',
            data: JSON.stringify(recipe),
            dataType: "json",
            processData: false,
            contentType: "application/json; charset=UTF-8",
            success: function (data) {
                showAlert("Success!", "success");
                setTimeout(function () { window.location.href = "zymatic_recipes"; }, 2000);
            },
            error: function (request, status, error) {
                showAlert("Error: " + request.responseText, "danger");
                //setTimeout(function () { window.location.href = "zymatic_recipes";}, 2000);
            },
        });
    });
});

function update_recipe(recipe_id) {
    var table = Tabulator.prototype.findTable("#t_" + recipe_id)[0];
    if (table) {
        var recipe = {};
        recipe.id = recipe_id
        recipe.steps = table.getData();
        $.ajax({
            url: 'update_zymatic_recipe',
            type: 'POST',
            data: JSON.stringify(recipe),
            dataType: "json",
            processData: false,
            contentType: "application/json; charset=UTF-8",
            success: function (data) {
                //showAlert("Success!", "success");
                setTimeout(function () { window.location.href = "zymatic_recipes"; }, 2000);
            },
            error: function (request, status, error) {
                //showAlert("Error: " + request.responseText, "danger");
                //setTimeout(function () { window.location.href = "zymatic_recipes";}, 2000);
            },
        });
    }
};

function download_recipe(recipe_id, recipe_name) {
    var table = Tabulator.prototype.findTable("#t_" + recipe_id)[0];
    if (table) {
        window.location = '/recipes/zymatic/' + recipe_id + '/' + recipe_name + '.json';
    }
};

function clone_recipe(recipe) {
    recipe.id = ''
    recipe.name = recipe.name + " (copy " + Math.floor((Math.random() * 100) + 1) + ")";
    $.ajax({
        url: 'new_zymatic_recipe',
        type: 'POST',
        data: JSON.stringify(recipe),
        dataType: "json",
        processData: false,
        contentType: "application/json; charset=UTF-8",
        success: function (data) {
            showAlert("Success!", "success")
            setTimeout(function () { window.location.href = "zymatic_recipes"; }, 2000);
        },
        error: function (request, status, error) {
            showAlert("Error: " + request.responseText, "danger")
            //setTimeout(function () { window.location.href = "zymatic_recipes";}, 2000);
        },
    });
}

function delete_recipe(recipe_id) {
    if (confirm("Are you sure?")) {
        $.ajax({
            url: 'delete_zymatic_recipe',
            type: 'POST',
            data: JSON.stringify(recipe_id),
            dataType: "json",
            processData: false,
            contentType: "application/json; charset=UTF-8",
            success: function (data) {
                //showAlert("Success!", "success");
                setTimeout(function () { window.location.href = "zymatic_recipes"; }, 2000);
            },
            error: function (request, status, error) {
                //showAlert("Error: " + request.responseText, "danger");
                //setTimeout(function () { window.location.href = "zymatic_recipes";}, 2000);
            },
        });
    }
};

function delete_file(filename) {
    delete_server_file(filename, 'recipe', 'zymatic_recipes');
};
