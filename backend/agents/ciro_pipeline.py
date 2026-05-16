"""CIRO 5-Agent Sequential Pipeline using Google ADK.

Pipeline flow:
  Signal Ingestion → Event Detection → Reasoning & Analysis → Action Planning → Simulation

Each agent is an LlmAgent with a tool that calls the corresponding FastAPI endpoint.
The SequentialAgent orchestrates them in order, passing state between steps.

Run with:
    adk web agents        (browser UI)
    adk run agents        (CLI)
"""

from __future__ import annotations

import json
import os
from dotenv import load_dotenv

import httpx
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import FunctionTool

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# Backend base URL (the running FastAPI server)
# ---------------------------------------------------------------------------
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


# ---------------------------------------------------------------------------
# Tool Functions — each calls a FastAPI endpoint
# ---------------------------------------------------------------------------

def ingest_signal(raw_text: str, source: str = "social") -> dict:
    """Submit a raw signal to the Signal Ingestion Agent for normalisation.

    This tool accepts raw crisis-related text (in Urdu or English) from social
    media, weather reports, or traffic feeds. It normalises the signal by
    detecting the language, extracting the location, tagging severity, and
    building a SignalBatch.

    Args:
        raw_text: The raw signal text. Can be Urdu (romanised or script) or English.
                  Example: "G-10 mein pani bhar gaya hai, gaariyan phans gayi hain"
        source: The signal source type. One of "social", "weather", or "traffic".

    Returns:
        A SignalBatch dictionary containing normalised signals with language,
        location, severity_hint, and keywords extracted.
    """
    response = httpx.post(
        f"{BACKEND_URL}/ingest/signal",
        json={"source": source, "text": raw_text},
        timeout=10.0,
    )
    return response.json()


def detect_crisis(signal_batch_json: str) -> dict:
    """Detect a crisis event from a batch of normalised signals.

    This tool analyses a SignalBatch to determine the crisis type (flood,
    heatwave, blockage, accident), compute a confidence score, and assign
    a severity level.

    Args:
        signal_batch_json: JSON string of a SignalBatch object from the ingestion step.

    Returns:
        A CrisisEvent dictionary with crisis_type, confidence, severity, and location.
    """
    batch = json.loads(signal_batch_json) if isinstance(signal_batch_json, str) else signal_batch_json
    response = httpx.post(
        f"{BACKEND_URL}/detect/crisis",
        json=batch,
        timeout=10.0,
    )
    return response.json()


def analyse_crisis(crisis_event_json: str) -> dict:
    """Analyse a detected crisis using AI reasoning to assess impact and urgency.

    This tool takes a CrisisEvent and produces a structured analysis including
    impact bullets, affected population estimate, infrastructure at risk,
    and urgency level.

    Args:
        crisis_event_json: JSON string of a CrisisEvent object from the detection step.

    Returns:
        A CrisisAnalysis dictionary with impact, affected_population,
        infrastructure_at_risk, urgency, and summary.
    """
    event = json.loads(crisis_event_json) if isinstance(crisis_event_json, str) else crisis_event_json
    response = httpx.post(
        f"{BACKEND_URL}/reason/analyse",
        json=event,
        timeout=10.0,
    )
    return response.json()


def plan_actions(crisis_event_json: str) -> dict:
    """Generate a coordinated response plan for a detected crisis.

    This tool maps the crisis type and severity to a list of executable actions
    such as rerouting traffic, dispatching rescue teams, sending alerts, and
    opening relief centres.

    Args:
        crisis_event_json: JSON string of a CrisisEvent object.

    Returns:
        An ActionPlan dictionary with an ordered list of response actions.
    """
    event = json.loads(crisis_event_json) if isinstance(crisis_event_json, str) else crisis_event_json
    response = httpx.post(
        f"{BACKEND_URL}/plan/actions",
        json=event,
        timeout=10.0,
    )
    return response.json()


def execute_simulation(action_plan_json: str) -> dict:
    """Execute a simulation of all planned response actions.

    This tool takes an ActionPlan and executes each action against a simulated
    city state. It captures before/after snapshots of traffic congestion,
    creates emergency tickets and citizen alerts, and computes outcome metrics.

    Args:
        action_plan_json: JSON string of an ActionPlan object from the planning step.

    Returns:
        A SimulationResult dictionary with before/after state, tickets created,
        alerts sent, and congestion reduction metrics.
    """
    plan = json.loads(action_plan_json) if isinstance(action_plan_json, str) else action_plan_json
    response = httpx.post(
        f"{BACKEND_URL}/simulate/execute",
        json=plan,
        timeout=10.0,
    )
    return response.json()


