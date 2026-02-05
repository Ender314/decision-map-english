# -*- coding: utf-8 -*-
"""
Monitoring Timeline component - Visual timeline of outcomes, tripwires, and risks.
Provides a chronological overview of the decision monitoring phase.
"""

import streamlit as st
from datetime import date, datetime, timedelta
from collections import defaultdict
import plotly.graph_objects as go
from config.constants import RISK_PROB_MAP, RISK_IMPACT_MAP


def get_recommended_alternative():
    """Get the recommended alternative from scenarios/MCDA analysis.
    
    Calculates a composite score: 50% MCDA + 50% scenario EV.
    Falls back to first qualified alternative if no analysis data available.
    Only considers alternatives that pass all No Negociables.
    
    Returns:
        Tuple of (alt_id, alt_name) or (None, None)
    """
    from utils.calculations import mcda_totals_and_ranking, get_disqualified_alternatives
    
    scenarios = st.session_state.get("scenarios", {})
    mcda_scores_df = st.session_state.get("mcda_scores_df")
    mcda_criteria = st.session_state.get("mcda_criteria", [])
    all_alts = st.session_state.get("alts", [])
    
    if not all_alts:
        return None, None
    
    # Filter out disqualified alternatives
    disqualified_alts = get_disqualified_alternatives()
    alts = [a for a in all_alts if a["id"] not in disqualified_alts]
    
    if not alts:
        return None, None
    
    # Build composite ranking if we have both MCDA and scenarios
    if scenarios and mcda_scores_df is not None and not mcda_scores_df.empty:
        _, mcda_ranking = mcda_totals_and_ranking(mcda_scores_df.copy(), mcda_criteria)
        
        combined_data = []
        for alt in alts:
            alt_id = alt["id"]
            alt_name = alt["text"].strip()
            if not alt_name:
                continue
                
            scenario_data = scenarios.get(alt_id, {})
            ev = scenario_data.get("ev", 5.0)
            ev_scaled = ev / 2.0
            
            mcda_score = next((item["score"] for item in mcda_ranking if item["alternativa"] == alt_name), None)
            
            if mcda_score is not None:
                composite = 0.5 * mcda_score + 0.5 * ev_scaled
                combined_data.append({
                    "id": alt_id,
                    "name": alt_name,
                    "composite": composite
                })
        
        if combined_data:
            winner = max(combined_data, key=lambda x: x["composite"])
            return winner["id"], winner["name"]
    
    # Fallback: first qualified alternative
    first_alt = next((a for a in alts if a["text"].strip()), None)
    if first_alt:
        return first_alt["id"], first_alt["text"].strip()
    
    return None, None


def render_recommended_alternative_banner():
    rec_id, rec_name = get_recommended_alternative()
    if not rec_name:
        return
    
    st.caption("Alternativa recomendada")
    st.markdown(f"**{rec_name}**")


# Extended probability/impact maps including "ninguno" for resolved risks
EXTENDED_PROB_MAP = {"ninguno": 0, **RISK_PROB_MAP}
EXTENDED_IMPACT_MAP = {"ninguno": 0, **RISK_IMPACT_MAP}


def calculate_risk_score_extended(probability: str, impact: str) -> float:
    """Calculate risk score including 'ninguno' option for resolved risks."""
    prob_val = EXTENDED_PROB_MAP.get(probability, 1)
    impact_val = EXTENDED_IMPACT_MAP.get(impact, 1)
    return prob_val * impact_val


