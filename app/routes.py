from flask import Blueprint, render_template, request, jsonify, current_app

from app.agents.graph import graph

from app.database.db import (
    get_connection,
    initialize_database,
    save_system_metrics,
    get_metric_history,
    update_system_alerts,
    get_alert_history
)

from app.tools.system_tool import (
    check_service_status,
    get_system_metrics
)

main = Blueprint("main", __name__)


# =====================================
# CONFIGURATION
# =====================================

SERVICES = [
    "vpn",
    "email",
    "database",
    "firewall",
    "web"
]


# =====================================
# DASHBOARD
# =====================================

@main.route("/")
def dashboard():
    return render_template("index.html")


# =====================================
# AI CHAT
# =====================================

@main.route("/api/chat", methods=["POST"])
def chat():

    data = request.get_json(silent=True) or {}
    query = data.get("message", "").strip()

    if not query:
        return jsonify({"error": "Please enter a message."}), 400

    try:
        result = graph.invoke({"user_query": query})

        return jsonify({
            "response": result.get("response", ""),
            "intent": result.get("intent", "UNKNOWN"),
            "sources": result.get("sources", "")
        })

    except Exception:
        current_app.logger.exception("Chat request failed")

        return jsonify({
            "error": "Unable to process your request. Check application logs."
        }), 500


# =====================================
# TICKET HISTORY
# =====================================

@main.route("/api/tickets", methods=["GET"])
def tickets():

    connection = None

    try:
        initialize_database()
        connection = get_connection()

        rows = connection.execute("""
            SELECT *
            FROM tickets
            ORDER BY id DESC
        """).fetchall()

        return jsonify([dict(row) for row in rows])

    except Exception:
        current_app.logger.exception("Ticket retrieval failed")

        return jsonify({
            "error": "Unable to retrieve tickets."
        }), 500

    finally:
        if connection:
            connection.close()


# =====================================
# INCIDENT DETAILS
# =====================================

@main.route("/api/tickets/<int:ticket_id>", methods=["GET"])
def incident_details(ticket_id):

    connection = None

    try:
        initialize_database()
        connection = get_connection()

        ticket = connection.execute("""
            SELECT *
            FROM tickets
            WHERE id = ?
        """, (ticket_id,)).fetchone()

        if not ticket:
            return jsonify({
                "error": "Incident not found."
            }), 404

        ticket_data = dict(ticket)

        # Retrieve linked system alert
        alert = None

        if ticket_data.get("source_alert_id") is not None:

            alert_row = connection.execute("""
                SELECT *
                FROM system_alerts
                WHERE id = ?
            """, (ticket_data["source_alert_id"],)).fetchone()

            if alert_row:
                alert = dict(alert_row)

        # Retrieve investigation notes
        notes = connection.execute("""
            SELECT *
            FROM incident_notes
            WHERE ticket_id = ?
            ORDER BY id DESC
        """, (ticket_id,)).fetchall()

        return jsonify({
            "ticket": ticket_data,
            "linked_alert": alert,
            "notes": [dict(note) for note in notes]
        })

    except Exception:
        current_app.logger.exception("Incident details retrieval failed")

        return jsonify({
            "error": "Unable to retrieve incident details."
        }), 500

    finally:
        if connection:
            connection.close()


# =====================================
# ACKNOWLEDGE INCIDENT
# =====================================

