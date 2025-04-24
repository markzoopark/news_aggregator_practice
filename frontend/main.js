const apiBase = 'http://localhost:8000';
const filterSelect = document.getElementById('filter-select');
const tableBody = document.querySelector('#articles-table tbody');
const ctx = document.getElementById('sentiment-chart').getContext('2d');
let allArticles = [];
let STUDENT_ID;
async function loadConfig() {
	const res = await fetch('http://localhost:8000/info');
	const json = await res.json();
	STUDENT_ID = json.student_id;
}
// Викличемо loadConfig() перед loadData()
window.addEventListener('load', async () => {
	await loadConfig();
	await loadData();
});

async function loadData() {
	// Спочатку фетчимо новини та аналіз
	await fetch(`${apiBase}/fetch/${STUDENT_ID}`, { method: 'POST' });
	const res = await fetch(`${apiBase}/analyze/${STUDENT_ID}`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
	});

	const json = await res.json();
	allArticles = json.articles.map((a) => ({
		...a,
		date: new Date(a.published),
	}));
	render();
}

function render() {
	const filter = filterSelect.value;
	const filtered = allArticles.filter(
		(a) => filter === 'all' || a.sentiment === filter
	);
	// Оновлюємо таблицю
	tableBody.innerHTML = filtered
		.sort((a, b) => b.date - a.date)
		.map(
			(a) => `
      <tr>
        <td>${a.date.toLocaleString()}</td>
        <td>${a.sentiment}</td>
        <td><a href="${a.link}" target="_blank">${a.title}</a></td>
      </tr>
    `
		)
		.join('');
	// Оновлюємо діаграму
	const counts = { positive: 0, neutral: 0, negative: 0 };
	filtered.forEach((a) => counts[a.sentiment]++);
	chart.data.datasets[0].data = [
		counts.positive,
		counts.neutral,
		counts.negative,
	];
	chart.update();
}

// Ініціалізація Chart.js
const chart = new Chart(ctx, {
	type: 'pie',
	data: {
		labels: ['Позитивні', 'Нейтральні', 'Негативні'],
		datasets: [{ data: [0, 0, 0] }],
	},
	options: {
		responsive: true,
		maintainAspectRatio: true, // або false, якщо хочете ігнорувати початкове співвідношення
		aspectRatio: 2, // співвідношення width/height = 2 (наприклад 600×300)
		plugins: {
			legend: { position: 'top' },
		},
	},
});

filterSelect.addEventListener('change', render);
