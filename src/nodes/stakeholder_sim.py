# src/nodes/stakeholder_sim.py
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any
from agents import llm
from prompts_advanced import PERSONA_PROMPTS, SYNTHESIS_PROMPT


def _run_persona(name: str, prompt_template, inputs: Dict[str, Any]) -> tuple:
    response = llm.invoke(prompt_template.format_messages(**inputs))
    return name, response.content


def node_stakeholder_sim(state: Dict[str, Any]) -> Dict[str, Any]:
    inputs = {
        "disruption_type": state.get("disruption_type", ""),
        "what_if_summary": state.get("what_if_summary", ""),
        "scenario_kpis": state.get("scenario_kpis", {}),
        "dispatch_plan": state.get("dispatch_plan", "No plan yet."),
    }

    reactions: Dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(_run_persona, name, tmpl, inputs): name
            for name, tmpl in PERSONA_PROMPTS.items()
        }
        for future in as_completed(futures):
            name, reaction = future.result()
            reactions[name] = reaction

    reactions_text = "\n\n".join(f"**{k}:** {v}" for k, v in reactions.items())
    synthesis = llm.invoke(SYNTHESIS_PROMPT.format_messages(reactions=reactions_text)).content

    return {
        "stakeholder_reactions": reactions,
        "stakeholder_synthesis": synthesis,
    }
