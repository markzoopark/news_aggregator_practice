const apiBase = 'http://localhost:8000';
const filterSelect = document.getElementById('filter-select');
const tableBody = document.querySelector('#articles-table tbody');
const ctx = document.getElementById('sentiment-chart').getContext('2d');
let allArticles = [];
let STUDENT_ID;
let chart;

async function loadConfig() {
	try {
		const res = await fetch(`${apiBase}/info`);
		if (!res.ok) {
			console.error('Failed to load config', res.status);
			alert('Не вдалося завантажити конфігурацію студента.');
			return false;
		}
		const json = await res.json();
		STUDENT_ID = json.student_id;
		console.log('STUDENT_ID loaded:', STUDENT_ID);
		return true;
	} catch (error) {
		console.error('Error loading config:', error);
		alert('Помилка завантаження конфігурації студента.');
		return false;
	}
}

async function loadInitialData() {
	console.log('loadInitialData called');
	const configLoaded = await loadConfig();
	if (!configLoaded) {
		return;
	}
	await loadData();
}

async function loadData() {
	console.log('loadData called for STUDENT_ID:', STUDENT_ID);
	const token = localStorage.getItem('token');
	if (!token) {
		console.warn('No token found, cannot load data.');
		return;
	}

	if (!STUDENT_ID) {
		console.error('STUDENT_ID is not set. Cannot load data.');
		alert(
			'Не вдалося визначити ID студента. Спробуйте оновити сторінку або увійти знову.'
		);
		return;
	}

	try {
		console.log(`Fetching news for ${STUDENT_ID}...`);
		const fetchRes = await fetch(`${apiBase}/fetch/${STUDENT_ID}`, {
			method: 'POST',
			headers: {
				Authorization: `Bearer ${token}`,
			},
		});

		if (!fetchRes.ok) {
			console.error(
				'Fetch failed:',
				fetchRes.status,
				await fetchRes.text()
			);
			if (fetchRes.status === 401 || fetchRes.status === 403) {
				alert(
					'Помилка авторизації при завантаженні новин. Спробуйте увійти знову.'
				);
				if (typeof logout === 'function') logout();
			} else {
				alert(
					`Не вдалося завантажити новини. Статус: ${fetchRes.status}`
				);
			}
			return;
		}
		console.log('Fetch successful');

		console.log(`Analyzing news for ${STUDENT_ID}...`);
		const analyzeRes = await fetch(`${apiBase}/analyze/${STUDENT_ID}`, {
			method: 'POST',
			headers: {
				Authorization: `Bearer ${token}`,
			},
		});

		if (!analyzeRes.ok) {
			console.error(
				'Analyze failed:',
				analyzeRes.status,
				await analyzeRes.text()
			);
			if (analyzeRes.status === 401 || analyzeRes.status === 403) {
				alert(
					'Помилка авторизації при аналізі новин. Спробуйте увійти знову.'
				);
				if (typeof logout === 'function') logout();
			} else {
				alert(
					`Не вдалося проаналізувати новини. Статус: ${analyzeRes.status}`
				);
			}
			return;
		}

		const json = await analyzeRes.json();
		console.log(
			'Analyze successful, articles received:',
			json.articles.length
		);
		allArticles = json.articles.map((a) => ({
			...a,
			date: new Date(a.published || Date.now()),
		}));
		render();
	} catch (error) {
		console.error('Error during data loading or analysis:', error);
		alert('Сталася помилка під час завантаження або аналізу даних.');
	}
}

function render() {
	console.log('Rendering data...');
	const filter = filterSelect.value;
	const filtered = allArticles.filter(
		(a) => filter === 'all' || a.sentiment === filter
	);

	tableBody.innerHTML = filtered
		.sort((a, b) => b.date - a.date)
		.map(
			(a) => `
      <tr>
        <td>${a.date.toLocaleString()}</td>
        <td>${a.sentiment || 'N/A'}</td
        <td><a href="${a.link || '#'}" target="_blank">${
				a.title || 'No Title'
			}</a></td
      </tr>
    `
		)
		.join('');

	const counts = { positive: 0, neutral: 0, negative: 0 };
	filtered.forEach((a) => {
		if (counts.hasOwnProperty(a.sentiment)) {
			counts[a.sentiment]++;
		}
	});

	if (!chart) {
		initializeChart();
	}

	if (chart) {
		chart.data.datasets[0].data = [
			counts.positive,
			counts.neutral,
			counts.negative,
		];
		chart.update();
	} else {
		console.error('Chart object is not initialized.');
	}
}

function initializeChart() {
	console.log('Initializing chart...');
	if (!ctx) {
		console.error('Canvas context not found for chart initialization.');
		return;
	}
	if (chart) {
		chart.destroy();
	}
	chart = new Chart(ctx, {
		type: 'pie',
		data: {
			labels: ['Позитивні', 'Нейтральні', 'Негативні'],
			datasets: [
				{
					data: [0, 0, 0],
					backgroundColor: [
						'rgba(75, 192, 192, 0.6)',
						'rgba(201, 203, 207, 0.6)',
						'rgba(255, 99, 132, 0.6)',
					],
					borderColor: [
						'rgba(75, 192, 192, 1)',
						'rgba(201, 203, 207, 1)',
						'rgba(255, 99, 132, 1)',
					],
					borderWidth: 1,
				},
			],
		},
		options: {
			responsive: true,
			maintainAspectRatio: false,
			plugins: {
				legend: {
					position: 'top',
				},
				title: {
					display: true,
					text: 'Розподіл тональності новин',
				},
			},
		},
	});
}

function clearDashboard() {
	console.log('Clearing dashboard...');
	allArticles = [];
	if (tableBody) tableBody.innerHTML = '';
	if (chart) {
		chart.data.datasets[0].data = [0, 0, 0];
		chart.update();
	} else {
		initializeChart();
	}
	if (filterSelect) filterSelect.value = 'all';
}

if (ctx) {
} else {
	console.warn('Canvas context not found initially.');
}

filterSelect.addEventListener('change', render);

function logout() {
	localStorage.removeItem('token');
	const loginSection = document.getElementById('login-section');
	const dashboardSection = document.getElementById('dashboard-section');
	if (loginSection) loginSection.style.display = 'block';
	if (dashboardSection) dashboardSection.style.display = 'none';
	clearDashboard();
}

// Ініціалізація (якщо скрипт login.js ще не робить це після успішного входу)
// Переконайся, що loadInitialData() викликається після успішного логіну в login.js
// Або розкоментуй цей блок, якщо хочеш спробувати завантажити дані при відкритті сторінки, якщо токен вже є
// if (localStorage.getItem('token')) {
//    loadInitialData();
// }
