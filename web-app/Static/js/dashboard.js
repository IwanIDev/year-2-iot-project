async function init() {
    fetch('/dashboard/data')
        .then(response => response.json())
        .then(data => {
            var chart_data = [{
                labels: data.xs[0],
                values: data.ys[0],
                type:'pie',
            }];
            var layout = {title:'Recycling by type'};
            Plotly.newPlot("typeRatio",chart_data,layout);

            chart_data = [{
                x: data.xs[1],
                y: data.ys[1],
                mode:"lines",
                type:"scatter"
            }];
            layout = {
                title:"Days this week",
                xaxis:{
                    range:[-1,chart_data[0].x.length],
                    title:"Days"
                },
                yaxis:{
                    title:"Total items"
                }
            };
            Plotly.newPlot("dailyTrend", chart_data, layout);
        })
}

init();