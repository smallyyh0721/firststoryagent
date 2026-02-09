"""
LLM Prompt templates for the RDMA Agent system.
"""

SYSTEM_PROMPT = """You are an expert RDMA network engineer and troubleshooting agent.
You analyze RDMA infrastructure issues including InfiniBand, RoCE, Mellanox/NVIDIA NICs,
switches, and the Linux OFED stack.

Your responsibilities:
1. Analyze detected issues using the provided diagnostic data
2. Identify root causes based on error patterns, counters, and logs
3. Create step-by-step action plans using available diagnostic skills
4. Execute skills to gather more information when needed
5. Provide clear remediation recommendations

When creating action plans, you MUST output valid JSON in the following format:
{
    "root_cause_hypothesis": "Brief description of suspected root cause",
    "confidence": 0.0-1.0,
    "action_plan": [
        {
            "step": 1,
            "description": "What this step does",
            "skill": "skill_name",
            "params": {"param1": "value1"},
            "expected_outcome": "What we expect to learn"
        }
    ],
    "immediate_actions": ["action1", "action2"],
    "escalation_needed": false
}

Be precise, technical, and systematic. Always consider multiple hypotheses."""

ANALYSIS_PROMPT_TEMPLATE = """## Detected Issue
{issue_summary}

## Severity: {severity}
## Category: {category}

## Diagnostic Data Collected
{diagnostic_data}

## Relevant Knowledge Base Context
{rag_context}

## Available Diagnostic Skills
{available_skills}

## Task
Analyze this RDMA issue. Identify the most likely root cause and create a step-by-step
action plan using the available skills to confirm the diagnosis and resolve the issue.

Output your analysis as JSON with the structure specified in your system instructions."""

ACTION_RESULT_PROMPT_TEMPLATE = """## Original Issue
{issue_summary}

## Current Hypothesis
{hypothesis}

## Action Plan Progress
Steps completed: {completed_steps}/{total_steps}

## Latest Action Result
Skill: {skill_name}
Parameters: {skill_params}
Output:
```
{skill_output}
```

## Previous Step Results
{previous_results}

## Available Skills
{available_skills}

## Task
Based on this new information:
1. Does the evidence support or refute the current hypothesis?
2. Should we continue with the action plan, modify it, or escalate?
3. If continuing, what is the next step?

Output your updated analysis as JSON:
{{
    "hypothesis_status": "confirmed|refuted|needs_more_data",
    "updated_hypothesis": "...",
    "confidence": 0.0-1.0,
    "next_action": {{
        "skill": "skill_name",
        "params": {{}},
        "reason": "why this step"
    }} or null,
    "findings_so_far": "summary of what we've learned",
    "resolution": "if issue is resolved, describe what fixed it" or null,
    "escalation_needed": false
}}"""

FINAL_REPORT_PROMPT = """## Issue Summary
{issue_summary}

## Investigation Log
{investigation_log}

## All Findings
{findings}

## Task
Write a concise final report covering:
1. Issue description
2. Root cause (confirmed or best hypothesis)
3. Actions taken
4. Resolution status
5. Recommendations for prevention

Output as plain text, well-structured with headers."""
