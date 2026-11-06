/* ============================================
   AIOpsGenie - INTEGRATED FRONTEND
   Dashboard + Monitoring + AI + Incidents
============================================ */

"use strict";


/* ============================================
   GLOBAL CONFIGURATION
============================================ */

const API = {
    chat: "/api/chat",
    tickets: "/api/tickets",
    stats: "/api/stats",
    system: "/api/system",
    history: "/api/system/history?limit=60",
    alerts: "/api/alerts?limit=50",
    services: "/api/services"
};

let selectedIncidentId = null;

let cpuChart = null;
let memoryChart = null;
let diskChart = null;

let dashboardRefreshTimer = null;


/* ============================================
   GENERAL HELPERS
============================================ */

function getElement(id) {
    return document.getElementById(id);
}


function createElement(tag, className = "", text = "") {

    const element = document.createElement(tag);

    if (className) {
        element.className = className;
    }

    if (text !== undefined && text !== null) {
        element.textContent = String(text);
    }

    return element;

}


async function apiRequest(url, options = {}) {

    const response = await fetch(url, {
        cache: "no-store",
        ...options
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || `Request failed: ${response.status}`);
    }

    return data;

}


function showError(container, message) {

    if (!container) return;

    container.replaceChildren(
        createElement("p", "notice", message)
    );

}


function formatDate(value) {

    if (!value) return "N/A";

    return String(value);

}


function createTable(headers, rows) {

    const table = createElement("table");

    const thead = createElement("thead");
    const headerRow = createElement("tr");

    headers.forEach(header => {
        headerRow.appendChild(
            createElement("th", "", header)
        );
    });

    thead.appendChild(headerRow);

    const tbody = createElement("tbody");

    rows.forEach(row => {
        tbody.appendChild(row);
    });

    table.append(thead, tbody);

    return table;

}


/* ============================================
   AI ASSISTANT
============================================ */

function addMessage(message, sender) {

    const container = getElement("chatMessages");

    if (!container) return;

    const messageElement = createElement(
        "div",
        `message ${sender}`,
        message
    );

    container.appendChild(messageElement);

    container.scrollTop = container.scrollHeight;

}


async function handleChat(event) {

    event.preventDefault();

    const input = getElement("userMessage");
    const form = getElement("chatForm");

    const message = input.value.trim();

    if (!message) return;

    addMessage(message, "user");

    input.value = "";

    const button = form.querySelector("button");

    button.disabled = true;
    button.textContent = "Thinking...";

    try {

        const data = await apiRequest(API.chat, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: message
            })

        });

        addMessage(
            data.response || "No response received.",
            "bot"
        );

        if (data.sources) {

            addMessage(
                `Sources: ${data.sources}`,
                "bot"
            );

        }

        await Promise.all([
            loadTickets(),
            loadStats()
        ]);

    } catch (error) {

        addMessage(
            `Error: ${error.message}`,
            "bot"
        );

    } finally {

        button.disabled = false;
        button.textContent = "Send";

        input.focus();

    }

}


/* ============================================
   SYSTEM HEALTH MONITORING
============================================ */

function createMetricCard(title, value, description) {

    const card = createElement("div", "card metric-card");

    card.appendChild(
        createElement("h3", "", title)
    );

    card.appendChild(
        createElement("div", "metric-value", `${value}%`)
    );

    const progressTrack = createElement(
        "div",
        "progress-track"
    );

    const progressBar = createElement(
        "div",
        "progress-bar"
    );

    progressBar.style.width = `${Math.max(0, Math.min(100, value))}%`;

    progressTrack.appendChild(progressBar);

    card.appendChild(progressTrack);

    card.appendChild(
        createElement("p", "metric-description", description)
    );

    return card;

}


