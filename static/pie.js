document.addEventListener("DOMContentLoaded", function() {
    const ctx = document.getElementById('myPieChart').getContext('2d');

    // Generate a unique color for each slice of the pie
    const generateColors = (numColors) => {
        const colors = [];
        for (let i = 0; i < numColors; i++) {
            // Random RGBA color with 0.6 opacity for background color
            const color = `rgba(${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, 0.6)`;
            colors.push(color);
        }
        return colors;
    };

    // Generate a color palette based on the number of labels
    const backgroundColors = generateColors(chartData.labels.length);
    const borderColors = backgroundColors.map(color => color.replace('0.6', '1'));  // Change opacity to 1 for borders

    // Create the pie chart using Chart.js
    const myPieChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: chartData.labels,       // Dynamic labels from Flask
            datasets: [{
                data: chartData.values,     // Dynamic values from Flask
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top'
                }
            }
        }
    });
});