def interpolate_risk_scores(assessments: list, date_range: list, start_date: date = None) -> list:
    """
    Interpolate risk scores between assessment dates using linear interpolation.
    Similar to dimensionado chart's spline approach.
    
    Args:
        assessments: List of assessment dicts with date, probability, impact
        date_range: List of dates to interpolate scores for
        start_date: Optional date when the risk was created. Returns None for dates before this.
        
    Returns:
        List of interpolated scores for each date in date_range (None for dates before start_date)
    """
    if not assessments or not date_range:
        return []
    
    # Sort assessments by date
    sorted_assessments = sorted(assessments, key=lambda x: x.get("date", ""))
    
    # Convert to date objects and scores
    assessment_points = []
    for a in sorted_assessments:
        a_date = parse_date(a.get("date"))
        if a_date:
            score = calculate_risk_score_extended(
                a.get("probability", "medio"),
                a.get("impact", "medio")
            )
            assessment_points.append((a_date, score))
    
    if not assessment_points:
        return [None] * len(date_range)
    
    # Use first assessment date as start_date if not provided
    if start_date is None:
        start_date = assessment_points[0][0]
    
    # Interpolate for each date in range
    interpolated = []
    for target_date in date_range:
        # Return None for dates before the risk existed
        if target_date < start_date:
            interpolated.append(None)
            continue
        
        # Find surrounding assessment points
        before = None
        after = None
        
        for a_date, score in assessment_points:
            if a_date <= target_date:
                before = (a_date, score)
            if a_date >= target_date and after is None:
                after = (a_date, score)
        
        if before is None and after is None:
            interpolated.append(None)
        elif before is None:
            # Before first assessment but after start_date - use first value
            interpolated.append(after[1])
        elif after is None:
            # After last assessment - fade out if resolved, else hold
            if before[1] == 0:
                interpolated.append(0)
            else:
                # Gradual fade over 30 days after last assessment
                days_after = (target_date - before[0]).days
                fade_factor = max(0, 1 - (days_after / 30))
                interpolated.append(before[1] * fade_factor)
        elif before[0] == after[0]:
            # Exact match
            interpolated.append(before[1])
        else:
            # Linear interpolation between points
            total_days = (after[0] - before[0]).days
            days_from_before = (target_date - before[0]).days
            if total_days > 0:
                ratio = days_from_before / total_days
                interpolated_score = before[1] + (after[1] - before[1]) * ratio
                interpolated.append(interpolated_score)
            else:
                interpolated.append(before[1])
    
    return interpolated


def parse_date(date_val):
    """Parse various date formats to date object."""
    if date_val is None:
        return None
    if isinstance(date_val, date):
        return date_val
    if isinstance(date_val, datetime):
        return date_val.date()
    if isinstance(date_val, str) and date_val.strip():
        try:
            return datetime.fromisoformat(date_val).date()
        except:
            return None
    return None


