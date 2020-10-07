$(document).ready(function(){
    var event_name = 'brew_session_update|' + table_data.chart_id
    socket.on(event_name, function (event)
    {
        var data = JSON.parse(event);
        $('#table_head:last-child').after('<tr class="' + data.time + '"></tr>');
        $('.' + data.time).append('<td>' + data.time + '</td>');
        for (var i = 0; i < data.data.length; i++){
            self.series[i].addPoint([data.time, data.data[i]]);
            $('.' + data.time).append('<tr>' + data.data[i] + '</tr>');
        }
    });
});