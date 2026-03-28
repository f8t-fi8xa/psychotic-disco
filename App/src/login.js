import { login, init_csrf, API_URL } from "./auth.js";
login_block().then(async (res) => {

    await init_csrf()

    document.getElementById('form').addEventListener('submit', async (event) => {
        event.preventDefault();

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const error = document.getElementById('error');

        const ok = await login(username, password);

        if (ok) {
            window.location.href = '/index.html'
        }
        else {
            error.style.display = 'block'
        }
    });
});

async function login_block() {
    const res = await fetch(`${API_URL}/api/me`, {credentials: 'include'})
    if (res.ok) {window.location.replace('/index.html');}
}