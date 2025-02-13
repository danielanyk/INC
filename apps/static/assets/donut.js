function bruh(){
  const path = window.location.pathname;  
  
  var batchID = path.split('/')[2];

  if (path=="/" || path=="/index"){
    batchID = bID;
  }
  
  
  fetch(`/update_image_table/${batchID}`)
    .then(response => response.json())
    .then(data => {
      const defectsCount = {
        'Mild': 0,
        'Normal': 0,
        'Severe': 0,
        'Very Severe': 0
      };

      data.forEach(item => {
        item.severity.forEach(sev => {
          const severityLabel = getSeverityLabel(sev);
          defectsCount[severityLabel] += 1;
        })
      });
      if (Object.values(defectsCount).every(val => val === 0))
        {
          
        }


  const getChartOptions = () => {
    let colors = {}
    let fontFamily = 'Inter, sans-serif'

    if (document.documentElement.classList.contains('dark')) {
      colors = {
        primary: '#1A56DB',
        secondary: '#FDBA8C',
        tertiary: '#16BDCA',
        quaternary: '#E74694',
        labelColor: '#FFFFFF',
        borderColor: '#374151'
      }
    } else {
      colors = {
        primary: '#1A56DB',
        secondary: '#FDBA8C',
        tertiary: '#16BDCA',
        quaternary: '#E74694',
        labelColor: '#6B7280',
        borderColor: '#F3F4F6'
      }
    }

    return {
      series: Object.values(defectsCount),
      colors: [colors.primary, colors.tertiary, colors.secondary, colors.quaternary],
      chart: {
        height: 400,
        width: 400,
        type: 'donut',
        fontFamily: fontFamily,
        foreColor: colors.labelColor
      },
      stroke: {
        colors: ['transparent'],
        lineCap: '',
      },
      plotOptions: {
        pie: {
          donut: {
            labels: {
              show: true,
              name: {
                show: true,
                fontFamily: fontFamily,
                offsetY: 20,
              },
              total: {
                showAlways: true,
                show: true,
                label: 'Detected Defects',
                fontFamily: fontFamily,
                formatter: function(w) {
                  const sum = w.globals.seriesTotals.reduce((a, b) => a + b, 0);

                  return sum
                },
              },
              value: {
                show: true,
                fontFamily: fontFamily,
                offsetY: -20,
                formatter: function(value) {
                  return value 
                },
              },
            },
            size: '80%',
          },
        },
      },
      grid: {
        padding: {
          top: -2,
        },
      },
      labels: ['Mild', 'Normal', 'Severe', 'Very Severe'],
      dataLabels: {
        enabled: false,
      },
      legend: {
        position: 'bottom',
        fontFamily: fontFamily,
        labels: {
          colors: [colors.labelColor]
        }
      },
      yaxis: {
        labels: {
          formatter: function(value) {
            return value 
          },
        },
      },
      xaxis: {
        labels: {
          formatter: function(value) {
            return value 
          },
        },
        axisTicks: {
          show: false,
        },
        axisBorder: {
          show: false,
        },
      },
    }
  }
  
  

  if (document.getElementById('donut-chart') && typeof ApexCharts !== 'undefined') {
    var chart = new ApexCharts(document.getElementById('donut-chart'), getChartOptions())
    chart.render()

    // init again when toggling dark mode
    document.addEventListener('dark-mode', function() {
      chart.updateOptions(getChartOptions())
    })

  }
})
}

function update(){
  const path = window.location.pathname;  
  
  var batchID = path.split('/')[2];
  if (path=="/" || path=="/index"){
    batchID = bID;
  }

  fetch(`/update_image_table/${batchID}`)
    .then(response => response.json())
    .then(data => {
      const defectsCount = {
        'Mild': 0,
        'Normal': 0,
        'Severe': 0,
        'Very Severe': 0
      };

      data.forEach(item => {
        item.severity.forEach(sev => {
          const severityLabel = getSeverityLabel(sev);
          defectsCount[severityLabel] += 1;
        })
      });
      if (Object.values(defectsCount)==[0,0,0,0])
        {
          
        }

  });


}
document.addEventListener('DOMContentLoaded', function() {
  bruh();
  update();
  setInterval(update, 5000);
});

function getSeverityLabel(severity) {
  if (severity < 1) {
    return 'Mild';
  }
  switch (severity) {
    case 1:
      return 'Mild';
    case 2:
      return 'Normal';
    case 3:
      return 'Severe';
    default:
      return 'Very Severe';
  }
}