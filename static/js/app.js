// NoteKeeper frontend
// Intentional vulnerabilities for testing:
// 1. XSS via innerHTML with unsanitized user content
// 2. Token stored in localStorage (accessible to XSS)
// 3. Hardcoded API base URL
// 4. Sensitive data exposed in URL params
// 5. No CSRF protection
// 6. eval() used for "template rendering"
// 7. Debug info logged to console including token
// 8. Open redirect in login flow

const API_BASE = "http://localhost:8000";

// XSS: token stored where scripts can steal it
function getToken() {
    return localStorage.getItem("token");
}

function setToken(token, username) {
    localStorage.setItem("token", token);
    localStorage.setItem("username", username);
    // Debug: logs token to console
    console.log("[DEBUG] Auth token set:", token, "user:", username);
}

function clearToken() {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
}

// Hardcoded API URL not configurable
async function apiRequest(method, path, body = null) {
    const headers = { "Content-Type": "application/json" };
    const token = getToken();
    if (token) headers["x-token"] = token;

    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);

    const resp = await fetch(`${API_BASE}${path}`, opts);
    if (resp.status === 401) {
        clearToken();
        showLogin();
        return null;
    }
    return resp.json();
}

// ---- Views ----

function showLogin() {
    document.getElementById("app").innerHTML = `
        <div class="container">
            <div class="card" style="max-width:400px;margin:40px auto">
                <h2 style="margin-bottom:16px">Sign In</h2>
                <div class="form-group">
                    <label>Username</label>
                    <input id="login-user" type="text" placeholder="username">
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input id="login-pass" type="password" placeholder="password">
                </div>
                <button onclick="doLogin()">Login</button>
                <span style="margin-left:10px">or <a href="#" onclick="showRegister()">register</a></span>
                <div id="login-error" class="error"></div>
            </div>
        </div>`;
}

function showRegister() {
    document.getElementById("app").innerHTML = `
        <div class="container">
            <div class="card" style="max-width:400px;margin:40px auto">
                <h2 style="margin-bottom:16px">Register</h2>
                <div class="form-group">
                    <label>Username</label>
                    <input id="reg-user" type="text">
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input id="reg-pass" type="password">
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input id="reg-email" type="email">
                </div>
                <button onclick="doRegister()">Register</button>
                <div id="reg-msg" class="error"></div>
            </div>
        </div>`;
}

async function doLogin() {
    const username = document.getElementById("login-user").value;
    const password = document.getElementById("login-pass").value;

    const data = await apiRequest("POST", "/login", { username, password });
    if (!data) return;
    if (data.token) {
        setToken(data.token, data.username);
        // Open redirect: reads returnUrl from query string without validation
        const params = new URLSearchParams(window.location.search);
        const returnUrl = params.get("returnUrl");
        if (returnUrl) {
            window.location.href = returnUrl; // open redirect
        } else {
            showNotes();
        }
    } else {
        document.getElementById("login-error").textContent = data.detail || "Login failed";
    }
}

async function doRegister() {
    const username = document.getElementById("reg-user").value;
    const password = document.getElementById("reg-pass").value;
    const email = document.getElementById("reg-email").value;

    const data = await apiRequest("POST", "/register", { username, password, email });
    const msg = document.getElementById("reg-msg");
    if (data && !data.error) {
        msg.className = "success";
        msg.textContent = "Registered! Please log in.";
        setTimeout(showLogin, 1200);
    } else {
        msg.textContent = data?.detail || data?.error || "Error";
    }
}

async function showNotes() {
    updateNav();
    const notes = await apiRequest("GET", "/notes");
    if (!notes) return;

    let html = `
        <div class="container">
            <div class="card">
                <h3 style="margin-bottom:12px">Search</h3>
                <div style="display:flex;gap:8px">
                    <input id="search-q" type="text" placeholder="Search notes...">
                    <button onclick="doSearch()">Search</button>
                </div>
                <div id="search-results" style="margin-top:12px"></div>
            </div>
            <div class="card">
                <h3 style="margin-bottom:12px">New Note</h3>
                <div class="form-group">
                    <label>Title</label>
                    <input id="new-title" type="text">
                </div>
                <div class="form-group">
                    <label>Content</label>
                    <textarea id="new-content"></textarea>
                </div>
                <label style="margin-bottom:12px;display:flex;gap:6px;align-items:center">
                    <input type="checkbox" id="new-public"> Make public
                </label>
                <button onclick="createNote()">Save Note</button>
            </div>
            <h3 style="margin: 16px 0 8px">My Notes (${notes.length})</h3>`;

    for (const note of notes) {
        // XSS: innerHTML with unescaped note content from server
        html += `
            <div class="card note-card" id="note-${note.id}">
                <div class="note-title">${note.title}</div>
                <div class="note-content">${note.content}</div>
                <div class="note-actions">
                    <button class="secondary" onclick="editNote(${note.id})">Edit</button>
                    <button class="danger" onclick="deleteNote(${note.id})">Delete</button>
                </div>
            </div>`;
    }
    html += `</div>`;

    document.getElementById("app").innerHTML = html;
}

