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
	  
	  labels: {
        format: '{value:,.3f}'
	  },
	  
	  tickPositioner: function () {
        var positions = [],
        maxTick = this.dataMax * 1000,
        step = (maxTick - this.dataMin * 1000) / (TickAmountValue - 1),
        tick = this.dataMin * 1000 - 1;

        if (this.dataMax !== null && this.dataMin !== null) {
          while (tick <= maxTick) {
            positions.push(tick/1000);
            tick += step;
          }
        }
        return positions;
	  },
	  
      opposite: true
  }],
  
  series: graph_data.series,
});
