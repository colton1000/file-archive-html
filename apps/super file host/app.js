"use strict";

const STORAGE_KEY = "super-projects.workspace.v1";
const THEME_KEY = "super-projects.theme";
const languageColors = {
  JavaScript: "#f1e05a",
  TypeScript: "#3178c6",
  Python: "#3572a5",
  HTML: "#e34c26",
  CSS: "#563d7c",
  Rust: "#dea584",
  Go: "#00add8",
};
const starterProjects = [
  { id: "stargazer-ui", name: "stargazer-ui", description: "A tiny component library for interfaces with a little more wonder.", visibility: "public", language: "TypeScript", stars: 24, starred: true, updatedAt: "2026-10-20T12:00:00.000Z", color: "#b7a0ff", symbol: "✳" },
  { id: "field-notes", name: "field-notes", description: "Collect ideas, sketches, and the little things worth remembering.", visibility: "public", language: "JavaScript", stars: 12, starred: false, updatedAt: "2026-10-18T12:00:00.000Z", color: "#70e1ad", symbol: "✎" },
  { id: "moonshot-api", name: "moonshot-api", description: "A friendly API for turning ambitious ideas into small next steps.", visibility: "private", language: "Python", stars: 0, starred: false, updatedAt: "2026-10-16T12:00:00.000Z", color: "#88baff", symbol: "↗" },
  { id: "good-days", name: "good-days", description: "A little habit tracker that makes room for imperfect progress.", visibility: "public", language: "CSS", stars: 8, starred: false, updatedAt: "2026-10-12T12:00:00.000Z", color: "#f4c96b", symbol: "☼" },
];

const elements = {
  authScreen: document.querySelector("#auth-screen"),
  appContent: document.querySelector("#app-content"),
  authForm: document.querySelector("#auth-form"),
  authUsername: document.querySelector("#auth-username"),
  authPassword: document.querySelector("#auth-password"),
  authConfirmPassword: document.querySelector("#auth-confirm-password"),
  confirmPasswordWrap: document.querySelector("#confirm-password-wrap"),
  authMessage: document.querySelector("#auth-message"),
  authSubmit: document.querySelector("#auth-submit"),
  authTabs: [...document.querySelectorAll("[data-auth-mode]")],
  authIntro: document.querySelector("#auth-intro"),
  passwordStrength: document.querySelector("#password-strength"),
  strengthLabel: document.querySelector("#strength-label"),
  strengthHint: document.querySelector("#strength-hint"),
  strengthTrack: document.querySelector(".strength-track"),
  strengthFill: document.querySelector("#strength-fill"),
  logoutButton: document.querySelector("#logout-button"),
  workspaceName: document.querySelector("#workspace-name"),
  userLabel: document.querySelector("#user-label"),
  userAvatar: document.querySelector(".topbar-actions .avatar"),
  list: document.querySelector("#project-list"),
  empty: document.querySelector("#empty-state"),
  emptyTitle: document.querySelector("#empty-title"),
  emptyCopy: document.querySelector("#empty-copy"),
  search: document.querySelector("#global-search"),
  filterButtons: [...document.querySelectorAll("[data-filter]")],
  sort: document.querySelector("#sort-projects"),
  navButtons: [...document.querySelectorAll("[data-view]")],
  pageTitle: document.querySelector("#page-title"),
  sectionTitle: document.querySelector("#projects-heading"),
  sectionSubtitle: document.querySelector("#section-subtitle"),
  count: document.querySelector("#project-count"),
  stats: {
    total: document.querySelector("#stat-total"),
    public: document.querySelector("#stat-public"),
    starred: document.querySelector("#stat-starred"),
  },
  createDialog: document.querySelector("#create-dialog"),
  createForm: document.querySelector("#create-form"),
  projectName: document.querySelector("#project-name"),
  formError: document.querySelector("#form-error"),
  detailDialog: document.querySelector("#detail-dialog"),
  toastRegion: document.querySelector("#toast-region"),
  themeToggle: document.querySelector(".theme-toggle"),
};

let toastTimer;
let memoryStorage = new Map();
let usingMemoryStorage = false;
let storage = getBrowserStorage();
let storageKey = STORAGE_KEY;
let projects = [];
let activeView = "dashboard";
let activeFilter = "all";
let selectedProjectId = null;
let editingProjectId = null;
let authMode = "login";

