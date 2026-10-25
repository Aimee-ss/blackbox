Black Box AI — Cross-Company Safe Database Access

A Python-based prototype that demonstrates controlled information sharing between Company A and Company B without returning individual database records through the normal query API.

The system stores synthetic telemetry in a shared SQLite database and provides a Python privacy gateway that validates query requests, tracks illustrative privacy budgets, adds random noise to aggregate results, and rejects simulated attempts to access confidential company records.

Security notice: This project is for local demonstration purposes only. It is not production-secure, does not provide a hardware-isolated Trusted Execution Environment (TEE), and does not implement formally verified differential privacy. Never use real company secrets or expose the unauthenticated administrative database endpoint to a network.
Table of Contents
Overview
Architecture
Project Structure
Technology Stack
Database Design
How the Privacy Gateway Works
Query Modes
Privacy Budget
Laplace Noise and Differential Privacy
API Endpoints
Installation and Setup
Running the Application
Disclaimer
Overview

Companies often want to learn from shared software telemetry without disclosing proprietary implementation details, individual performance records, or confidential keys.

Black Box AI demonstrates one possible approach:

Store synthetic telemetry from multiple companies in a central database.
Route requests through a Flask backend rather than exposing direct database access through the normal query interface.
Validate the requested tenant and query mode.
Check and deduct the tenant's illustrative privacy budget.
Return a noisy aggregate for an approved query.
Reject the simulated private-record access request without querying the confidential key.

The goal is to demonstrate the principle of controlled information sharing rather than unrestricted raw-data sharing.

The current implementation is a prototype of this architecture, not a guarantee that all company data is protected.

Architecture
text
              Company A Workspace
                       |
              Company B Workspace
                       |
                       v
              Flask Privacy Gateway
                       |
          +------------+------------+
          |            |            |
          v            v            v
      Tenant and   Query Mode   Budget Check
      Input Check   Validation
          |            |            |
          +------------+------------+
                       |
                       v
               SQLite Telemetry DB
                       |
              +--------+--------+
              |                 |
              v                 v
        Safe Aggregate     Private-Key
        + Random Noise      Request
              |                 |
              v                 v
        Approximate        Request Denied
        Fleet Average      No Key Returned

Three logical layers
Layer 1 — Private data storage

SQLite stores telemetry records belonging to Company A and Company B. The raw records remain in the database even when the query interface returns only an aggregate.

Layer 2 — Privacy gateway

The Flask backend validates the tenant identifier and query mode, checks the available demo budget, and determines which response to return.

Layer 3 — Controlled information sharing

The normal query endpoint returns an approximate fleet-wide build duration for a safe query and a rejection message for the simulated private-key access mode.

The company workspaces in the dashboard are a user-interface separation, not an independent security boundary.

Project Structure
text
blackbox-ai/
├── blackbox.py
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── main.js

File	Purpose
blackbox.py	Flask application, SQLite initialization, privacy budget, noise generation, and API endpoints
templates/index.html	Dashboard layout, company workspaces, query selectors, and database viewer
static/style.css	Dark theme, workspace panels, terminal logs, table styling, and responsive layout
static/main.js	API requests, query results, logs, database refresh, and demo reset

The application uses Flask's standard template and static-file directories to serve the frontend.

Technology Stack
Python: Backend logic and application orchestration.
Flask: HTTP server, routing, and JSON API responses.
SQLite: In-memory storage of synthetic telemetry.
HTML: Dashboard structure.
CSS: Dashboard presentation and responsive styling.
JavaScript: Frontend interaction and asynchronous API requests.
Laplace noise: An illustrative technique for perturbing aggregate results.
Database Design

The init_db() function creates a SQLite table called shared_telemetry.

Schema
Field	Type	Purpose
id	Integer	Unique, automatically generated record identifier
company_owner	Text	Identifies the company associated with the record
build_duration_sec	Real	Software build duration in seconds
active_bugs	Integer	Number of active software bugs
proprietary_patch_key	Text	Synthetic confidential key used in the demonstration
Synthetic sample data

The application initializes four records.

