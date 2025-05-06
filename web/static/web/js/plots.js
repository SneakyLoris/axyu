const pie_data = JSON.parse(document.getElementById('pie-data').textContent);

var layout = {
  height: 400,
  width: 500
};

Plotly.newPlot('piePlot', pie_data, layout);