function getBrowserStorage() {
  try {
    return window.localStorage;
  } catch (error) {
    console.error("Browser storage is unavailable:", error);
    usingMemoryStorage = true;
    notify("Browser storage is unavailable. Changes will last only for this visit.", true);
    return createMemoryStorage();
  }
}

function createMemoryStorage() {
  return {
    getItem(key) { return memoryStorage.get(key) ?? null; },
    setItem(key, value) { memoryStorage.set(key, String(value)); },
  };
}

function readProjects() {
  try {
    const stored = storage.getItem(storageKey);
    if (stored === null) return structuredClone(starterProjects);
    const parsed = JSON.parse(stored);
    if (!Array.isArray(parsed) || !parsed.every(isProject)) {
      throw new Error("Saved project data has an unexpected format.");
    }
    return parsed;
  } catch (error) {
    if (error instanceof SyntaxError || error instanceof Error && error.message.includes("unexpected format")) {
      console.error("Could not read saved super projects:", error);
      notify("Saved project data could not be read. Starting with the sample projects.", true);
      return structuredClone(starterProjects);
    }
    switchToMemoryStorage();
    return structuredClone(starterProjects);
  }
}

function isProject(value) {
  return value !== null && typeof value === "object" &&
    typeof value.id === "string" && typeof value.name === "string" &&
    typeof value.description === "string" &&
    (value.visibility === "public" || value.visibility === "private") &&
    Number.isInteger(value.stars) && typeof value.starred === "boolean" &&
    typeof value.updatedAt === "string";
}

function switchToMemoryStorage() {
  if (usingMemoryStorage) return;
  usingMemoryStorage = true;
  storage = createMemoryStorage();
  notify("Browser storage is unavailable. Changes will last only for this visit.", true);
}

function saveProjects() {
  try {
    storage.setItem(storageKey, JSON.stringify(projects));
    return true;
  } catch (error) {
    if (!usingMemoryStorage) {
      console.error("Could not save super projects:", error);
      memoryStorage.set(storageKey, JSON.stringify(projects));
      switchToMemoryStorage();
      return true;
    }
    console.error("Could not save super projects:", error);
    notify("Your changes could not be saved. Check browser storage and try again.", true);
    return false;
  }
}

function escapeText(value) {
  return String(value ?? "");
}

function makeElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = escapeText(text);
  return element;
}

function createProjectCard(project) {
  const card = makeElement("article", "project-card");
  card.tabIndex = 0;
  card.setAttribute("aria-label", `${project.name}, ${project.visibility} project`);
  card.addEventListener("click", () => showProject(project.id));
  card.addEventListener("keydown", event => {
    if (event.target === card && (event.key === "Enter" || event.key === " ")) {
      event.preventDefault();
      showProject(project.id);
    }
  });

  const symbol = makeElement("span", "project-symbol", project.symbol || project.name.charAt(0).toUpperCase());
  symbol.style.color = project.color || "var(--green)";
  symbol.style.backgroundColor = `${project.color || "#70e1ad"}1c`;
  card.append(symbol);

  const main = makeElement("div", "project-main");
  const titleLine = makeElement("div", "project-title-line");
  const name = makeElement("button", "project-name", project.name);
  name.type = "button";
  name.addEventListener("click", event => {
    event.stopPropagation();
    showProject(project.id);
  });
  const visibility = makeElement("span", "visibility-badge", project.visibility);
  titleLine.append(name, visibility);
  main.append(titleLine);

  const description = makeElement("p", "project-description", project.description || "A new idea, ready to take shape.");
  main.append(description);
  const metadata = makeElement("div", "project-meta");
  if (project.language) {
    const language = makeElement("span", "", project.language);
    const dot = makeElement("span", "language-dot");
    dot.style.backgroundColor = languageColors[project.language] || "#8b98a7";
    language.prepend(dot);
    metadata.append(language);
  }
  const stars = makeElement("span", "", `☆ ${project.stars}`);
  metadata.append(stars);
  metadata.append(makeElement("span", "project-updated", `Updated ${relativeDate(project.updatedAt)}`));
  main.append(metadata);
  card.append(main);

  const starButton = makeElement("button", `project-star${project.starred ? " is-starred" : ""}`, `${project.starred ? "★" : "☆"} ${project.stars}`);
  starButton.type = "button";
  starButton.setAttribute("aria-label", `${project.starred ? "Unstar" : "Star"} ${project.name}`);
  starButton.setAttribute("aria-pressed", String(project.starred));
  starButton.addEventListener("click", event => {
    event.stopPropagation();
    toggleStar(project.id);
  });
  card.append(starButton);
  return card;
}

