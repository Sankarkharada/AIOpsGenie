from app.database.db import get_connection, sync_incident_ticket

connection = get_connection()
cursor = connection.cursor()

alert_id = None
ticket_id = None

try:
    print("\nAIOPSGENIE INCIDENT LIFECYCLE TEST")
    print("=" * 50)

    # 1. Create a temporary critical alert
    cursor.execute("""
        INSERT INTO system_alerts (
            metric,
            severity,
            value,
            threshold,
            message,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "CPU_TEST",
        "CRITICAL",
        95,
        90,
        "Temporary lifecycle integration test alert.",
        "ACTIVE"
    ))

    alert_id = cursor.lastrowid
    connection.commit()

    print(f"\n[1] Temporary alert created: #{alert_id}")

    # 2. Synchronize alert and create incident ticket
    result = sync_incident_ticket(alert_id)
    print("[2] Ticket creation:", result)

    assert result["action"] == "CREATED"

    ticket_id = result["ticket_id"]

    # 3. Check duplicate prevention
    duplicate_result = sync_incident_ticket(alert_id)

    print("[3] Duplicate prevention:", duplicate_result)

    assert duplicate_result["action"] == "EXISTING"
    assert duplicate_result["ticket_id"] == ticket_id

    # 4. Simulate alert recovery
    cursor.execute("""
        UPDATE system_alerts
        SET
            status = 'RESOLVED',
            resolved_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (alert_id,))

    connection.commit()

    print("[4] Temporary alert marked RESOLVED.")

    # 5. Synchronize the resolved alert
    resolution_result = sync_incident_ticket(alert_id)

    print("[5] Automatic ticket resolution:", resolution_result)

    assert resolution_result["action"] == "RESOLVED"

    # 6. Verify final ticket state
    ticket = cursor.execute("""
        SELECT
            id,
            status,
            resolution_summary,
            resolved_at,
            updated_at
        FROM tickets
        WHERE id = ?
    """, (ticket_id,)).fetchone()

    print("\n[6] FINAL TICKET STATE")
    print("-" * 50)
    print(dict(ticket))

    assert ticket["status"] == "RESOLVED"
    assert ticket["resolution_summary"]
    assert ticket["resolved_at"]
    assert ticket["updated_at"]

    print("\nALL INCIDENT LIFECYCLE CHECKS PASSED.")

except Exception as error:
    connection.rollback()
    print("\nTEST FAILED:", error)
    raise

finally:
    # Remove only this test's temporary records
    if alert_id is not None:
        connection.execute(
            "DELETE FROM tickets WHERE source_alert_id = ?",
            (alert_id,)
        )
        connection.execute(
            "DELETE FROM system_alerts WHERE id = ?",
            (alert_id,)
        )
        connection.commit()

        print("\nTemporary test records cleaned up.")

    connection.close()