@main.route(
    "/api/tickets/<int:ticket_id>/acknowledge",
    methods=["POST"]
)
def acknowledge_incident(ticket_id):

    connection = None

    try:
        initialize_database()
        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute("""
            SELECT status
            FROM tickets
            WHERE id = ?
        """, (ticket_id,))

        ticket = cursor.fetchone()

        if not ticket:
            return jsonify({
                "error": "Incident not found."
            }), 404

        if ticket["status"] != "OPEN":
            return jsonify({
                "error": (
                    "Only OPEN incidents can be acknowledged.",
                    "Current status: " + ticket["status"]
                )
            }), 409

        cursor.execute("""
            UPDATE tickets
            SET
                status = 'ACKNOWLEDGED',
                acknowledged_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (ticket_id,))

        connection.commit()

        return jsonify({
            "message": "Incident acknowledged successfully.",
            "ticket_id": ticket_id,
            "status": "ACKNOWLEDGED"
        })

    except Exception:
        if connection:
            connection.rollback()

        current_app.logger.exception("Incident acknowledgement failed")

        return jsonify({
            "error": "Unable to acknowledge incident."
        }), 500

    finally:
        if connection:
            connection.close()


# =====================================
# ASSIGN INCIDENT
# =====================================

@main.route(
    "/api/tickets/<int:ticket_id>/assign",
    methods=["POST"]
)
def assign_incident(ticket_id):

    data = request.get_json(silent=True) or {}

    assigned_to = data.get("assigned_to", "")

    if not isinstance(assigned_to, str) or not assigned_to.strip():
        return jsonify({
            "error": "Please provide a valid analyst name."
        }), 400

    connection = None

    try:
        initialize_database()
        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute("""
            SELECT id
            FROM tickets
            WHERE id = ?
        """, (ticket_id,))

        if not cursor.fetchone():
            return jsonify({
                "error": "Incident not found."
            }), 404

        cursor.execute("""
            UPDATE tickets
            SET
                assigned_to = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (assigned_to.strip(), ticket_id))

        connection.commit()

        return jsonify({
            "message": "Incident assigned successfully.",
            "ticket_id": ticket_id,
            "assigned_to": assigned_to.strip()
        })

    except Exception:
        if connection:
            connection.rollback()

        current_app.logger.exception("Incident assignment failed")

        return jsonify({
            "error": "Unable to assign incident."
        }), 500

    finally:
        if connection:
            connection.close()


# =====================================
# ADD INVESTIGATION NOTE
# =====================================

@main.route(
    "/api/tickets/<int:ticket_id>/notes",
    methods=["POST"]
)
def add_incident_note(ticket_id):

    data = request.get_json(silent=True) or {}

    note = data.get("note", "")
    author = data.get("author", "USER")

    if not isinstance(note, str) or not note.strip():
        return jsonify({
            "error": "Investigation note cannot be empty."
        }), 400

    if not isinstance(author, str) or not author.strip():
        return jsonify({
            "error": "Author cannot be empty."
        }), 400

    connection = None

    try:
        initialize_database()
        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute("""
            SELECT id
            FROM tickets
            WHERE id = ?
        """, (ticket_id,))

        if not cursor.fetchone():
            return jsonify({
                "error": "Incident not found."
            }), 404

        cursor.execute("""
            INSERT INTO incident_notes (
                ticket_id,
                author,
                note
            )
            VALUES (?, ?, ?)
        """, (
            ticket_id,
            author.strip(),
            note.strip()
        ))

        note_id = cursor.lastrowid

        connection.commit()

        return jsonify({
            "message": "Investigation note added successfully.",
            "note_id": note_id,
            "ticket_id": ticket_id
        }), 201

    except Exception:
        if connection:
            connection.rollback()

        current_app.logger.exception("Adding incident note failed")

        return jsonify({
            "error": "Unable to add investigation note."
        }), 500

    finally:
        if connection:
            connection.close()


# =====================================
# RESOLVE INCIDENT
# =====================================

