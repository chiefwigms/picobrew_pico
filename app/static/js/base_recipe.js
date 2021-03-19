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