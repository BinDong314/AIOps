# /itsm_agent/agent_logic.py

import logging
import requests
from typing import Dict

# --- LangChain Core Imports ---
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor

from config import settings

# --- Basic Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- 2. DEFINE TOOLS FOR THE AGENT ---

@tool
def get_procedure_suggestion(ticket_id: str) -> str:
    """
    Queries the RAG (Retrieval-Augmented Generation) server to get a ranked list of
    suggested procedures or knowledge base articles relevant to a given ticket ID.
    This should be the primary tool for finding resolution steps.
    """
    logging.info(f"TOOL: Querying RAG server for ticket '{ticket_id}'...")
    # --- IMPLEMENTATION LOGIC HERE ---
    # Example:
    # try:
    #     response = requests.post(settings.RAG_SERVER_URL, json={"ticket_id": ticket_id})
    #     response.raise_for_status()
    #     return response.json()['suggestion']
    # except Exception as e:
    #     return f"Error connecting to RAG server: {e}"
    return f"Placeholder: RAG suggestion for ticket {ticket_id} would be returned here. Example: 'KB00123: Reset user password', 'KB00456: Troubleshoot VPN connection'."

@tool
def query_esdb(ticket_id: str) -> str:
    """
    Queries the ESDB (Elasticsearch Database) to retrieve raw logs, metrics, or historical
    data related to a specific ticket ID. Use this to find error messages or past occurrences.
    """
    logging.info(f"TOOL: Querying ESDB for ticket '{ticket_id}'...")
    # --- IMPLEMENTATION LOGIC HERE ---
    return f"Placeholder: ESDB data for ticket {ticket_id} would be returned. Example: 'Found 5 related error logs from host web-prod-03'."

@tool
def query_stardust(ticket_id: str) -> Dict:
    """
    Queries the 'Stardust' system to get structured information about the user, assets,
    and services associated with a ticket ID.
    """
    logging.info(f"TOOL: Querying Stardust for ticket '{ticket_id}'...")
    # --- IMPLEMENTATION LOGIC HERE ---
    return {
        "ticket_id": ticket_id,
        "user": "Alice",
        "affected_asset": "Laptop-12345",
        "service": "Corporate VPN",
        "summary": "User reports inability to connect to VPN."
    }

def setup_agent() -> AgentExecutor:
    """Creates and returns the LangChain agent and executor."""
    logging.info("Setting up ITSM agent...")

    tools = [get_procedure_suggestion, query_esdb, query_stardust]

    # Use a prompt that is tailored for reacting to instructions and using tools
    prompt = hub.pull("hwchase17/react")

    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL_NAME,
        temperature=0,
        openai_api_base=settings.OPENAI_API_BASE,
        openai_api_key=settings.OPENAI_API_KEY,
    )

    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10
    )

    logging.info("Agent setup complete.")
    return agent_executor