ID	Company	Build duration	Active bugs	Example key
1	Company_A	42.5	12	PATCH_SECURE_A88X
2	Company_A	48.1	8	PATCH_SECURE_A12B
3	Company_B	55.4	24	KEY_ENCRYPT_B991
4	Company_B	51.9	19	KEY_ENCRYPT_B443

These values are fictional and must not be replaced with real confidential information in this demonstration.

Database lifecycle

The database is created using:

python
sqlite3.connect(":memory:", check_same_thread=False)


This means:

The database is held in memory.
The initial records are created when the Python process starts.
The database contents disappear when the process stops.
The sample data is recreated on the next application startup.

The db_lock protects the shared SQLite connection from simultaneous access by multiple request handlers.

How the Privacy Gateway Works
1. Company A submits a request

The frontend sends a JSON request to /api/query containing the tenant identifier and query mode.

Example:

json
{
  "tenant": "A",
  "mode": "safe"
}


The Flask backend checks whether the tenant and mode are recognized.

Important: The current version trusts the tenant identifier supplied by the client. It does not authenticate the user or establish that the requester actually belongs to Company A.
2. The backend checks the demo budget

Each tenant starts with a budget of 2.00 illustrative units.

The gateway checks whether sufficient budget remains and deducts the relevant query cost.

3. The backend handles the query

For a safe query, the application calculates the average build duration across all four records, generates random noise, and returns an approximate result.

For an attack query, the application returns a rejection message without executing a query for the other company's proprietary patch key.

4. The frontend displays the result

The JavaScript updates the workspace with:

The returned response.
The remaining demo budget.
Query-processing logs.
A security notification when a simulated private-record request is rejected.

These logs are demonstration messages. They are not a substitute for a production security audit log.

Query Modes

The prototype supports two modes: safe and attack.

Safe query — Aggregate build duration

The backend runs the following SQL query:

sql
SELECT AVG(build_duration_sec)
FROM shared_telemetry;


The raw fleet-wide average is:

42.5
+
48.1
+
55.4
+
51.9
4
=
49.475

The application adds a randomly generated noise value to the average and prevents the returned duration from falling below zero.

Illustrative output:

text
Approximate fleet average build duration: 49.62 seconds


The displayed value is an example, not a guaranteed output. Each execution can return a different result because the noise is random.

The safe query:

Returns an approximate fleet-wide aggregate.
Does not return individual telemetry rows through /api/query.
Does not return the proprietary patch keys.
Includes explanatory logs and the remaining demo budget.

Scope limitation: The safe query calculates the average across both companies. It does not currently filter the aggregate to Company A's records or Company B's records.

Attack query — Simulated private-key access

The attack mode represents an attempt to access the other company's confidential key.

The backend returns a rejection message similar to:

text
Request denied. Private company records are not available
through this query.


It also returns logs indicating that access was rejected.

The implementation does not query the private key in this branch. However, the request still consumes 1.50 budget units because the budget deduction occurs before the query mode is processed.

The attack mode is a predefined demonstration scenario, not a general-purpose security testing engine.

Privacy Budget

The application initializes the budgets as follows:

python
privacy_budgets = {
    "A": 2.00,
    "B": 2.00,
}

QUERY_COSTS = {
    "safe": 0.10,
    "attack": 1.50,
}

Example budget usage
Query	Cost	Remaining from 2.00
Initial budget	0.00	2.00
One safe query	0.10	1.90
One attack query, from a fresh budget	1.50	0.50

The budget is maintained independently for tenants A and B, with access synchronized by budget_lock.

When the remaining budget is insufficient, the request is rejected.

Current limitations
The budget is stored in process memory.
Restarting the application resets the budgets.
The reset endpoint restores both budgets.
The costs are illustrative values rather than parameters in a formally implemented differential-privacy accounting system.
The code does not calibrate the Laplace noise using the remaining budget or the requested epsilon cost.

Therefore, the budget demonstrates a useful design concept but does not prove a particular mathematical privacy guarantee.

Laplace Noise and Differential Privacy

The application generates noise using a custom Laplace sampling function:

python
def generate_laplace_noise(scale):
    if scale <= 0:
        return 0.0

    u = random.random() - 0.5

    return (
        -scale
        * math.copysign(1.0, u)
        * math.log1p(-2.0 * abs(u))
    )


