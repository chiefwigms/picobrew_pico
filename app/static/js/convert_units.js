// utility function to convert temperature units
function convert_temperature(temp, units) {
    if (units.toLowerCase() == 'imperial') {
        return (temp * 9/5) + 32  // convert celcius to fahrenheit
    }
    return (temp - 32) * 5/9  // convert fahrenheit to celcius
}

// TODO: expanding and then collapsing the values don't update (and can't force redraw?)

// tabulator formatter, formats temperature to correct units for display based on selected units
function mutate_temperature(value, formatterParams, onRendered) {
    let selected_units = $("#unit_selector > label.active > input")[0].id;    
    // convert if C as server stores F
    return selected_units == "imperial" ? value : convert_temperature(value, selected_units);
}

// if set to c -> convert to F
// if set to f -> keep
function mutator_edit_temperature(value, formatterParams, onRendered) {
    let selected_units = $("#unit_selector > label.active > input")[0].id;    
    // convert to F if C as server stores F
    return selected_units == "imperial" ? value : convert_temperature(value, "imperial");
}

// tabulator formatter, formats temperature to correct units for display based on selected units
function format_temperature(cell, formatterParams, onRendered) {
    let selected_units = $("#unit_selector > label.active > input")[0].id;
 
    // convert into call to convert_units with optional table selector
    let temp_units = selected_units == "metric" ? "C" : "F";
    
    // convert if C as server stores F
    return temp_units == "F" ? cell.getValue() : convert_temperature(cell.getValue(), "C");
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
    
    // <div class="tabulator-col" role="columnheader" aria-sort="none" tabulator-field="temperature" title="" style="min-width: 40px; width: 100px;">
    //   <div class="tabulator-col-content">
    //     <div class="tabulator-col-title">Temp (°F)</div>
    //   </div>
    // </div>
    let temp_header_ref = ".tabulator-col[tabulator-field='temperature'] > div.tabulator-col-content > div.tabulator-col-title";
    $(temp_header_ref).text("Temp (°" + temp_units + ")");
    
    // <div class="tabulator-cell" role="gridcell" tabulator-field="temperature" tabindex="0" title="[0 - 208]" style="width: 100px; text-align: center; height: 29px;">104</div>
    let temp_cells_ref = ".tabulator-cell[tabulator-field='temperature']";
    $(temp_cells_ref).each(function(index, elem) {
        let current_temp = elem.textContent;
        elem.innerText = convert_temperature(current_temp, units);
    }); 
    
    // let re = new RegExp('\[(\d+)\ \-\ (\d)+\]');
    // matches = re.
    // temp_range = $(".tabulator-cell tabulator-field='temperature'").title;
    // temp_range.
}

$(function() {
    // select local storage set units
    let selected_units = localStorage.getItem("units");
    if (selected_units == null) selected_units = "imperial";

    $("#unit_selector > label > input#" + selected_units ).parent().addClass("active");
    $("#unit_selector > label > input#" + selected_units ).attr( 'checked', true );
    $("#unit_selector > label > input#" + selected_units ).parent().siblings().removeClass("active");

    // clear localStorage and initially convert units to previously stored value
    localStorage.removeItem("units");
    convert_units(selected_units);
});