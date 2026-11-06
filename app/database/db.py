import sqlite3
from pathlib import Path

DB_PATH = Path("data/aiopsgenie.db")


def get_connection():

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

    # Support tickets
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT DEFAULT 'OPEN',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migration: link incident tickets to system alerts
    ticket_columns = [
        row["name"]
        for row in cursor.execute(
            "PRAGMA table_info(tickets)"
        ).fetchall()
    ]

    if "source_alert_id" not in ticket_columns:

        cursor.execute("""
            ALTER TABLE tickets
            ADD COLUMN source_alert_id INTEGER
        """)

            # =====================================
    # ENTERPRISE INCIDENT MANAGEMENT MIGRATION
    # =====================================

    ticket_columns = [
        row["name"]
        for row in cursor.execute(
            "PRAGMA table_info(tickets)"
        ).fetchall()
    ]

    new_columns = {
        "assigned_to": "TEXT",
        "acknowledged_at": "TIMESTAMP",
        "resolution_summary": "TEXT",
        "resolved_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP"
    }

    for column_name, column_type in new_columns.items():

        if column_name not in ticket_columns:

            cursor.execute(
                f"ALTER TABLE tickets ADD COLUMN "
                f"{column_name} {column_type}"
            )

    # =====================================
    # INCIDENT INVESTIGATION NOTES
    # =====================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incident_notes (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            ticket_id INTEGER NOT NULL,

            author TEXT DEFAULT 'USER',

            note TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (ticket_id)
                REFERENCES tickets(id)
                ON DELETE CASCADE

        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_incident_notes_ticket_id
        ON incident_notes(ticket_id)
    """)

    # Prevent duplicate tickets for the same system alert
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS
        idx_tickets_source_alert_id
        ON tickets(source_alert_id)
        WHERE source_alert_id IS NOT NULL
    """)

    # Historical system metrics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cpu_percent REAL NOT NULL,
            memory_percent REAL NOT NULL,
            disk_percent REAL NOT NULL,
            health TEXT NOT NULL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # System alerts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric TEXT NOT NULL,
            severity TEXT NOT NULL,
            value REAL NOT NULL,
            threshold REAL NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


# =====================================
# SYSTEM METRICS
# =====================================

def save_system_metrics(metrics):

    connection = get_connection()

    connection.execute("""
        INSERT INTO system_metrics (
            cpu_percent,
            memory_percent,
            disk_percent,
            health
        )
        VALUES (?, ?, ?, ?)
    """, (
        metrics["cpu_percent"],
        metrics["memory_percent"],
        metrics["disk_percent"],
        metrics["health"]
    ))

    connection.commit()
    connection.close()


