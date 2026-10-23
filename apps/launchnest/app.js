"use strict";

const DATABASE_NAME = "launchnest-library";
const DATABASE_VERSION = 1;
const STORE_NAME = "pages";

const fileInput = document.querySelector("#fileInput");
const dropZone = document.querySelector("#dropZone");
const pageList = document.querySelector("#pageList");
const pageCount = document.querySelector("#pageCount");
const searchInput = document.querySelector("#searchInput");
const notice = document.querySelector("#notice");
const previewTitle = document.querySelector("#previewTitle");
const previewActions = document.querySelector("#previewActions");
const previewEmpty = document.querySelector("#previewEmpty");
const previewFrame = document.querySelector("#previewFrame");
const launchButton = document.querySelector("#launchButton");
const deleteButton = document.querySelector("#deleteButton");

let database;
let pages = [];
let selectedPageId = null;
let noticeTimeout;
const objectUrls = [];

function openDatabase() {
  return new Promise((resolve, reject) => {
    if (!("indexedDB" in window)) {
      reject(new Error("This browser does not support saved page storage."));
      return;
    }

    const request = indexedDB.open(DATABASE_NAME, DATABASE_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: "id" });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error("Could not open the page library."));
    request.onblocked = () => reject(new Error("The page library is busy in another tab. Close other LaunchNest tabs and reload."));
  });
}

function runTransaction(mode, operation) {
  return new Promise((resolve, reject) => {
    let transaction;
    let result;
    try {
      transaction = database.transaction(STORE_NAME, mode);
      result = operation(transaction.objectStore(STORE_NAME));
    } catch (error) {
      reject(error);
      return;
    }

    transaction.oncomplete = () => resolve(result);
    transaction.onerror = () => reject(transaction.error || new Error("The page library could not be updated."));
    transaction.onabort = () => reject(transaction.error || new Error("The page library update was cancelled."));
  });
}

function getPages() {
  let result;
  return runTransaction("readonly", (store) => {
    const request = store.getAll();
    request.onsuccess = () => {
      result = request.result;
    };
    return {
      get value() {
        return result;
      }
    };
  }).then((holder) => holder.value);
}

function savePage(page) {
  return runTransaction("readwrite", (store) => store.put(page));
}

function removePage(id) {
  return runTransaction("readwrite", (store) => store.delete(id));
}

function showNotice(message, isError = false) {
  window.clearTimeout(noticeTimeout);
  notice.textContent = message;
  notice.classList.toggle("is-error", isError);
  notice.classList.add("is-visible");
  noticeTimeout = window.setTimeout(() => notice.classList.remove("is-visible"), 6500);
}

function formatDate(timestamp) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric"
  }).format(new Date(timestamp));
}

function createPageCard(page) {
  const card = document.createElement("article");
  card.className = "page-card";
  card.classList.toggle("is-selected", page.id === selectedPageId);

  const top = document.createElement("div");
  top.className = "card-top";

  const badge = document.createElement("span");
  badge.className = "file-badge";
  badge.textContent = "HTML";
  badge.setAttribute("aria-hidden", "true");

  const info = document.createElement("div");
  info.className = "card-info";

  const title = document.createElement("h3");
  title.textContent = page.name;
  title.title = page.name;

  const filename = document.createElement("p");
  filename.textContent = page.filename;
  filename.title = page.filename;

  info.append(title, filename);
  top.append(badge, info);

  const actions = document.createElement("div");
  actions.className = "card-actions";

  const date = document.createElement("span");
  date.className = "card-date";
  date.textContent = `Added ${formatDate(page.addedAt)}`;

  const previewButton = document.createElement("button");
  previewButton.className = "preview-button";
  previewButton.type = "button";
  previewButton.textContent = page.id === selectedPageId ? "Viewing" : "Preview";
  previewButton.setAttribute("aria-label", `Preview ${page.name}`);
  previewButton.addEventListener("click", () => selectPage(page.id));

  actions.append(date, previewButton);
  card.append(top, actions);
  return card;
}

function renderPages() {
  const query = searchInput.value.trim().toLocaleLowerCase();
  const filteredPages = pages
    .filter((page) => `${page.name} ${page.filename}`.toLocaleLowerCase().includes(query))
    .sort((left, right) => right.addedAt - left.addedAt);

  pageCount.textContent = String(pages.length);
  pageList.replaceChildren();

  if (filteredPages.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-library";
    const title = document.createElement("strong");
    const description = document.createElement("span");

    if (pages.length === 0) {
      title.textContent = "Your launchpad is ready.";
      description.textContent = "Add an HTML page above and it will be waiting here next time.";
    } else {
      title.textContent = "No pages found.";
      description.textContent = "Try another search, or clear the search field.";
    }

    empty.append(title, description);
    pageList.append(empty);
    return;
  }

  for (const page of filteredPages) {
    pageList.append(createPageCard(page));
  }
}

