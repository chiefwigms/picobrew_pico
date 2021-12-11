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

    yAxis: [{
      title: {
        text: 'Temperature (F)'
      },

      labels: {
        format: '{value:,.0f}'
      },

      tickPositioner: function () {
        var positions = [],
        incrementNum = 6,
        tick = this.dataMin,
        increment = (this.dataMax - this.dataMin) / incrementNum;

        if (this.dataMax !== null && this.dataMin !== null) {
          for (let i = 0; i <= incrementNum; i++) {
            positions.push(tick),
            tick += increment;
          }
        }
        TickAmountValue = positions.length;
        return positions;
      },
    }, {
      title: {
        text: 'Specific Gravity'
      },

      labels: {
        format: '{value:,.3f}'
      },

      tickPositioner: function () {
        var positions = [],
        incrementNum = TickAmountValue - 1,
        maxTick = this.dataMax,
        tick = this.dataMin,
        increment = (maxTick - this.dataMin) / incrementNum;

        if (this.dataMax !== null && this.dataMin !== null) {
          for (let i = 0; i <= incrementNum; i++) {
            positions.push(tick),
            tick += increment;
          }
        }
        return positions;
      },

      opposite: true
    }],

    series: graph_data.series,
  });
}