@main.route(
    "/api/tickets/<int:ticket_id>/resolve",
    methods=["POST"]
)
def resolve_incident(ticket_id):

    data = request.get_json(silent=True) or {}

    resolution_summary = data.get("resolution_summary", "")

    if (
        not isinstance(resolution_summary, str)
        or not resolution_summary.strip()
    ):
        return jsonify({
            "error": "Please provide a resolution summary."
        }), 400

    connection = None

    try:
        initialize_database()
        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute("""
            SELECT status
            FROM tickets
            WHERE id = ?
        """, (ticket_id,))

        ticket = cursor.fetchone()

        if not ticket:
            return jsonify({
                "error": "Incident not found."
            }), 404

        if ticket["status"] == "RESOLVED":
            return jsonify({
                "error": "Incident is already resolved."
            }), 409

        cursor.execute("""
            UPDATE tickets
            SET
                status = 'RESOLVED',
                resolution_summary = ?,
                resolved_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            resolution_summary.strip(),
            ticket_id
        ))

        connection.commit()

        return jsonify({
            "message": "Incident resolved successfully.",
            "ticket_id": ticket_id,
            "status": "RESOLVED",
            "resolution_summary": resolution_summary.strip()
        })

    except Exception:
        if connection:
            connection.rollback()

        current_app.logger.exception("Incident resolution failed")

        return jsonify({
            "error": "Unable to resolve incident."
        }), 500

    finally:
        if connection:
            connection.close()


# =====================================
# SERVICE MONITORING
# =====================================

@main.route("/api/services")
def services():

    results = []

    for service in SERVICES:
        results.append(check_service_status(service))

    return jsonify(results)


# =====================================
# TICKET STATISTICS
# =====================================

@main.route("/api/stats")
def stats():

    connection = None

    try:
        initialize_database()
        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) AS total,

                COALESCE(SUM(
                    CASE WHEN status = 'OPEN'
                    THEN 1 ELSE 0 END
                ), 0) AS open_tickets,

                COALESCE(SUM(
                    CASE WHEN status = 'ACKNOWLEDGED'
                    THEN 1 ELSE 0 END
                ), 0) AS acknowledged_tickets,

                COALESCE(SUM(
                    CASE WHEN status = 'IN_PROGRESS'
                    THEN 1 ELSE 0 END
                ), 0) AS in_progress_tickets,

                COALESCE(SUM(
                    CASE WHEN status = 'RESOLVED'
                    THEN 1 ELSE 0 END
                ), 0) AS resolved_tickets,

                COALESCE(SUM(
                    CASE WHEN priority = 'CRITICAL'
                    THEN 1 ELSE 0 END
                ), 0) AS critical_tickets,

                COALESCE(SUM(
                    CASE WHEN priority = 'HIGH'
                    THEN 1 ELSE 0 END
                ), 0) AS high_tickets

            FROM tickets
        """)

        result = dict(cursor.fetchone())

        return jsonify(result)

    except Exception:
        current_app.logger.exception("Ticket statistics failed")

        return jsonify({
            "error": "Unable to retrieve ticket statistics."
        }), 500

    finally:
        if connection:
            connection.close()


# =====================================
# LIVE SYSTEM MONITORING
# =====================================

@main.route("/api/system")
def system_metrics():

    try:
        initialize_database()

        metrics = get_system_metrics()

        save_system_metrics(metrics)

        update_system_alerts(metrics)

        return jsonify(metrics)

    except Exception:
        current_app.logger.exception("System monitoring failed")

        return jsonify({
            "error": "Unable to retrieve system metrics."
        }), 500


# =====================================
# HISTORICAL SYSTEM METRICS
# =====================================

@main.route("/api/system/history")
def system_metrics_history():

    try:
        initialize_database()

        limit = request.args.get("limit", 60, type=int)
        limit = max(1, min(limit, 500))

        history = get_metric_history(limit)

        return jsonify({
            "total": len(history),
            "metrics": history
        })

    except Exception:
        current_app.logger.exception("System history retrieval failed")

        return jsonify({
            "error": "Unable to retrieve system metrics history."
        }), 500


# =====================================
# SYSTEM ALERT HISTORY
# =====================================

@main.route("/api/alerts")
def alerts():

    try:
        initialize_database()

        limit = request.args.get("limit", 50, type=int)
        limit = max(1, min(limit, 500))

        alert_history = get_alert_history(limit)

        return jsonify({
            "total": len(alert_history),
            "alerts": alert_history
        })

    except Exception:
        current_app.logger.exception("Alert history retrieval failed")

        return jsonify({
            "error": "Unable to retrieve alert history."
        }), 500