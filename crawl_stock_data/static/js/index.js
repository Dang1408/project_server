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
                    let transfer_data = data.map(item => [parseInt(item["timestamp"]),
                                                            parseFloatAndFix(item["open"]),
                                                            parseFloatAndFix(item["high"]),
                                                            parseFloatAndFix(item["low"]),
                                                            parseFloatAndFix(item["close"])]);
                    let volume_date = data.map(item => [parseInt(item["timestamp"]),
                                                            parseInt(item["volume"])]);
                    render_chart(transfer_data, volume_date);
                    $("#line-chart").show();
                    $("#show-before-searching").show();
                })
                .fail(function(){
                    Swal.fire({
                        icon: 'error',
                        title: 'Oops...',
                        text: data.error,
                        footer: '<a href="#">Why do I have this issue?</a>'
                      });
                });
        }