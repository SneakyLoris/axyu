var layout = {
  height: 300,
  width: 400
};

const pie_data = JSON.parse(document.getElementById('pie-data').textContent);
Plotly.newPlot('piePlot', pie_data, layout);

var heat_layout = {
  height: 300,
  width: 400,
  title: {
      text: 'Частота изучения слов'
  }
};
const heat_data = JSON.parse(document.getElementById('heat-data').textContent);
Plotly.newPlot('plot2', heat_data, heat_layout);



console.log(document.getElementById('plot2') ? "Элемент найден" : "Элемент НЕ найден");
