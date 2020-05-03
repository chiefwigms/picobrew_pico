var plusIcon = function(cell, formatterParams){
    return "<i class='far fa-plus-square fa-lg'></i>";
}
var minusIcon = function(cell, formatterParams){
    return "<i class='far fa-minus-square fa-lg'></i>";
}
var editCheck = function(cell){
    return !(["Preparing To Brew", "Heating"].includes(cell.getRow().getCell("name").getValue()));
}
var table = new Tabulator("#recipe-table", {
    data:[{name:"Preparing To Brew", location:"Prime", temperature:"0", step_time:"3", drain_time:"0"},
          {name:"Heating", location:"PassThru", temperature:"110", step_time:"0", drain_time:"0"},
          {name:"Dough In", location:"Mash", temperature:"110", step_time:"7", drain_time:"0"},
          {name:"Mash 1", location:"Mash", temperature:"148", step_time:"45", drain_time:"0"},
          {name:"Mash 2", location:"Mash", temperature:"156", step_time:"0", drain_time:"0"},
          {name:"Mash Out", location:"Mash", temperature:"178", step_time:"7", drain_time:"2"},
          {name:"Hops 1", location:"Adjunct1", temperature:"202", step_time:"10", drain_time:"0"},
          {name:"Hops 2", location:"Adjunct2", temperature:"202", step_time:"8", drain_time:"0"},
          {name:"Hops 3", location:"Adjunct3", temperature:"202", step_time:"8", drain_time:"0"},
          {name:"Hops 4", location:"Adjunct4", temperature:"202", step_time:"8", drain_time:"5"},
    ],
    movableRows:true,
    headerSort:false,
    layout:"fitDataFill",
    resizableColumns:false,
    tooltipGenerationMode:"hover",
    columns:[
        {rowHandle:true, formatter:"handle", headerSort:false, frozen:true, minWidth:50},
        {title:"Step #", formatter:"rownum", hozAlign:"center", minWidth:60},
        {title:"Name", field:"name", width:200, tooltip:false, validator:["required", "string"], editable:editCheck, editor:"input"},
        {title:"Location", field:"location", width:120, hozAlign:"center", tooltip:false, validator:["required", "string"], editable:editCheck, editor:"select", editorParams:{
            values:[
              //"Prime",
                "Mash",
                "PassThru",
                "Adjunct1",
                "Adjunct2",
                "Adjunct3",
                "Adjunct4",
            ]
        }},
        {title:"Temp (°F)", field:"temperature", width:100, hozAlign:"center", validator:["required", "min:0", "max:208", "numeric"], editable:editCheck, editor:"number", editorParams:{
            min:0,
            max:208,
        }},
        {title:"Time (min)", field:"step_time", width:100, hozAlign:"center", validator:["required", "min:0", "max:120", "numeric"], editable:editCheck, editor:"number", editorParams:{
            min:0,
            max:120,
        }},
        {title:"Drain (min)", field:"drain_time", width:100, hozAlign:"center", validator:["required", "min:0", "max:10", "numeric"], editable:editCheck, editor:"number", editorParams:{
            min:0,
            max:10,
        }},
        {formatter:plusIcon, width:49, hozAlign:"center", cellClick:function(e, cell){
            table.addRow({}, false, cell.getRow());
        }},
        {formatter:minusIcon, width:49, hozAlign:"center", cellClick:function(e, cell){
            cell.getRow().delete();
        }},
    ],
    tooltips:function(column){
        var tip = ""
        switch (column.getField()) {
            case "temperature":
                tip = "[0 - 208]";
                break;
            case "step_time":
                tip = "[0 - 120]";
                break;
            case "drain_time":
                tip = "[0 - 10]";
                break;
            default:
                break;
        }
        return tip;
    },
});
$(document).ready(function(){
	$('button').click(function(){
        var recipe = {}
        recipe.id = ''
        recipe.name = document.getElementById('recipe_header').elements['recipe_name'].value;
        recipe.abv = document.getElementById('recipe_header').elements['abv'].value;
        recipe.ibu = document.getElementById('recipe_header').elements['ibu'].value;
        recipe.abv_tweak = -1
        recipe.ibu_tweak = -1
        recipe.image = ''
        recipe.steps = table.getData();
		$.ajax({
			url: 'new_recipe_save',
			type: 'POST',
            data: JSON.stringify(recipe),
            dataType: "json",
            processData: false,
            contentType: "application/json; charset=UTF-8",
		});
	});
});