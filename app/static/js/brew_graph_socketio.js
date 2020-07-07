Highcharts.setOptions({
    time: {
        useUTC: false
    }
});

Highcharts.chart(graph_data.chart_id, {
  chart: {
    events: {
      load: function () {
        var self = this
        var socket = io.connect('//' + document.domain + ':' + location.port)
        var event_name = 'brew_session_update|' + graph_data.chart_id
        socket.on(event_name, function (event)
        {
            var data = JSON.parse(event);
            self.setTitle({text: data.session}, {text: data.step});
            for (var i = 0; i < data.data.length; i++){
              self.series[i].addPoint([data.time, data.data[i]]);
            }
            if (data.event)
            {
              self.xAxis[0].addPlotLine({ 'color': 'black', 'width': '2', 'value': data.time, 'label': {'text': data.event, 'style': {'color': 'white', 'fontWeight': 'bold'}, 'verticalAlign': 'top', 'x': -15, 'y': 0}});
            }
        });
      },
    },

    type: 'spline',
    zoomType: 'xy'
  },

  credits: {
    enabled: false
  },

  colors: ['#39F', '#F0F', '#FF6', '#F00', '#6C5', '#000'],

  plotOptions: {
    spline: {
      marker: {
        enabled: true
      }
    }
  },

  title: graph_data.title,

  subtitle: graph_data.subtitle,

  xAxis: {
    type: 'datetime',
    title: {
      text: 'Time'
    },
    plotLines: graph_data.xaplotlines
  },

  yAxis: {
    title: {
      text: 'Temperature (F)'
    },
    min: 0
    //max: 230
  },

  series: graph_data.series,
});
