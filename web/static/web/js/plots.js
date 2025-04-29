const bar_ctx = document.getElementById('myChart');
            new Chart(bar_ctx, {
                type: 'bar',
                data: {
                    labels: ['A', 'B', 'C'],
                    datasets: [{
                        label: 'Пример',
                        data: [12, 19, 3],
                    }]
                }
            });

const pie_ctx = document.getElementById('piePlot');
new Chart(pie_ctx, {
    type: 'doughnut',
    data: JSON.parse(document.getElementById('pie-data').textContent)
});


const session_time_ctx = document.getElementById('sessionTimePlot');
new Chart(session_ctx, {
    type: 'line',
    data: JSON.parse(document.getElementById('session-time-data').textContent)
});

const session_count_ctx = document.getElementById('sessionCountPlot');
new Chart(session_ctx, {
    type: 'bar',
    data: JSON.parse(document.getElementById('session-count-data').textContent)
});