async function loadSystemMetrics() {

    const container = getElement("systemCards");
    const healthBadge = getElement("systemHealth");
    const updated = getElement("systemUpdated");

    try {

        const metrics = await apiRequest(API.system);

        container.replaceChildren();

        container.appendChild(
            createMetricCard(
                "CPU Usage",
                metrics.cpu_percent,
                "Processor utilization"
            )
        );

        container.appendChild(
            createMetricCard(
                "RAM Usage",
                metrics.memory_percent,
                `${metrics.memory_used_gb} GB / ${metrics.memory_total_gb} GB`
            )
        );

        container.appendChild(
            createMetricCard(
                "Disk Usage",
                metrics.disk_percent,
                `${metrics.disk_used_gb} GB / ${metrics.disk_total_gb} GB`
            )
        );

        healthBadge.textContent = metrics.health;

        healthBadge.className =
            `health-badge ${String(metrics.health).toLowerCase()}`;

        updated.textContent =
            `Last updated: ${new Date().toLocaleTimeString()}`;

    } catch (error) {

        showError(container, error.message);

        healthBadge.textContent = "Unavailable";

        healthBadge.className = "health-badge critical";

    }

}


/* ============================================
   HISTORICAL METRICS CHARTS
============================================ */

function createMetricChart(canvasId, label, color, labels, values, existingChart) {

    const canvas = getElement(canvasId);

    if (!canvas || typeof Chart === "undefined") {
        return existingChart;
    }

    if (existingChart) {

        existingChart.data.labels = labels;

        existingChart.data.datasets[0].data = values;

        existingChart.update("none");

        return existingChart;

    }

    return new Chart(canvas, {

        type: "line",

        data: {

            labels: labels,

            datasets: [{

                label: label,

                data: values,

                borderColor: color,

                backgroundColor: color + "22",

                borderWidth: 2,

                fill: true,

                tension: 0.3,

                pointRadius: 2

            }]

        },

        options: {

            responsive: true,

            maintainAspectRatio: true,

            animation: false,

            scales: {

                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: value => `${value}%`
                    }
                }

            },

            plugins: {

                legend: {
                    display: true
                }

            }

        }

    });

}


async function loadMetricHistory() {

    try {

        const data = await apiRequest(API.history);

        const metrics = data.metrics || [];

        if (!metrics.length) {
            return;
        }

        const labels = metrics.map(item => {

            if (!item.recorded_at) return "";

            return item.recorded_at.split(" ")[1] || item.recorded_at;

        });

        cpuChart = createMetricChart(
            "cpuChart",
            "CPU Usage",
            "#38bdf8",
            labels,
            metrics.map(item => item.cpu_percent),
            cpuChart
        );

        memoryChart = createMetricChart(
            "memoryChart",
            "RAM Usage",
            "#a78bfa",
            labels,
            metrics.map(item => item.memory_percent),
            memoryChart
        );

        diskChart = createMetricChart(
            "diskChart",
            "Disk Usage",
            "#4ade80",
            labels,
            metrics.map(item => item.disk_percent),
            diskChart
        );

    } catch (error) {

        console.error("Metric history error:", error);

    }

}


/* ============================================
   SYSTEM ALERTS
============================================ */

function createAlertCard(alert, historical = false) {

    const card = createElement(
        "div",
        `card alert-card ${String(alert.severity).toLowerCase()}`
    );

    card.appendChild(
        createElement(
            "h3",
            "",
            `${alert.metric} — ${alert.severity}`
        )
    );

    card.appendChild(
        createElement(
            "p",
            "",
            alert.message
        )
    );

    card.appendChild(
        createElement(
            "p",
            "",
            `Current value: ${alert.value}% | Threshold: ${alert.threshold}%`
        )
    );

    card.appendChild(
        createElement(
            "small",
            "",
            `Created: ${formatDate(alert.created_at)}`
        )
    );

    if (historical && alert.status === "RESOLVED") {

        card.appendChild(
            createElement(
                "p",
                "alert-resolved",
                `Resolved: ${formatDate(alert.resolved_at)}`
            )
        );

    }

    return card;

}


