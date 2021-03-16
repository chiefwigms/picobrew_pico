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
      var event_name = 'still_session_update|' + graph_data.chart_id
      socket.on(event_name, function (event)
      {
          var data = JSON.parse(event);
          self.setTitle(graph_data.title, 'Manual Still');
          for (point of data['data']) {
            self.series[0].addPoint([point.time, point.t1]);
            self.series[1].addPoint([point.time, point.t2]);
            self.series[2].addPoint([point.time, point.t3]);
            self.series[3].addPoint([point.time, point.t4]);
            self.series[4].addPoint([point.time, point.pres]);  
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
