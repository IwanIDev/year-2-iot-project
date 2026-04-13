async function init() {
    fetch('/live/data')
        .then(response => response.json())
        .then(data => {
            // most recent category
            document.getElementById("recent").textContent = data.recent;

            // items today
            document.getElementById("today_count").textContent = data.today_count;

            // hourly average
            chart_data = [{
                x: data.xs[0],
                y: data.ys[0],
                type:"bar",
                orientation:"v",
            }];
            layout = {
                title:"Recycling by hour",
                xaxis:{
                    range:[-1,25],
                    title:"Time of day"
                },
                yaxis:{
                    title:"Items recycled"
                }
            };
            Plotly.newPlot("hourlyAverage", chart_data, layout);
        })
}

init();