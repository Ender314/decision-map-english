# -*- coding: utf-8 -*-
"""
Retrospective tab - Post-decision monitoring and learning.
Inspired by Agile retrospectives: outcomes tracking, tripwires, and lessons learned.
"""

import streamlit as st
import pandas as pd
import uuid
from datetime import date, datetime
import plotly.graph_objects as go
from config.constants import OUTCOME_ATTRIBUTION, OUTCOME_SENTIMENT, TRIPWIRE_STATUS


LEGACY_RETRO_VALUE_MAP = {
    "decisión": "decision",
    "decision": "decision",
    "azar": "luck",
    "mixto": "mixed",
    "positivo": "positive",
    "negativo": "negative",
    "neutral": "neutral",
    "activo": "active",
    "disparado": "triggered",
    "superado": "resolved",
}


def _normalize_retro_value(value: str) -> str:
    key = str(value or "").strip().lower()
    return LEGACY_RETRO_VALUE_MAP.get(key, key)


def count_active_tripwires() -> int:
    """Count tripwires that are active."""
    retro = st.session_state.get("retro", {})
    tripwires = retro.get("tripwires", [])
    return sum(1 for t in tripwires if _normalize_retro_value(t.get("status")) == "active")


def count_triggered_tripwires() -> int:
    """Count tripwires that have been triggered."""
    retro = st.session_state.get("retro", {})
    tripwires = retro.get("tripwires", [])
    return sum(1 for t in tripwires if _normalize_retro_value(t.get("status")) == "triggered")


