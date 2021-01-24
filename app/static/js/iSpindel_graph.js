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
        text: 'Specific Gravity'
      },
      min: 1.0,
      //max: 1.1
      opposite: true
  }],
  
  series: graph_data.series,
});
