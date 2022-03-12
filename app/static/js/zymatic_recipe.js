const fixedRows = 0;
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
    layout: "fitDataFill",
    tooltipGenerationMode: "hover",
    columnDefaults:{
        headerSort: false,
        hozAlign: "center",
        resizableColumns: false,
        tooltipsHeader: recipe_tooltips("ZSeries"),
        tooltips: recipe_tooltips("ZSeries"),
    },
    columns: [
        {
            rowHandle: true, formatter: "handle", frozen: true, width: 50,
        },
        {
            title: "Step #", formatter: "rownum", width: 60,
        },
        {
            title: "Name", field: "name", width: 200,
            validator: ["required", "string", "minLength:1", "maxLength:19", "regex:^[a-zA-Z0-9_@\\-\\ ]*$"],
            editor: "input"
        },
        {
            title: "Location", field: "location", width: 120,
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
            title: "Temp (°F)", field: "temperature", width: 100,
            validator: ["required", "min:0", "max:208", "numeric"],
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
            title: "Drain (min)", field: "drain_time", width: 100,
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
            formatter: plusIcon, width: 49,
            cellClick: function (e, cell) {
                cell.getTable().addRow(Object.assign({}, cell.getRow().getData()), false, cell.getRow()).then(function(row) {
                    row.update({name: "New Step"});
                });
            }
        },
        {
            formatter: minusIcon, width: 49,
            cellClick: function (e, cell) {
                cell.getRow().delete();
                if (cell.getTable().getRows().length==fixedRows) {
                    cell.getTable().addRow(Object.assign({},default_data[fixedRows]));
                }
            }
        },
    ],
    dataLoaded: data_loaded,
};

function data_loaded(data) {
    calculate_hop_timing(data)
}

function isRowMoved(row){
	return true;
}

$(document).ready(function () {
    $('#b_new_recipe').click(function () {
        var form = document.getElementById('f_new_recipe');
        if (!validate(form)) {
            return false;
        }

        var recipe = {}
        recipe.id = ''
        recipe.name = form.elements['recipe_name'].value;
        recipe.notes = form.elements['notes'].value;
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

    $('#upload_recipe_file').on('change', function () {
        upload_recipe_file('zymatic', $(this).prop('files')[0], 'zymatic_recipes');
    });

    for (element of document.getElementsByTagName("input")) {
        const $feedback = $(element).siblings(".invalid-feedback", ".invalid-tooltip");
        if (element.pattern && element.required && $feedback) {
            element.addEventListener('change', (event) => {
                $(element).closest("form").removeClass("was-validated");
                $feedback.hide();
          });
        }
    }
});

function validate(form) {
    for (element of form.getElementsByTagName('input')) {
        const $feedback = $(element).siblings(".invalid-feedback", ".invalid-tooltip");
        if (element.pattern) {
            const re = new RegExp(element.pattern)
            if (!re.test(element.value)) {
                $(form).addClass("was-validated");
                $feedback.show();
                return false;
            }
        }
    };
    return  true;
}

function update_recipe(recipe_id) {
    var table = Tabulator.findTable("#t_" + recipe_id)[0];
    if (table) {
        var recipe = {};
        recipe.id = recipe_id
        recipe.name = $('#recipe_name_' + recipe_id).val()
        recipe.notes = $('#notes_' + recipe_id).val()
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
                showAlert("Error: " + request.responseText, "danger");
                //setTimeout(function () { window.location.href = "zymatic_recipes";}, 2000);
            },
        });
    }
};

function download_recipe(recipe_id, recipe_name) {
    var table = Tabulator.findTable("#t_" + recipe_id)[0];
    if (table) {
        window.location = '/recipes/zymatic/' + recipe_id + '/' + unescapeHtml(recipe_name) + '.json';
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
            showAlert("Error: " + request.responseText, "danger");
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
                showAlert("Error: " + request.responseText, "danger");
                //setTimeout(function () { window.location.href = "zymatic_recipes";}, 2000);
            },
        });
    }
};

function delete_file(filename) {
    delete_server_file(filename, 'recipe', 'zymatic_recipes');
};
