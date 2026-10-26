import { createServer } from "node:http";
import { randomBytes, scrypt as scryptCallback, timingSafeEqual } from "node:crypto";
import { promisify } from "node:util";
import { mkdirSync, readFileSync, renameSync, unlinkSync, writeFileSync } from "node:fs";
import { dirname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scrypt = promisify(scryptCallback);
const ROOT = dirname(fileURLToPath(import.meta.url));
const DATA_DIR = resolve(process.env.SUPER_PROJECTS_DATA_DIR || join(ROOT, "data"));
const DATABASE_PATH = join(DATA_DIR, "users.json");
const PORT = Number.parseInt(process.env.PORT || "3000", 10);
const MAX_BODY_BYTES = 16 * 1024;
const PASSWORD_MAX_BYTES = 128;
const PASSWORD_MIN_BYTES = 12;
const SESSION_DURATION_MS = 7 * 24 * 60 * 60 * 1000;
const RATE_WINDOW_MS = 15 * 60 * 1000;
const RATE_LIMIT = 10;
const COOKIE_NAME = "super_projects_session";
const COMMON_PASSWORDS = new Set([
  "bad", "password", "password123", "12345678", "qwerty123", "letmein", "admin123",
]);
const SCRYPT_OPTIONS = { N: 32768, r: 8, p: 1, maxmem: 64 * 1024 * 1024 };
const STATIC_FILES = new Map([
  ["/", ["index.html", "text/html; charset=utf-8"]],
  ["/index.html", ["index.html", "text/html; charset=utf-8"]],
  ["/app.js", ["app.js", "text/javascript; charset=utf-8"]],
  ["/styles.css", ["styles.css", "text/css; charset=utf-8"]],
]);
const sessions = new Map();
const rateLimits = new Map();

if (!Number.isInteger(PORT) || PORT < 1 || PORT > 65535) {
  throw new Error("PORT must be an integer between 1 and 65535.");
}

mkdirSync(DATA_DIR, { recursive: true, mode: 0o700 });
let database = loadDatabase();

function loadDatabase() {
  try {
    const contents = readFileSync(DATABASE_PATH, "utf8");
    const parsed = JSON.parse(contents);
    if (!Array.isArray(parsed.users) || !parsed.users.every(isStoredUser)) {
      throw new Error("The account database has an unexpected format.");
    }
    return { users: parsed.users };
  } catch (error) {
    if (error.code === "ENOENT") return { users: [] };
    throw new Error(`Could not load ${DATABASE_PATH}: ${error.message}`, { cause: error });
  }
}

function isStoredUser(user) {
  return user !== null && typeof user === "object" &&
    typeof user.id === "string" &&
    typeof user.username === "string" &&
    /^[a-z0-9_-]{3,24}$/.test(user.username) &&
    typeof user.salt === "string" &&
    /^[a-f0-9]{32}$/.test(user.salt) &&
    typeof user.passwordHash === "string" &&
    /^[a-f0-9]{128}$/.test(user.passwordHash) &&
    typeof user.createdAt === "string";
}

function saveDatabase() {
  const temporaryPath = `${DATABASE_PATH}.${process.pid}.${randomBytes(6).toString("hex")}.tmp`;
  try {
    writeFileSync(temporaryPath, `${JSON.stringify(database, null, 2)}\n`, { encoding: "utf8", mode: 0o600, flag: "wx" });
    renameSync(temporaryPath, DATABASE_PATH);
  } catch (error) {
    try {
      unlinkSync(temporaryPath);
    } catch (cleanupError) {
      if (cleanupError.code !== "ENOENT") console.error("Could not remove a temporary account database file:", cleanupError);
    }
    throw new Error("Could not safely save the account database.", { cause: error });
  }
}

function sendJson(response, status, value, extraHeaders = {}) {
  response.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    ...extraHeaders,
  });
  response.end(JSON.stringify(value));
}

function sendError(response, status, message, extraHeaders = {}) {
  sendJson(response, status, { error: message }, extraHeaders);
}

function applySecurityHeaders(response) {
  response.setHeader("X-Content-Type-Options", "nosniff");
  response.setHeader("X-Frame-Options", "DENY");
  response.setHeader("Referrer-Policy", "no-referrer");
  response.setHeader("Cross-Origin-Resource-Policy", "same-origin");
  response.setHeader("Content-Security-Policy", "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'");
}

function isAllowedHost(request) {
  if (typeof request.headers.host !== "string") return false;
  try {
    const host = new URL(`http://${request.headers.host}`);
    return (host.hostname === "localhost" || host.hostname === "127.0.0.1") &&
      host.port === String(PORT) && host.pathname === "/";
  } catch {
    return false;
  }
}

