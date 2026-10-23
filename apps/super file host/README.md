# Super Projects

A GitHub-inspired project dashboard with a small Node.js account server. It has no third-party package dependencies.

## Requirements

- Node.js 18 or newer

## Start the app

From this folder, run:

```powershell
npm start
```

Then open <http://localhost:3000>. Do not open `index.html` directly: account registration and sign-in require the Node.js server.

Run the server's account/authentication integration tests with:

```powershell
npm test
```

## Accounts and passwords

- Create an account with a unique username (3–24 letters, numbers, `_`, or `-`) and password.
- Sign in to any account you have registered by entering its username and password. There is no shared or administrator password, and you cannot sign in to another person's account without that account's password.
- Passwords must be at least 12 characters and no more than 128 UTF-8 bytes. The live strength meter calls its lowest rating **Bad** and checks for a few common weak passwords.
- The server hashes passwords with Node's scrypt implementation and a random salt; it never stores the submitted password as plain text.
- Sessions use random, HTTP-only, same-site cookies. Sign out to invalidate the current session.
- Accounts are saved in `data/users.json`; this private data directory is excluded from Git. Back it up securely if you need to preserve accounts.

## Project data and limitations

Project lists are saved in this browser's local storage, separately for each signed-in username. They are not uploaded or synchronized to the server or other devices. Public/private is still descriptive metadata and does not publish or protect projects.

The server intentionally binds to `127.0.0.1` and accepts localhost requests only. This is a local development app, not a production hosting setup. Do not expose it to the internet as-is; a public deployment needs HTTPS, secure-cookie configuration, production-grade persistent storage, backups, and operational protections.