def render_retro_tab():
    """Render the Retrospective tab.
    
    Note: This view is intentionally decoupled from alternatives.
    """
    st.subheader("🔄 Retrospective")
    
    # Initialize/normalize retro payload (some load paths may leave partial dicts).
    retro_defaults = {
        "decision_date": None,
        "review_date": None,
        "chosen_alternative_id": None,
        "outcomes": [],
        "tripwires": [],
        "lessons_learned": "",
        "decision_quality_score": 3,
        "outcome_quality_score": 3,
    }

    current_retro = st.session_state.get("retro")
    if not isinstance(current_retro, dict):
        current_retro = {}

    for key, default in retro_defaults.items():
        if key not in current_retro:
            current_retro[key] = default.copy() if isinstance(default, list) else default

    st.session_state["retro"] = current_retro
    retro = st.session_state["retro"]
    
    # Decision date
    col1, col2 = st.columns(2)
    with col1:
        decision_date = st.date_input(
            "Decision date",
            value=retro.get("decision_date") or date.today(),
            key="retro_decision_date"
        )
        retro["decision_date"] = decision_date
    
    with col2:
        review_date = st.date_input(
            "Last review date",
            value=retro.get("review_date") or date.today(),
            key="retro_review_date"
        )
        retro["review_date"] = review_date
    
    st.markdown("---")
    
    # Tabs for different sections
    retro_tabs = st.tabs(["📈 Outcomes", "⚡ Tripwires", "📝 Lessons"])
    
    # === OUTCOMES TAB ===
    with retro_tabs[0]:
        st.markdown("### 📈 Outcome Tracking")
        st.caption("Record observed outcomes and separate what came from the decision vs. luck.")
        
        outcomes = retro.get("outcomes", [])
        for i, outcome in enumerate(outcomes):
            normalized_attr = _normalize_retro_value(outcome.get("attribution", "mixed"))
            normalized_sent = _normalize_retro_value(outcome.get("sentiment", "neutral"))
            if outcome.get("attribution") != normalized_attr:
                retro["outcomes"][i]["attribution"] = normalized_attr
            if outcome.get("sentiment") != normalized_sent:
                retro["outcomes"][i]["sentiment"] = normalized_sent
        
        # Add new outcome
        with st.expander("➕ Record new outcome", expanded=len(outcomes) == 0):
            with st.form("add_outcome_form", clear_on_submit=True):
                o_desc = st.text_area(
                    "What happened?",
                    placeholder="Describe the observed outcome...",
                    key="new_outcome_desc"
                )
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    o_date = st.date_input("Date", value=date.today(), key="new_outcome_date")
                with c2:
                    o_attr = st.selectbox(
                        "Attribution",
                        OUTCOME_ATTRIBUTION,
                        index=0,
                        key="new_outcome_attr",
                        help="Is this outcome due to the decision, luck, or a mix?"
                    )
                with c3:
                    o_sent = st.selectbox(
                        "Sentiment",
                        OUTCOME_SENTIMENT,
                        index=1,
                        key="new_outcome_sent"
                    )
                
                o_notes = st.text_input(
                    "Attribution notes",
                    placeholder="Why do you think this is decision- or luck-driven?",
                    key="new_outcome_notes"
                )
                
                if st.form_submit_button("Record outcome", type="primary"):
                    if o_desc.strip():
                        new_outcome = {
                            "id": str(uuid.uuid4()),
                            "description": o_desc.strip(),
                            "date": o_date.isoformat() if o_date else None,
                            "attribution": o_attr,
                            "attribution_notes": o_notes.strip(),
                            "sentiment": o_sent
                        }
                        retro["outcomes"].append(new_outcome)
                    else:
                        st.warning("Describe the observed outcome")
        
        # Display outcomes
        if outcomes:
            # Sort by date descending
            sorted_outcomes = sorted(
                outcomes,
                key=lambda x: x.get("date", ""),
                reverse=True
            )
            
            for outcome in sorted_outcomes:
                sent_icon = {"positive": "✅", "neutral": "➖", "negative": "❌"}.get(outcome.get("sentiment", "neutral"), "➖")
                attr_icon = {"decision": "🎯", "luck": "🎲", "mixed": "🔀"}.get(outcome.get("attribution", "mixed"), "🔀")
                
                with st.expander(f"{sent_icon} {outcome['description'][:50]}... — {outcome.get('date', 'No date')}"):
                    st.markdown(f"**Description:** {outcome['description']}")
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown(f"**Date:** {outcome.get('date', 'N/A')}")
                    with c2:
                        st.markdown(f"**Attribution:** {attr_icon} {outcome.get('attribution', 'mixed')}")
                    with c3:
                        st.markdown(f"**Sentiment:** {sent_icon} {outcome.get('sentiment', 'neutral')}")
                    
                    if outcome.get("attribution_notes"):
                        st.markdown(f"**Notes:** {outcome['attribution_notes']}")
                    
                    if st.button("🗑️ Delete", key=f"del_outcome_{outcome['id']}"):
                        retro["outcomes"] = [o for o in retro["outcomes"] if o["id"] != outcome["id"]]
            
            # Attribution summary chart
            st.markdown("---")
            st.markdown("#### 📊 Attribution Summary")
            
            attr_counts = {"decision": 0, "luck": 0, "mixed": 0}
            sent_counts = {"positive": 0, "neutral": 0, "negative": 0}
            
            for o in outcomes:
                attr = o.get("attribution", "mixed")
                sent = o.get("sentiment", "neutral")
                if attr in attr_counts:
                    attr_counts[attr] += 1
                if sent in sent_counts:
                    sent_counts[sent] += 1
            
            c1, c2 = st.columns(2)
            
            with c1:
                # Attribution pie chart
                fig_attr = go.Figure(data=[go.Pie(
                    labels=["Decision 🎯", "Luck 🎲", "Mixed 🔀"],
                    values=list(attr_counts.values()),
                    hole=0.4,
                    marker_colors=["#2196f3", "#9c27b0", "#ff9800"]
                )])
                fig_attr.update_layout(
                    title="Outcome Attribution",
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20),
                    showlegend=True
                )
                st.plotly_chart(fig_attr, width="stretch", config={"displayModeBar": False})
            
            with c2:
                # Sentiment pie chart
                fig_sent = go.Figure(data=[go.Pie(
                    labels=["Positive ✅", "Neutral ➖", "Negative ❌"],
                    values=list(sent_counts.values()),
                    hole=0.4,
                    marker_colors=["#4caf50", "#9e9e9e", "#f44336"]
                )])
                fig_sent.update_layout(
                    title="Outcome Sentiment",
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20),
                    showlegend=True
                )
                st.plotly_chart(fig_sent, width="stretch", config={"displayModeBar": False})
            
            # Insight
            decision_outcomes = attr_counts["decision"]
            chance_outcomes = attr_counts["luck"]
            positive_outcomes = sent_counts["positive"]
            negative_outcomes = sent_counts["negative"]
            
            if decision_outcomes > chance_outcomes and positive_outcomes > negative_outcomes:
                st.success("💡 Most positive outcomes are attributed to the decision. Strong choice.")
            elif chance_outcomes > decision_outcomes and positive_outcomes > negative_outcomes:
                st.info("💡 Positive outcomes are mostly luck-driven. Re-evaluate decision quality.")
            elif negative_outcomes > positive_outcomes:
                st.warning("💡 There are more negative than positive outcomes. Review lessons learned.")
        
        else:
            st.info("No outcomes recorded yet. Add your first outcome above.")
    
    # === TRIPWIRES TAB ===
    with retro_tabs[1]:
        st.markdown("### ⚡ Tripwires")
        st.caption("Define events or conditions that should trigger a decision review.")
        
        tripwires = retro.get("tripwires", [])
        for i, tripwire in enumerate(tripwires):
            normalized_status = _normalize_retro_value(tripwire.get("status", "active"))
            if tripwire.get("status") != normalized_status:
                retro["tripwires"][i]["status"] = normalized_status
        
        # Count active and triggered
        active_count = sum(1 for t in tripwires if t.get("status") == "active")
        triggered_count = sum(1 for t in tripwires if t.get("status") == "triggered")
        
        if triggered_count > 0:
            st.error(f"🚨 **{triggered_count} tripwire(s) triggered** — Consider reviewing the decision")
        
        # Add new tripwire
        with st.expander("➕ Add tripwire", expanded=len(tripwires) == 0):
            with st.form("add_tripwire_form", clear_on_submit=True):
                t_trigger = st.text_input(
                    "Trigger event/condition *",
                    placeholder="What should make you reconsider?",
                    key="new_tripwire_trigger"
                )
                
                c1, c2 = st.columns(2)
                with c1:
                    t_target_date = st.date_input(
                        "Target date *",
                        value=date.today(),
                        key="new_tripwire_date",
                        help="When should this tripwire be reviewed?"
                    )
                with c2:
                    t_threshold = st.text_input(
                        "Quantitative threshold (optional)",
                        placeholder="E.g. 'Sales < 10,000 EUR'",
                        key="new_tripwire_threshold"
                    )
                
                if st.form_submit_button("Add tripwire", type="primary"):
                    if t_trigger.strip():
                        new_tripwire = {
                            "id": str(uuid.uuid4()),
                            "trigger": t_trigger.strip(),
                            "target_date": t_target_date.isoformat() if t_target_date else None,
                            "threshold": t_threshold.strip(),
                            "status": "active",
                            "triggered_date": None,
                            "action_taken": ""
                        }
                        retro["tripwires"].append(new_tripwire)
                    else:
                        st.warning("Define the trigger event")
        
        # Display tripwires
        if tripwires:
            # Sort by target_date
            sorted_tripwires = sorted(
                tripwires,
                key=lambda x: x.get("target_date", "9999-12-31")
            )
            
            for tripwire in sorted_tripwires:
                status = tripwire.get("status", "active")
                status_icon = {"active": "🟢", "triggered": "🔴", "resolved": "🏁"}.get(status, "🟢")
                target_date_str = tripwire.get("target_date", "No date")
                
                with st.expander(f"{status_icon} [{target_date_str}] {tripwire['trigger'][:40]}..."):
                    st.markdown(f"**Trigger:** {tripwire['trigger']}")
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        # Parse existing date for the date input
                        existing_date = None
                        if tripwire.get("target_date"):
                            try:
                                existing_date = datetime.fromisoformat(tripwire["target_date"]).date()
                            except:
                                existing_date = date.today()
                        else:
                            existing_date = date.today()
                        
                        new_target_date = st.date_input(
                            "Target date",
                            value=existing_date,
                            key=f"tw_date_{tripwire['id']}"
                        )
                        if new_target_date:
                            tripwire["target_date"] = new_target_date.isoformat()
                    
                    with c2:
                        new_status = st.selectbox(
                            "Status",
                            TRIPWIRE_STATUS,
                            index=TRIPWIRE_STATUS.index(status),
                            key=f"tw_status_{tripwire['id']}"
                        )
                        if new_status != status:
                            tripwire["status"] = new_status
                            if new_status == "triggered" and not tripwire.get("triggered_date"):
                                tripwire["triggered_date"] = date.today().isoformat()
                    
                    with c3:
                        if tripwire.get("triggered_date"):
                            st.markdown(f"**Triggered:** {tripwire['triggered_date']}")
                    
                    if tripwire.get("threshold"):
                        st.markdown(f"**Threshold:** {tripwire['threshold']}")
                    
                    if status == "triggered":
                        action = st.text_area(
                            "Action taken",
                            value=tripwire.get("action_taken", ""),
                            key=f"tw_action_{tripwire['id']}",
                            placeholder="What did you do when it triggered?"
                        )
                        tripwire["action_taken"] = action
                    
                    if st.button("🗑️ Delete", key=f"del_tw_{tripwire['id']}"):
                        retro["tripwires"] = [t for t in retro["tripwires"] if t["id"] != tripwire["id"]]
            
            # Summary metrics
            st.markdown("---")
            m1, m2, m3 = st.columns(3)
            m1.metric("Active", active_count)
            m2.metric("Triggered", triggered_count, delta=f"+{triggered_count}" if triggered_count > 0 else None, delta_color="inverse")
            m3.metric("Total", len(tripwires))
        
        else:
            st.info("No tripwires defined yet. Add your first one above.")
            st.caption("💡 **Tripwire examples:**")
            st.caption("- 'If sales drop more than 20% within 3 months'")
            st.caption("- 'If a competitor launches a similar product'")
            st.caption("- 'If key team members resign'")
    
    # === LESSONS TAB ===
    with retro_tabs[2]:
        st.markdown("### 📝 Lessons Learned")
        
        # Quality scores
        st.markdown("#### Self-assessment")
        
        c1, c2 = st.columns(2)
        with c1:
            decision_score = st.slider(
                "Decision quality (process)",
                min_value=1, max_value=5, value=retro.get("decision_quality_score", 3),
                key="retro_decision_score",
                help="How well did you follow a rigorous decision process?"
            )
            retro["decision_quality_score"] = decision_score
            
            if decision_score <= 2:
                st.caption("😕 Process needs improvement")
            elif decision_score <= 3:
                st.caption("😐 Acceptable process")
            else:
                st.caption("😊 Strong process")
        
        with c2:
            outcome_score = st.slider(
                "Outcome quality",
                min_value=1, max_value=5, value=retro.get("outcome_quality_score", 3),
                key="retro_outcome_score",
                help="How good were the achieved outcomes?"
            )
            retro["outcome_quality_score"] = outcome_score
            
            if outcome_score <= 2:
                st.caption("😕 Poor outcomes")
            elif outcome_score <= 3:
                st.caption("😐 Acceptable outcomes")
            else:
                st.caption("😊 Strong outcomes")
        
        # Decision quality matrix insight
        st.markdown("---")
        if decision_score >= 4 and outcome_score >= 4:
            st.success("🏆 **Strong decision, strong outcome** — keep it up.")
        elif decision_score >= 4 and outcome_score <= 2:
            st.info("🎲 **Strong decision, weak outcome** — luck can still work against you. Process was solid.")
        elif decision_score <= 2 and outcome_score >= 4:
            st.warning("🍀 **Weak decision, strong outcome** — likely luck. Improve process for next time.")
        elif decision_score <= 2 and outcome_score <= 2:
            st.error("⚠️ **Weak decision, weak outcome** — review what failed in the process.")
        
        st.markdown("---")
        
        # Lessons learned text
        lessons = st.text_area(
            "Lessons learned",
            value=retro.get("lessons_learned", ""),
            key="retro_lessons",
            height=200,
            placeholder="What did you learn from this decision?\n\n- What would you do differently?\n- What information was missing?\n- Which biases appeared?\n- What worked well?"
        )
        retro["lessons_learned"] = lessons
        
        # Quick prompts
        st.caption("💡 **Reflection prompts:**")
        prompts = [
            "What information would have changed my decision?",
            "Which cognitive biases may have affected me?",
            "Did I consult the right people?",
            "Did I spend the right amount of analysis time?",
            "What will I do differently next time?",
        ]
        for prompt in prompts:
            st.caption(f"  • {prompt}")

