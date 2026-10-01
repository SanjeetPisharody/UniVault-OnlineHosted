# UniVault

UniVault is a Flask and SQLite portal for browsing, previewing, downloading, and sharing university study materials.

The application runs locally on the host computer, with its SQLite database and uploaded files stored on that computer. The local Flask server can be made publicly accessible through **Tailscale Funnel**, without port forwarding or a paid domain.

## Features

* Public material browsing, search, filters, previews, downloads, statistics, and contributor leaderboard.
* Student accounts with uploads, reviews, ratings, upvotes, persistent bookmarks, profile, and account settings.
* Administrator dashboard for users and uploaded materials.
* Protected administrator and owner actions.
* Responsive academic atlas interface with an animated isometric library illustration.
* Resource-type collections.
* Keyboard shortcut for search (`/`).
* Saved grid or list layout preference.
* Profile photo support for users and material uploaders.
* SQLite storage for users, materials, reviews, bookmarks, ratings, and uploaded file data.

---

## Run the website locally

Install the Python packages once:

```powershell
python -m pip install -r requirements.txt
```

Start UniVault:

```powershell
cd A:\Univault-main
python app.py
```

Flask runs locally at:

```text
http://127.0.0.1:5000
```

UniVault does not require Tailscale to run locally.

The Flask application and the Tailscale Funnel are separate processes. Starting Flask does not automatically start Tailscale Funnel.

---

## Public hosting with Tailscale Funnel

UniVault can be exposed to the Internet using Tailscale Funnel.

### Requirements

The hosting computer must have:

* Windows running
* Python installed
* UniVault installed
* Tailscale installed and signed in
* An active Internet connection
* The Flask application running
* Tailscale running in the background

No port forwarding is required.

No paid domain is required for the Tailscale-provided public address.

### Start UniVault

Open PowerShell:

```powershell
cd A:\Univault-main
python app.py
```

Keep this window running.

### Start Tailscale Funnel

Open a second PowerShell window and run:

```powershell
tailscale funnel 5000
```

Tailscale will provide the public HTTPS address for the application.

Keep both processes running:

```text
PowerShell 1
└── Flask / UniVault
    └── python app.py

PowerShell 2
└── Tailscale Funnel
    └── tailscale funnel 5000
```

The public website is forwarded to the Flask application running on the hosting computer.

---

## Important hosting limitation

UniVault is **self-hosted on the Windows computer**.

It is not running on a permanent cloud server.

Therefore, the public website is available only while the hosting computer is:

* Powered on.
* Connected to the Internet.
* Connected to the Tailscale network.
* Running Tailscale.
* Running the UniVault Flask application.
* Running the Tailscale Funnel.

If the hosting computer is shut down, restarted without starting UniVault again, disconnected from the Internet, or Tailscale/Funnel is stopped, the public website will become unavailable.

### Example

```text
Hosting laptop ON
        │
        ├── Internet connected
        │
        ├── Tailscale running
        │
        ├── Flask running
        │
        └── Tailscale Funnel running
                    │
                    ▼
             Public UniVault
```

The database and uploaded files remain on the hosting computer.

---

## Data storage

UniVault uses SQLite.

The primary database is:

```text
data/univault.db
```

Uploaded files are stored locally under:

```text
static/uploads/
```

The application creates the `data/` directory when required.

The database contains information such as:

* User accounts
* Administrator account
* Materials
* Reviews
* Ratings
* Bookmarks
* Upvotes
* Contributors
* Material metadata
* Uploaded file data where applicable

### Important

The GitHub repository should contain the **application source code**, not the live database or user-uploaded content.

Do not commit:

```text
data/univault.db
data/.univault_secret_key
static/uploads/
```

These files may contain private user data, uploaded documents, authentication information, or other runtime data.

---

## Secret key

UniVault generates a secret key when required and stores it locally in:

```text
data/.univault_secret_key
```

An environment variable can also be used:

```powershell
$env:UNIVAULT_SECRET_KEY = "your-secret-key"
```

The environment variable takes precedence over the local secret-key file.

Never commit or share the secret key.

---

## Accounts and security

Registration is available through:

```text
/register
```