async function loadAlerts() {

    const activeContainer = getElement("activeAlerts");
    const historyContainer = getElement("alertHistory");
    const badge = getElement("activeAlertBadge");

    try {

        const data = await apiRequest(API.alerts);

        const alerts = data.alerts || [];

        const active = alerts.filter(
            alert => alert.status === "ACTIVE"
        );

        const resolved = alerts.filter(
            alert => alert.status === "RESOLVED"
        );

        activeContainer.replaceChildren();

        historyContainer.replaceChildren();

        badge.textContent = `${active.length} Active`;

        badge.className = active.length
            ? "health-badge warning"
            : "health-badge healthy";

        if (!active.length) {

            activeContainer.appendChild(
                createElement(
                    "p",
                    "alert-empty",
                    "No active system alerts."
                )
            );

        } else {

            active.forEach(alert => {

                activeContainer.appendChild(
                    createAlertCard(alert)
                );

            });

        }

        if (!alerts.length) {

            historyContainer.appendChild(
                createElement(
                    "p",
                    "alert-empty",
                    "No alert history available."
                )
            );

        } else {

            alerts.forEach(alert => {

                historyContainer.appendChild(
                    createAlertCard(alert, true)
                );

            });

        }

    } catch (error) {

        showError(activeContainer, error.message);

        showError(historyContainer, error.message);

    }

}


/* ============================================
   SERVICE OVERVIEW
============================================ */

function serviceStatusClass(status) {

    return String(status).toLowerCase() === "operational"
        ? "operational"
        : "notice";

}


async function loadServices() {

    const cardsContainer = getElement("serviceCards");
    const tableContainer = getElement("serviceTable");

    try {

        const services = await apiRequest(API.services);

        cardsContainer.replaceChildren();

        const rows = [];

        services.forEach(service => {

            const card = createElement("div", "card");

            card.appendChild(
                createElement(
                    "h3",
                    "",
                    service.service.toUpperCase()
                )
            );

            card.appendChild(
                createElement(
                    "p",
                    serviceStatusClass(service.status),
                    service.status
                )
            );

            card.appendChild(
                createElement(
                    "p",
                    "metric-description",
                    service.message
                )
            );

            cardsContainer.appendChild(card);

            const row = createElement("tr");

            [
                service.service.toUpperCase(),
                service.status,
                service.message
            ].forEach(value => {

                row.appendChild(
                    createElement("td", "", value)
                );

            });

            rows.push(row);

        });

        tableContainer.replaceChildren(
            createTable(
                ["Service", "Status", "Description"],
                rows
            )
        );

    } catch (error) {

        showError(cardsContainer, error.message);

        showError(tableContainer, error.message);

    }

}


/* ============================================
   TICKET HISTORY
============================================ */

async function loadTickets() {

    const container = getElement("ticketTable");

    try {

        const tickets = await apiRequest(API.tickets);

        if (!Array.isArray(tickets)) {
            throw new Error("Invalid ticket response.");
        }

        if (!tickets.length) {

            container.textContent = "No tickets available.";

            return;

        }

        const rows = [];

        tickets.forEach(ticket => {

            const row = createElement("tr");

            const values = [

                ticket.id,
                ticket.title,
                ticket.priority,
                ticket.status,
                ticket.assigned_to || "Unassigned",
                ticket.created_at

            ];

            values.forEach(value => {

                row.appendChild(
                    createElement("td", "", value)
                );

            });

            rows.push(row);

        });

        container.replaceChildren(

            createTable(
                [
                    "ID",
                    "Title",
                    "Priority",
                    "Status",
                    "Assigned Analyst",
                    "Created At"
                ],
                rows
            )

        );

    } catch (error) {

        showError(container, error.message);

    }

}


/* ============================================
   TICKET STATISTICS
============================================ */

