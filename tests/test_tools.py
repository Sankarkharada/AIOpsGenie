from app.tools.ticket_tool import create_ticket, get_ticket_status

from app.tools.system_tool import check_service_status


def main():

    print("\n--- CREATE SUPPORT TICKET ---")

    ticket = create_ticket(
        title="VPN Connection Failure",
        description="User receiving VPN-403 authentication error.",
        priority="HIGH"
    )

    print(ticket)

    print("\n--- CHECK TICKET STATUS ---")

    status = get_ticket_status(ticket["ticket_id"])

    print(status)

    print("\n--- CHECK SERVICE STATUS ---")

    service = check_service_status("vpn")

    print(service)


if __name__ == "__main__":

    main()