## Python HTML Studio



A local, dependency-free project switcher. Python stores multiple named projects and multiple named CSS/JavaScript assets in `projects.json`. The HTML page previews and switches between them.



## Start



```bash

python studio.py

```



This starts the local server, opens the studio page in your browser at `http://127.0.0.1:8000/index.html`, and shows the interactive `studio>` prompt in the terminal. Use the prompt to create and edit projects while the browser preview is connected. Keep the terminal open while using the studio; enter `quit` or press Ctrl+C to stop it.

To use the command-line editor without starting the browser server, run:



```bash

python studio.py interactive

```



Or manage projects directly with command-line commands:



```bash

python studio.py new "My Page"

python studio.py html my-page page\_body.html

python studio.py css my-page main-style styles.css

python studio.py css my-page mobile-style mobile.css
python studio.py js my-page controls app.js
python studio.py js my-page effects effects.js
python studio.py icon my-page logo logo.png
python studio.py backup projects
python studio.py serve
```

The `source` can be a file path or short inline code. Using files is recommended for larger code.

At the interactive `studio>` prompt, enter `icon` and provide a project, icon name, and image file path to add an icon. Reference it in HTML or CSS as `icon:NAME`, for example `<img src="icon:logo" alt="Logo">`. Supported icon files are GIF, JPEG, PNG, SVG, ICO, and WebP. Use `remove PROJECT icon NAME` to remove one. Enter `backup projects` to create a timestamped copy of `projects.json` in the `backups` folder.



The project selector switches pages. The browser refreshes project data every three seconds and only reloads the preview when the selected project changes or its saved content is updated.



Export one project as a normal standalone HTML file:



```bash

python studio.py export my-page finished.html

```



No Flask or other packages are required. Python 3.9+ is recommended.



\### Entering multiline code

Each project has one main HTML page, so `html` updates that page and does not ask for an asset name. First create the project with `new`, then enter `html` and its project ID/name. Press Enter for each code line; blank lines are preserved. When finished, type `.end` on its own line and press Enter to save. CSS and JavaScript assets do have names. Startup errors print a traceback and prompt you to press Enter before closing.



