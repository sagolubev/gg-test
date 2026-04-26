// NoteKeeper frontend
// Intentional vulnerabilities for testing:
// 1. XSS via innerHTML with unsanitized user content
// 2. Token stored in localStorage (accessible to XSS)
// 3. Hardcoded API base URL
// 4. Sensitive data exposed in URL params
// 5. No CSRF protection
// 6. Debug info logged to console including token
// 7. Open redirect in login flow

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

    const html = `
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
            <h3 style="margin: 16px 0 8px">My Notes (${notes.length})</h3>
            <div id="notes-list"></div>
        </div>`;

    document.getElementById("app").innerHTML = html;

    const notesList = document.getElementById("notes-list");
    for (const note of notes) {
        const card = document.createElement("div");
        card.className = "card note-card";
        card.id = `note-${note.id}`;

        const title = document.createElement("div");
        title.className = "note-title";
        title.textContent = note.title ?? "";

        const content = document.createElement("div");
        content.className = "note-content";
        content.textContent = note.content ?? "";

        const actions = document.createElement("div");
        actions.className = "note-actions";

        const edit = document.createElement("button");
        edit.className = "secondary";
        edit.textContent = "Edit";
        edit.onclick = () => editNote(note.id);

        const del = document.createElement("button");
        del.className = "danger";
        del.textContent = "Delete";
        del.onclick = () => deleteNote(note.id);

        actions.append(edit, del);
        card.append(title, content, actions);
        notesList.appendChild(card);
    }
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

    const card = document.getElementById(`note-${id}`);
    const titleGroup = document.createElement("div");
    titleGroup.className = "form-group";

    const titleInput = document.createElement("input");
    titleInput.id = `edit-title-${id}`;
    titleInput.type = "text";
    titleInput.value = note.title ?? "";
    titleGroup.appendChild(titleInput);

    const contentGroup = document.createElement("div");
    contentGroup.className = "form-group";

    const contentTextarea = document.createElement("textarea");
    contentTextarea.id = `edit-content-${id}`;
    contentTextarea.value = note.content ?? "";
    contentGroup.appendChild(contentTextarea);

    const actions = document.createElement("div");
    actions.style.display = "flex";
    actions.style.gap = "8px";

    const save = document.createElement("button");
    save.textContent = "Save";
    save.onclick = () => saveNote(id);

    const cancel = document.createElement("button");
    cancel.className = "secondary";
    cancel.textContent = "Cancel";
    cancel.onclick = showNotes;

    actions.append(save, cancel);
    card.replaceChildren(titleGroup, contentGroup, actions);
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

    container.replaceChildren();
    for (const note of results) {
        const card = document.createElement("div");
        card.className = "note-card card";
        card.style.marginBottom = "8px";

        const title = document.createElement("div");
        title.className = "note-title";
        appendHighlightedText(title, note.title ?? "", q);

        const content = document.createElement("div");
        content.className = "note-content";
        content.textContent = note.content ?? "";

        card.append(title, content);
        container.appendChild(card);
    }
}

function appendHighlightedText(parent, text, term) {
    if (!term) {
        parent.textContent = text;
        return;
    }

    const source = String(text);
    const needle = String(term).toLowerCase();
    const haystack = source.toLowerCase();
    let index = 0;
    let matchIndex = haystack.indexOf(needle, index);

    while (matchIndex !== -1) {
        parent.appendChild(document.createTextNode(source.slice(index, matchIndex)));

        const highlight = document.createElement("span");
        highlight.className = "highlight";
        highlight.textContent = source.slice(matchIndex, matchIndex + needle.length);
        parent.appendChild(highlight);

        index = matchIndex + needle.length;
        matchIndex = haystack.indexOf(needle, index);
    }

    parent.appendChild(document.createTextNode(source.slice(index)));
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