function visibleProjects() {
  const query = elements.search.value.trim().toLocaleLowerCase();
  let filtered = projects.filter(project => {
    if (activeView === "starred" && !project.starred) return false;
    if (activeFilter !== "all" && project.visibility !== activeFilter) return false;
    return !query || [project.name, project.description, project.language, project.visibility]
      .some(value => String(value || "").toLocaleLowerCase().includes(query));
  });
  if (elements.sort.value === "name") filtered.sort((a, b) => a.name.localeCompare(b.name));
  else if (elements.sort.value === "stars") filtered.sort((a, b) => b.stars - a.stars || a.name.localeCompare(b.name));
  else filtered.sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
  return activeView === "dashboard" && !query ? filtered.slice(0, 4) : filtered;
}

function render() {
  elements.list.replaceChildren();
  const shownProjects = visibleProjects();
  for (const project of shownProjects) elements.list.append(createProjectCard(project));

  const hasProjects = shownProjects.length > 0;
  elements.list.hidden = !hasProjects;
  elements.empty.hidden = hasProjects;
  if (!hasProjects) {
    const searching = elements.search.value.trim().length > 0;
    const noProjects = projects.length === 0;
    elements.emptyTitle.textContent = searching ? "No matches just yet." :
      activeView === "starred" ? "Nothing starred yet." :
      activeFilter !== "all" ? `No ${activeFilter} projects yet.` :
      noProjects ? "Your next big thing starts here." : "Nothing to show here.";
    elements.emptyCopy.textContent = searching ? "Try another search, or clear the search box." :
      activeView === "starred" ? "Star a project to keep it close at hand." :
      activeFilter !== "all" ? "Try another visibility filter or create a project." :
      "Create a super project and give your idea a place to grow.";
  }

  elements.stats.total.textContent = String(projects.length);
  elements.stats.public.textContent = String(projects.filter(project => project.visibility === "public").length);
  elements.stats.starred.textContent = String(projects.filter(project => project.starred).length);
  elements.count.textContent = String(projects.length);
  document.querySelector("#copyright-year").textContent = String(new Date().getFullYear());
  elements.navButtons.forEach(button => button.classList.toggle("is-active", button.dataset.view === activeView));
  elements.sectionTitle.textContent = activeView === "starred" ? "Your starred projects" :
    activeView === "projects" ? "All super projects" : "Your super projects";
  elements.sectionSubtitle.textContent = activeView === "dashboard" ? "The latest from your workspace" :
    activeView === "starred" ? "The ones you want to keep close" : `${projects.length} ${projects.length === 1 ? "project" : "projects"} in your workspace`;
  const heading = activeView === "starred" ? ["Your ", "favorites."] :
    activeView === "projects" ? ["Your work, ", "all in one place."] :
    ["Good things are ", "building."];
  const highlight = makeElement("span", "", heading[1]);
  elements.pageTitle.replaceChildren(document.createTextNode(heading[0]), highlight);
  document.title = activeView === "starred" ? "Starred — Super Projects" :
    activeView === "projects" ? "All projects — Super Projects" : "Super Projects — your creative home";
  elements.filterButtons.forEach(button => {
    const selected = button.dataset.filter === activeFilter;
    button.classList.toggle("is-selected", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
}

function setAuthMode(mode) {
  authMode = mode;
  const registering = mode === "register";
  elements.authTabs.forEach(button => {
    const selected = button.dataset.authMode === mode;
    button.classList.toggle("is-selected", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
  elements.authIntro.textContent = registering
    ? "Create an account to make a home for your projects."
    : "Sign in to pick up where you left off.";
  elements.authSubmit.textContent = registering ? "Create account" : "Sign in";
  elements.confirmPasswordWrap.hidden = !registering;
  elements.authConfirmPassword.required = registering;
  elements.authPassword.autocomplete = registering ? "new-password" : "current-password";
  elements.passwordStrength.hidden = !registering;
  elements.authMessage.hidden = true;
  elements.authForm.reset();
  if (registering) updatePasswordStrength("");
}

function updatePasswordStrength(password) {
  const commonPasswords = new Set(["bad", "password", "password123", "12345678", "qwerty123", "letmein", "admin123"]);
  let score = 0;
  const normalized = password.toLocaleLowerCase();
  const predictable = commonPasswords.has(normalized) || /^(.{1,4})\1{2,}$/u.test(normalized) || /(.)\1{5,}/u.test(normalized);
  if (password.length >= 8 && !predictable) {
    score = password.length >= 16 ? 3 : password.length >= 12 ? 2 : 1;
    const characterGroups = [
      /[a-z]/.test(password),
      /[A-Z]/.test(password),
      /[0-9]/.test(password),
      /[^A-Za-z0-9]/.test(password),
    ].filter(Boolean).length;
    if (characterGroups >= 3) score++;
    if (password.length >= 20 && score < 4) score++;
  }
  const labels = ["Bad", "Weak", "Fair", "Good", "Strong"];
  const hints = [
    "This password is easy to guess. Use at least 12 characters.",
    "Still easy to guess. Try a longer, less predictable password.",
    "Getting better. A longer, unique passphrase is safer.",
    "Good password. Keep it unique to this account.",
    "Strong password. A unique passphrase is a good choice.",
  ];
  elements.passwordStrength.dataset.strength = String(score);
  elements.strengthLabel.textContent = labels[score];
  elements.strengthHint.textContent = hints[score];
  elements.strengthTrack.setAttribute("aria-valuenow", String(score));
  elements.strengthFill.style.width = `${score * 25}%`;
}

function showAuthMessage(message) {
  elements.authMessage.textContent = message;
  elements.authMessage.hidden = false;
}

async function authRequest(endpoint, payload) {
  const response = await fetch(endpoint, {
    method: payload ? "POST" : "GET",
    credentials: "same-origin",
    headers: payload ? { "Content-Type": "application/json", Accept: "application/json" } : { Accept: "application/json" },
    body: payload ? JSON.stringify(payload) : undefined,
  });
  let result;
  try {
    result = await response.json();
  } catch {
    throw new Error("The server returned an unreadable response.");
  }
  if (!response.ok) throw new Error(typeof result.error === "string" ? result.error : "The request could not be completed.");
  return result;
}

function showAuthenticatedApp(user) {
  storageKey = `${STORAGE_KEY}.${user.username}`;
  projects = readProjects();
  elements.workspaceName.textContent = `${user.username}'s workspace`;
  elements.userLabel.textContent = user.username;
  elements.userAvatar.textContent = user.username.charAt(0).toLocaleUpperCase();
  elements.userAvatar.setAttribute("aria-label", `${user.username} account`);
  elements.authScreen.hidden = true;
  elements.appContent.hidden = false;
  activeView = "dashboard";
  activeFilter = "all";
  render();
}

function showSignedOut() {
  projects = [];
  elements.appContent.hidden = true;
  elements.authScreen.hidden = false;
  setAuthMode("login");
}

async function initializeAuth() {
  try {
    const result = await authRequest("/api/auth/me");
    if (result.user) showAuthenticatedApp(result.user);
  } catch (error) {
    console.error("Could not check the current login session:", error);
    showAuthMessage("Could not connect to Super Projects. Start the Node.js server, then reload this page.");
  }
}

function relativeDate(dateValue) {
  const date = new Date(dateValue);
  if (Number.isNaN(date.getTime())) return "just now";
  const days = Math.max(0, Math.floor((Date.now() - date.getTime()) / 86400000));
  if (days === 0) return "today";
  if (days === 1) return "yesterday";
  if (days < 30) return `${days} days ago`;
  if (days < 365) return `${Math.floor(days / 30)} months ago`;
  return `${Math.floor(days / 365)} years ago`;
}

function toggleStar(id) {
  const project = projects.find(item => item.id === id);
  if (!project) return;
  project.starred = !project.starred;
  project.stars = Math.max(0, project.stars + (project.starred ? 1 : -1));
  project.updatedAt = new Date().toISOString();
  if (saveProjects()) render();
}

function showProject(id) {
  const project = projects.find(item => item.id === id);
  if (!project) return;
  selectedProjectId = id;
  document.querySelector("#detail-title").textContent = project.name;
  document.querySelector("#detail-description").textContent = project.description || "A new idea, ready to take shape.";
  const meta = document.querySelector("#detail-meta");
  meta.replaceChildren(
    makeElement("span", "", `${project.visibility === "public" ? "◉" : "◌"} ${project.visibility}`),
    makeElement("span", "", `☆ ${project.stars} stars`),
    makeElement("span", "", project.language || "No language specified"),
    makeElement("span", "", `Updated ${relativeDate(project.updatedAt)}`)
  );
  const starButton = document.querySelector("#detail-star");
  starButton.textContent = project.starred ? "★ Unstar project" : "☆ Star project";
  if (!elements.detailDialog.open) elements.detailDialog.showModal();
}

function notify(message, isError = false) {
  const toast = makeElement("div", `toast${isError ? " toast-error" : ""}`, message);
  elements.toastRegion.append(toast);
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toast.remove(), 4400);
}

function openCreateDialog() {
  editingProjectId = null;
  elements.formError.hidden = true;
  elements.createForm.reset();
  document.querySelector("#create-title").textContent = "Create a super project";
  elements.createForm.querySelector('[type="submit"]').textContent = "Create project →";
  elements.createDialog.showModal();
  elements.projectName.focus();
}

function setView(view) {
  activeView = view;
  if (view !== "dashboard") activeFilter = "all";
  render();
}

elements.authTabs.forEach(button => button.addEventListener("click", () => setAuthMode(button.dataset.authMode)));
elements.authPassword.addEventListener("input", () => updatePasswordStrength(elements.authPassword.value));
elements.authForm.addEventListener("submit", async event => {
  event.preventDefault();
  elements.authMessage.hidden = true;
  const username = elements.authUsername.value.trim();
  const password = elements.authPassword.value;
  if (authMode === "register") {
    if (new TextEncoder().encode(password).length < 12) {
      showAuthMessage("Choose a password with at least 12 characters.");
      elements.authPassword.focus();
      return;
    }
    if (password !== elements.authConfirmPassword.value) {
      showAuthMessage("Those passwords do not match.");
      elements.authConfirmPassword.focus();
      return;
    }
  }
  elements.authSubmit.disabled = true;
  elements.authSubmit.textContent = authMode === "register" ? "Creating account…" : "Signing in…";
  try {
    const result = await authRequest(`/api/auth/${authMode}`, { username, password });
    if (!result.user || typeof result.user.username !== "string") {
      throw new Error("The server returned an invalid account response.");
    }
    showAuthenticatedApp(result.user);
  } catch (error) {
    showAuthMessage(error instanceof Error ? error.message : "The request could not be completed.");
  } finally {
    elements.authSubmit.disabled = false;
    elements.authSubmit.textContent = authMode === "register" ? "Create account" : "Sign in";
  }
});

elements.logoutButton.addEventListener("click", async () => {
  elements.logoutButton.disabled = true;
  try {
    await authRequest("/api/auth/logout", {});
    showSignedOut();
  } catch (error) {
    notify(error instanceof Error ? error.message : "Could not sign out. Please try again.", true);
  } finally {
    elements.logoutButton.disabled = false;
  }
});

document.querySelectorAll("[data-open-create]").forEach(button => button.addEventListener("click", openCreateDialog));
document.querySelectorAll("[data-close-dialog]").forEach(button => button.addEventListener("click", () => {
  button.closest("dialog").close();
}));
document.querySelectorAll("[data-view]").forEach(button => button.addEventListener("click", () => setView(button.dataset.view)));
document.querySelectorAll("[data-view-link]").forEach(link => link.addEventListener("click", event => {
  event.preventDefault();
  setView(link.dataset.viewLink);
}));
elements.filterButtons.forEach(button => button.addEventListener("click", () => {
  activeFilter = button.dataset.filter;
  render();
}));
elements.search.addEventListener("input", render);
elements.sort.addEventListener("change", render);

elements.createForm.addEventListener("submit", event => {
  event.preventDefault();
  const formData = new FormData(elements.createForm);
  const name = String(formData.get("name") || "").trim();
  const description = String(formData.get("description") || "").trim();
  const visibility = formData.get("visibility") === "private" ? "private" : "public";
  if (!/^[-A-Za-z0-9._]{1,40}$/.test(name)) {
    elements.formError.textContent = "Use 1–40 letters, numbers, periods, hyphens, or underscores.";
    elements.formError.hidden = false;
    elements.projectName.focus();
    return;
  }
  if (projects.some(project => project.id !== editingProjectId && project.name.toLocaleLowerCase() === name.toLocaleLowerCase())) {
    elements.formError.textContent = "A project with that name already exists. Choose a different name.";
    elements.formError.hidden = false;
    elements.projectName.focus();
    return;
  }
  if (editingProjectId) {
    const project = projects.find(item => item.id === editingProjectId);
    if (!project) {
      elements.formError.textContent = "This project is no longer available. Close this form and try again.";
      elements.formError.hidden = false;
      return;
    }
    project.name = name;
    project.description = description;
    project.visibility = visibility;
    project.updatedAt = new Date().toISOString();
    const updatedProjectId = project.id;
    if (saveProjects()) {
      editingProjectId = null;
      elements.createDialog.close();
      render();
      showProject(updatedProjectId);
      notify(`${name} was updated.`);
    }
    return;
  }
  const colors = ["#70e1ad", "#b7a0ff", "#88baff", "#f4c96b", "#ff9e82"];
  const symbols = ["✳", "✎", "↗", "☼", "◇"];
  const project = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    name,
    description,
    visibility,
    language: "",
    stars: 0,
    starred: false,
    updatedAt: new Date().toISOString(),
    color: colors[projects.length % colors.length],
    symbol: symbols[projects.length % symbols.length],
  };
  projects.unshift(project);
  if (saveProjects()) {
    elements.createDialog.close();
    activeView = "projects";
    activeFilter = "all";
    render();
    notify(`${name} is ready for its first big idea.`);
  }
});

document.querySelector("#detail-star").addEventListener("click", () => {
  if (!selectedProjectId) return;
  toggleStar(selectedProjectId);
  const project = projects.find(item => item.id === selectedProjectId);
  if (project) showProject(project.id);
});
document.querySelector("#detail-edit").addEventListener("click", () => {
  const project = projects.find(item => item.id === selectedProjectId);
  if (!project) return;
  editingProjectId = project.id;
  elements.formError.hidden = true;
  elements.projectName.value = project.name;
  document.querySelector("#project-description").value = project.description;
  document.querySelector("#project-visibility").value = project.visibility;
  document.querySelector("#create-title").textContent = `Edit ${project.name}`;
  elements.createForm.querySelector('[type="submit"]').textContent = "Save changes →";
  elements.createDialog.showModal();
  elements.projectName.focus();
});
document.querySelector("#detail-delete").addEventListener("click", () => {
  const project = projects.find(item => item.id === selectedProjectId);
  if (!project || !window.confirm(`Delete "${project.name}"? This cannot be undone.`)) return;
  projects = projects.filter(item => item.id !== selectedProjectId);
  if (saveProjects()) {
    elements.detailDialog.close();
    selectedProjectId = null;
    render();
    notify(`${project.name} was deleted.`);
  }
});

elements.themeToggle.addEventListener("click", () => {
  const theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = theme;
  try {
    window.localStorage.setItem(THEME_KEY, theme);
  } catch (error) {
    console.error("Could not save color theme preference:", error);
    notify("Your theme changed, but the preference could not be saved.", true);
  }
});
elements.search.addEventListener("keydown", event => {
  if (event.key === "Escape" && elements.search.value) {
    elements.search.value = "";
    render();
  }
});
document.addEventListener("keydown", event => {
  if (event.key === "/" && !event.altKey && !event.ctrlKey && !event.metaKey &&
      !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName)) {
    event.preventDefault();
    elements.search.focus();
  }
});

try {
  const savedTheme = window.localStorage.getItem(THEME_KEY);
  if (savedTheme === "light" || savedTheme === "dark") document.documentElement.dataset.theme = savedTheme;
} catch (error) {
  console.error("Could not read color theme preference:", error);
  notify("Your saved theme could not be loaded.", true);
}
initializeAuth();
