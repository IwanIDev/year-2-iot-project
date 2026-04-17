const dropdown = document.getElementById("timeFrame");
dropdown.onchange = function(){init();}

async function init(){
    fetch('dashboard/data?time='+dropdown.value)
        .then(response => response.json())
        .then(data => {
            // recycling by type
            var chart_data = [{
                labels: data.xs[0],
                values: data.ys[0],
                type:'pie',
            }];
            var layout = {title:'Responsible refuse by type'};
            Plotly.newPlot("typeRatio",chart_data,layout);

            // all types on days this week
            chart_data = [{
                x: data.xs[1],
                y: data.ys[1],
                mode:"lines",
                type:"scatter"
            }];
            layout = {
                title:"Responsible refuse by day",
                xaxis:{
                    range:[-1,chart_data[0].x.length],
                    title:"Days"
                },
                yaxis:{
                    title:"Total items"
                }
            };
            Plotly.newPlot("dailyTrend", chart_data, layout);

            // hourly average
            chart_data = [{
                x: data.xs[2],
                y: data.ys[2],
                type:"bar",
                orientation:"v",
            }];
            layout = {
                title:"Hourly averages",
                xaxis:{
                    range:[-1,24],
                    title:"Time of day"
                },
                yaxis:{
                    title:"Total items"
                }
            };
            Plotly.newPlot("hourlyAverage", chart_data, layout);

            // history
            chart_data = [{
                type: "table",
                "header":{
                    values: [
                        ["<b>Time</b>"],
                        ["<b>Category</b>"]
                    ],
                    fill: {color:"#107AB0"}
                },
                "cells":{
                    values: data.table_data,
                }
            }];
            layout = {
                title:"History"
            };
            Plotly.newPlot("history",chart_data,layout)
        })
}

init();