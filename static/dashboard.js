// Dashboard JS for Neon Dark Theme

// Load Chart.js from CDN dynamically
const loadChartJs = () => {
  return new Promise((resolve, reject) => {
    if (window.Chart) {
      resolve();
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Failed to load Chart.js'));
    document.head.appendChild(script);
  });
};

const initBarChart = (ctx) => {
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['A01', 'A02', 'A03'],
      datasets: [{
        label: 'Dataset 1',
        data: [65, 59, 80],
        backgroundColor: ['#ff4d6d', '#7f5af0', '#3a86ff'],
        borderRadius: 5,
        barPercentage: 0.5,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: { enabled: true }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: '#53354a' },
          ticks: { color: '#eaeaea' }
        },
        x: {
          grid: { display: false },
          ticks: { color: '#eaeaea' }
        }
      }
    }
  });
};

const initCircularProgress = (element, percent, color) => {
  const circle = element.querySelector('.progress');
  const radius = circle.r.baseVal.value;
  const circumference = 2 * Math.PI * radius;
  circle.style.strokeDasharray = circumference;
  const offset = circumference - (percent / 100) * circumference;
  circle.style.strokeDashoffset = offset;
  circle.style.stroke = color;
};

const setupSidebarToggle = () => {
  const sidebar = document.querySelector('.sidebar');
  const toggleBtn = document.querySelector('.sidebar-toggle');
  if (!toggleBtn) return;
  toggleBtn.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
  });
};

document.addEventListener('DOMContentLoaded', async () => {
  try {
    await loadChartJs();
    const barCtx = document.getElementById('bar-chart').getContext('2d');
    initBarChart(barCtx);

    // Initialize circular progress bars
    document.querySelectorAll('.circular-progress').forEach((el) => {
      const percent = parseInt(el.dataset.percent, 10) || 0;
      const color = el.dataset.color || '#ff4d6d';
      initCircularProgress(el, percent, color);
    });

    setupSidebarToggle();
  } catch (error) {
    console.error('Error initializing dashboard:', error);
  }
});
