document.addEventListener('DOMContentLoaded', function() {

  fetch('get_defect_count')
  .then(response => response.json())
  .then(data => {
    const severityCounts = {
      1: 0,
      2: 0,
      3: 0,
    };

    data.forEach(defect => {
      severityCounts[defect.Severity] += defect.Count;
    });

    renderChart(severityCounts, data);
  })
  .catch((error) => {
    console.error('Error:', error);
  });

  function renderChart(severityCounts, dataset) {
    const chartOptions = getChartOptions(severityCounts, dataset);

    if (document.getElementById('donut-chart') && typeof ApexCharts !== 'undefined') {
      const chart = new ApexCharts(document.getElementById('donut-chart'), chartOptions);
      chart.render();


      // init again when toggling dark mode
      document.addEventListener('dark-mode', function() {
        chart.updateOptions(getChartOptions(severityCounts));
      });

      // Handle checkbox change event
      const checkboxes = document.querySelectorAll('#donutdefects input[type="checkbox"]');
      checkboxes.forEach((checkbox) => {
        checkbox.addEventListener('change', (event) => handleCheckboxChange(event, chart, severityCounts, dataset));
      });
    }
  }

  function getChartOptions(severityCounts, dataset) {
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
      series: [severityCounts[1], severityCounts[2], severityCounts[3]],
      colors: [colors.primary, colors.tertiary, colors.secondary],
      chart: {
        height: 400,
        width: '100%',
        type: 'donut',
        fontFamily: fontFamily,
        foreColor: colors.labelColor,
        events: {
          dataPointSelection: (event, chartContext, config) => { 
            const severitySelect = document.getElementById('severity');
            const selectedLabel = config.w.config.labels[config.dataPointIndex];
            // alert(selectedLabel);
            const label = {
              'Low': 1,
              'Medium': 2,
              'Severe': 3,
            }
            const selectedValue = label[selectedLabel];
            severitySelect.value = selectedValue;
            document.getElementById('apply').click();
          }
        }
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
      labels: ['Low', 'Medium', 'Severe'],
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

  document.querySelectorAll('#donutdefects input[type="checkbox"]').forEach(checkbox => {
    checkbox.addEventListener('change', function() {
        handleDonutCheckboxChange(this);
    });
  });

  // Function to handle checkbox change event for donut chart
  function handleDonutCheckboxChange(checkbox) {
    const selectedDefect = checkbox.value;
    const dropdown2Checkbox = document.querySelector(`#dropdown2 input[value="${selectedDefect}"]`);
    
    if (checkbox.checked) {
        dropdown2Checkbox.checked = true;
    } else {
        dropdown2Checkbox.checked = false;
    }
  }

  // Main function to handle checkbox change event
  function handleCheckboxChange(event, chart, severityCounts, dataset) {
    const checkboxes = document.querySelectorAll('#donutdefects input[type="checkbox"]');
    const selectedDefects = Array.from(checkboxes).filter(checkbox => checkbox.checked).map(checkbox => checkbox.value);
    
    if (selectedDefects.length > 0) {
        const counts = [0, 0, 0];
        selectedDefects.forEach(selectedDefect => {
            document.getElementById('apply').click(); 
            const matchingDefects = dataset.filter(defect => defect.Defect === selectedDefect);
            matchingDefects.forEach(defect => {
                counts[defect.Severity - 1] += defect.Count;
            });
        });
        chart.updateSeries(counts);
    } else {
        const dropdown2Checkboxes = document.querySelectorAll('#dropdown2 input[type="checkbox"]');
        dropdown2Checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        chart.updateSeries([severityCounts[1], severityCounts[2], severityCounts[3]]);
    }
  }

});
