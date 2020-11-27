// utility function to convert temperature units
function convert_temperature(temp, units) {
    if (units.toLowerCase() == 'imperial') {
        return (temp * 9 / 5) + 32  // convert celcius to fahrenheit
    }
    return (temp - 32) * 5 / 9  // convert fahrenheit to celcius
}

function temperature_editor(cell, onRendered, success, cancel, editorParams) {
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
    onRendered(function () {
        editor.focus();
        editor.style.css = "100%";
    });

    //when the value has been set, trigger the cell to update (converting to F if display is C)
    function successFunc() {
        success(selected_units == "imperial" ? editor.value : convert_temperature(editor.value, "imperial"));
    }

    editor.addEventListener("change", successFunc);
    editor.addEventListener("blur", successFunc);

    //return the editor element
    return editor;
}

// TODO: expanding and then collapsing the values don't update (and can't force redraw?)

// tabulator formatter, formats temperature to correct units for display based on selected units
function format_temperature(cell, formatterParams, onRendered) {
    // format_temperature is called when table is visble before DOM is loaded on new recipe UI
    if ($("#unit_selector > label.active > input").length != 0) {
        let selected_units = $("#unit_selector > label.active > input")[0].id;

        // convert into call to convert_units with optional table selector
        let temp_units = selected_units == "metric" ? "C" : "F";

        // convert if C as server stores F
        return temp_units == "F" ? cell.getValue() : convert_temperature(cell.getValue(), "C");
    } else {
        return cell.getValue();
    }
}

// converts all visible tabulator tables upon selection of units
function convert_units(units) {
    for (index in tables) {
        tables[index]
    }
    let prev_units = localStorage.getItem("units");

    // no-opt; reselected same units
    if (prev_units == units) return;

    localStorage.setItem("units", units);

    let temp_units = units == "metric" ? "C" : "F";

    let temp_header_ref = ".tabulator-col[tabulator-field='temperature'] > div.tabulator-col-content > div.tabulator-col-title";
    $(temp_header_ref).text("Temp (°" + temp_units + ")");

    let temp_cells_ref = ".tabulator-cell[tabulator-field='temperature']";
    $(temp_cells_ref).each(function (index, elem) {
        let current_temp = elem.textContent;
        elem.innerText = convert_temperature(current_temp, units);
    });
}

$(function () {
    recall_selected_units(true);
});

function recall_selected_units(convert = false) {
    // select local storage set units
    let selected_units = localStorage.getItem("units");
    if (selected_units == null)
        selected_units = "imperial";
        convert = false;

    $("#unit_selector > label > input#" + selected_units).parent().addClass("active");
    $("#unit_selector > label > input#" + selected_units).attr('checked', true);
    $("#unit_selector > label > input#" + selected_units).parent().siblings().removeClass("active");

    // clear localStorage and initially convert units to previously stored value
    localStorage.removeItem("units");
    // default javascript is imperial units
    if (convert) {
        convert_units(selected_units);
    }
}