def render_monitoring_timeline():
    """Render the monitoring timeline overview."""
    render_recommended_alternative_banner()
    st.markdown("---")
    st.markdown("### 📅 Línea Temporal de Seguimiento")
    
    retro = st.session_state.get("retro", {})
    outcomes = retro.get("outcomes", [])
    tripwires = retro.get("tripwires", [])
    risks = st.session_state.get("risks", {})
    decision_date = parse_date(retro.get("decision_date"))
    
    # Collect all timeline events
    events = []
    
    # Add decision date as starting point
    if decision_date:
        events.append({
            "date": decision_date,
            "type": "decision",
            "title": "Decisión tomada",
            # "description": st.session_state.get("decision", "")[:50] + "...",
            "description": st.session_state.get("decision", "")[:5],
            "color": "#2196f3",
            "symbol": "diamond",
            "legend_group": "Decisión"
        })
    
    # Add outcomes
    for outcome in outcomes:
        outcome_date = parse_date(outcome.get("date"))
        if outcome_date:
            sentiment = outcome.get("sentiment", "neutral")
            color = {"positivo": "#4caf50", "neutral": "#607d8b", "negativo": "#f44336"}.get(sentiment, "#607d8b")
            events.append({
                "date": outcome_date,
                "type": "outcome",
                # "title": outcome.get("description", "")[:80] + "...",
                "title": outcome.get("description", "")[:] ,
                "description": f"Atribución: {outcome.get('attribution', 'mixto')}",
                "color": color,
                "symbol": "circle",
                "sentiment": sentiment,
                "legend_group": "Resultados"
            })
    
    # Add tripwires
    for tripwire in tripwires:
        tripwire_date = parse_date(tripwire.get("target_date"))
        if tripwire_date:
            status = tripwire.get("status", "activo")
            if status == "activo":
                color = "#ff9800"  # Orange for active
                symbol = "triangle-up"
            elif status == "disparado":
                color = "#e91e63"  # Pink/red for triggered
                symbol = "x"
            else:
                color = "#9e9e9e"  # Gray for dismissed
                symbol = "triangle-down"
            
            events.append({
                "date": tripwire_date,
                "type": "tripwire",
                # "title": tripwire.get("trigger", "")[:50] + "...",
                "title": tripwire.get("trigger", "")[:],
                "description": tripwire.get("threshold", "") or f"Estado: {status}",
                "color": color,
                "symbol": symbol,
                "status": status,
                "legend_group": "Tripwires"
            })
    
    # Add risks (with created_at date)
    for risk_id, risk in risks.items():
        risk_date = parse_date(risk.get("created_at"))
        if risk_date:
            risk_title = (risk.get("title", "") or "").strip()
            # risk_title_display = risk_title[:50] + "..." if len(risk_title) > 39 else risk_title
            risk_title_display = risk_title
            events.append({
                "date": risk_date,
                "type": "risk",
                "title": risk_title_display,
                "description": f"Cat: {risk.get('category', '')} | {risk.get('probability', '')}/{risk.get('impact', '')}",
                "color": "#9c27b0",  # Purple for risks
                "symbol": "triangle-right",
                "legend_group": "Riesgos"
            })
    
    if not events:
        st.info("No hay eventos en la línea temporal. Define la fecha de decisión y añade resultados, tripwires o riesgos.")
        
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Resultados", len(outcomes))
        col2.metric("Tripwires", len(tripwires))
        col3.metric("Riesgos", len(risks))
        active_tripwires = sum(1 for t in tripwires if t.get("status") == "activo")
        col4.metric("Tripwires Activos", active_tripwires)
        return
    
    # Sort events by date, then by type for consistent ordering
    type_order = {"decision": 0, "risk": 1, "tripwire": 2, "outcome": 3}
    events.sort(key=lambda x: (x["date"], type_order.get(x["type"], 99)))
    
    # Calculate vertical offsets for same-date events (stacking)
    # Separate stacking for above (risks, tripwires, decision) and below (outcomes) the axis
    above_counts = defaultdict(int)  # For risks, tripwires, decision
    below_counts = defaultdict(int)  # For outcomes
    
    for event in events:
        date_key = event["date"]
        if event["type"] == "outcome":
            event["stack_index"] = below_counts[date_key]
            below_counts[date_key] += 1
            event["y_direction"] = -1  # Below axis
        else:
            event["stack_index"] = above_counts[date_key]
            above_counts[date_key] += 1
            event["y_direction"] = 1  # Above axis
    
    # Calculate max stack height for y-axis range
    max_above = max(above_counts.values()) if above_counts else 1
    max_below = max(below_counts.values()) if below_counts else 1
    y_spacing = 0.4  # Vertical spacing between stacked items
    
    # Risk evolution toggle (placed before figure so we can integrate it)
    show_risk_evolution = False
    if risks:
        show_risk_evolution = st.checkbox("📈 Mostrar evolución de riesgos", value=False, 
                                          key="monitoring_timeline_risk_evolution_toggle",
                                          help="Muestra la evolución del score de riesgo superpuesta en la línea temporal")
    
    # Create timeline visualization with interactive legend
    fig = go.Figure()
    
    # Group events by legend_group for clickable legend
    legend_groups = defaultdict(list)
    for event in events:
        legend_groups[event["legend_group"]].append(event)
    
    # Define legend group properties
    legend_props = {
        "Decisión": {"color": "#2196f3", "symbol": "diamond"},
        "Resultados": {"color": "#4caf50", "symbol": "circle"},
        "Tripwires": {"color": "#ff9800", "symbol": "triangle-up"},
        "Riesgos": {"color": "#9c27b0", "symbol": "triangle-right"}
    }
    
    # Add decision marker at y=0 (keep as diamond symbol)
    decision_events = [e for e in events if e["type"] == "decision"]
    if decision_events:
        x_dec = [e["date"] for e in decision_events]
        y_dec = [0 for _ in decision_events]  # Decision always at y=0
        hovers_dec = [
            f"<b>{e['title']}</b><br>"
            f"Fecha: {e['date']}<br>"
            f"{e['description']}"
            for e in decision_events
        ]
        fig.add_trace(go.Scatter(
            x=x_dec,
            y=y_dec,
            mode="markers",
            marker=dict(size=18, color="#2196f3", symbol="diamond", line=dict(width=2, color="white")),
            name="◆ Decisión",
            legendgroup="Decisión",
            showlegend=True,
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hovers_dec
        ))
    
    # Add emoji markers for risks (⚠️)
    risk_events = [e for e in events if e["type"] == "risk"]
    if risk_events:
        x_risk = [e["date"] for e in risk_events]
        y_risk = [e.get("y_direction", 1) * (0.2 + e["stack_index"] * y_spacing) for e in risk_events]
        text_risk = ["⚠️" for _ in risk_events]
        hovers_risk = [
            f"<b>{e['title']}</b><br>"
            f"Fecha: {e['date']}<br>"
            f"{e['description']}"
            for e in risk_events
        ]
        fig.add_trace(go.Scatter(
            x=x_risk,
            y=y_risk,
            mode="text",
            text=text_risk,
            textfont=dict(size=16),
            name="⚠️ Riesgos",
            legendgroup="Riesgos",
            showlegend=True,
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hovers_risk
        ))
    
    # Add emoji markers for tripwires (⚡ active, 💥 triggered, 🏁 surpassed)
    tripwire_events = [e for e in events if e["type"] == "tripwire"]
    if tripwire_events:
        tripwire_emoji_map = {"activo": "⚡", "disparado": "💥", "superado": "🏁"}
        x_trip = [e["date"] for e in tripwire_events]
        y_trip = [e.get("y_direction", 1) * (0.2 + e["stack_index"] * y_spacing) for e in tripwire_events]
        text_trip = [tripwire_emoji_map.get(e.get("status", "activo"), "⚡") for e in tripwire_events]
        hovers_trip = [
            f"<b>{e['title']}</b><br>"
            f"Fecha: {e['date']}<br>"
            f"{e['description']}"
            for e in tripwire_events
        ]
        fig.add_trace(go.Scatter(
            x=x_trip,
            y=y_trip,
            mode="text",
            text=text_trip,
            textfont=dict(size=16),
            name="⚡ Tripwires",
            legendgroup="Tripwires",
            showlegend=True,
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hovers_trip
        ))
    
    # Add emoji text markers for outcomes
    outcome_events = [e for e in events if e["type"] == "outcome"]
    if outcome_events:
        emoji_map = {"positivo": "✅", "neutral": "➖", "negativo": "❌"}
        x_emoji = [e["date"] for e in outcome_events]
        y_emoji = [e.get("y_direction", -1) * (0.2 + e["stack_index"] * y_spacing) for e in outcome_events]
        text_emoji = [emoji_map.get(e.get("sentiment", "neutral"), "➖") for e in outcome_events]
        hovers_emoji = [
            f"<b>{e['title']}</b><br>"
            f"Fecha: {e['date']}<br>"
            f"{e['description']}"
            for e in outcome_events
        ]
        
        fig.add_trace(go.Scatter(
            x=x_emoji,
            y=y_emoji,
            mode="text",
            text=text_emoji,
            textfont=dict(size=16),
            name="✅ Resultados",
            legendgroup="Resultados",
            showlegend=True,
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hovers_emoji
        ))
    
    # Add today marker
    today = date.today()
    min_date = min(e["date"] for e in events)
    max_date = max(max(e["date"] for e in events), today)  # Ensure chart extends to today
    
    # Extend date range slightly for better visualization
    if min_date <= today or today <= max_date:
        fig.add_vline(x=today, line_dash="dash", line_color="#673ab7", opacity=0.7)
        fig.add_annotation(
            x=today, y=max_above * y_spacing + 0.5,
            text="Hoy",
            showarrow=False,
            font=dict(size=10, color="#673ab7")
        )
    
    # Add risk evolution traces if toggled on
    y_range_max = max_above * y_spacing + 0.6
    if show_risk_evolution and risks:
        add_risk_evolution_to_figure(fig, risks, min_date, max_date, today, y_range_max)
    
    # Layout with interactive legend
    fig.update_layout(
        height=int((220 + (max(max_above, max_below) * 25)) * 1.6),  # Dynamic height based on stacking
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            itemclick="toggle",
            itemdoubleclick="toggleothers",
            font=dict(size=11)
        ),
        xaxis=dict(
            title="",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.05)"
        ),
        yaxis=dict(
            title="",
            showticklabels=False,
            range=[-(0.3 + max_below * y_spacing), y_range_max],
            showgrid=False,
            zeroline=True,
            zerolinecolor="#e0e0e0",
            zerolinewidth=2
        ),
        plot_bgcolor="white",
        margin=dict(l=20, r=20, t=50, b=40),
        hovermode="closest"
    )
    
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    # Legend help text
    st.caption("💡 Haz clic en la leyenda para mostrar/ocultar categorías. Doble clic para aislar una categoría.")
    
    # Summary metrics
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1])
    
    with col1:
        st.metric("Resultados", len(outcomes))
    
    with col2:
        positive = sum(1 for o in outcomes if o.get("sentiment") == "positivo")
        negative = sum(1 for o in outcomes if o.get("sentiment") == "negativo")
        delta = positive - negative if outcomes else None
        st.metric("Balance", f"+{positive}/-{negative}", delta=delta if delta else None)
    
    with col3:
        active = sum(1 for t in tripwires if t.get("status") == "activo")
        st.metric("Tripwires Activos", active)
    
    with col4:
        triggered = sum(1 for t in tripwires if t.get("status") == "disparado")
        st.metric("Disparados", triggered, delta=f"+{triggered}" if triggered > 0 else None, delta_color="inverse")
    
    with col5:
        st.metric("Riesgos", len(risks))
    
    with col6:
        st.markdown("")
        st.button("🔄 Refresh data", key="refresh_monitoring_timeline_chart")
    
    # Upcoming tripwires warning
    upcoming = []
    for t in tripwires:
        if t.get("status") == "activo":
            t_date = parse_date(t.get("target_date"))
            if t_date and t_date >= today:
                days_until = (t_date - today).days
                if days_until <= 30:
                    upcoming.append((days_until, t))
    
    if upcoming:
        upcoming.sort(key=lambda x: x[0])
        st.warning(f"⚠️ **{len(upcoming)} tripwire(s) próximo(s) en los siguientes 30 días:**")
        for days, t in upcoming[:3]:
            if days == 0:
                st.markdown(f"  - **HOY**: {t.get('trigger', '')[:100]}")
            elif days == 1:
                st.markdown(f"  - **Mañana**: {t.get('trigger', '')[:100]}")
            else:
                st.markdown(f"  - **En {days} días**: {t.get('trigger', '')[:100]}")


