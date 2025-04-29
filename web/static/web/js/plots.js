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

