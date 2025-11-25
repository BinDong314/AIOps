# /itsm_agent/client.py

import requests
import argparse
import sys

# --- Configuration ---
# The URL where your FastAPI agent server is running.
AGENT_SERVER_URL = "http://127.0.0.1:8000/invoke"

def summarize_ticket(ticket_id: str):
    """
    Sends a request to the ITSM agent to summarize a given ticket.

    Args:
        ticket_id: The ID of the ticket to be summarized (e.g., "TKT-12345").
    """
    print(f"Requesting summary for ticket: {ticket_id}...")

    # 1. Construct the prompt for the agent.
    prompt = f"Please summarize ticket {ticket_id}. Find the user, the core problem, and any affected services."

    # 2. Prepare the JSON payload for the POST request.
    #    The key 'prompt' must match the Pydantic model in the FastAPI app.
    payload = {
        "prompt": prompt
    }

    try:
        # 3. Send the POST request to the agent server.
        #    - `json=payload` automatically sets the Content-Type header to application/json.
        #    - `timeout=30` prevents the client from waiting indefinitely.
        response = requests.post(AGENT_SERVER_URL, json=payload, timeout=30)

        # 4. Check for HTTP errors (e.g., 404 Not Found, 500 Internal Server Error).
        #    This will raise an exception if the status code is 4xx or 5xx.
        response.raise_for_status()

        # 5. Parse the JSON response from the server.
        response_data = response.json()
        summary = response_data.get("response", "No response field found in the server's reply.")

        # 6. Print the result in a clean format.
        print("\n--- Agent Summary ---")
        print(summary)
        print("---------------------\n")

    except requests.exceptions.RequestException as e:
        # Handle network-related errors (e.g., connection refused).
        print(f"\n[ERROR] Could not connect to the agent server at {AGENT_SERVER_URL}", file=sys.stderr)
        print(f"Please ensure the server is running and accessible.", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Handle other potential errors (e.g., JSON parsing).
        print(f"\n[ERROR] An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    # --- Command-Line Interface Setup ---
    parser = argparse.ArgumentParser(
        description="A client to request ticket summaries from the AIOps AI Agent."
    )
    parser.add_argument(
        "ticket_id",
        type=str,
        help="The ID of the ticket you want to summarize (e.g., TKT-12345)."
    )
    args = parser.parse_args()

    # Call the main function with the ticket ID from the command line.
    summarize_ticket(args.ticket_id)