function hasSameOrigin(request) {
  if (typeof request.headers.origin !== "string" || typeof request.headers.host !== "string") return false;
  try {
    const origin = new URL(request.headers.origin);
    return origin.protocol === "http:" &&
      (origin.hostname === "localhost" || origin.hostname === "127.0.0.1") &&
      origin.host === request.headers.host;
  } catch {
    return false;
  }
}

async function readJsonBody(request) {
  if (!request.headers["content-type"]?.toLowerCase().startsWith("application/json")) {
    throw Object.assign(new Error("Send this request as JSON."), { status: 415 });
  }
  const chunks = [];
  let size = 0;
  for await (const chunk of request) {
    size += chunk.length;
    if (size > MAX_BODY_BYTES) {
      throw Object.assign(new Error("The request is too large."), { status: 413 });
    }
    chunks.push(chunk);
  }
  let value;
  try {
    value = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  } catch {
    throw Object.assign(new Error("The request body must be valid JSON."), { status: 400 });
  }
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw Object.assign(new Error("The request body must be a JSON object."), { status: 400 });
  }
  return value;
}

function checkRateLimit(request, response) {
  const now = Date.now();
  const key = request.socket.remoteAddress || "unknown";
  let bucket = rateLimits.get(key);
  if (!bucket || bucket.expiresAt <= now) {
    bucket = { count: 0, expiresAt: now + RATE_WINDOW_MS };
    rateLimits.set(key, bucket);
  }
  bucket.count++;
  if (rateLimits.size > 10000) {
    for (const [address, entry] of rateLimits) {
      if (entry.expiresAt <= now) rateLimits.delete(address);
    }
  }
  if (bucket.count <= RATE_LIMIT) return true;
  const retryAfter = Math.max(1, Math.ceil((bucket.expiresAt - now) / 1000));
  sendError(response, 429, "Too many sign-in attempts. Please wait and try again.", { "Retry-After": String(retryAfter) });
  return false;
}

function findSession(request) {
  const cookieHeader = request.headers.cookie || "";
  const cookie = cookieHeader.split(";").map(part => part.trim()).find(part => part.startsWith(`${COOKIE_NAME}=`));
  if (!cookie) return null;
  const token = cookie.slice(COOKIE_NAME.length + 1);
  const session = sessions.get(token);
  if (!session) return null;
  if (session.expiresAt <= Date.now()) {
    sessions.delete(token);
    return null;
  }
  return { token, session };
}

function publicUser(user) {
  return { username: user.username, createdAt: user.createdAt };
}

function setSessionCookie(response, token, maxAge = SESSION_DURATION_MS / 1000) {
  const secure = process.env.COOKIE_SECURE === "1" ? "; Secure" : "";
  response.setHeader("Set-Cookie", `${COOKIE_NAME}=${token}; Path=/; HttpOnly; SameSite=Strict; Max-Age=${maxAge}${secure}`);
}

async function hashPassword(password, salt) {
  const derived = await scrypt(password, salt, 64, SCRYPT_OPTIONS);
  return derived.toString("hex");
}

function validateAccountInput(body) {
  if (typeof body.username !== "string" || typeof body.password !== "string") {
    return { error: "Enter a username and password." };
  }
  const username = body.username.trim().toLowerCase();
  if (!/^[a-z0-9_-]{3,24}$/.test(username)) {
    return { error: "Username must be 3–24 characters using letters, numbers, underscores, or hyphens." };
  }
  const passwordBytes = Buffer.byteLength(body.password, "utf8");
  if (passwordBytes > PASSWORD_MAX_BYTES) {
    return { error: "Password must be 128 bytes or fewer." };
  }
  return { username, password: body.password, passwordBytes };
}

function isPredictablePassword(password, username) {
  const normalized = password.toLowerCase();
  return COMMON_PASSWORDS.has(normalized) ||
    normalized === username ||
    /^(.{1,4})\1{2,}$/u.test(normalized) ||
    /(.)\1{5,}/u.test(normalized);
}