function selectPage(id) {
  const page = pages.find((item) => item.id === id);
  if (!page) {
    showNotice("That saved page is no longer available. Refresh the library and try again.", true);
    return;
  }

  selectedPageId = id;
  previewTitle.textContent = page.name;
  previewTitle.title = page.name;
  previewActions.hidden = false;
  previewEmpty.hidden = true;
  previewFrame.hidden = false;
  previewFrame.srcdoc = page.content;
  renderPages();
}

function createPageId() {
  if (window.crypto && typeof window.crypto.randomUUID === "function") {
    return window.crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

async function importFiles(fileList) {
  const selectedFiles = Array.from(fileList);
  if (selectedFiles.length === 0) {
    return;
  }

  const htmlFiles = selectedFiles.filter((file) => /\.html?$/i.test(file.name));
  const rejectedCount = selectedFiles.length - htmlFiles.length;
  const errors = [];
  let savedCount = 0;

  for (const file of htmlFiles) {
    try {
      const content = await file.text();
      const filename = file.name;
      const name = filename.replace(/\.html?$/i, "") || filename;
      await savePage({
        id: createPageId(),
        name,
        filename,
        content,
        addedAt: Date.now()
      });
      savedCount += 1;
    } catch (error) {
      errors.push(`${file.name}: ${error.message || "could not be saved"}`);
    }
  }

  if (savedCount > 0) {
    try {
      pages = await getPages();
      renderPages();
    } catch (error) {
      showNotice(`Files were imported, but the library could not refresh: ${error.message || "storage error"}`, true);
      return;
    }
  }

  if (errors.length > 0) {
    showNotice(`Saved ${savedCount} file(s). ${errors.join(" ")}`, true);
  } else if (rejectedCount > 0) {
    showNotice(`Saved ${savedCount} HTML file(s). ${rejectedCount} non-HTML file(s) were skipped.`, true);
  } else if (savedCount > 0) {
    showNotice(`Added ${savedCount} HTML page${savedCount === 1 ? "" : "s"} to your launchpad.`);
  } else {
    showNotice("Choose .html or .htm files to add to your launchpad.", true);
  }
}

function launchSelectedPage() {
  const page = pages.find((item) => item.id === selectedPageId);
  if (!page) {
    showNotice("Select a saved page before launching it.", true);
    return;
  }

  const pageBlob = new Blob([page.content], { type: "text/html;charset=utf-8" });
  const pageUrl = URL.createObjectURL(pageBlob);
  objectUrls.push(pageUrl);
  const link = document.createElement("a");
  link.href = pageUrl;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.click();
}

async function deleteSelectedPage() {
  const page = pages.find((item) => item.id === selectedPageId);
  if (!page) {
    return;
  }

  if (!window.confirm(`Remove "${page.name}" from your LaunchNest library?`)) {
    return;
  }

  try {
    await removePage(page.id);
    pages = pages.filter((item) => item.id !== page.id);
    selectedPageId = null;
    previewTitle.textContent = "Preview";
    previewTitle.removeAttribute("title");
    previewActions.hidden = true;
    previewFrame.removeAttribute("srcdoc");
    previewFrame.hidden = true;
    previewEmpty.hidden = false;
    renderPages();
    showNotice("Page removed from your library.");
  } catch (error) {
    showNotice(`Could not remove this page: ${error.message || "storage error"}`, true);
  }
}

fileInput.addEventListener("change", async () => {
  await importFiles(fileInput.files);
  fileInput.value = "";
});

searchInput.addEventListener("input", renderPages);
launchButton.addEventListener("click", launchSelectedPage);
deleteButton.addEventListener("click", deleteSelectedPage);

for (const eventName of ["dragenter", "dragover"]) {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.add("is-dragging");
  });
}

for (const eventName of ["dragleave", "drop"]) {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.remove("is-dragging");
  });
}

dropZone.addEventListener("drop", async (event) => {
  await importFiles(event.dataTransfer.files);
});

window.addEventListener("beforeunload", () => {
  for (const url of objectUrls) {
    URL.revokeObjectURL(url);
  }
});

async function start() {
  try {
    database = await openDatabase();
    pages = await getPages();
    renderPages();
  } catch (error) {
    showNotice(`Could not open your saved library: ${error.message || "storage is unavailable"}`, true);
    pageList.replaceChildren();
    const empty = document.createElement("div");
    empty.className = "empty-library";
    const title = document.createElement("strong");
    title.textContent = "Browser storage is unavailable.";
    const description = document.createElement("span");
    description.textContent = "Try opening LaunchNest in a modern browser with site storage enabled.";
    empty.append(title, description);
    pageList.append(empty);
  }
}

start();
