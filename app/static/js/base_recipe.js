function edit_recipe(recipe_id) {
    $('#view_' + recipe_id).toggleClass('d-none');
    $('#form_' + recipe_id).toggleClass('d-none');
};

function toggle_sync_recipe(recipe_id, recipe_type) {
    $.ajax({
        url: 'sync_recipe?' + $.param({recipe_id, recipe_type}),
        type: 'POST',
        success: function (data) {
            $sync_btn = $(`#bsync_${recipe_id}`);
            $sync_btn.toggleClass("btn-secondary btn-success");
            $sync_btn.find("i").toggleClass("fa-check-square fa-sync");
            
            const tooltip = $sync_btn.attr('title');
            if (tooltip.indexOf("Sync") != -1) {
                $sync_btn.attr('title', tooltip.replace("Sync", "Archive"))
            } else {
                $sync_btn.attr('title', tooltip.replace("Archive", "Sync"))
            }
        },
        error: function (request, status, error) {
            showAlert(`Error: ${request.responseText}`, "danger");
            //setTimeout(function () { window.location.href = "pico_recipes";}, 2000);
        },
    });
}

// tabulator utility functions for recipe table functionalities

function subscribe_table_callbacks(table) {
    table.on("dataLoading", function() {
        isDataLoading=true;
    })

    table.on("dataLoaded", function(data) {
        isDataLoading=false;
        calculate_hop_timing(data);
    })

    table.on("cellEdited", function(cell) {
        var column = cell.getColumn();
        var columnField = column.getField();

        if (columnField == "location") {
            calculate_hop_timing(cell.getTable().getData(), cell.getTable())
        } else if (columnField == "step_time") {
            total_time = cell.getValue() + cell.getData().drain_time;
            cell.getRow().getCell("total_time").setValue(total_time);
            calculate_hop_timing(cell.getTable().getData(), cell.getTable())
        } else if (columnField == "drain_time") {
            total_time = cell.getValue() + cell.getData().drain_time;
            cell.getRow().getCell("total_time").setValue(total_time);
        }
    })
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

function recipe_tooltips(machine_type) {
    let locations = ["Mash", "Adjunct 1-4", "PassThru"]
    if (machine_type == "ZSeries" || machine_type == "Zymatic") {
        locations.push("Pause")
    } else {
        locations.push("Prime")
    }
    return function(column) {
        var tip = ""
        let selected_units = $("#unit_selector > label.active > input").length > 0 ? $("#unit_selector > label.active > input")[0].id : "imperial";
        switch (column.getField()) {
            case "step_num":
                tip = "Sequential Step Number (not modifiable)"
                break;
            case "name":
                tip = "Name of the Step (19 characters maximum)"
                break;
            case "location":
                tip = `Location for Step [${locations.join(", ")}]`
                break;
            case "temperature":
                tip = 'Temperature: '
                if (selected_units == 'imperial') {
                    tip += `[0 - 208] (°F)`;
                } else {
                    tip += `[${convert_temperature(0, selected_units)} - ${convert_temperature(208, selected_units)}] (°C)`;
                }
                break;
            case "step_time":
                tip = "Step Duration: [0 - 180] (minutes)";
                break;
            case "drain_time":
                tip = "Drain Duration: [0 - 10] (minutes)";
                break;
            case "total_time":
                tip = "Calculated Step Duration: Time + Drain (minutes)";
                break;
            case "hop_time":
                tip = "Hop Contact Time (boil time) - amount of time (minutes) that this adjunct is exposed to the hot wort/liquor.";
                break;
            case "add_step":
                tip = "Add a New Step After";
                break;
            case "remove_step":
                tip = "Remove this Step";
                break;
            default:
                break;
        }
        return tip;
    }
}