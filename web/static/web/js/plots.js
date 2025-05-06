var test_data = [{
  values: [19, 26, 55],
  labels: ['Residential', 'Non-Residential', 'Utility'],
  type: 'pie'
}];

var raw_data = JSON.parse(document.getElementById('pie-data')

var pie_data = [{
    values: raw_data.values,
    labels: raw_data.labels,
    type: 'pie'
}];

var layout = {
  height: 400,
  width: 500
};

Plotly.newPlot('piePlot', [{
  values: [19, 26, 55],
  labels: ['Residential', 'Non-Residential', 'Utility'],
  type: 'pie'
}];, layout);