For safe queries, the noise is generated and added to the raw average:

python
noise = generate_laplace_noise(scale=0.5)
protected_average = max(0.0, raw_average + noise)


The intention is to make the reported aggregate less directly revealing than an exact result.

However, adding random noise alone does not establish differential privacy.

A rigorous implementation requires, among other things:

A defined privacy model and protected unit of data.
Appropriate bounds on input data.
A sensitivity calculation for each supported query.
Noise calibrated to the sensitivity and privacy parameters.
Accounting for privacy loss across repeated queries.
Controls that prevent query manipulation or reconstruction attacks.

The prototype's illustrative epsilon costs are not connected to a formal privacy accountant. Its noise scale is fixed at 0.5, independent of the query's privacy cost.

The implementation must therefore not be described as providing a verified differential-privacy guarantee.

API Endpoints
Method	Endpoint	Purpose
GET	/	Serves the dashboard
POST	/api/query	Processes safe or attack-mode queries
GET	/api/admin/view-db	Returns all demo database rows
POST	/api/reset	Resets both privacy budgets
POST /api/query

Request:

json
{
  "tenant": "A",
  "mode": "safe"
}


A successful query returns a JSON response containing its status, remaining budget, output, and logs.

Example structure:

json
{
  "status": "APPROVED",
  "remaining_budget": 1.9,
  "output": "Approximate fleet average build duration: 49.62 seconds",
  "logs": [
    "Authorized aggregate query accepted.",
    "Database returned an aggregate, not individual rows."
  ]
}


The numerical result and remaining budget depend on the request history and generated noise.

GET /api/admin/view-db

This endpoint returns the raw records, including the simulated confidential patch keys.

Critical security limitation: The endpoint has no authentication or administrator-only authorization. Anyone who can reach it can retrieve all rows.

It exists only to support the local demonstration and should be removed or properly protected before any deployment.

POST /api/reset

Resets the in-memory budgets to their initial values:

json
{
  "status": "RESET_SUCCESS"
}


The reset endpoint does not recreate the database; the sample records remain unchanged.

Installation and Setup
Prerequisites
Python 3.9 or later recommended.
pip.
A modern web browser.
A terminal or command prompt.
1. Create the project directory

Create the following folders and files:

text
blackbox-ai/
├── blackbox.py
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── main.js


Place the corresponding project code in each file.

2. Install Flask

Open a terminal in the project directory and run:

bash
python -m pip install flask

3. Optional: Create a virtual environment

Create one using:

bash
python -m venv .venv


Activate it on Windows:

powershell
.venv\Scripts\Activate.ps1


On macOS or Linux:

bash
source .venv/bin/activate


Then install Flask inside the environment:

bash
python -m pip install flask

4. Start the application

Run:

bash
python blackbox.py


The application prints its local dashboard address and attempts to open the browser automatically.

5. Open the dashboard

Navigate to:

http://127.0.0.1:5050/

The Flask server is configured to listen on the loopback address 127.0.0.1, on port 5050.

Running the Application

Once the dashboard loads, you can explore the following features:

Submit a safe query: Select the safe query in either company workspace and submit it to view an approximate fleet-wide build duration.
Simulate a private-key request: Select the attack mode to see the rejection response and security logs.
Review the demo database: Use the database viewer to inspect the synthetic rows. This feature deliberately exposes raw demo records and must not be used as a production admin interface.
Observe budget changes: Compare the remaining budget before and after each request.
Reset the demonstration: Click Reset Demo to restore both tenant budgets to 2.00 and refresh the database display.

Keep the server running while interacting with the dashboard. If the server stops, frontend API requests will fail.

Disclaimer

Black Box AI is an educational prototype for demonstrating controlled data sharing, aggregate queries, budget tracking, and simulated access rejection.

It does not guarantee confidentiality, isolation between companies, protection against reconstruction, or formally verified differential privacy. Its raw-data administrative endpoint is intentionally demonstrative and unsafe for production use.

Use synthetic data only. Do not expose this prototype to a public or company network without first implementing and validating appropriate security control.
