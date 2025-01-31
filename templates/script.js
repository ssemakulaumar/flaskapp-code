async function fetchVisualization() {
    try {
        const response = await fetch('/api/visualize');
        const data = await response.json();

        if (response.ok) {
            document.getElementById('trade-chart').src = data.image;
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error fetching visualization:', error);
        alert('An error occurred while fetching the visualization.');
    }
}

// Fetch the chart on page load
fetchVisualization();
