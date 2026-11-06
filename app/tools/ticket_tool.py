from app.database.db import get_connection, initialize_database


def create_ticket(title, description, priority="MEDIUM"):

    initialize_database()

    allowed_priorities = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

    priority = priority.upper()

    if priority not in allowed_priorities:
        priority = "MEDIUM"

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO tickets (title, description, priority)
        VALUES (?, ?, ?)
        """,
        (title, description, priority)
    )

    ticket_id = cursor.lastrowid

    connection.commit()

    connection.close()

    return {
        "ticket_id": ticket_id,
        "title": title,
        "priority": priority,
        "status": "OPEN"
    }


def get_ticket_status(ticket_id):

    initialize_database()

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM tickets WHERE id = ?",
        (ticket_id,)
    )

    ticket = cursor.fetchone()

    connection.close()

    if ticket is None:
        return {
            "error": "Ticket not found."
        }

    return dict(ticket)