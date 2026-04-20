// async function fetchLiveData() {
//     fetch('/live/data')
//         .then(response => response.json())
//         .then(data => {
//         })
//         .catch(error => {
//             console.error("Failed to fetch live data:", error);
//         });
// }

function renderPage(data) {
  // most recent category
  document.getElementById("recent").textContent = data.recent;

  // items today
  document.getElementById("today_count").textContent = data.today_count;

  // hourly average
  const chart_data = [{
      x: data.xs[0],
      y: data.ys[0],
      type:"bar",
      orientation:"v",
  }];
  const layout = {
      title:"Responsible refuse by hour",
      xaxis:{
          range:[-1,25],
          title:"Time of day"
      },
      yaxis:{
          title:"Items disposed of"
      }
  };
  Plotly.newPlot("hourlyAverage", chart_data, layout);

  // Update timestamp to current time
  const now = new Date();
  const options = { 
    weekday: 'long', 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  };
  const timestamp = now.toLocaleDateString(undefined, options);
  document.getElementById("timestamp").textContent = `Last updated: ${timestamp}`;
}

async function fetchLiveData() {
  try {
    const response = await fetch('/live/data');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json(); 
    renderPage(data);
  } catch (error) {
    console.error("Failed to fetch live data:", error);
  }
}

fetchLiveData();
setInterval(fetchLiveData, 5000);
