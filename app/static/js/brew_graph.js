Highcharts.setOptions({
    time: {
        useUTC: false
    }
});

Highcharts.chart(graph_data.chart_id, {
  chart: {
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

  tooltip: {
    formatter: function() {
        var s = '<b>'+ Highcharts.dateFormat('%A, %b %e %k:%M:%S.%L', // Friday, Jan ## ##:##:##.####
          new Date(this.x)) +'</b>';

        $.each(this.points, function(i, point) {
            s += '<br/><span style="color:' + point.color + '">\u25CF</span> ' + point.series.name + ': ' + point.y;
        });

        return s;
    },
    shared: true
  },

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