def get_metric_history(limit=60):

    limit = max(1, min(int(limit), 500))

    connection = get_connection()

    rows = connection.execute("""
        SELECT
            id,
            cpu_percent,
            memory_percent,
            disk_percent,
            health,
            recorded_at
        FROM system_metrics
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()

    connection.close()

    return [dict(row) for row in reversed(rows)]


# =====================================
# SYSTEM ALERT MANAGEMENT
# =====================================

def update_system_alerts(metrics):

    thresholds = {

        "CPU": {
            "value": metrics["cpu_percent"],
            "warning": 75,
            "critical": 90
        },

        "RAM": {
            "value": metrics["memory_percent"],
            "warning": 80,
            "critical": 90
        },

        "DISK": {
            "value": metrics["disk_percent"],
            "warning": 85,
            "critical": 95
        }

    }

    connection = get_connection()
    cursor = connection.cursor()

    affected_alert_ids = []

    try:

        for metric, config in thresholds.items():

            value = config["value"]

            if value >= config["critical"]:

                severity = "CRITICAL"
                threshold = config["critical"]

            elif value >= config["warning"]:

                severity = "WARNING"
                threshold = config["warning"]

            else:

                severity = None
                threshold = None

            active_alert = cursor.execute("""
                SELECT id
                FROM system_alerts
                WHERE metric = ?
                AND status = 'ACTIVE'
                ORDER BY id DESC
                LIMIT 1
            """, (metric,)).fetchone()

            if severity:

                message = (
                    f"{metric} usage is {value}% "
                    f"and has crossed the {severity} threshold "
                    f"of {threshold}%."
                )

                if active_alert:

                    alert_id = active_alert["id"]

                    cursor.execute("""
                        UPDATE system_alerts
                        SET severity = ?,
                            value = ?,
                            threshold = ?,
                            message = ?
                        WHERE id = ?
                    """, (
                        severity,
                        value,
                        threshold,
                        message,
                        alert_id
                    ))

                else:

                    cursor.execute("""
                        INSERT INTO system_alerts (
                            metric,
                            severity,
                            value,
                            threshold,
                            message
                        )
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        metric,
                        severity,
                        value,
                        threshold,
                        message
                    ))

                    alert_id = cursor.lastrowid

                affected_alert_ids.append(alert_id)

            elif active_alert:

                alert_id = active_alert["id"]

                cursor.execute("""
                    UPDATE system_alerts
                    SET status = 'RESOLVED',
                        resolved_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (alert_id,))

                affected_alert_ids.append(alert_id)

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()

    # Synchronize incident tickets after alert changes
    for alert_id in affected_alert_ids:

        sync_incident_ticket(alert_id)


def get_alert_history(limit=50):

    limit = max(1, min(int(limit), 500))

    connection = get_connection()

    rows = connection.execute("""
        SELECT
            id,
            metric,
            severity,
            value,
            threshold,
            message,
            status,
            created_at,
            resolved_at
        FROM system_alerts
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()

    connection.close()

    return [dict(row) for row in rows]


# =====================================
# AUTOMATIC INCIDENT TICKET MANAGEMENT
# =====================================

def sync_incident_ticket(alert_id):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # Retrieve corresponding alert
        alert = cursor.execute("""
            SELECT
                id,
                metric,
                severity,
                value,
                threshold,
                message,
                status
            FROM system_alerts
            WHERE id = ?
        """, (alert_id,)).fetchone()

        if not alert:
            return {
                "success": False,
                "message": "Alert not found."
            }

        # Retrieve existing incident ticket
        ticket = cursor.execute("""
            SELECT
                id,
                status,
                resolution_summary,
                resolved_at
            FROM tickets
            WHERE source_alert_id = ?
        """, (alert_id,)).fetchone()

        # =====================================
        # CREATE TICKET FOR CRITICAL ALERT
        # =====================================

        if (
            alert["status"] == "ACTIVE"
            and alert["severity"] == "CRITICAL"
        ):

            description = (
                f"Automatic incident generated by AIOpsGenie.\n\n"
                f"Alert ID: {alert['id']}\n"
                f"Metric: {alert['metric']}\n"
                f"Severity: {alert['severity']}\n"
                f"Current Value: {alert['value']}%\n"
                f"Threshold: {alert['threshold']}%\n"
                f"Details: {alert['message']}"
            )

            if ticket:
                return {
                    "success": True,
                    "ticket_id": ticket["id"],
                    "action": "EXISTING",
                    "message": "Incident ticket already exists."
                }

            cursor.execute("""
                INSERT INTO tickets (
                    title,
                    description,
                    priority,
                    status,
                    source_alert_id
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                f"Critical {alert['metric']} Usage Incident",
                description,
                "CRITICAL",
                "OPEN",
                alert_id
            ))

            ticket_id = cursor.lastrowid

            connection.commit()

            return {
                "success": True,
                "ticket_id": ticket_id,
                "action": "CREATED",
                "message": "Critical incident ticket created."
            }

        # =====================================
        # AUTOMATIC INCIDENT RESOLUTION
        # =====================================

        if (
            alert["status"] == "RESOLVED"
            and ticket
            and ticket["status"] in (
                "OPEN",
                "ACKNOWLEDGED",
                "IN_PROGRESS"
            )
        ):

            automatic_summary = (
                f"Automatically resolved by AIOpsGenie. "
                f"The linked {alert['metric']} system alert "
                f"returned below its configured threshold. "
                f"Alert ID: {alert_id}."
            )

            cursor.execute("""
                UPDATE tickets
                SET
                    status = 'RESOLVED',

                    resolution_summary = COALESCE(
                        NULLIF(TRIM(resolution_summary), ''),
                        ?
                    ),

                    resolved_at = COALESCE(
                        resolved_at,
                        CURRENT_TIMESTAMP
                    ),

                    updated_at = CURRENT_TIMESTAMP

                WHERE id = ?
            """, (
                automatic_summary,
                ticket["id"]
            ))

            connection.commit()

            return {
                "success": True,
                "ticket_id": ticket["id"],
                "action": "RESOLVED",
                "message": "Incident ticket automatically resolved."
            }

        connection.commit()

        return {
            "success": True,
            "action": "NO_ACTION",
            "message": "No incident ticket action required."
        }

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()

# =====================================
# MAIN
# =====================================

if __name__ == "__main__":

    initialize_database()

    print("AIOpsGenie database initialized successfully.")