async function loadStats() {

    const container = getElement("statsCards");

    try {

        const stats = await apiRequest(API.stats);

        const items = [

            ["Total Tickets", stats.total],

            ["Open Tickets", stats.open_tickets],

            ["Critical Tickets", stats.critical_tickets],

            ["High Priority", stats.high_tickets]

        ];

        container.replaceChildren();

        items.forEach(([title, value]) => {

            const card = createElement("div", "card");

            card.appendChild(
                createElement("h3", "", title)
            );

            card.appendChild(
                createElement(
                    "div",
                    "metric-value",
                    value ?? 0
                )
            );

            container.appendChild(card);

        });

    } catch (error) {

        showError(container, error.message);

    }

}


/* ============================================
   INCIDENT MANAGEMENT
============================================ */

function createIncidentElement(tag, className = "", text = "") {

    return createElement(tag, className, text);

}


/* --------------------------------------------
   INCIDENT STATISTICS
-------------------------------------------- */

async function loadIncidentStats() {

    const container = getElement("incidentStats");

    try {

        const stats = await apiRequest(API.stats);

        const items = [

            ["Total Incidents", stats.total],

            ["Open", stats.open_tickets],

            ["Acknowledged", stats.acknowledged_tickets],

            ["In Progress", stats.in_progress_tickets],

            ["Resolved", stats.resolved_tickets],

            ["Critical", stats.critical_tickets]

        ];

        container.replaceChildren();

        items.forEach(([title, value]) => {

            const card = createElement(
                "div",
                "card incident-stat-card"
            );

            card.appendChild(
                createElement("h3", "", title)
            );

            card.appendChild(
                createElement(
                    "h2",
                    "incident-stat-value",
                    value ?? 0
                )
            );

            container.appendChild(card);

        });

    } catch (error) {

        showError(container, error.message);

    }

}


/* --------------------------------------------
   INCIDENT TABLE
-------------------------------------------- */

async function loadIncidents() {

    const container = getElement("incidentTable");

    try {

        const incidents = await apiRequest(API.tickets);

        if (!Array.isArray(incidents)) {
            throw new Error("Invalid incident response.");
        }

        if (!incidents.length) {

            container.textContent = "No incidents available.";

            await loadIncidentStats();

            return;

        }

        const rows = [];

        incidents.forEach(incident => {

            const row = createElement("tr");

            const values = [

                incident.id,
                incident.title

            ];

            values.forEach(value => {

                row.appendChild(
                    createElement("td", "", value)
                );

            });


            const priorityCell = createElement("td");

            priorityCell.appendChild(
                createElement(
                    "span",
                    `priority-badge ${String(incident.priority).toLowerCase()}`,
                    incident.priority
                )
            );

            row.appendChild(priorityCell);


            const statusCell = createElement("td");

            statusCell.appendChild(
                createElement(
                    "span",
                    `incident-status ${String(incident.status).toLowerCase()}`,
                    incident.status
                )
            );

            row.appendChild(statusCell);


            row.appendChild(
                createElement(
                    "td",
                    "",
                    incident.assigned_to || "Unassigned"
                )
            );

            row.appendChild(
                createElement(
                    "td",
                    "",
                    incident.created_at
                )
            );


            const actionCell = createElement("td");

            const viewButton = createElement(
                "button",
                "small-button",
                "View"
            );

            viewButton.type = "button";

            viewButton.addEventListener("click", () => {
                viewIncident(incident.id);
            });

            actionCell.appendChild(viewButton);

            row.appendChild(actionCell);

            rows.push(row);

        });

        container.replaceChildren(

            createTable(
                [
                    "ID",
                    "Incident",
                    "Priority",
                    "Status",
                    "Assigned Analyst",
                    "Created",
                    "Action"
                ],
                rows
            )

        );

        await loadIncidentStats();

    } catch (error) {

        showError(container, error.message);

    }

}


/* --------------------------------------------
   INCIDENT DETAILS
-------------------------------------------- */