async function handleRegister(request, response) {
  const body = await readJsonBody(request);
  const input = validateAccountInput(body);
  if (input.error) return sendError(response, 400, input.error);
  if (input.passwordBytes < PASSWORD_MIN_BYTES) {
    return sendError(response, 400, "Choose a password with at least 12 characters.");
  }
  if (isPredictablePassword(input.password, input.username)) {
    return sendError(response, 400, "Choose a less predictable password.");
  }
  if (database.users.some(user => user.username === input.username)) {
    return sendError(response, 409, "That username is already taken. Try signing in or choose another.");
  }

  const salt = randomBytes(16).toString("hex");
  const passwordHash = await hashPassword(input.password, salt);
  const user = {
    id: randomBytes(16).toString("hex"),
    username: input.username,
    salt,
    passwordHash,
    createdAt: new Date().toISOString(),
  };
  if (database.users.some(existing => existing.username === user.username)) {
    return sendError(response, 409, "That username is already taken. Try signing in or choose another.");
  }
  database.users.push(user);
  try {
    saveDatabase();
  } catch (error) {
    database.users.pop();
    throw error;
  }
  const token = randomBytes(32).toString("base64url");
  sessions.set(token, { userId: user.id, expiresAt: Date.now() + SESSION_DURATION_MS });
  setSessionCookie(response, token);
  sendJson(response, 201, { user: publicUser(user) });
}

async function handleLogin(request, response) {
  const body = await readJsonBody(request);
  const input = validateAccountInput(body);
  if (input.error) return sendError(response, 400, input.error);
  const user = database.users.find(candidate => candidate.username === input.username);
  const salt = user?.salt || "00000000000000000000000000000000";
  const expectedHash = user?.passwordHash || "0".repeat(128);
  const actualHash = await hashPassword(input.password, salt);
  const matches = timingSafeEqual(Buffer.from(actualHash, "hex"), Buffer.from(expectedHash, "hex"));
  if (!user || !matches) return sendError(response, 401, "Invalid username or password.");

  const token = randomBytes(32).toString("base64url");
  sessions.set(token, { userId: user.id, expiresAt: Date.now() + SESSION_DURATION_MS });
  setSessionCookie(response, token);
  sendJson(response, 200, { user: publicUser(user) });
}

async function handleApi(request, response, pathname) {
  applySecurityHeaders(response);
  if (pathname !== "/api/auth/me" && !hasSameOrigin(request)) {
    return sendError(response, 403, "This request did not come from this app.");
  }

  if (request.method === "GET" && pathname === "/api/auth/me") {
    const current = findSession(request);
    const user = current && database.users.find(candidate => candidate.id === current.session.userId);
    return sendJson(response, 200, { user: user ? publicUser(user) : null });
  }

  if (request.method !== "POST") {
    response.setHeader("Allow", "GET, POST");
    return sendError(response, 405, "This method is not allowed.");
  }
  if (!checkRateLimit(request, response)) return;

  if (pathname === "/api/auth/register") return handleRegister(request, response);
  if (pathname === "/api/auth/login") return handleLogin(request, response);
  if (pathname === "/api/auth/logout") {
    const current = findSession(request);
    if (current) sessions.delete(current.token);
    setSessionCookie(response, "", 0);
    return sendJson(response, 200, { ok: true });
  }
  return sendError(response, 404, "This endpoint does not exist.");
}

function serveStatic(response, pathname) {
  const entry = STATIC_FILES.get(normalize(pathname));
  if (!entry) {
    response.writeHead(404, { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store" });
    response.end("Not found");
    return;
  }
  const [filename, contentType] = entry;
  const body = readFileSync(join(ROOT, filename));
  response.writeHead(200, {
    "Content-Type": contentType,
    "Cache-Control": "no-cache",
    "Content-Length": body.length,
  });
  response.end(body);
}

const server = createServer(async (request, response) => {
  applySecurityHeaders(response);
  if (!isAllowedHost(request)) {
    return sendError(response, 403, "This local development server only accepts localhost requests.");
  }
  let pathname;
  try {
    pathname = new URL(request.url, `http://${request.headers.host}`).pathname;
  } catch {
    return sendError(response, 400, "The request URL is invalid.");
  }
  try {
    if (pathname.startsWith("/api/")) {
      await handleApi(request, response, pathname);
      return;
    }
    if (request.method !== "GET" && request.method !== "HEAD") {
      response.setHeader("Allow", "GET, HEAD");
      return sendError(response, 405, "This method is not allowed.");
    }
    serveStatic(response, pathname);
  } catch (error) {
    console.error("Request failed:", error);
    if (response.headersSent) {
      response.destroy(error);
      return;
    }
    sendError(response, Number.isInteger(error.status) ? error.status : 500,
      Number.isInteger(error.status) ? error.message : "The server could not complete this request.");
  }
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`Super Projects is running at http://localhost:${PORT}`);
  console.log("Accounts are stored locally in the data/ directory.");
});

function shutdown() {
  server.close(() => process.exit(0));
}
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