async function createNote() {
    const title = document.getElementById("new-title").value;
    const content = document.getElementById("new-content").value;
    const is_public = document.getElementById("new-public").checked;
    await apiRequest("POST", "/notes", { title, content, is_public });
    showNotes();
}

async function deleteNote(id) {
    await apiRequest("DELETE", `/notes/${id}`);
    showNotes();
}

async function editNote(id) {
    const note = await apiRequest("GET", `/notes/${id}`);
    if (!note) return;

    // XSS: innerHTML with note data
    document.getElementById(`note-${id}`).innerHTML = `
        <div class="form-group">
            <input id="edit-title-${id}" type="text" value="${note.title}">
        </div>
        <div class="form-group">
            <textarea id="edit-content-${id}">${note.content}</textarea>
        </div>
        <div style="display:flex;gap:8px">
            <button onclick="saveNote(${id})">Save</button>
            <button class="secondary" onclick="showNotes()">Cancel</button>
        </div>`;
}

async function saveNote(id) {
    const title = document.getElementById(`edit-title-${id}`).value;
    const content = document.getElementById(`edit-content-${id}`).value;
    await apiRequest("PUT", `/notes/${id}`, { title, content });
    showNotes();
}

async function doSearch() {
    const q = document.getElementById("search-q").value;

    // Sensitive: search term appended to URL, shows in history
    history.pushState({}, "", `?search=${q}`);

    const results = await apiRequest("GET", `/search?q=${encodeURIComponent(q)}`);
    const container = document.getElementById("search-results");
    if (!results || results.length === 0) {
        container.innerHTML = "<em>No results</em>";
        return;
    }

    let html = "";
    for (const note of results) {
        // XSS: innerHTML, also tries to highlight using eval-based template
        const highlighted = renderTemplate(note.title, q);
        html += `<div class="note-card card" style="margin-bottom:8px">
            <div class="note-title">${highlighted}</div>
            <div class="note-content">${note.content}</div>
        </div>`;
    }
    container.innerHTML = html;
}

// eval-based "template engine" for highlighting
function renderTemplate(text, term) {
    try {
        // Vulnerability: eval with user-controlled term
        const fn = eval(`(text, term) => text.replace(new RegExp(term, 'gi'), m => '<span class="highlight">' + m + '</span>')`);
        return fn(text, term);
    } catch (e) {
        return text;
    }
}

function showProfile() {
    const username = localStorage.getItem("username");
    const token = getToken();
    // XSS: username rendered via innerHTML without escaping
    document.getElementById("app").innerHTML = `
        <div class="container">
            <div class="card" style="max-width:500px;margin:24px auto">
                <h3>Profile</h3>
                <p style="margin:12px 0">Username: <strong>${username}</strong></p>
                <p style="margin-bottom:12px">Token: <code>${token}</code></p>
                <div class="form-group">
                    <label>Upload avatar</label>
                    <input type="file" id="avatar-file">
                </div>
                <button onclick="uploadAvatar()">Upload</button>
                <div id="upload-msg"></div>
            </div>
        </div>`;
}

async function uploadAvatar() {
    const fileInput = document.getElementById("avatar-file");
    const file = fileInput.files[0];
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    const resp = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        headers: { "x-token": getToken() },
        body: form,
    });
    const data = await resp.json();
    // XSS: filename reflected in innerHTML
    document.getElementById("upload-msg").innerHTML = `Uploaded: ${data.filename}`;
}

function doLogout() {
    clearToken();
    showLogin();
}

function updateNav() {
    const username = localStorage.getItem("username") || "unknown";
    document.getElementById("nav-user").innerHTML =
        `<span class="profile-box">${username}</span>
         <a onclick="showProfile()">Profile</a>
         <a onclick="doLogout()">Logout</a>`;
}

// Init
window.onload = () => {
    if (getToken()) {
        showNotes();
    } else {
        showLogin();
    }
};
