var plusIcon = function (cell, formatterParams) {
    return "<i class='far fa-plus-square fa-lg'></i>";
}
var minusIcon = function (cell, formatterParams) {
    return "<i class='far fa-minus-square fa-lg'></i>";
}
// provide selector for default mash profiles (single infusion w/ mashout, single infusion w/o mashout, high efficiency multi-step, etc)
var default_data = [{ name: "Heat Water", location: "PassThru", temperature: 104, step_time: 0, drain_time: 0 },
                    { name: "Dough In", location: "Mash", temperature: 104, step_time: 20, drain_time: 4 },
                    { name: "Heat to Mash 1", location: "Mash", temperature: 145, step_time: 0, drain_time: 4 },
                    { name: "Mash 1", location: "Mash", temperature: 145, step_time: 40, drain_time: 4 },
                    { name: "Heat to Mash 2", location: "Mash", temperature: 161, step_time: 0, drain_time: 4 },
                    { name: "Mash 2", location: "Mash", temperature: 161, step_time: 80, drain_time: 4 },
                    { name: "Heat to Mash Out", location: "Mash", temperature: 175, step_time: 0, drain_time: 4 },
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
var recipe_table = {
    movableRows: true,
    headerSort: false,
    layout: "fitDataFill",
    resizableColumns: false,
    tooltipGenerationMode: "hover",
    columns: [
        { rowHandle: true, formatter: "handle", headerSort: false, frozen: true, width: 50 },
        { title: "Step #", formatter: "rownum", hozAlign: "center", width: 60 },
        { title: "Name", field: "name", width: 200, validator: ["required", "minLength:1", "maxLength:19", "string"], editor: "input" },
        {
            title: "Location", field: "location", width: 120, hozAlign: "center", tooltip: false, validator: ["required", "string"], editor: "select", editorParams: {
                values: [
                    "PassThru",
                    "Mash",
                    "Adjunct1",
                    "Adjunct2",
                    "Adjunct3",
                    "Adjunct4",
                    "Pause",
                ]
            }
        },
        {
            title: "Temp (°F)", field: "temperature", width: 100, hozAlign: "center",
            validator: ["required", "min:0", "max:208", "numeric"], 
            editorParams: {
                min: 0,     // -18 C
                max: 208,   // 98 C
            },
            editor: function(cell, onRendered, success, cancel, editorParams){
                //cell - the cell component for the editable cell
                //onRendered - function to call when the editor has been rendered
                //success - function to call to pass the successfuly updated value to Tabulator
                //cancel - function to call to abort the edit and return to a normal cell
                //editorParams - params object passed into the editorParams column definition property
            
                //create and style editor
                var editor = document.createElement("input");

                let selected_units = $("#unit_selector > label.active > input")[0].id;  
            
                // Set value of editor to the current value of the cell (converting if display is C)
                editor.value = selected_units == "imperial" ? cell.getValue() : convert_temperature(cell.getValue(), "metric");
            
                //set focus on the select box when the editor is selected (timeout allows for editor to be added to DOM)
                onRendered(function(){
                    editor.focus();
                    editor.style.css = "100%";
                });
            
                //when the value has been set, trigger the cell to update (converting to F if display is C)
                function successFunc(){
                    success(selected_units == "imperial" ? editor.value : convert_temperature(editor.value, "imperial"));
                }
            
                editor.addEventListener("change", successFunc);
                editor.addEventListener("blur", successFunc);
            
                //return the editor element
                return editor;
            },
            formatter: function(cell, formatterParams, onRendered){
                console.log("formatter called");
                return format_temperature(cell, formatterParams, onRendered);
            },
            // mutator: function(value, data, type, params, component) {
            //     // stored in f; might be viewed in c;
            //     console.log("mutator called");
            //     return mutate_temperature(value);
            // },
            // mutatorEdit: function(value, data, type, params, component) {
            //     // stored in f; might be viewed in c;
            //     // if set to c -> convert to F
            //     // if set to f -> keep
            //     console.log("mutator edit called")
            //     return mutator_edit_temperature(value);
            // },
            // accessor: function(value, data, type, params, column) {
            //     console.log("accessor called")
            //     return mutate_temperature(value);
            // }
        },
        {
            title: "Time (min)", field: "step_time", width: 100, hozAlign: "center", validator: ["required", "min:0", "max:180", "numeric"], editor: "number", editorParams: {
                min: 0,
                max: 180,
            }
        },
        {
            title: "Drain (min)", field: "drain_time", width: 100, hozAlign: "center", validator: ["required", "min:0", "max:10", "numeric"], editor: "number", editorParams: {
                min: 0,
                max: 10,
            }
        },
        {
            formatter: plusIcon, width: 49, hozAlign: "center", cellClick: function (e, cell) {
                cell.getTable().addRow({}, false, cell.getRow());
            }
        },
        {
            formatter: minusIcon, width: 49, hozAlign: "center", cellClick: function (e, cell) {
                cell.getRow().delete();
            }
        },
    ],
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
            default:
                break;
        }
        return tip;
    },
};
$(document).ready(function () {
    $('#b_new_recipe').click(function () {
        var recipe = {}
        recipe.id = ''
        recipe.name = document.getElementById('f_new_recipe').elements['recipe_name'].value;
        recipe.steps = table.getData();
        $.ajax({
            url: 'new_zseries_recipe_save',
            type: 'POST',
            data: JSON.stringify(recipe),
            dataType: "json",
            processData: false,
            contentType: "application/json; charset=UTF-8",
            success: function(data) {
                showAlert("Success!", "success")
                setTimeout(function() { window.location.href = "zseries_recipes";}, 2000);
            },
            error: function(request, status, error) {
                showAlert("Error: " + request.responseText, "danger")
            },
        });
    });

    function showAlert(msg, type) {
        $('#alert').html("<div class='w-75 alert text-center alert-" + type + "'>" + msg + "</div>");
        $('#alert').show();
    }
});
function update_recipe(recipe_id){
    var table = Tabulator.prototype.findTable("#t_"+recipe_id)[0];
    if (table){
        var recipe = {};
        recipe.id = recipe_id
        recipe.steps = table.getData();
        // convert temperatures to F
        $.ajax({
			url: 'update_zseries_recipe',
			type: 'POST',
            data: JSON.stringify(recipe),
            dataType: "json",
            processData: false,
            contentType: "application/json; charset=UTF-8",
            success: function(data) {
                //showAlert("Success!", "success");
                setTimeout(function () { window.location.href = "zseries_recipes";}, 2000);
            },
            error: function(request, status, error) {
                //showAlert("Error: " + request.responseText, "danger");
                //setTimeout(function () { window.location.href = "zseries_recipes";}, 2000);
            },
		});
    }
};
function delete_recipe(recipe_id){
    if (confirm("Are you sure?")){
		$.ajax({
			url: 'delete_zseries_recipe',
			type: 'POST',
            data: JSON.stringify(recipe_id),
            dataType: "json",
            processData: false,
            contentType: "application/json; charset=UTF-8",
            success: function(data) {
                //showAlert("Success!", "success");
                setTimeout(function () { window.location.href = "zseries_recipes";}, 2000);
            },
            error: function(request, status, error) {
                //showAlert("Error: " + request.responseText, "danger");
                //setTimeout(function () { window.location.href = "zseries_recipes";}, 2000);
            },
		});
    }
};
function delete_file(filename){
    delete_server_file(filename, 'recipe', 'zseries_recipes');
};
