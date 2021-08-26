Highcharts.setOptions({
    time: {
        useUTC: false
    }
});
	  
var TickAmountValue = 7;

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
	  tickPositioner: function () {
        var positions = [],
        tick = Math.floor(this.dataMin),
        increment = Math.ceil((this.dataMax - this.dataMin) / 6);

        if (this.dataMax !== null && this.dataMin !== null) {
          for (tick; tick - increment <= this.dataMax; tick += increment) {
            positions.push(tick);
          }
        }
		TickAmountValue = positions.length;
        return positions;
	  },
    }, {
      title: {
        text: 'Specific Gravity'
      },
	  tickAmount: TickAmountValue,
	  tickInterval: 0.01,
      opposite: true
  }],
  
  series: graph_data.series,
});
