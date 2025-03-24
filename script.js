let charts = {
    bp: null,
    oxygen: null,
    pulse: null
};

function initializeCharts() {
    const chartConfig = {
        type: 'line',
        options: {
            responsive: true,
            animation: {
                duration: 1000
            },
            plugins: {
                legend: {
                    labels: {
                        font: {
                            family: "'Segoe UI', sans-serif",
                            size: 12
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                }
            }
        }
    };

    charts.bp = new Chart(document.getElementById('bpChart'), {
        ...chartConfig,
        data: {
            labels: [],
            datasets: [{
                label: 'Historical',
                data: [],
                borderColor: '#6B46C1',
                backgroundColor: 'rgba(107, 70, 193, 0.1)',
                tension: 0.4,
                fill: true
            }, {
                label: 'Forecast',
                data: [],
                borderColor: '#F687B3',
                borderDash: [5, 5],
                tension: 0.4
            }]
        }
    });

    charts.oxygen = new Chart(document.getElementById('oxygenChart'), {
        ...chartConfig,
        data: {
            labels: [],
            datasets: [{
                label: 'Historical',
                data: [],
                borderColor: '#4299E1',
                backgroundColor: 'rgba(66, 153, 225, 0.1)',
                tension: 0.4,
                fill: true
            }, {
                label: 'Forecast',
                data: [],
                borderColor: '#F687B3',
                borderDash: [5, 5],
                tension: 0.4
            }]
        }
    });

    charts.pulse = new Chart(document.getElementById('pulseChart'), {
        ...chartConfig,
        data: {
            labels: [],
            datasets: [{
                label: 'Historical',
                data: [],
                borderColor: '#48BB78',
                backgroundColor: 'rgba(72, 187, 120, 0.1)',
                tension: 0.4,
                fill: true
            }, {
                label: 'Forecast',
                data: [],
                borderColor: '#F687B3',
                borderDash: [5, 5],
                tension: 0.4
            }]
        }
    });
}

function updateCharts(data) {
    const vitals = ['BP', 'Oxygen_Level', 'Pulse'];
    const chartKeys = ['bp', 'oxygen', 'pulse'];

    vitals.forEach((vital, index) => {
        const chartData = data.vital_predictions[vital];
        const chart = charts[chartKeys[index]];

        // Generate forecast timestamps
        const lastTimestamp = chartData.timestamps[chartData.timestamps.length - 1];
        const forecastLabels = Array(chartData.forecast.length).fill(lastTimestamp);

        // Update chart data
        chart.data.labels = [...chartData.timestamps, ...forecastLabels];
        chart.data.datasets[0].data = [...chartData.historical, null];
        chart.data.datasets[1].data = [...Array(chartData.historical.length).fill(null), ...chartData.forecast];
        chart.update();
    });
}

async function updateVitals() {
    try {
        const response = await fetch('/update_vitals?patient_id=default');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        updateCharts(data);
    } catch (error) {
        console.error('Error updating vitals:', error);
    }
}

function displayHealthRisk(result) {
    const resultContainer = document.getElementById('resultContainer');
    resultContainer.style.display = 'block';

    let riskColor;
    switch(result.health_risk) {
        case "Low":
            riskColor = '#48BB78';
            break;
        case "Medium":
            riskColor = '#ECC94B';
            break;
        case "High":
            riskColor = '#F56565';
            break;
    }

    document.getElementById('riskLevel').innerHTML = `
        <h3 style="color: ${riskColor}; font-size: 1.5rem; margin-bottom: 1rem;">
            ${result.health_risk} Risk Level
        </h3>
        <div style="margin-bottom: 1.5rem;">
            <p style="margin-bottom: 0.5rem;">${result.nutrition_plan.general_advice}</p>
            <p style="margin-bottom: 0.5rem;">${result.nutrition_plan.calories_recommendation}</p>
            <p style="margin-bottom: 0.5rem;">${result.nutrition_plan.hydration}</p>
            <p>${result.nutrition_plan.exercise_recommendation}</p>
        </div>
    `;
}

function displayNutritionPlan(result) {
    document.getElementById('nutritionDetails').innerHTML = `
        <h3 style="margin-bottom: 1rem;">Recommended Tamil Nadu Meal Plan</h3>
        ${Object.entries(result.nutrition_plan.meal_plan)
            .map(([meal, items]) => `
                <div class="meal-section">
                    <h4 style="color: #4A5568;">${meal.charAt(0).toUpperCase() + meal.slice(1)}</h4>
                    <div class="meal-items">
                        ${items.map(item => `
                            <span class="meal-item">${item}</span>
                        `).join('')}
                    </div>
                </div>
            `).join('')}
    `;
}

async function handleFormSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    // Convert string values to numbers
    for (let key in data) {
        if (key !== 'Gender') {
            data[key] = Number(data[key]);
        }
    }

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        // Display results
        displayHealthRisk(result);
        displayNutritionPlan(result);
        
        // Update charts with new predictions
        updateCharts(result);

    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while processing your request. Please try again.');
    }
}

// Initialize everything when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize charts
    initializeCharts();
    
    // Add form submit handler
    const form = document.getElementById('healthForm');
    form.addEventListener('submit', handleFormSubmit);
    
    // Handle obesity toggle
    const obesityToggle = document.getElementById('obesityToggle');
    const toggleLabel = document.getElementById('toggleLabel');
    const obesityLevelContainer = document.getElementById('obesityLevelContainer');
    const obesityLevel = document.getElementById('obesityLevel');

    obesityToggle.addEventListener('change', function() {
        toggleLabel.textContent = this.checked ? 'Yes' : 'No';
        obesityLevelContainer.style.display = this.checked ? 'block' : 'none';
        obesityLevel.required = this.checked;
    });
});