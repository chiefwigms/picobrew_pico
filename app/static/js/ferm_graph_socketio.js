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
        var event_name = 'ferm_session_update|' + graph_data.chart_id
        socket.on(event_name, function (event) {
          var data = JSON.parse(event);
          self.setTitle(graph_data.title, { text: 'Voltage: ' + data['voltage'] + 'V' });
          for (point of data['data']) {
            self.series[0].addPoint([point.time, point.temp]);
            self.series[1].addPoint([point.time, point.pres]);
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

  colors: ['#F93', '#9F3', '#06C', '#036', '#000'],

  plotOptions: {
    spline: {
      marker: {
        enabled: true
      }
    }
  },

  title: graph_data.title,

  subtitle: graph_data.subtitle,

  tooltip: {
    formatter: function () {
      var s = '<b>' + Highcharts.dateFormat('%A, %b %e %k:%M:%S.%L', // Friday, Jan ## ##:##:##.####
        new Date(this.x)) + '</b>';

      $.each(this.points, function (i, point) {
        s += '<br/><span style="color:' + point.color + '">\u25CF</span> ' + point.series.name + ': ' + point.y;
      });

      return s;
    },
    shared: true
  },

  xAxis: {
    type: 'datetime',
    dateTimeLabelFormats: {
      day: '%b %e'
    },
    title: {
      text: 'Time'
    },
  },

  yAxis: [
    {
      title: {
        text: 'Temperature (F)'
      },
      //min: 50
      //max: 90
    }, {
      title: {
        text: 'Pressure (psi)'
      },
      min: 0,
      //max: 15
      opposite: true
    }],

  series: graph_data.series,
});
