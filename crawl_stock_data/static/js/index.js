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
    if (!$.fn.DataTable.isDataTable('#profitTable')) {
        $('#profitTable').DataTable({
            "searching": false,
            "paging": false,
            "info": false,
            "ordering": false,
            "data": data,
            "columns": [
                {title: "Symbol", data: "symbol"}, // Symbol column
              {
                  title:"Actual profit", data:"profit_actual", redner: function(data, type, row) {
                      return data;
                  }
              }, // Actual Profit column (right-aligned)
              {
                  title:"Predicted profit", data:"profit_model", redner: function(data, type, row) {
                      return data;
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
    } else {
        $("#profitTable").DataTable().clear().rows.add(data).draw();
    }

}

function initDatatableStockData(data) {
    $("#symbol-table").DataTable({
        "searching": false,
        "paging": false,
        "info": false,
        "ordering": false,
        "data": data,
        "columns": [
            {title: "#", data: "symbol", render: function(data, type, row, meta) {
                return meta.row + 1;
            }, width: "10%"}, // Symbol column
            {title: "Symbol", data: "symbol", width: "30"}, // Symbol column
            {title: "Company Name", data: "name", width: "50%"}, // Company Name column
        ],
        "columnDefs": [{
          "targets": "_all",
          "className": "dt-center"
        }],
        "language": {
          "emptyTable": "No data available",
          "zeroRecords": "No matching records found"
        },
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
        let temp_data = data.map(item => {
            return{
                time: item.date,
                open: parseFloatAndFix(item.open),
                high: parseFloatAndFix(item.high),
                low: parseFloatAndFix(item.low),
                close: parseFloatAndFix(item.close),
                macd: item.MACD_12_26_9,
                macds: item.MACDs_12_26_9,
            }

        })

        render_chart_with_macd(data);
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

function render_chart_with_macd(data) {
    // Parse date strings into JavaScript Date objects
    data.forEach(item => {
        item.date = new Date(item.date).getTime();
    });

    // Extract MACD and Signal Line data from the input data
    const macdData = data.map(item => [item.date, item.MACD_12_26_9]);
    const signalLineData = data.map(item => [item.date, item.MACDs_12_26_9]);
    const closeData = data.map(item => [item.date, item.close]);

    const buySignalData = data
        .filter(item => item.Buy_Signal)
        .map(item => ({
            x: item.date,
            y: item.close,
        }));

    const sellSignalData = data
        .filter(item => item.Sell_Signal)
        .map(item => ({
            x: item.date,
            y: item.close,
        }));

    console.log(buySignalData)
    // Create the chart with two y-axes (panels)
    Highcharts.stockChart('lineChart', {
        chart: {
            // backgroundColor: '#222',
        },
        title: {
            text: 'NYSE Stock Chart with MACD and Signals',
            style: {
                color: '#C3BCDB',
            },
        },
        rangeSelector: {
            selected: 1,
        },
        yAxis: [{
            title: {
                text: 'Closing Price',
                style: {
                    color: '#C3BCDB',
                },
            },
            labels: {
                style: {
                    color: '#C3BCDB',
                },
            },
            height: '70%', // Set the height of the first panel
        }, {
            title: {
                text: 'MACD',
                style: {
                    color: '#C3BCDB',
                },
            },
            labels: {
                style: {
                    color: '#C3BCDB',
                },
            },
            top: '75%', // Position the second panel below the first one
            height: '25%', // Set the height of the second panel
            offset: 0, // Align the second panel with the first one
        }],
        annotations: [{
            labels: [{
                point: {
                    xAxis: 0, // x-axis for the annotation label
                    yAxis: 0, // y-axis for the annotation label
                    x: data[0].date, // x-coordinate (date)
                    y: data[0].close, // y-coordinate (close price)
                },
                text: 'Close Price',
                color: 'green', // Label text color
                backgroundColor: 'white', // Label background color
                borderColor: 'green', // Label border color
                borderWidth: 1, // Label border width
                shape: 'rect', // Label shape (rectangle)
                padding: 5, // Label padding
            }, {
                point: {
                    xAxis: 0, // x-axis for the annotation label
                    yAxis: 1, // y-axis for the annotation label
                    x: data[0].date, // x-coordinate (date)
                    y: data[0].MACD_12_26_9, // y-coordinate (MACD value)
                },
                text: 'MACD (Blue Line)',
                color: 'blue',
                backgroundColor: 'white',
                borderColor: 'blue',
                borderWidth: 1,
                shape: 'rect',
                padding: 5,
            }, {
                point: {
                    xAxis: 0, // x-axis for the annotation label
                    yAxis: 1, // y-axis for the annotation label
                    x: data[0].date, // x-coordinate (date)
                    y: data[0].MACDs_12_26_9, // y-coordinate (Signal line value)
                },
                text: 'Signal Line (Red Line)',
                color: 'red',
                backgroundColor: 'white',
                borderColor: 'red',
                borderWidth: 1,
                shape: 'rect',
                padding: 5,
            }]
        }],
        series: [{
            type: 'line',
            name: 'Closing Price',
            data: closeData,
            yAxis: 0, // Use the first y-axis (panel) for closing price
            tooltip: {
                valueDecimals: 2, // Number of decimals in tooltip when hovering over a data point
                valueSuffix: ' USD', // Label for the tooltip when hovering over a data point
            }
        }, {
            type: 'line',
            name: 'MACD',
            data: macdData,
            yAxis: 1, // Use the second y-axis (panel) for MACD
            color: 'blue',
            lineWidth: 2,
            tooltip: {
                valueSuffix: ' MACD', // Add a unit label to the tooltip

            },
        }, {
            type: 'line',
            name: 'Signal Line',
            data: signalLineData,
            yAxis: 1, // Use the second y-axis (panel) for the signal line
            color: 'red',
            lineWidth: 2,
            tooltip: {
                valueSuffix: ' Signal', // Add a unit label to the tooltip
            },
        }, {
            type: 'scatter',
            name: 'Buy Signals',
            data: buySignalData,
            marker: {
                symbol: 'triangle',
                fillColor: 'green',
                lineColor: 'green', // Border color of the marker
                radius : 8
            },
            yAxis: 0, // Use the first y-axis (panel) for buy signals
            tooltip: {
                pointFormat: '<span style="color:green">●</span> Buy Signal<br>',
            },
        }, {
            type: 'scatter',
            name: 'Sell Signals',
            data: sellSignalData,
            marker: {
                symbol: 'triangle-down',
                fillColor: 'red',
                lineColor: 'red',
                radius : 8
            },
            yAxis: 0, // Use the first y-axis (panel) for sell signals
            tooltip: {
                pointFormat: '<span style="color:red">●</span> Sell Signal<br>',
            },
        }],
    });
}