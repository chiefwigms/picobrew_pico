var plusIcon = function(cell, formatterParams){
    return "<i class='far fa-plus-square fa-lg'></i>";
}
var minusIcon = function(cell, formatterParams){
    return "<i class='far fa-minus-square fa-lg'></i>";
}
var default_data = [{name:"Heat Mash", location:"PassThru", temperature:"152", step_time:"0", drain_time:"0"},
                    {name:"Mash", location:"Mash", temperature:"152", step_time:"90", drain_time:"8"},
                    {name:"Heat to Mash Out", location:"PassThru", temperature:"175", step_time:"0", drain_time:"0"},
                    {name:"Mash Out", location:"Mash", temperature:"175", step_time:"15", drain_time:"8"},
                    {name:"Heat to Boil", location:"PassThru", temperature:"207", step_time:"0", drain_time:"0"},
                    {name:"Pre-hop Boil", location:"PassThru", temperature:"207", step_time:"45", drain_time:"0"},
                    {name:"Hops 1", location:"Adjunct1", temperature:"207", step_time:"10", drain_time:"0"},
                    {name:"Hops 2", location:"Adjunct2", temperature:"207", step_time:"5", drain_time:"0"},
                    {name:"Hops 3", location:"Adjunct3", temperature:"207", step_time:"8", drain_time:"0"},
                    {name:"Balance Temps", location:"PassThru", temperature:"0", step_time:"1", drain_time:"8"},
                    {name:"Cool to Whirlpool", location:"PassThru", temperature:"175", step_time:"0", drain_time:"0"},
                    {name:"Whirlpool", location:"Adjunct4", temperature:"175", step_time:"20", drain_time:"5"},
                    {name:"Connect Chiller", location:"Pause", temperature:"0", step_time:"0", drain_time:"0"}, 
                    {name:"Chill", location:"PassThru", temperature:"66", step_time:"10", drain_time:"10"},
                    ];
var recipe_table = {
    movableRows:true,
    headerSort:false,
    layout:"fitDataFill",
    resizableColumns:false,
    tooltipGenerationMode:"hover",
    columns:[
        {rowHandle:true, formatter:"handle", headerSort:false, frozen:true, width:50},
        {title:"Step #", formatter:"rownum", hozAlign:"center", width:60},
        {title:"Name", field:"name", width:200, validator:["required", "minLength:1", "maxLength:19", "string"], editor:"input"},
        {title:"Location", field:"location", width:120, hozAlign:"center", tooltip:false, validator:["required", "string"], editor:"select", editorParams:{
            values:[
                "PassThru",
                "Mash",
                "Adjunct1",
                "Adjunct2",
                "Adjunct3",
                "Adjunct4",
                "Pause",
            ]
        }},
        {title:"Temp (°F)", field:"temperature", width:100, hozAlign:"center", validator:["required", "min:0", "max:208", "numeric"], editor:"number", editorParams:{
            min:0,
            max:208,
        }},
        {title:"Time (min)", field:"step_time", width:100, hozAlign:"center", validator:["required", "min:0", "max:180", "numeric"], editor:"number", editorParams:{
            min:0,
            max:180,
        }},
        {title:"Drain (min)", field:"drain_time", width:100, hozAlign:"center", validator:["required", "min:0", "max:10", "numeric"], editor:"number", editorParams:{
            min:0,
            max:10,
        }},
        {formatter:plusIcon, width:49, hozAlign:"center", cellClick:function(e, cell){
            cell.getTable().addRow({}, false, cell.getRow());
        }},
        {formatter:minusIcon, width:49, hozAlign:"center", cellClick:function(e, cell){
            cell.getRow().delete();
        }},
    ],
    tooltips:function(column){
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
$(document).ready(function(){
	$('#b_new_recipe').click(function(){
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
            success: function(data) {
                showAlert("Success!", "success");
                setTimeout(function () { window.location.href = "zymatic_recipes";}, 2000);
            },
            error: function(request, status, error) {
                showAlert("Error: " + request.responseText, "danger");
                //setTimeout(function () { window.location.href = "zymatic_recipes";}, 2000);
            },
		});
    });
    function showAlert(msg, type){
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
        $.ajax({
			url: 'update_zymatic_recipe',
			type: 'POST',
            data: JSON.stringify(recipe),
            dataType: "json",
            processData: false,
            contentType: "application/json; charset=UTF-8",
            success: function(data) {
                //showAlert("Success!", "success");
                setTimeout(function () { window.location.href = "zymatic_recipes";}, 2000);
            },
            error: function(request, status, error) {
                //showAlert("Error: " + request.responseText, "danger");
                //setTimeout(function () { window.location.href = "zymatic_recipes";}, 2000);
            },
		});
    }
};
function delete_recipe(recipe_id){
    if (confirm("Are you sure?")){
		$.ajax({
			url: 'delete_zymatic_recipe',
			type: 'POST',
            data: JSON.stringify(recipe_id),
            dataType: "json",
            processData: false,
            contentType: "application/json; charset=UTF-8",
            success: function(data) {
                //showAlert("Success!", "success");
                setTimeout(function () { window.location.href = "zymatic_recipes";}, 2000);
            },
            error: function(request, status, error) {
                //showAlert("Error: " + request.responseText, "danger");
                //setTimeout(function () { window.location.href = "zymatic_recipes";}, 2000);
            },
		});
    }
};
