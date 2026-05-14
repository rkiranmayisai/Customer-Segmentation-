document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('csvFileInput');
    const statsGrid = document.getElementById('statsGrid');
    const chartsSection = document.getElementById('chartsSection');
    
    let segmentChartInstance = null;
    let contractChartInstance = null;

    fileInput.addEventListener('change', async function(e) {
        const file = e.target.files[0];
        if (file) {
            // Update UI to show parsing
            document.querySelector('.upload-content h3').innerText = 'AI Analysis in progress...';
            document.querySelector('.upload-content i').className = 'fa-solid fa-spinner fa-spin';
            
            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('http://localhost:8000/process', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Analysis failed');
                }

                const result = await response.json();
                
                document.querySelector('.upload-content h3').innerText = file.name;
                document.querySelector('.upload-content i').className = 'fa-solid fa-file-csv';
                
                displayResults(result);
            } catch (err) {
                alert('Error processing data: ' + err.message);
                document.querySelector('.upload-content h3').innerText = 'Upload Customer CSV Data';
                document.querySelector('.upload-content i').className = 'fa-solid fa-cloud-arrow-up';
            }
        }
    });

    function displayResults(data) {
        // Reveal dashboard elements
        statsGrid.style.display = 'grid';
        chartsSection.style.display = 'grid';

        // Update Stats UI
        document.getElementById('totalCustomers').innerText = data.stats.totalCustomers.toLocaleString();
        document.getElementById('churnRate').innerText = data.stats.churnRate + '%';
        document.getElementById('avgTenure').innerText = data.stats.avgTenure + ' mo';
        document.getElementById('avgCharge').innerText = '$' + data.stats.avgCharge;

        // Render Charts
        renderSegmentChart(data.segments);
        renderContractChart(data.contracts);
    }


    function renderSegmentChart(segments) {
        const ctx = document.getElementById('segmentChart').getContext('2d');
        if (segmentChartInstance) segmentChartInstance.destroy();

        segmentChartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(segments),
                datasets: [{
                    data: Object.values(segments),
                    backgroundColor: [
                        'rgba(245, 158, 11, 0.85)',  // Champions (Amber)
                        'rgba(232, 121, 249, 0.85)', // Loyalists (Fuchsia)
                        'rgba(74, 222, 128, 0.85)',  // New Customers (Green)
                        'rgba(251, 146, 60, 0.85)'   // At Risk (Orange)
                    ],
                    borderColor: 'rgba(30, 41, 59, 1)',
                    borderWidth: 4,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: '#fff1f2', font: { family: "'Outfit', sans-serif" } }
                    }
                }
            }
        });
    }

    function renderContractChart(contracts) {
        const ctx = document.getElementById('contractChart').getContext('2d');
        if (contractChartInstance) contractChartInstance.destroy();

        // Filter out empty contracts if any
        let labels = Object.keys(contracts).filter(k => k && k !== 'undefined');
        let data = labels.map(k => contracts[k]);

        contractChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Number of Customers',
                    data: data,
                    backgroundColor: 'rgba(245, 158, 11, 0.85)',
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(245, 158, 11, 0.08)' },
                        ticks: { color: '#fca5a5', font: { family: "'Outfit', sans-serif" } }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#fca5a5', font: { family: "'Outfit', sans-serif" } }
                    }
                }
            }
        });
    }
});