async function viewIncident(ticketId) {

    const container = getElement("incidentDetailContent");

    selectedIncidentId = ticketId;

    container.textContent = "Loading incident details...";

    try {

        const data = await apiRequest(
            `/api/tickets/${ticketId}`
        );

        const ticket = data.ticket;

        container.replaceChildren();


        // Ticket information

        const details = createElement(
            "div",
            "incident-information"
        );

        const fields = [

            ["Incident ID", ticket.id],

            ["Title", ticket.title],

            ["Description", ticket.description],

            ["Priority", ticket.priority],

            ["Status", ticket.status],

            ["Assigned Analyst", ticket.assigned_to || "Unassigned"],

            ["Created At", ticket.created_at],

            ["Acknowledged At", ticket.acknowledged_at || "Not acknowledged"],

            ["Resolved At", ticket.resolved_at || "Not resolved"],

            ["Resolution Summary", ticket.resolution_summary || "Not available"]

        ];

        fields.forEach(([label, value]) => {

            const item = createElement("div", "detail-item");

            item.appendChild(
                createElement("strong", "", label)
            );

            item.appendChild(
                createElement("p", "", value ?? "")
            );

            details.appendChild(item);

        });

        container.appendChild(details);


        // Linked system alert

        if (data.linked_alert) {

            const alert = data.linked_alert;

            const alertCard = createElement(
                "div",
                "linked-alert-card"
            );

            alertCard.appendChild(
                createElement(
                    "h4",
                    "",
                    "Linked System Alert"
                )
            );

            alertCard.appendChild(
                createElement(
                    "p",
                    "",
                    `${alert.metric} | ${alert.severity} | ${alert.status}`
                )
            );

            alertCard.appendChild(
                createElement(
                    "p",
                    "",
                    alert.message
                )
            );

            container.appendChild(alertCard);

        }


        // Investigation notes

        const notesSection = createElement(
            "div",
            "investigation-section"
        );

        notesSection.appendChild(
            createElement(
                "h3",
                "",
                "Investigation Notes"
            )
        );

        const notes = data.notes || [];

        if (!notes.length) {

            notesSection.appendChild(
                createElement(
                    "p",
                    "",
                    "No investigation notes yet."
                )
            );

        } else {

            notes.forEach(note => {

                const noteCard = createElement(
                    "div",
                    "note-card"
                );

                noteCard.appendChild(
                    createElement(
                        "strong",
                        "",
                        `${note.author} — ${note.created_at}`
                    )
                );

                noteCard.appendChild(
                    createElement(
                        "p",
                        "",
                        note.note
                    )
                );

                notesSection.appendChild(noteCard);

            });

        }

        container.appendChild(notesSection);


        // Incident actions

        const actions = createElement(
            "div",
            "incident-actions"
        );

        actions.appendChild(
            createElement("h3", "", "Incident Actions")
        );


        // Assign analyst

        const assignForm = createElement(
            "form",
            "incident-form"
        );

        const analystInput = createElement("input");

        analystInput.type = "text";

        analystInput.placeholder = "Enter analyst name";

        analystInput.value = ticket.assigned_to || "";

        analystInput.required = true;

        const assignButton = createElement(
            "button",
            "",
            "Assign Analyst"
        );

        assignButton.type = "submit";

        assignForm.append(analystInput, assignButton);

        assignForm.addEventListener("submit", async event => {

            event.preventDefault();

            await performIncidentAction(
                `/api/tickets/${ticketId}/assign`,
                {
                    assigned_to: analystInput.value.trim()
                }
            );

        });

        actions.appendChild(assignForm);


        // Acknowledge

        if (ticket.status === "OPEN") {

            const acknowledgeButton = createElement(
                "button",
                "action-button",
                "Acknowledge Incident"
            );

            acknowledgeButton.addEventListener("click", async () => {

                await performIncidentAction(
                    `/api/tickets/${ticketId}/acknowledge`,
                    {}
                );

            });

            actions.appendChild(acknowledgeButton);

        }


        // Add note

        if (ticket.status !== "RESOLVED") {

            const noteForm = createElement(
                "form",
                "incident-form"
            );

            const noteInput = createElement("textarea");

            noteInput.placeholder = "Enter investigation findings...";

            noteInput.required = true;

            const noteButton = createElement(
                "button",
                "",
                "Add Investigation Note"
            );

            noteButton.type = "submit";

            noteForm.append(noteInput, noteButton);

            noteForm.addEventListener("submit", async event => {

                event.preventDefault();

                await performIncidentAction(
                    `/api/tickets/${ticketId}/notes`,
                    {
                        author: "SOC Analyst",
                        note: noteInput.value.trim()
                    }
                );

            });

            actions.appendChild(noteForm);

        }


        // Resolve incident

        if (ticket.status !== "RESOLVED") {

            const resolveForm = createElement(
                "form",
                "incident-form"
            );

            const resolutionInput = createElement("textarea");

            resolutionInput.placeholder = "Enter resolution summary...";

            resolutionInput.required = true;

            const resolveButton = createElement(
                "button",
                "resolve-button",
                "Resolve Incident"
            );

            resolveButton.type = "submit";

            resolveForm.append(
                resolutionInput,
                resolveButton
            );

            resolveForm.addEventListener("submit", async event => {

                event.preventDefault();

                if (!confirm("Are you sure you want to resolve this incident?")) {
                    return;
                }

                await performIncidentAction(
                    `/api/tickets/${ticketId}/resolve`,
                    {
                        resolution_summary: resolutionInput.value.trim()
                    }
                );

            });

            actions.appendChild(resolveForm);

        }

        container.appendChild(actions);

        getElement("incidentDetails").scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    } catch (error) {

        showError(container, error.message);

    }

}


