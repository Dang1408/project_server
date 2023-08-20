function initDateTimepicker() {
    // Set the format 'yyyy-mm-dd'
    var dateFormat = 'YYYY-MM-DD';

    // Calculate the date 2 years before today
    var twoYearsAgo = moment().subtract(2, 'years').format(dateFormat);

    // Set the date for #from-date input
    $("input[name=from-date]").val(twoYearsAgo);

    // Set the date for #to-date input as today
    var today = moment().format(dateFormat);
    $("input[name=to-date]").val(today);

    // Initialize the datetimepickers
    $("#to-date").datetimepicker({
        format: dateFormat,
        defaultDate: today,
        icons: {
            time: "fa fa-clock-o",
            date: "fa fa-calendar",
            up: "fa fa-chevron-up",
            down: "fa fa-chevron-down",
            previous: 'fa fa-chevron-left',
            next: 'fa fa-chevron-right',
            today: 'fa fa-screenshot',
            clear: 'fa fa-trash',
            close: 'fa fa-remove'
        }
    });

    $("input[name=from-date]").datetimepicker({
        format: dateFormat,
        defaultDate: twoYearsAgo,
        icons: {
            time: "fa fa-clock-o",
            date: "fa fa-calendar",
            up: "fa fa-chevron-up",
            down: "fa fa-chevron-down",
            previous: 'fa fa-chevron-left',
            next: 'fa fa-chevron-right',
            today: 'fa fa-screenshot',
            clear: 'fa fa-trash',
            close: 'fa fa-remove'
        }
    });
}

function initDatatableCompareProfit(data) {
    $('#profitTable').DataTable({
        "searching": false,
        "paging": false,
        "info": false,
        "ordering": false,
        "data": [{
          "symbol": "AAPL",
          "profit_actual": 11.91000366210929,
          "profit_model": 11.91000366210929
        }],
        "columns": [
            {title: "Symbol", data: "symbol"}, // Symbol column
          {
              title:"Actual profit", data:"profit_actual", redner: function(data, type, row) {
                  return parseFloatAndFix(data)
              }
          }, // Actual Profit column (right-aligned)
          {
              title:"Predicted profit", data:"profit_model", redner: function(data, type, row) {
                  return parseFloatAndFix(data)
              }
          } // Predicted Profit column (right-aligned)
        ],
        "columnDefs": [{
          "targets": "_all",
          "className": "dt-center"
        }],
        "language": {
          "emptyTable": "No data available",
          "zeroRecords": "No matching records found"
        },
        "caption": "Comparison of Profit using MACD Strategy (Actual vs. Predicted)"
      });
}

function render_chart(data, volume) {
    Highcharts.stockChart('lineChart', {
        rangeSelector: {
            selected: 1
        },
        title: {
            text: 'AAPL Stock Price'
        },
        series: [
            {
                type: 'candlestick',
                name: 'Stock Prices',
                data: data
            },
            {
                type: 'column', // Column type for volume series
                name: 'Volume',
                data: volume,
                yAxis: 1 // Use the secondary y-axis for volume
            },
            {
                name: 'Moving Average',
                type: 'sma', // Simple Moving Average
                linkedTo: 'candlestick', // The data series to which this indicator is linked
                params: {
                    period: 10 // Period for the moving average (e.g., 10 days)
                }
            }
        ],
        yAxis: [
            { // Primary y-axis for candlestick and SMA
                labels: {
                    align: 'right',
                    x: -3
                },
                title: {
                    text: 'OHLC'
                },
                height: '60%',
                lineWidth: 2
            },
            { // Secondary y-axis for volume
                labels: {
                    align: 'right',
                    x: -3
                },
                title: {
                    text: 'Volume'
                },
                top: '65%',
                height: '35%',
                offset: 0,
                lineWidth: 2
            }
        ]
    });
}

