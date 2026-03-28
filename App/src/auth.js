export const API_URL = "https://psychotic-disco-production.up.railway.app";
let csrf_token = null;

export function get_csrf() {
    return csrf_token
}

export async function init_csrf() {
    const res = await fetch(`${API_URL}/api/csrf-token`, {credentials: 'include'});
    const data = await res.json();
    csrf_token = data.token;
}

export async function check_creds() {
    const res = await fetch(`${API_URL}/api/me`,{credentials: 'include'});
    if (!res.ok) {window.location.replace('/login.html')};
}

export async function login(username, password) {
    const res = await fetch(`${API_URL}/api/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token
        },
        credentials: 'include',
        body: JSON.stringify({ username, password })
    });
    return res.ok;
}

export async function logout() {
    await fetch(`${API_URL}/api/logout`, {
            method: 'POST',
            headers: {'X-CSRFToken': csrf_token},
            credentials: 'include'
    });
    window.location.replace('/login.html');
}