/* --------------------------------------------
   INCIDENT ACTION HANDLER
-------------------------------------------- */

async function performIncidentAction(url, payload) {

    try {

        const data = await apiRequest(url, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(payload)

        });

        alert(data.message || "Incident updated successfully.");

        await Promise.all([

            loadIncidents(),

            loadTickets(),

            loadStats(),

            loadAlerts()

        ]);

        if (selectedIncidentId !== null) {
            await viewIncident(selectedIncidentId);
        }

    } catch (error) {

        alert(error.message);

        console.error("Incident action failed:", error);

    }

}


/* ============================================
   DASHBOARD REFRESH
============================================ */

async function refreshDashboard() {

    await Promise.allSettled([

        loadSystemMetrics(),

        loadMetricHistory(),

        loadAlerts(),

        loadServices(),

        loadTickets(),

        loadStats(),

        loadIncidents()

    ]);

}


function startDashboard() {

    // Chat form

    const chatForm = getElement("chatForm");

    if (chatForm) {

        chatForm.addEventListener(
            "submit",
            handleChat
        );

    }


    // Incident refresh button

    const refreshButton = getElement("refreshIncidents");

    if (refreshButton) {

        refreshButton.addEventListener("click", async () => {

            await loadIncidents();

            if (selectedIncidentId !== null) {
                await viewIncident(selectedIncidentId);
            }

        });

    }


    // Initial dashboard loading

    refreshDashboard();


    // Refresh monitoring data every 10 seconds

    dashboardRefreshTimer = setInterval(() => {

        Promise.allSettled([

            loadSystemMetrics(),

            loadMetricHistory(),

            loadAlerts()

        ]);

    }, 10000);


    // Refresh incident data every 15 seconds

    setInterval(() => {

        loadIncidents();

    }, 15000);

}


/* ============================================
   APPLICATION INITIALIZATION
============================================ */

if (document.readyState === "loading") {

    document.addEventListener(
        "DOMContentLoaded",
        startDashboard
    );

} else {

    startDashboard();

}