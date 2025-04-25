const API_BASE = 'http://localhost:8000'; // Визначте ваш API base URL

document.addEventListener('DOMContentLoaded', () => {
	const loginForm = document.getElementById('login-form');
	const loginSection = document.getElementById('login-section');
	const dashboardSection = document.getElementById('dashboard-section');
	const logoutButton = document.getElementById('logout-button');

	const token = localStorage.getItem('token');

	if (token) {
		// Якщо токен є, показуємо дашборд і ховаємо форму входу
		if (loginSection) loginSection.style.display = 'none';
		if (dashboardSection) dashboardSection.style.display = 'block';
		// Запускаємо завантаження даних дашборду (якщо функція доступна глобально)
		if (typeof loadInitialData === 'function') {
			loadInitialData(); // Ця функція має бути визначена в main.js
		} else {
			console.warn('loadInitialData function not found in main.js');
			// Можливо, потрібно викликати щось інше з main.js
		}
	} else {
		// Якщо токена немає, показуємо форму входу і ховаємо дашборд
		if (loginSection) loginSection.style.display = 'block';
		if (dashboardSection) dashboardSection.style.display = 'none';
	}

	if (loginForm) {
		loginForm.addEventListener('submit', async (e) => {
			e.preventDefault();
			const form = e.target;
			const data = new URLSearchParams(new FormData(form));
			try {
				const res = await fetch(`${API_BASE}/token`, {
					method: 'POST',
					mode: 'cors',
					credentials: 'include',
					headers: {
						'Content-Type': 'application/x-www-form-urlencoded',
					},
					body: data,
				});
				if (!res.ok) {
					const errorData = await res.json().catch(() => ({
						detail: 'Login failed. Unknown error.',
					}));
					alert(
						`Login failed: ${
							errorData.detail || 'Invalid credentials'
						}`
					);
					return;
				}
				const { access_token } = await res.json();
				localStorage.setItem('token', access_token);
				// Не перезавантажуємо сторінку, а просто оновлюємо UI
				if (loginSection) loginSection.style.display = 'none';
				if (dashboardSection) dashboardSection.style.display = 'block';
				// Запускаємо завантаження даних дашборду
				if (typeof loadInitialData === 'function') {
					loadInitialData();
				} else {
					console.warn(
						'loadInitialData function not found in main.js after login'
					);
				}
				// window.location = "/"; // Перенаправлення більше не потрібне
			} catch (error) {
				console.error('Login request failed:', error);
				alert('Login request failed. Check the console for details.');
			}
		});
	}

	if (logoutButton) {
		logoutButton.addEventListener('click', () => {
			localStorage.removeItem('token');
			// Показуємо форму входу, ховаємо дашборд
			if (loginSection) loginSection.style.display = 'block';
			if (dashboardSection) dashboardSection.style.display = 'none';
			// Очищаємо дані дашборду (необов'язково, залежить від логіки main.js)
			if (typeof clearDashboard === 'function') {
				// Припустимо, є функція очищення
				clearDashboard();
			}
			// window.location = "/"; // Можна перезавантажити сторінку, якщо простіше
		});
	}
});