New registrations create student accounts.

Login is available through:

```text
/login
```

The initial administrator account is seeded as:

```text
Sanjeet
```

The administrator password is protected using Werkzeug's secure password hashing.

The administrator password is not stored as plaintext, logged, rendered, or returned by the API.

The permanent owner account is protected separately using the stored owner flag in the database.

Server-side authorization checks are used for administrator and student actions. Browser-side state is not trusted for authorization.

State-changing requests use session-based CSRF protection.

---

## Public access security

Tailscale Funnel makes the selected UniVault service publicly accessible.

Anyone who has the public address may be able to reach the website, so application-level security remains important.

Before making UniVault publicly accessible:

* Use a strong administrator password.
* Do not share administrator credentials.
* Do not expose the SQLite database directly.
* Do not expose the `data/` directory as a static web directory.
* Do not expose `.env` files or secret-key files.
* Do not commit passwords, tokens, or API keys to GitHub.
* Keep Flask, Python, Tailscale, and project dependencies updated.
* Review uploaded-file validation before allowing unrestricted public uploads.
* Keep regular backups of the database and uploaded files.
* Stop Tailscale Funnel when public access is no longer required.

Tailscale Funnel provides the public network connection; UniVault remains responsible for authentication, authorization, CSRF protection, file validation, and application security.

---

## Backup

Because UniVault is self-hosted, the hosting computer is also the primary location of the application data.

Back up both:

```text
data/univault.db
```

and:

```text
static/uploads/
```

For a complete backup, preserve the entire project data and upload directories.

Do not upload private runtime data to the public GitHub repository.

---

## Moving UniVault to another computer

UniVault can be moved to another Windows computer.

Copy the project source code and install the required dependencies:

```powershell
python -m pip install -r requirements.txt
```

If transferring existing data, copy:

```text
data/univault.db
```

and:

```text
static/uploads/
```

to the corresponding locations on the new computer.

Then run:

```powershell
python app.py
```

The new computer can be connected to Tailscale and configured as the new hosting machine.

---

## Testing

Run the application tests:

```powershell
python test_app.py
```

Check Python syntax:

```powershell
python -m py_compile app.py database.py test_app.py
```

Check the JavaScript syntax:

```powershell
node --check static/js/app.js
```

Run the unittest suite:

```powershell
python -m unittest -v test_app
```

---

## Project layout

```text
UniVault/
│
├── app.py
├── database.py
├── requirements.txt
├── test_app.py
│
├── templates/
│   ├── ...
│
├── static/
│   ├── js/
│   │   └── app.js
│   ├── css/
│   └── uploads/
│
├── data/
│   ├── univault.db
│   └── .univault_secret_key
│
└── README.md
```

### Runtime files

The following are local runtime data and should not be committed to GitHub:

```text
data/
static/uploads/
```

---

## Hosting architecture

```text
                    INTERNET
                        │
                        ▼
              Tailscale Funnel
                        │
                        ▼
                Windows Laptop
                        │
                 ┌──────┴──────┐
                 │             │
                 ▼             ▼
              Flask          SQLite
           UniVault App      Database
                 │
                 ▼
           static/uploads/
```

The public connection terminates through Tailscale's Funnel service and is forwarded to the Flask application running locally on the hosting computer.

The actual UniVault application, database, and uploaded files remain on the host computer.

---

## GitHub

GitHub is used to store and version the UniVault source code.

Before pushing changes, check:

```powershell
git status
```

Make sure private runtime data is not included.

Then:

```powershell
git add .
git commit -m "Update UniVault"
git push origin main
```

Do not commit:

```text
data/univault.db
data/.univault_secret_key
static/uploads/
.env
```

---

## Important distinction

GitHub, Tailscale, Flask, and SQLite have different roles:

```text
GitHub
└── Source-code storage and version control

Tailscale Funnel
└── Public access to the locally hosted application

Flask
└── Runs the UniVault web application

SQLite
└── Stores UniVault application data

Windows laptop
└── Actual hosting computer
```

If the hosting laptop is turned off, UniVault's public website will not be available until the laptop is powered on, connected to the Internet, and the required services are running again.