def get_risk_assessments_with_creation(risk: dict) -> list:
    """
    Get assessments for a risk, using creation date as first assessment if needed.
    
    Args:
        risk: Risk dict with optional assessments and created_at fields
        
    Returns:
        List of assessment dicts
    """
    assessments = risk.get("assessments", [])
    created_at = risk.get("created_at")
    
    # If no assessments but has created_at, create initial assessment from risk definition
    if not assessments and created_at:
        return [{
            "date": created_at,
            "probability": risk.get("probability", "medio"),
            "impact": risk.get("impact", "medio")
        }]
    
    return assessments


def add_risk_evolution_to_figure(fig, risks: dict, min_date: date, max_date: date, today: date, y_range_max: float):
    """
    Add risk evolution traces to an existing Plotly figure.
    
    Args:
        fig: Plotly figure to add traces to
        risks: Dict of risks
        min_date: Start date for the chart
        max_date: End date for the chart
        today: Current date for reference line
        y_range_max: Maximum y value for scaling risk scores
    """
    # Find the max date across all risk assessments (not just timeline events)
    all_assessment_dates = []
    for risk in risks.values():
        for assessment in risk.get("assessments", []):
            a_date = parse_date(assessment.get("date"))
            if a_date:
                all_assessment_dates.append(a_date)
    
    # Calculate actual max date including assessments
    actual_max_date = max_date
    if all_assessment_dates:
        actual_max_date = max(max_date, max(all_assessment_dates))
    
    # Generate date range for interpolation (daily granularity)
    chart_start = min_date - timedelta(days=0)
    chart_end = max(actual_max_date, today) + timedelta(days=1)
    
    num_days = (chart_end - chart_start).days + 1
    date_range = [chart_start + timedelta(days=i) for i in range(num_days)]
    
    # Color palette for different risks
    colors = ["#e91e63", "#9c27b0", "#673ab7", "#3f51b5", "#2196f3", 
              "#00bcd4", "#009688", "#4caf50", "#8bc34a", "#cddc39"]
    
    # Max risk score for scaling (prob 3 * impact 4 = 12)
    max_score = 12.0
    # Scale factor to fit risk scores into the timeline y-range
    scale_factor = y_range_max / max_score
    
    # Store all interpolated scores for average calculation (with None handling)
    all_scores = []
    
    # Add a line for each risk
    for i, (risk_id, risk) in enumerate(risks.items()):
        assessments = get_risk_assessments_with_creation(risk)
        if not assessments:
            continue
        
        # Get risk creation date for interpolation start
        risk_start_date = parse_date(risk.get("created_at"))
        
        # Interpolate scores for this risk (starting from creation date)
        scores = interpolate_risk_scores(assessments, date_range, start_date=risk_start_date)
        # Scale scores to fit timeline y-range (None values stay None)
        scaled_scores = [s * scale_factor if s is not None else None for s in scores]
        all_scores.append(scores)  # Store unscaled for average calculation
        
        # Get risk title (truncated)
        title = risk.get("title", "Riesgo")[:33]
        if len(risk.get("title", "")) > 33:
            title += "..."
        # Get risk title
        # title = risk.get("title", "Riesgo")
        
        color = colors[i % len(colors)]
        
        # Add line trace (Plotly handles None values as gaps)
        fig.add_trace(go.Scatter(
            x=date_range,
            y=scaled_scores,
            mode="lines",
            name=f"📈 {title}",
            legendgroup=f"risk_evo_{risk_id}",
            line=dict(color=color, width=2, shape="spline"),
            fill="tozeroy",
            fillcolor=f"rgba{tuple(list(int(color.lstrip('#')[j:j+2], 16) for j in (0, 2, 4)) + [0.15])}",
            hovertemplate=(
                f"<b>{title}</b><br>"
                "Fecha: %{x}<br>"
                f"Score: %{{customdata:.1f}}<br>"
                "<extra></extra>"
            ),
            customdata=scores  # Original unscaled scores for hover
        ))
        
        # Add assessment points as markers
        for assessment in assessments:
            a_date = parse_date(assessment.get("date"))
            if a_date:
                a_score = calculate_risk_score_extended(
                    assessment.get("probability", "medio"),
                    assessment.get("impact", "medio")
                )
                scaled_a_score = a_score * scale_factor
                fig.add_trace(go.Scatter(
                    x=[a_date],
                    y=[scaled_a_score],
                    mode="markers",
                    marker=dict(size=8, color=color, symbol="circle", line=dict(width=1, color="white")),
                    name=f"📈 {title}",
                    legendgroup=f"risk_evo_{risk_id}",
                    showlegend=False,
                    hovertemplate=(
                        f"<b>{title}</b><br>"
                        f"Evaluación: {a_date}<br>"
                        f"P: {assessment.get('probability', '')}<br>"
                        f"I: {assessment.get('impact', '')}<br>"
                        f"Score: {a_score}<br>"
                        "<extra></extra>"
                    )
                ))
    