def get_outcome_summary() -> dict:
    """Fetch the aggregated outcome metrics from the most recent simulation.

    Returns:
        An OutcomeSummary dictionary with congestion_reduction_pct,
        vehicles_rerouted, min_eta_minutes, alerts_dispatched, etc.
    """
    response = httpx.get(
        f"{BACKEND_URL}/outcome/summary",
        timeout=10.0,
    )
    return response.json()


# ---------------------------------------------------------------------------
# Agent Definitions
# ---------------------------------------------------------------------------

signal_ingestion_agent = LlmAgent(
    name="signal_ingestion_agent",
    model="gemini-2.0-flash",
    instruction="""You are the Signal Ingestion Agent for CIRO (Crisis Intelligence & Response Orchestrator).

Your role is to receive raw crisis signals from Pakistani cities and normalise them.

When the user provides a signal text:
1. Call the `ingest_signal` tool with the text and appropriate source type
2. Report the results: what language was detected, what location was extracted, what severity was tagged
3. Store the full SignalBatch result in state for the next agent

Always call the tool - never make up results.""",
    tools=[ingest_signal],
)

event_detection_agent = LlmAgent(
    name="event_detection_agent",
    model="gemini-2.0-flash",
    instruction="""You are the Event Detection Agent for CIRO.

Your role is to detect what type of crisis is occurring from the signal data.

When you receive signal data from the previous step:
1. Take the SignalBatch from the conversation and call `detect_crisis` with it as a JSON string
2. Report the crisis type, confidence score, severity level, and location
3. Store the full CrisisEvent result for the next agent

Crisis types: FLOOD, HEATWAVE, BLOCKAGE, ACCIDENT
Severity levels: LOW, MEDIUM, HIGH, CRITICAL""",
    tools=[detect_crisis],
)

reasoning_agent = LlmAgent(
    name="reasoning_analysis_agent",
    model="gemini-2.0-flash",
    instruction="""You are the Reasoning & Analysis Agent for CIRO, powered by Gemini.

Your role is to produce a detailed analysis of the detected crisis.

When you receive a CrisisEvent from the previous step:
1. Call `analyse_crisis` with the CrisisEvent as a JSON string
2. Report the impact bullets, affected population, infrastructure at risk, and urgency level
3. Store the full CrisisAnalysis result for the next agent""",
    tools=[analyse_crisis],
)

action_planning_agent = LlmAgent(
    name="action_planning_agent",
    model="gemini-2.0-flash",
    instruction="""You are the Action Planning Agent for CIRO.

Your role is to generate a coordinated response plan based on the crisis.

When you receive crisis data from the previous steps:
1. Call `plan_actions` with the CrisisEvent as a JSON string
2. Report each planned action (reroute traffic, dispatch rescue, send alerts, etc.)
3. Store the full ActionPlan result for the simulation agent""",
    tools=[plan_actions],
)

simulation_agent = LlmAgent(
    name="simulation_agent",
    model="gemini-2.0-flash",
    instruction="""You are the Simulation Engine Agent for CIRO.

Your role is to execute all planned actions against a simulated city state and report outcomes.

When you receive an ActionPlan from the previous step:
1. Call `execute_simulation` with the ActionPlan as a JSON string
2. Then call `get_outcome_summary` to get the final metrics
3. Report the before/after state, tickets created, alerts sent, and congestion reduction

Present the final results clearly with:
- Congestion reduction percentage
- Number of emergency tickets created
- Number of citizens alerted
- Response ETA""",
    tools=[execute_simulation, get_outcome_summary],
)


# ---------------------------------------------------------------------------
# Sequential Pipeline — the root agent
# ---------------------------------------------------------------------------

root_agent = SequentialAgent(
    name="ciro_crisis_pipeline",
    description=(
        "CIRO Crisis Intelligence & Response Orchestrator — "
        "a 5-agent pipeline that ingests crisis signals, detects events, "
        "analyses impact, plans response actions, and simulates outcomes "
        "for Pakistani urban crises."
    ),
    sub_agents=[
        signal_ingestion_agent,
        event_detection_agent,
        reasoning_agent,
        action_planning_agent,
        simulation_agent,
    ],
)
