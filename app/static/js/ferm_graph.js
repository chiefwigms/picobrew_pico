Highcharts.setOptions({
    time: {
        useUTC: false
    }
});

function initiatizeChart(graph_data) {
  Highcharts.chart(graph_data.chart_id, {
    chart: {
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
}
