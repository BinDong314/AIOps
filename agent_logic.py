import logging
import requests
from typing import Dict, Any

# --- LangChain Core Imports ---
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor

from config import settings

# --- Basic Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- DEFINE TOOLS FOR THE AGENT ---

@tool
def get_snow_ticket_info(ticket_id: str) -> Dict[str, Any]:
    """
    This should always be the first step. It queries ServiceNow to get the initial, structured
    details of a ticket, such as the user, a summary of the problem, and the primary
    affected configuration item (CI) like a router or server name.
    """
    logging.info(f"TOOL: Querying ServiceNow for ticket '{ticket_id}'...")
    # --- IMPLEMENTATION LOGIC HERE ---
    # In a real scenario, you would query the ServiceNow API.
    return {
        "ticket_id": ticket_id,
        "caller": "David B.",
        "short_description": "High latency and packet loss to core router cr5.lbnl.gov",
        "affected_ci": "cr5.lbnl.gov",
        "priority": "2 - High",
        "description": "User reports that connections routing through cr5.lbnl.gov have been experiencing high latency (200ms+) and intermittent packet loss since 14:00 today."
    }

@tool
def rag_search_wiki(query: str) -> str:
    """
    Use this tool to search the official knowledge base and wikis for standard operating
    procedures (SOPs), troubleshooting guides, and configuration manuals. It is best used for
    finding 'how-to' information. For example, 'how to check BGP status on a Juniper router'.
    """
    logging.info(f"TOOL: Querying RAG Wiki for '{query}'...")
    # --- IMPLEMENTATION LOGIC HERE ---
    return f"Placeholder: Wiki search results for '{query}'. Example: 'KB00871: Standard Procedure for Diagnosing High Latency on Juniper MX Series Routers'."

@tool
def rag_search_ticket(query: str) -> str:
    """
    Use this tool to search a database of past tickets to find similar historical issues.
    This is useful for identifying recurring problems or seeing how a similar, unusual issue
    was resolved in the past. Use keywords from the current ticket's description as the query.
    """
    logging.info(f"TOOL: Querying RAG Ticket DB for '{query}'...")
    # --- IMPLEMENTATION LOGIC HERE ---
    return f"Placeholder: Found 3 similar past tickets for '{query}'. Ticket TKT-45123 from last month was resolved by restarting the monitoring process on the device."

@tool
def query_esdb_data(query: str) -> str:
    """
    Queries ESDB (Elasticsearch) for network telemetry data. Use this to find specific
    network metrics like packet loss, latency, NetFlow data, or firewall logs for a device.
    The query should be specific, e.g., 'latency for cr5.lbnl.gov over the last 3 hours'.
    """
    logging.info(f"TOOL: Querying ESDB for '{query}'...")
    # --- IMPLEMENTATION LOGIC HERE ---
    return f"Placeholder: ESDB data for query '{query}'. Example: 'Latency for cr5.lbnl.gov spiked to 210ms at 14:05. No packet loss detected. Firewall logs show no anomalous drops.'"

@tool
def query_stardust_data(device_name: str) -> Dict[str, Any]:
    """
    Queries Stardust for system monitoring and hardware status of a specific network device.
    Use this to get real-time information like SNMP data, including CPU utilization, memory usage,
    interface operational status (up/down), and traffic counters (input/output bits per second).
    The input must be a device name (e.g., 'cr5.lbnl.gov').
    """
    logging.info(f"TOOL: Querying Stardust for device '{device_name}'...")
    # --- IMPLEMENTATION LOGIC HERE ---
    return {
        "device": device_name,
        "cpu_utilization_percent": 85.5,
        "memory_utilization_percent": 70.1,
        "interface_status": {
            "xe-0/0/1": {"status": "up", "input_bps": 1.5e9, "output_bps": 2.3e9},
            "xe-0/0/2": {"status": "up", "input_bps": 4.1e9, "output_bps": 3.8e9}
        },
        "comment": "CPU utilization is abnormally high."
    }

def setup_agent() -> AgentExecutor:
    """Creates and returns the LangChain agent and executor."""
    logging.info("Setting up AIOps agent...")

    # The list of tools the agent has access to.
    tools = [
        get_snow_ticket_info,
        query_stardust_data,
        query_esdb_data,
        rag_search_wiki,
        rag_search_ticket
    ]

    # Pull a standard prompt template that works well with ReAct agents.
    prompt = hub.pull("hwchase17/react")

    # Configure the LLM
    llm = ChatOpenAI(
        model=settings.LLM_MODEL_NAME,
        temperature=0, # Set to 0 for more deterministic, fact-based reasoning
        openai_api_base=settings.LLM_API_BASE,
        openai_api_key=settings.LLM_API_KEY
    )

    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True, # Set to True to see the agent's thought process
        handle_parsing_errors=True,
        max_iterations=10
    )

    logging.info("Agent setup complete.")
    return agent_executor