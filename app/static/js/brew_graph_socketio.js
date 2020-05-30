Highcharts.setOptions({
    time: {
        useUTC: false
    }
});

Highcharts.chart(graph_data.chart_id, {
  chart: {
    events: {
      load: function () {
        var socket = io.connect('http://' + document.domain + ':' + location.port)
        var self = this
        var event_name = 'brew_session_update|' + graph_data.chart_id
        socket.on(event_name, function (event)
        {
            var data = JSON.parse(event);
            self.setTitle({text: data.session}, {text: data.step});
            self.series[0].addPoint([data.time, data.wort]);
            self.series[1].addPoint([data.time, data.therm]);
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

  colors: ['#6CF', '#39F', '#06C', '#036', '#000'],

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
