"""End-to-end pipeline test script.

Runs the full 5-agent pipeline: Ingest → Detect → Reason → Plan → Simulate
Then checks the outcome summary.
"""

import httpx
import json

BASE = "http://localhost:8000"

def main():
    print("=" * 60)
    print("CIRO E2E Pipeline Test – Urdu Flood (G-10)")
    print("=" * 60)

    # Step 1: Ingest
    r = httpx.post(f"{BASE}/ingest/signal", json={
        "source": "social",
        "text": "G-10 mein pani bhar gaya hai, gaariyan phans gayi hain"
    })
    batch = r.json()
    print(f"\n--- STEP 1: INGEST (Status {r.status_code}) ---")
    print(f"  Batch ID:  {batch['batch_id']}")
    print(f"  Signals:   {len(batch['signals'])}")
    print(f"  Location:  {batch['primary_location']}")
    print(f"  Language:  {batch['signals'][0]['language']}")
    print(f"  Severity:  {batch['signals'][0]['severity_hint']}")
    print(f"  Keywords:  {batch['signals'][0]['keywords']}")
    assert r.status_code == 200
    assert batch['signals'][0]['language'] == 'ur'
    assert batch['primary_location'] == 'G-10'

    # Step 2: Detect
    r2 = httpx.post(f"{BASE}/detect/crisis", json=batch)
    event = r2.json()
    print(f"\n--- STEP 2: DETECT (Status {r2.status_code}) ---")
    print(f"  Crisis:    {event['crisis_type']}")
    print(f"  Confidence:{event['confidence']}")
    print(f"  Severity:  {event['severity']}")
    print(f"  Location:  {event['location']}")
    print(f"  Explanation: {event['explanation']}")
    assert r2.status_code == 200
    assert event['crisis_type'] == 'flood'

    # Step 3: Reason
    r3 = httpx.post(f"{BASE}/reason/analyse", json=event)
    analysis = r3.json()
    print(f"\n--- STEP 3: REASON (Status {r3.status_code}) ---")
    print(f"  Urgency:   {analysis['urgency']}")
    print(f"  Population:{analysis['affected_population']}")
    print(f"  Infra Risk:{analysis['infrastructure_at_risk']}")
    for bullet in analysis['impact']:
        print(f"  - {bullet}")
    assert r3.status_code == 200

    # Step 4: Plan
    r4 = httpx.post(f"{BASE}/plan/actions", json=event)
    plan = r4.json()
    print(f"\n--- STEP 4: PLAN (Status {r4.status_code}) ---")
    print(f"  Plan ID:   {plan['plan_id']}")
    print(f"  Actions:   {[a['type'] for a in plan['actions']]}")
    assert r4.status_code == 200

    # Step 5: Simulate
    r5 = httpx.post(f"{BASE}/simulate/execute", json=plan)
    sim = r5.json()
    print(f"\n--- STEP 5: SIMULATE (Status {r5.status_code}) ---")
    print(f"  Executed:  {sim['actions_executed']}")
    print(f"  Tickets:   {len(sim['tickets_created'])}")
    print(f"  Alerts:    {len(sim['alerts_sent'])}")
    print(f"  Congestion Reduction: {sim['estimated_congestion_reduction']}%")
    print(f"  Avg Before: {sim['state_before']['avg_congestion']}")
    print(f"  Avg After:  {sim['state_after']['avg_congestion']}")
    assert r5.status_code == 200

    # Outcome Summary
    r6 = httpx.get(f"{BASE}/outcome/summary")
    outcome = r6.json()
    print(f"\n--- OUTCOME SUMMARY (Status {r6.status_code}) ---")
    print(f"  Congestion Reduction: {outcome['congestion_reduction_pct']}%")
    print(f"  Vehicles Rerouted:    {outcome['vehicles_rerouted']}")
    print(f"  Alerts Dispatched:    {outcome['alerts_dispatched']}")
    print(f"  Tickets Created:      {outcome['tickets_created']}")
    print(f"  Min ETA:              {outcome['min_eta_minutes']} min")
    print(f"  Resources Opened:     {outcome['resources_opened']}")
    assert r6.status_code == 200

    # Trace
    r7 = httpx.get(f"{BASE}/trace/latest")
    trace = r7.json()
    print(f"\n--- TRACE (Status {r7.status_code}) ---")
    print(f"  Run ID:    {trace['run_id']}")
    print(f"  Steps:     {len(trace['steps'])}")
    for step in trace['steps']:
        print(f"    [{step['agent']}] {step['step']} ({step['duration_ms']}ms)")

    print("\n" + "=" * 60)
    print("ALL E2E PIPELINE STEPS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
