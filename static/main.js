
const API_URL = window.location.origin;

function writeLog(tenant, message, cls = "green") {
    const box = document.getElementById("log" + tenant);
    if (!box) return;

    const line = document.createElement("div");
    line.className = cls;
    line.textContent =
        "[" + new Date().toLocaleTimeString() + "] " + message;

    box.appendChild(line);
    box.scrollTop = box.scrollHeight;
}

async function sendQuery(tenant) {
    const mode = document.getElementById("queryMode" + tenant).value;
    const button = document.getElementById("btn" + tenant);

    writeLog(tenant, "Sending query to local privacy gateway...", "blue");

    if (button) button.disabled = true;

    try {
        const response = await fetch(API_URL + "/api/query", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                tenant: tenant,
                mode: mode
            })
        });

        const data = await response.json();

        if (!response.ok || data.status === "ERROR") {
            writeLog(tenant, data.log || "Query failed.", "red");
        }

        if (data.remaining_budget !== undefined) {
            document.getElementById("budgetDisplay" + tenant)
                .textContent = Number(data.remaining_budget).toFixed(2);
        }

        document.getElementById("out" + tenant).textContent =
            "Returned payload: " + (data.output || data.log || "No output");

        (data.logs || []).forEach(message => {
            let cls = "green";

            if (message.includes("ACCESS CONTROL")) {
                cls = "red";
            } else if (message.includes("DP ENGINE")) {
                cls = "pink";
            }

            writeLog(tenant, message, cls);
        });

        if (mode === "attack" && data.status === "REJECTED") {
            const rival = tenant === "A" ? "B" : "A";

            writeLog(
                rival,
                "Security notice: private-record access attempt was rejected.",
                "orange"
            );
        }
    } catch (error) {
        writeLog(
            tenant,
            "Connection failed. Is Flask running?",
            "red"
        );
    } finally {
        if (button) button.disabled = false;
    }
}

async function refreshDatabaseTable() {
    try {
        const response = await fetch(API_URL + "/api/admin/view-db");

        if (!response.ok) {
            throw new Error("Database request failed");
        }

        const data = await response.json();
        const body = document.getElementById("dbTableBody");

        body.replaceChildren();

        (data.database_rows || []).forEach(row => {
            const tr = document.createElement("tr");

            [
                row.id,
                row.company_owner,
                row.build_duration_sec + " s",
                row.active_bugs,
                row.proprietary_patch_key
            ].forEach(value => {
                const td = document.createElement("td");
                td.textContent = String(value);
                tr.appendChild(td);
            });

            body.appendChild(tr);
        });
    } catch (error) {
        console.error("Database view failed:", error);
    }
}

async function resetEcosystem() {
    const button = document.getElementById("resetButton");
    if (button) button.disabled = true;

    try {
        const response = await fetch(API_URL + "/api/reset", {
            method: "POST"
        });

        if (!response.ok) {
            throw new Error("Reset request failed");
        }

        for (const tenant of ["A", "B"]) {
            document.getElementById("budgetDisplay" + tenant)
                .textContent = "2.00";

            document.getElementById("out" + tenant).textContent =
                "Output: demo reset.";

            document.getElementById("log" + tenant).replaceChildren();

            writeLog(tenant, "Demo workspace initialized.");
        }

        await refreshDatabaseTable();
    } catch (error) {
        console.error("Reset failed:", error);
    } finally {
        if (button) button.disabled = false;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-tenant]").forEach(button => {
        button.addEventListener("click", () => {
            sendQuery(button.dataset.tenant);
        });
    });

    document.getElementById("refreshDbButton")
        .addEventListener("click", refreshDatabaseTable);

    document.getElementById("resetButton")
        .addEventListener("click", resetEcosystem);

    resetEcosystem();
});
