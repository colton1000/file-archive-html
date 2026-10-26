import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { once } from "node:events";
import { createServer as createProbeServer } from "node:http";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, before, test } from "node:test";
import { fileURLToPath } from "node:url";

const serverPath = fileURLToPath(new URL("./server.mjs", import.meta.url));
const temporaryDirectory = mkdtempSync(join(tmpdir(), "super-projects-test-"));
let child;
let origin;
let readyOutput = "";

before(async () => {
  const probe = createProbeServer();
  probe.listen(0, "127.0.0.1");
  await once(probe, "listening");
  const address = probe.address();
  await new Promise((resolve, reject) => probe.close(error => error ? reject(error) : resolve()));
  const port = address.port;
  origin = `http://127.0.0.1:${port}`;

  child = spawn(process.execPath, [serverPath], {
    env: {
      ...process.env,
      PORT: String(port),
      SUPER_PROJECTS_DATA_DIR: temporaryDirectory,
    },
    stdio: ["ignore", "pipe", "pipe"],
  });
  const startup = new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error(`Server did not start. Output: ${readyOutput}`)), 10000);
    child.stdout.on("data", chunk => {
      readyOutput += chunk.toString();
      if (readyOutput.includes("is running at")) {
        clearTimeout(timeout);
        resolve();
      }
    });
    child.stderr.on("data", chunk => { readyOutput += chunk.toString(); });
    child.once("error", error => {
      clearTimeout(timeout);
      reject(error);
    });
    child.once("exit", code => {
      clearTimeout(timeout);
      reject(new Error(`Server exited before starting (${code}). ${readyOutput}`));
    });
  });
  await startup;
});

after(async () => {
  if (child && child.exitCode === null) {
    child.kill("SIGTERM");
    await once(child, "exit");
  }
  rmSync(temporaryDirectory, { recursive: true, force: true });
});

async function post(path, body, cookie) {
  const headers = {
    "Content-Type": "application/json",
    Origin: origin,
  };
  if (cookie) headers.Cookie = cookie;
  const response = await fetch(`${origin}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  return {
    response,
    data: await response.json(),
    cookie: response.headers.get("set-cookie")?.split(";")[0],
  };
}

test("serves Bootstrap 5 assets with integrity checks and a matching content security policy", async () => {
  const response = await fetch(origin);
  const html = await response.text();
  const policy = response.headers.get("content-security-policy");

  assert.equal(response.status, 200);
  assert.match(html, /bootstrap@5\.0\.2\/dist\/css\/bootstrap\.min\.css/);
  assert.match(html, /bootstrap@5\.0\.2\/dist\/js\/bootstrap\.bundle\.min\.js/);
  assert.match(html, /integrity="sha384-EVSTQN3\/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC"/);
  assert.match(html, /integrity="sha384-MrcW6ZMFYlzcLA8Nl\+NtUVF0sA7MsXsP1UyJoMp4YLEuNSfAP\+JcXn\/tWtIaxVXM"/);
  assert.match(policy, /script-src 'self' https:\/\/cdn\.jsdelivr\.net/);
  assert.match(policy, /style-src 'self' 'unsafe-inline' https:\/\/cdn\.jsdelivr\.net/);
});

test("register, login, session isolation, and logout work without storing plain-text passwords", async () => {
  const password = "Long!Unique-Phrase-9284";
  const registered = await post("/api/auth/register", { username: "First_User", password });
  assert.equal(registered.response.status, 201);
  assert.equal(registered.data.user.username, "first_user");
  assert.match(registered.response.headers.get("set-cookie"), /HttpOnly/);
  assert.match(registered.response.headers.get("set-cookie"), /SameSite=Strict/);
  assert.ok(registered.cookie);

  const me = await fetch(`${origin}/api/auth/me`, { headers: { Cookie: registered.cookie } });
  assert.equal((await me.json()).user.username, "first_user");

  const incorrectPassword = await post("/api/auth/login", { username: "first_user", password: "Wrong!Password-9284" });
  assert.equal(incorrectPassword.response.status, 401);
  assert.equal(incorrectPassword.data.error, "Invalid username or password.");

  const login = await post("/api/auth/login", { username: "FIRST_USER", password });
  assert.equal(login.response.status, 200);
  assert.equal(login.data.user.username, "first_user");

  const weak = await post("/api/auth/register", { username: "weak-user", password: "bad" });
  assert.equal(weak.response.status, 400);
  assert.match(weak.data.error, /12 characters/);

  const predictable = await post("/api/auth/register", { username: "repeat-user", password: "abababababab" });
  assert.equal(predictable.response.status, 400);
  assert.match(predictable.data.error, /less predictable/);

  const duplicate = await post("/api/auth/register", { username: "FIRST_USER", password });
  assert.equal(duplicate.response.status, 409);

  const second = await post("/api/auth/register", { username: "second_user", password: "Another!Unique-Phrase-9284" });
  assert.equal(second.response.status, 201);
  const secondMe = await fetch(`${origin}/api/auth/me`, { headers: { Cookie: second.cookie } });
  assert.equal((await secondMe.json()).user.username, "second_user");

  const csrf = await fetch(`${origin}/api/auth/logout`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
  assert.equal(csrf.status, 403);

  const logout = await post("/api/auth/logout", {}, login.cookie);
  assert.equal(logout.response.status, 200);
  const afterLogout = await fetch(`${origin}/api/auth/me`, { headers: { Cookie: login.cookie } });
  assert.equal((await afterLogout.json()).user, null);

  const storedAccounts = readFileSync(join(temporaryDirectory, "users.json"), "utf8");
  assert.equal(storedAccounts.includes(password), false);
  assert.match(storedAccounts, /"passwordHash"/);
});