function render_predicted_chart(currentData, predictedData) {
    // Create the chart
    Highcharts.chart('chart-example', {
        title: {
            text: 'Stock Prices - Current vs Predicted'
        },
        xAxis: {
            type: 'datetime',
            title: {
                text: 'Date'
            }
        },
        yAxis: {
            title: {
                text: 'Close Price'
            }
        },
        series: [
            {
                name: 'Current Close Price',
                data: currentData,
                type: 'line'
            },
            {
                name: 'Predicted Close Price',
                data: predictedData,
                type: 'line'
            }
        ]
    });
}

function parseFloatAndFix(value) {
    return parseFloat(parseFloat(value).toFixed(2));
}

function draw_chart_with_data(symbol, date_start, date_end) {
    $.ajax({
        url: 'http://127.0.0.1:8000/api/stock/drawl-chart',
        data : JSON.stringify({
            "symbol" : symbol,
            "date_start" : date_start,
            "date_end" : date_end
        }),
        type: 'POST',
        dataType: 'json',
        contentType: 'application/json',
    })
    .done(function(data){
        var temp_data = data.map(item => {
            return [parseInt(item.date), parseFloatAndFix(item.open), parseFloatAndFix(item.high),
                    parseFloatAndFix(item.low), parseFloatAndFix(item.close)]
        })

        render_chart_with_buy_sell_signal(temp_data);
        $("#line-chart").show();
        $("#show-before-searching").show();
    })
    .fail(function(data){
        Swal.fire({
            icon: 'error',
            title: 'Oops...',
            text: data.error,
            footer: '<a href="#">Why do I have this issue?</a>'
          });
    });
}

function addSignal(arg) {
  arg.series.addPoint({
    x: arg.point.x,
    y: arg.direction === 'up' ? arg.point.high - arg.triangleOffset : arg.point.low + arg.triangleOffset,
    marker: {
      symbol: arg.direction === 'up' ? 'triangle' : 'triangle-down',
      fillColor: arg.direction === 'up' ? 'green' : 'red',
      radius: arg.size
    }
  });
}

function render_chart_with_buy_sell_signal(data) {
  Highcharts.stockChart('lineChart', {
    chart: {
      events: {
        load() {
          const chart = this;
          const series = chart.series;
          const macdSeries = series.find((s) => s.options.type === 'macd');

          if (!macdSeries) {
            return;
          }

          const signalSeries = series.find((s) => s.options.type === 'scatter' && s.name === 'Signal');

          if (!signalSeries) {
            return;
          }

          const macdData = macdSeries.yData;
          const signalData = [];

          for (let i = 1; i < macdData.length; i++) {
            const prevMACD = macdData[i - 1];
            const currMACD = macdData[i];
            const prevPoint = macdSeries.points[i - 1];
            const currPoint = macdSeries.points[i];

            if ((prevMACD <= 0 && currMACD > 0) || (prevMACD >= 0 && currMACD < 0)) {
              signalData.push({
                x: currPoint.x,
                y: currMACD > 0 ? currPoint.high - 5 : currPoint.low + 5,
                direction: currMACD > 0 ? 'up' : 'down',
              });
            }
          }

          signalSeries.setData(signalData);
        }
      }
    },

    plotOptions: {
      series: {
        dataGrouping: {
          enabled: false
        }
      }
    },

    series: [
      {
        type: 'candlestick',
        name: 'Stock Data',
          id: 'Stock Data',
        data: data,
      },
      {
        type: 'scatter',
        name: 'Signal',
        marker: {
          symbol: 'triangle',
          fillColor: 'green',
          lineColor: 'black',
          lineWidth: 1,
          radius: 5,
        },
        data: [], // Empty data, will be filled dynamically in the load event
      },
      {
        type: 'macd',
        linkedTo: 'Stock Data', // Change this to 'candlestick'
        params: {
          shortPeriod: 12,
          longPeriod: 26,
          signalPeriod: 9,
          period: 26,
        },
      },
    ],
  });
}
