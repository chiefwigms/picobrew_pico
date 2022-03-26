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

    table.on("rowMoved", function(row) {
        calculate_hop_timing(row.getTable().getData(), row.getTable())
    })

    table.on("rowDeleted", function(row) {
        calculate_hop_timing(row.getTable().getData(), row.getTable())
    })

    table.on("rowAdded", function(row) {
        calculate_hop_timing(row.getTable().getData(), row.getTable())
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
        var adjunctSteps = data.filter(step => step.location.indexOf("Adjunct") == 0);

        var cumulative_hop_time = {
            "Adjunct1": 0,
            "Adjunct2": 0,
            "Adjunct3": 0,
            "Adjunct4": 0
        };
        adjunctSteps.slice().reverse().forEach(step => {
            for (x in cumulative_hop_time) {
                if (step.location >= x) {
                    cumulative_hop_time[x] += step.step_time
                }
            }

            if (provided_table) {
                provided_table.getRows()
                    .filter(row => row.getData().location == step.location)
                    .forEach(row => row.update({ "hop_time": cumulative_hop_time[step.location]}));
            }
            step['hop_time'] = cumulative_hop_time[step.location]
        });

        // clear non adjunct hop_time from table (change adjunct->mash/passthru)
        if (provided_table) {
            provided_table.getRows()
                .filter(row => row.getData().location.indexOf("Adjunct") != 0)
                .forEach(row => row.update({"hop_time": undefined}));
        }
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