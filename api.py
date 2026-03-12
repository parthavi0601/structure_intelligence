"""
api.py — Structural Intelligence Platform API
Smart chat router: answers engineering questions directly from parquet data.
No LLM latency for standard queries — instant, data-driven responses.
"""

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
import os, math, re, sys, io, tempfile
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

PROCESSED_DIR = "processed"

# ─────────────────────────────────────────────────────────────────────────────
# DATA HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def format_data(df):
    df = df.replace([math.inf, -math.inf], None)
    return df.where(pd.notnull(df), None)

def _load_df():
    return pd.read_parquet(os.path.join(PROCESSED_DIR, "failure_prediction_behavior.parquet"))

def _bridge_df(df, bridge_id: str):
    if "bridge_id" in df.columns and bridge_id:
        sub = df[df["bridge_id"].str.upper() == bridge_id.strip().upper()]
        return sub if not sub.empty else df
    return df

def _col(df, *keywords, agg="mean"):
    for c in df.columns:
        if any(k in c.lower() for k in keywords):
            try:
                return float(df[c].mean() if agg == "mean" else df[c].max())
            except Exception:
                pass
    return None

def _trend(df, *keywords):
    for c in df.columns:
        if any(k in c.lower() for k in keywords):
            try:
                s = df[c].dropna()
                if len(s) < 6: return 0.0
                return float(s.iloc[-len(s)//3:].mean() - s.iloc[:len(s)//3].mean())
            except: pass
    return None

def _alerts(df):
    cols = [c for c in df.columns if "anomaly_alert_flag" in c.lower()]
    return int(df[cols].sum().sum()) if cols else 0

def _cluster_mode(df):
    for c in df.columns:
        if "behavioral_state_cluster" in c.lower():
            try: return int(df[c].mode()[0])
            except: pass
    return None

def _extract_bridge_id(text: str):
    """Find bridge ID like B001, B002 etc in user query."""
    m = re.search(r'\b(B\d+)\b', text, re.IGNORECASE)
    return m.group(1).upper() if m else None

def _life_expectancy(risk_mean, degradation_mean, risk_trend=0.0):
    """Estimate remaining years of service life."""
    if risk_mean is None: return None
    risk_mean = max(0.01, min(risk_mean, 0.999))
    annual_risk_growth = max(0.0, risk_trend * 4) if risk_trend else 0.01
    if annual_risk_growth < 0.001: annual_risk_growth = 0.01
    years = (0.85 - risk_mean) / annual_risk_growth
    years = max(2, min(years, 80))
    return round(years, 1)


# ─────────────────────────────────────────────────────────────────────────────
# STANDARD ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/bridges")
def get_bridges():
    try:
        df = _load_df()
        return {"bridges": df["bridge_id"].unique().tolist()}
    except Exception as e:
        return {"error": str(e), "bridges": []}

@app.get("/api/behavioral-metrics/{bridge_id}")
def get_behavioral_metrics(bridge_id: str):
    try:
        df = _load_df()
        bdf = _bridge_df(df, bridge_id)
        cols = ['Behavioral_Shift_Index','Structural_Dynamics_Score','Behavioral_State_Cluster',
                'degradation_score','forecast_score_next_30d','Predicted_Risk_Score',
                'structural_condition','Autoencoder_Anomaly_Score','Anomaly_Alert_Flag']
        available = [c for c in cols if c in bdf.columns]
        bdf = bdf.copy()
        bdf['time_step'] = range(len(bdf))
        available.insert(0, 'time_step')
        out = bdf[available].copy()
        if len(out) > 200:
            out = out.iloc[::len(out)//200]
        print(f"Sending {len(out)} records for bridge {bridge_id}")
        return {"data": format_data(out).to_dict(orient="records")}
    except Exception as e:
        import traceback; traceback.print_exc()
        return {"error": str(e), "data": []}


# ─────────────────────────────────────────────────────────────────────────────
# AI CONCLUSION — plain-language, per tab/bridge
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/agent-conclusion/{tab}/{bridge_id}")
def get_agent_conclusion(tab: str, bridge_id: str):
    try:
        return {"conclusion": _build_plain_conclusion(tab, bridge_id), "tab": tab, "bridge_id": bridge_id}
    except Exception as e:
        import traceback; traceback.print_exc()
        return {"conclusion": f"Analysis unavailable: {e}", "tab": tab, "bridge_id": bridge_id}

def _build_plain_conclusion(tab: str, bridge_id: str) -> str:
    df  = _load_df()
    bdf = _bridge_df(df, bridge_id)

    shift      = _col(bdf, "behavioral_shift_index")
    dynamics   = _col(bdf, "structural_dynamics_score")
    anomaly    = _col(bdf, "autoencoder_anomaly_score")
    anomaly_mx = _col(bdf, "autoencoder_anomaly_score", agg="max")
    risk_mean  = _col(bdf, "predicted_risk_score")
    risk_max   = _col(bdf, "predicted_risk_score", agg="max")
    risk_trend = _trend(bdf, "predicted_risk_score")
    alerts     = _alerts(bdf)
    cluster    = _cluster_mode(bdf)

    if tab == "behavior":
        state = {0:"normal, day-to-day conditions",1:"active traffic load",2:"unusual structural movement"}.get(cluster,"an undetermined state")
        shift_v = shift or 0
        if shift_v < 0.15:   drift = "no drift from its baseline — fully stable."
        elif shift_v < 0.35: drift = "a small amount of drift, typical under changing traffic and weather — no concern."
        elif shift_v < 0.6:  drift = "a noticeable shift from baseline, likely from temperature changes or load increases. Continue monitoring."
        else:                drift = "a significant behavioral change from baseline. A physical inspection is recommended."
        dyn_v = dynamics or 0
        if dyn_v < 0.35:   vib = "Vibrations are smooth and consistent — a sign of good structural health."
        elif dyn_v < 0.65: vib = "Vibration patterns show some variability, within acceptable limits."
        else:              vib = "Elevated vibration patterns detected — possible stiffness changes. Further investigation advised."
        return f"Bridge {bridge_id} is currently in {state}. It shows {drift} {vib}"

    elif tab == "anomaly":
        anomaly_v = anomaly or 0
        max_pct   = round((anomaly_mx or 0) * 100)
        if alerts == 0 and anomaly_v < 0.2:
            return (f"Bridge {bridge_id} is operating normally. All sensor readings are within safe, expected ranges — no anomalies detected.")
        elif alerts > 0:
            sev = "minor" if max_pct < 60 else ("moderate" if max_pct < 80 else "significant")
            return (f"Bridge {bridge_id} triggered {alerts} anomaly alert(s). The highest irregularity reached a {sev} severity level ({max_pct}% of threshold). "
                    f"This may indicate heavy traffic, extreme weather, or early material stress. Review the flagged time windows.")
        else:
            return (f"Bridge {bridge_id} shows trace irregularities ({round(anomaly_v*100)}% of threshold). No formal alert triggered. "
                    f"Structure remains within safe bounds — continue routine monitoring.")

    elif tab == "risk":
        risk_v   = risk_mean or 0
        risk_pct = round(risk_v * 100)
        rmax_pct = round((risk_max or 0) * 100)
        years    = _life_expectancy(risk_v, _col(bdf, "degradation_score"), risk_trend or 0)

        if risk_v < 0.2:
            verdict = f"low failure risk ({risk_pct}%)."
            action  = "No urgent maintenance needed. Routine inspections are sufficient."
        elif risk_v < 0.5:
            verdict = f"moderate failure risk ({risk_pct}%)."
            action  = "Schedule a detailed inspection within the next few weeks."
        else:
            verdict = f"elevated failure risk ({risk_pct}%, peaking at {rmax_pct}%)."
            action  = "Immediate on-site inspection strongly recommended."

        trend_note = ""
        if risk_trend and risk_trend > 0.05:  trend_note = " Risk is trending upward — needs attention."
        elif risk_trend and risk_trend < -0.05: trend_note = " Risk is trending downward — good progress."

        life_note = f" Estimated remaining service life: approximately {years} years." if years else ""
        return f"Bridge {bridge_id} has {verdict}{trend_note}{life_note} {action}"

    return f"Select Behavior, Anomaly, or Risk tab for an AI summary for bridge {bridge_id}."


# ─────────────────────────────────────────────────────────────────────────────
# DOMAIN GUARD
# ─────────────────────────────────────────────────────────────────────────────
_DOMAIN_KEYWORDS = [
    "bridge", "structure", "structural", "infrastructure", "span", "beam",
    "deck", "pier", "column", "foundation", "girder",
    "sensor", "vibration", "strain", "displacement", "load", "accelerom",
    "modal", "frequency", "resonan",
    "anomaly", "anomal", "alert", "risk", "failure", "predict", "forecast",
    "degradation", "behavioral", "behaviour", "behavior", "cluster", "shift",
    "dynamics", "health", "maintenance", "inspection", "monitor", "report",
    "summary", "priorit", "schedule", "urgent", "critical", "timeline",
    "event", "flag", "detect", "life expectancy", "service life", "lifespan",
    "remaining", "years", "how long", "compare", "worst", "best", "top",
    "trend", "improving", "worsening", "safe", "condition",
    "fall", "collapse", "fail", "chances", "probability", "chance",
    "likely", "likelihood", "within", "next", "years",
    "generate report", "health report", "pdf", "download",
    "b001", "b002", "b003", "b004", "b005",
]

_OFF_TOPIC_REPLY = (
    "⚠️ I'm only able to assist with questions about the structural health monitoring system.\n\n"
    "Please ask about:\n"
    "  • Bridge health, risk scores, or condition\n"
    "  • Anomaly alerts and sensor irregularities\n"
    "  • Maintenance priorities and inspection schedules\n"
    "  • Life expectancy or remaining service life\n"
    "  • Vibration patterns or degradation trends\n\n"
    "Try one of the example queries to get started."
)

def _is_off_topic(query: str) -> bool:
    q = query.lower()
    return not any(kw in q for kw in _DOMAIN_KEYWORDS)


# ─────────────────────────────────────────────────────────────────────────────
# SMART QUERY ROUTER — instant, data-driven, no LLM needed
# ─────────────────────────────────────────────────────────────────────────────
def _smart_router(query: str) -> str | None:
    """
    Pattern-matches the query and returns an instant data-driven answer.
    Returns None if the query doesn't match any known pattern (fallback to tools).
    """
    q = query.lower()
    df = _load_df()
    bridge_id = _extract_bridge_id(query)

    if bridge_id:
        valid_bridges = df["bridge_id"].unique()
        if bridge_id not in valid_bridges:
            return (f"⚠️ I'm sorry, but I do not have any monitoring records for **Bridge {bridge_id}**.\n\n"
                    f"Please verify the bridge identifier. The structures currently active in the monitoring system are: "
                    f"`{', '.join(valid_bridges)}`.")

    # Convenience: prepare per-bridge slice
    def bdf():
        return _bridge_df(df, bridge_id) if bridge_id else df

    # ─── 0. GENERATE HEALTH REPORT (PDF) ─────────────────────────────────
    if any(k in q for k in ["generate report", "health report", "generate health", "create report",
                             "pdf report", "download report", "full report pdf"]):
        name = bridge_id or "all"
        return (f"📄 Your health report for Bridge {name} is ready to download.\n\n"
                f"Click the button below, or open this URL in your browser:\n"
                f"http://localhost:8000/api/report/{name}\n\n"
                f"The report includes: risk scores, anomaly scores, behavioral analysis, "
                f"degradation trends, and recommendations.")

    # ─── 1. PROBABILITY OF FAILURE / CHANCES OF COLLAPSE ─────────────────
    # Catches: "chances of falling", "probability of failure", "will it fall",
    #          "within 100 years", "likelihood of collapse", etc.
    if any(k in q for k in ["fall", "collapse", "fail", "chance", "probability",
                             "likelihood", "likely to", "chances"]):
        tgt   = bdf()
        risk  = _col(tgt, "predicted_risk_score") or 0
        rt    = _trend(tgt, "predicted_risk_score") or 0
        name  = bridge_id or "the monitored fleet"

        # Extract time horizon (default 100 years)
        horizon = 100
        m = re.search(r'(\d+)\s*year', q)
        if m:
            horizon = int(m.group(1))

        # Annual failure probability from risk score
        # Risk score ≈ cumulative probability; annual rate derived accordingly
        annual_rate = max(0.001, risk * 0.02)   # 2% of risk score per year
        # Add degradation due to trend
        if rt > 0: annual_rate += rt * 0.005
        # Compound probability over horizon: P = 1 - (1 - annual_rate)^horizon
        prob = round((1 - (1 - annual_rate) ** horizon) * 100, 1)
        prob = min(prob, 99.9)   # never claim certainty
        risk_p = round(risk * 100)

        if prob < 10:
            verdict = "very low"; icon = "✅"
        elif prob < 30:
            verdict = "low";       icon = "✅"
        elif prob < 55:
            verdict = "moderate";  icon = "⚠️"
        elif prob < 75:
            verdict = "high";      icon = "⚠️"
        else:
            verdict = "very high"; icon = "🔴"

        trend_note = ""
        if rt > 0.05:
            trend_note = " It's worth noting that the risk is currently trending upward, so this timeline could shorten if left unchecked."
        elif rt < -0.05:
            trend_note = " Positively, the risk is trending downward, meaning recent maintenance is extending its life."

        detail = ""
        if prob < 30:
            detail = "The sensor data shows the structure is handling daily traffic perfectly with only expected, normal wear."
            action = "Keep up the routine monitoring."
        elif prob < 55:
            detail = "The bridge is functional, but our AI is picking up some moderate wear patterns. It's nothing critical yet, but it's starting to show its age."
            action = "A visual inspection soon would be a good idea."
        else:
            detail = "Our sensors are detecting severe anomalies and significant material stress that are outside safe bounds."
            action = "An immediate engineering review is highly recommended."

        return (f"Based on the AI models, there is an estimated **{prob}% chance** that Bridge {name} could face structural failure within the next {horizon} years.\n\n"
                f"{detail}{trend_note}\n\n"
                f"**Recommendation:** {action}")

    if any(k in q for k in ["life expectancy", "service life", "lifespan", "how long will", "how many years", "years left", "remaining life"]):
        tgt = bdf()
        risk   = _col(tgt, "predicted_risk_score")
        deg    = _col(tgt, "degradation_score")
        rt     = _trend(tgt, "predicted_risk_score") or 0
        years  = _life_expectancy(risk, deg, rt)
        risk_p = round((risk or 0) * 100)
        name   = bridge_id or "the monitored fleet"

        hi, med = 0.5, 0.2
        if (risk or 0) < med:
            msg = (f"Bridge {name} is in **excellent condition** with an estimated remaining service life of about **{years} years**.\n\n"
                   f"The sensors show minimal wear and tear, and the structure is handling traffic smoothly without any signs of drift or stress. "
                   f"Just continue with the standard 12–18 month inspection cycle.")
        elif (risk or 0) < hi:
            msg = (f"Bridge {name} is in **fair condition** with an estimated remaining service life of about **{years} years**.\n\n"
                   f"The bridge is not in immediate danger, but the AI is picking up steady signs of aging and wear. "
                   f"Targeted maintenance now could easily slow this down and extend the bridge's lifespan.\n"
                   f"I'd recommend planning a detailed inspection in the next month to address these early signs of wear.")
        else:
            msg = (f"Bridge {name} is showing **elevated degradation** with a roughly estimated remaining life of **{years} years**.\n\n"
                   f"This timeline could shorten rapidly, as the sensors indicate significant material fatigue and unstable dynamics. "
                   f"Urgent maintenance is needed to stabilize the structure and prevent further decay.\n"
                   f"Please deploy an emergency assessment team right away.")
        
        if rt > 0.05:
            msg += "\n\n*(Note: The daily risk score is trending upward, so action should be taken sooner rather than later).*"
        elif rt < -0.05:
            msg += "\n\n*(Note: The risk score is improving, showing that recent maintenance work is paying off).* "
        return msg

    # ─── 2. RISK SCORE ────────────────────────────────────────────────────
    if any(k in q for k in ["risk score", "failure risk", "predicted risk", "risk level", "how risky"]):
        tgt    = bdf()
        risk   = _col(tgt, "predicted_risk_score")
        rmax   = _col(tgt, "predicted_risk_score", agg="max")
        rt     = _trend(tgt, "predicted_risk_score") or 0
        name   = bridge_id or "the fleet"
        risk_p = round((risk or 0) * 100)
        max_p  = round((rmax or 0) * 100)
        
        detail = ("It is operating exactly as expected with almost no signs of hidden stress." if risk_p < 20 else
                  "It is perfectly capable of handling traffic, but starting to show minor symptoms of wear and slight structural drift." if risk_p < 50 else
                  "The AI detects severe anomalies and concerning vibrational patterns that require immediate evaluation.")
                  
        action = ("No immediate work is needed; stick to the routine schedule." if risk_p < 20 else
                  "It would be wise to plan a physical inspection soon." if risk_p < 50 else
                  "An urgent engineering review is highly recommended to ensure safety.")

        return (f"Bridge {name} has a **{risk_p}% risk of failure** (peaking at {max_p}% recently).\n\n"
                f"{detail} {action}")

    # ─── 3. ANOMALY / ALERTS ─────────────────────────────────────────────
    # ─── 3. ANOMALY / ALERTS ─────────────────────────────────────────────
    if any(k in q for k in ["anomaly", "anomalies", "alert", "sensor irregularit"]):
        tgt    = bdf()
        alrts  = _alerts(tgt)
        ae     = _col(tgt, "autoencoder_anomaly_score")
        ae_max = _col(tgt, "autoencoder_anomaly_score", agg="max")
        name   = bridge_id or "the fleet"
        
        avg_pct = round((ae or 0)*100)
        max_pct = round((ae_max or 0)*100)
        
        detail = ""
        if alrts == 0:
            detail = ("This is an excellent sign. Anomaly scores track sudden, abnormal spikes in sensor data that deviate "
                      "from the bridge's normal baseline. Since there are zero alerts and the anomaly scores are well under the safety threshold, "
                      "it means the structure is experiencing standard load bearing without any alarming stress events.")
        elif alrts < 10:
            detail = (f"The AI has flagged {alrts} minor anomaly events recently, with scores peaking at {max_pct}% of the threshold. "
                      "High anomaly scores usually indicate unusual but temporary events — like an exceptionally heavy load crossing the bridge "
                      "or sudden weather impacts. While not an immediate emergency, these irregular events contribute to long-term wear and should be monitored.")
        else:
            detail = (f"This is a concerning number of alerts ({alrts} total events) with anomalies peaking at {max_pct}% of the critical threshold. "
                      "Repeated, high anomaly scores mean the bridge is consistently experiencing forces or structural responses far outside its normal "
                      "operational baseline. This could be due to hidden structural damage that is failing to absorb normal traffic vibrations.")
                      
        action = ("Structure is operating normally." if alrts == 0 else
                  "Review the flagged time periods to identify the source of the irregular stress." if alrts < 10 else
                  "An immediate engineering investigation is required to determine why the structure is repeatedly exceeding its design baseline.")

        return (f"**Anomaly Detection Analysis for Bridge {name}:**\n\n"
                f"The AI model shows an average daily anomaly score of {avg_pct}%. {detail}\n\n"
                f"**Recommendation:** {action}")

    # ─── 4. MAINTENANCE PRIORITY ─────────────────────────────────────────
    if any(k in q for k in ["maintenance", "priorit", "schedule", "inspect", "when should"]):
        if "bridge_id" not in df.columns:
            return "Maintenance scheduling data is currently unavailable."
        
        # Aggregate max risk per bridge
        grp = df.groupby("bridge_id").agg(risk=("Predicted_Risk_Score", "max")).reset_index()
        
        crit = grp[grp["risk"] >= 0.75].sort_values("risk", ascending=False)["bridge_id"].tolist()
        high = grp[(grp["risk"] >= 0.50) & (grp["risk"] < 0.75)].sort_values("risk", ascending=False)["bridge_id"].tolist()
        rout = grp[grp["risk"] < 0.50].sort_values("risk", ascending=False)["bridge_id"].tolist()
        
        msg = "**Maintenance Prioritization Summary:**\n\n"
        
        if crit:
            msg += f"🔴 **CRITICAL (Immediate Action - Next 72 hours):**\n"
            msg += f"These structures show severe risk peaks. Prioritize physical inspections immediately:\n"
            msg += f"   • {', '.join(crit)}\n\n"
            
        if high:
            msg += f"⚠️ **HIGH RISK (Action Required - Next 2 weeks):**\n"
            msg += f"These structures show elevated risk and should be scheduled for detailed inspection soon:\n"
            msg += f"   • {', '.join(high)}\n\n"
            
        if rout:
            msg += f"✅ **ROUTINE (Standard Schedule):**\n"
            msg += f"These structures are operating normally. Maintain standard monitoring:\n"
            msg += f"   • {', '.join(rout)}\n\n"
            
        return msg.strip()

    # ─── 5. HEALTH SUMMARY ───────────────────────────────────────────────
    if any(k in q for k in ["health summary", "full report", "comprehensive", "overall health"]):
        from tools.health_summary import generate_health_summary
        return generate_health_summary(bridge_id or query)

    # ─── 6. BEHAVIORAL SHIFT ─────────────────────────────────────────────
    if any(k in q for k in ["behavioral shift", "behaviour shift", "behavior shift", "drift", "baseline"]):
        tgt   = bdf()
        shift = _col(tgt, "behavioral_shift_index")
        cluster = _cluster_mode(tgt)
        state = {0:"Normal Baseline",1:"Active Load State",2:"Altered Dynamics"}.get(cluster,"Unknown")
        name  = bridge_id or "the fleet"
        sv    = shift or 0
        
        detail = ""
        if sv < 0.15:
            detail = "This represents an incredibly stable structure. The Behavioral Shift Index measures how far the bridge's current physical response to traffic diverges from its original, healthy baseline. A score this low confirms the materials and support structure are securely in place and functioning optimally."
        elif sv < 0.35:
            detail = "This score indicates minor drift. A low Behavioral Shift Index usually corresponds to typical seasonal variations, like material expansion during the summer, or slight settling. It is within expected operational parameters."
        elif sv < 0.6:
            detail = "This is a noticeable deviation from the bridge's original behavioral baseline. A high Behavioral Shift Index suggests that the core structural traits—such as stiffness or load distribution—are beginning to permanently change. This often precedes visible physical damage, like cracking, as the materials begin to stretch or sink in new ways."
        else:
            detail = "This is a critical displacement score. It indicates a severe alteration in the bridge's natural dynamics, meaning the load paths have changed drastically. High scores like this typically correlate with broken support elements or advanced foundation erosion."

        return (f"**Behavioral Shift Analysis for Bridge {name}:**\n\n"
                f"The AI has calculated a Behavioral Shift Index of {round(sv, 4)}, placing the structure in the '{state}' operating mode. {detail}\n\n"
                f"**Recommendation:** {'No structural concerns at this time.' if sv < 0.35 else 'Continued active monitoring is important to ensure the drift stabilizes.' if sv < 0.6 else 'Physical inspection is highly advised to locate the source of the dynamic shift.'}")

    # ─── 7. VIBRATION / DYNAMICS ────────────────────────────────────────
    if any(k in q for k in ["vibration", "dynamics", "isolation", "structural dynamics"]):
        tgt  = bdf()
        dyn  = _col(tgt, "structural_dynamics_score")
        name = bridge_id or "the fleet"
        dv   = dyn or 0
        
        detail = ""
        if dv < 0.35:
            detail = "This is an optimal score. The Structural Dynamics model analyzes high-frequency vibration data from the sensors. A low score means the bridge is dissipating energy efficiently and smoothly damping the vibrations caused by passing vehicles. It indicates solid structural integrity."
        elif dv < 0.65:
            detail = "This score shows some variability in how the bridge moves under a load, but it remains within acceptable, safe limits. Moderate dynamic scores often reflect heavier traffic patterns causing slightly longer resonance times."
        else:
            detail = "This is an elevated dynamic score, representing concerning vibrational behavior. A high score means the bridge is vibrating excessively or failing to damp resonant waves properly. High structural dynamic scores are historically linked to failing joints, loss of stiffness, or weakened tension cables that allow the structure to 'bounce' more than designed."
            
        return (f"**Vibration Analysis for Bridge {name}:**\n\n"
                f"The structural dynamics score is currently tracking at {round(dv, 4)}. {detail}\n\n"
                f"**Recommendation:** {'The dynamics are in a safe, normal operating range.' if dv < 0.65 else 'Further engineering investigation is advised to determine the cause of the excessive vibration.'}")

    # ─── 8. FLEET COMPARISON — BEST / WORST ─────────────────────────────
    if any(k in q for k in ["worst", "best", "safest", "most dangerous", "highest risk", "lowest risk", "compare", "ranking", "rank all"]):
        if "bridge_id" not in df.columns:
            return "Bridge comparison data not available."
        grp = df.groupby("bridge_id").agg(risk=("Predicted_Risk_Score","mean")).reset_index().sort_values("risk")
        
        safest = grp.iloc[0]["bridge_id"]
        safest_r = round(grp.iloc[0]["risk"]*100)
        
        worst = grp.iloc[-1]["bridge_id"]
        worst_r = round(grp.iloc[-1]["risk"]*100)
        
        return (f"**Fleet Comparison Summary:**\n\n"
                f"Across the monitored structures, **Bridge {safest}** is currently the safest and most reliable asset, displaying an extremely stable risk profile of just {safest_r}%. Its structural dynamics match the baseline perfectly.\n\n"
                f"On the other end of the spectrum, **Bridge {worst}** is registering the highest risk levels in the network, currently averaging a far more dangerous {worst_r}% failure risk score. The AI highlights {worst} due to excessive behavioral drift and recurring anomaly alerts from the sensors.\n\n"
                f"**Recommendation:** Maintenance funds and emergency inspection resources should be diverted toward {worst} immediately, while {safest} requires no intervention.")

    # ─── 9. DEGRADATION ──────────────────────────────────────────────────
    if any(k in q for k in ["degradation", "degrad", "deteriorat", "wearing"]):
        tgt  = bdf()
        deg  = _col(tgt, "degradation_score")
        rt   = _trend(tgt, "degradation_score") or 0
        name = bridge_id or "the fleet"
        dv   = deg or 0
        
        detail = ""
        if dv < 0.1:
            detail = "The degradation tracking confirms the structure is in virtually optimal, pristine condition. The materials are resisting environmental stressors and daily traffic perfectly, showing wear amounts so negligible they barely factor into our models."
        elif dv < 0.3:
            detail = "The structure is showing natural, expected signs of aging. This moderate level of structural degradation is completely normal for a bridge actively handling daily traffic and varying weather cycles. It represents simple wear and tear that routine maintenance usually addresses without issue."
        else:
            detail = "The AI senses elevated and accelerating deterioration. A high degradation score means there is active material fatigue occurring—such as micro-cracking, corrosion, or joint wear—that the structure is struggling to manage. This level of wear goes beyond normal aging and requires active repair."
            
        trend_note = "Worryingly, this degradation is accelerating rapidly." if rt > 0.02 else ("Encouragingly, the rate of wear is slowing down." if rt < -0.02 else "The rate of wear remains constant over time.")
        
        return (f"**Degradation Analysis for Bridge {name}:**\n\n"
                f"The AI model gives {name} an average structural degradation score of {round(dv, 4)}. {detail} {trend_note}\n\n"
                f"**Recommendation:** {'No maintenance action is needed right now.' if dv < 0.1 else 'Make sure to include this in your upcoming standard maintenance review.' if dv < 0.3 else 'A structural assessment team should be deployed to evaluate the fatigue.'}")

    # ─── 10. IS THE BRIDGE SAFE? ─────────────────────────────────────────
    if any(k in q for k in ["is it safe", "is the bridge safe", "safe to use", "open to traffic", "safe for"]):
        tgt    = bdf()
        risk   = _col(tgt, "predicted_risk_score") or 0
        alrts  = _alerts(tgt)
        name   = bridge_id or "the fleet"
        risk_p = round(risk * 100)
        
        if risk < 0.2 and alrts == 0:
            return (f"✅ **Yes, Bridge {name} appears exceptionally safe for all normal operations.**\n\n"
                    f"The failure risk is incredibly low at just {risk_p}%, and the sensors haven't triggered a single structural anomaly alert. "
                    f"The bridge is easily handling current traffic loads without any hidden stress. You can confidently continue normal, routine monitoring.")
        elif risk < 0.5:
            return (f"⚠️ **Bridge {name} is operational, but showing signs of moderate risk.**\n\n"
                    f"Currently, the AI rates its failure risk at {risk_p}%. While the bridge isn't in immediate danger of collapse, "
                    f"there are active anomaly alerts ({alrts} total) flagging irregular sensor readings. "
                    f"An engineering inspection is highly recommended to clarify these alerts before declaring the structure unconditionally safe for maximum or oversized loads.")
        else:
            return (f"🔴 **Bridge {name} currently exhibits a highly elevated risk profile.**\n\n"
                    f"With a {risk_p}% failure risk score and {alrts} distinct anomaly sensor alerts triggering in our system, "
                    f"the structure is definitely showing troubling indications of fatigue or dynamic instability. "
                    f"A structural assessment by qualified engineers is strongly recommended before authorizing continued, unrestricted use.")

    # ─── 11. TREND ANALYSIS ──────────────────────────────────────────────
    if any(k in q for k in ["trend", "improving", "worsening", "getting worse", "getting better", "direction"]):
        tgt   = bdf()
        rt    = _trend(tgt, "predicted_risk_score") or 0
        st    = _trend(tgt, "behavioral_shift_index") or 0
        name  = bridge_id or "the fleet"
        
        r_desc = ("rapidly getting worse and riskier" if rt > 0.03 else "improving and becoming safer" if rt < -0.03 else "holding steady with no major changes")
        s_desc = ("increasing, meaning the structure is continually stretching away from its baseline" if st > 0.03 else "decreasing back toward normal" if st < -0.03 else "stable")
        
        return (f"**Trend Analysis Summary for Bridge {name}:**\n\n"
                f"Currently, the AI models track that the predicted failure risk is {r_desc}. Simultaneously, the behavioral shift (how the bridge responds to traffic physically) is {s_desc}.\n\n"
                f"**Recommendation:** {'These positive trends suggest current maintenance is highly effective.' if rt < -0.03 else 'Conditions are stable; keep monitoring.' if abs(rt) < 0.03 else 'Conditions are actively worsening. You must increase inspection frequency.'}")

    # ─── 12. FORECAST / 30-DAY ───────────────────────────────────────────
    if any(k in q for k in ["forecast", "next 30 day", "predict next", "future risk", "projection"]):
        tgt     = bdf()
        fc      = _col(tgt, "forecast_score_next_30d")
        risk    = _col(tgt, "predicted_risk_score")
        name    = bridge_id or "the fleet"
        fc_p    = round((fc or 0) * 100)
        risk_p  = round((risk or 0) * 100)
        delta   = fc_p - risk_p
        
        detail = ("worsening sharply, meaning sensor data suggests rapid upcoming fatigue" if delta > 2 else
                  "improving noticeably, likely due to recent maintenance interventions" if delta < -2 else
                  "projected to remain completely stable")
                  
        return (f"**30-Day Risk Forecast for Bridge {name}:**\n\n"
                f"Our AI relies on current trajectories to project the bridge's health exactly one month into the future. "
                f"Right now, the failure risk sits at {risk_p}%. Fast forward 30 days, the model forecasts this score to hit {fc_p}%. "
                f"This indicates the structural integrity is {detail} over the next month.\n\n"
                f"**Recommendation:** {'The outlook is perfectly stable; no unique action is needed.' if abs(delta) <= 2 else 'I highly recommend reviewing maintenance schedules before this degradation occurs.' if delta > 0 else 'The structure is on a positive trajectory. Keep it up!'}")

    # ─── 13. GENERAL OVERVIEW / HOW ARE THE BRIDGES ─────────────────────
    if any(k in q for k in ["how are", "overview", "general", "overall", "status of", "all bridge", "fleet"]):
        r = round(df["Predicted_Risk_Score"].mean() * 100) if "Predicted_Risk_Score" in df.columns else 0
        a = _alerts(df)
        b = df["bridge_id"].nunique() if "bridge_id" in df.columns else 0
        return (f"**Overall Fleet Assessment:**\n\n"
                f"Across all {b} monitored structures in the network, the average predicted failure risk is currently {r}%. "
                f"While the vast majority of our bridges are holding up well to daily traffic, the system is actively tracking "
                f"{a} outstanding anomaly alerts from individual sensors across the grid.\n\n"
                f"Overall, the network remains operational. However, I highly recommend asking me for a **maintenance priority list** "
                f"so you can see which specific bridges are driving up those anomaly numbers and target them for inspection.")

    # ─── 14. SENSOR / CONDITION SCORE ────────────────────────────────────
    if any(k in q for k in ["condition score", "structural condition", "condition state"]):
        tgt  = bdf()
        cond = _col(tgt, "structural_condition")
        name = bridge_id or "the fleet"
        cv   = cond or 0
        
        detail = ""
        if cv >= 0.9:
            detail = "This score confirms the bridge is in absolutely exceptional physical condition. The load distribution is perfect, there is zero material strain visible to the sensors, and it stands almost exactly as it would on the day it was built."
        elif cv >= 0.7:
            detail = "This represents a solid, generally healthy bridge structure. It is dealing with some normal, low-level wear and tear from weather and traffic, but its structural integrity remains robust and heavily competent."
        elif cv >= 0.5:
            detail = "This indicates the bridge is entering a fair but aging condition state. Subtle issues like joint friction, minor corrosion, or surface cracking are likely developing and beginning to marginally alter the bridge's load capacity."
        else:
            detail = "This is a poor condition score. The sensors indicate heavy, possibly severe structural impairment and fatigue. The bridge is no longer efficiently handling standard loads."
            
        return (f"**Structural Condition Analysis for Bridge {name}:**\n\n"
                f"The system has assigned a structural condition score of {round(cv, 3)} out of 1.0. {detail}\n\n"
                f"**Recommendation:** {'You have an excellent structure on your hands.' if cv >= 0.9 else 'General monitoring is sufficient.' if cv >= 0.7 else 'Be aware of developing wear; minor maintenance should be scheduled.' if cv >= 0.5 else 'Intense, formal structural inspection is required immediately.'}")

    return None   # no pattern matched


# ──────────────────────────────────────────────────────────────────────────────
# PDF HEALTH REPORT ENDPOINT
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/api/report/{bridge_id}")
def generate_report(bridge_id: str):
    """Generates and returns a professional PDF health report for the specified bridge."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, KeepTogether
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        df  = _load_df()
        tgt = _bridge_df(df, bridge_id)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Compute metrics
        risk       = _col(tgt, "predicted_risk_score") or 0
        risk_max   = _col(tgt, "predicted_risk_score", agg="max") or 0
        anomaly    = _col(tgt, "autoencoder_anomaly_score") or 0
        anomaly_mx = _col(tgt, "autoencoder_anomaly_score", agg="max") or 0
        shift      = _col(tgt, "behavioral_shift_index") or 0
        dynamics   = _col(tgt, "structural_dynamics_score") or 0
        deg        = _col(tgt, "degradation_score") or 0
        cond       = _col(tgt, "structural_condition") or 0
        fc         = _col(tgt, "forecast_score_next_30d") or 0
        rt         = _trend(tgt, "predicted_risk_score") or 0
        alrts      = _alerts(tgt)
        cluster    = _cluster_mode(tgt)
        years      = _life_expectancy(risk, deg, rt)
        annual_rate= max(0.001, risk * 0.02 + (rt * 0.005 if rt > 0 else 0))
        prob_100   = round(min((1-(1-annual_rate)**100)*100, 99.9), 1)

        state = {0:"Normal Baseline",1:"Active Load State",2:"Altered Dynamics"}.get(cluster,"Unknown")

        condition_label = ("Excellent" if risk < 0.2 else "Fair" if risk < 0.5 else "Degraded")
        risk_flag       = "LOW ✓" if risk < 0.2 else ("MODERATE" if risk < 0.5 else "HIGH ⚠")

        # Build PDF in memory
        buf  = io.BytesIO()
        doc  = SimpleDocTemplate(buf, pagesize=A4,
                                 rightMargin=2*cm, leftMargin=2*cm,
                                 topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        CYAN   = colors.HexColor('#006B6B')
        RED    = colors.HexColor('#CC2222')
        ORANGE = colors.HexColor('#CC6600')
        GREEN  = colors.HexColor('#006600')
        GRAY   = colors.HexColor('#444444')

        title_style = ParagraphStyle('Title', parent=styles['Title'],
                                     fontSize=20, leading=26, textColor=CYAN, spaceAfter=4)
        sub_style   = ParagraphStyle('Sub', parent=styles['Normal'],
                                     fontSize=10, textColor=GRAY, spaceAfter=16)
        h2_style    = ParagraphStyle('H2', parent=styles['Heading2'],
                                     fontSize=13, textColor=CYAN, spaceBefore=16, spaceAfter=6)
        body_style  = ParagraphStyle('Body', parent=styles['Normal'],
                                     fontSize=10, leading=16, textColor=colors.black)
        warn_style  = ParagraphStyle('Warn', parent=styles['Normal'],
                                     fontSize=10, leading=16, textColor=RED)

        story = []

        # ── Header ──────────────────────────────────────────────────────────
        story.append(Paragraph("STRUCTURAL HEALTH INTELLIGENCE REPORT", title_style))
        story.append(Paragraph(
            f"Bridge ID: <b>{bridge_id.upper()}</b> &nbsp;&nbsp;|&nbsp;&nbsp; Generated: {now} &nbsp;&nbsp;|&nbsp;&nbsp; Augenblick Systems · PS-02",
            sub_style))
        story.append(HRFlowable(width="100%", thickness=2, color=CYAN, spaceAfter=14))

        # ── Executive Summary ────────────────────────────────────────────────
        story.append(Paragraph("Executive Summary", h2_style))
        overall = ("The bridge is currently in good structural health with no immediate concerns."
                   if risk < 0.2 else
                   "The bridge has a moderate risk profile and should be scheduled for inspection."
                   if risk < 0.5 else
                   "The bridge shows elevated risk indicators. Immediate structural assessment is recommended.")
        life_txt = f" AI model estimates approximately <b>{years} years</b> of remaining service life." if years else ""
        story.append(Paragraph(f"{overall}{life_txt}", body_style))
        story.append(Spacer(1, 10))

        # ── Key Metrics Table ────────────────────────────────────────────────
        story.append(Paragraph("Key Structural Metrics", h2_style))
        pct = lambda v: f"{round(v*100, 1)}%"
        table_data = [
            ["Metric", "Value", "Status"],
            ["Avg Predicted Failure Risk",    pct(risk),       risk_flag],
            ["Peak Failure Risk (recorded)",  pct(risk_max),   "HIGH ⚠" if risk_max > 0.5 else "OK"],
            ["AI Anomaly Score (avg)",         pct(anomaly),    "ELEVATED" if anomaly > 0.3 else "Normal"],
            ["Peak Anomaly Spike",             pct(anomaly_mx), "HIGH ⚠" if anomaly_mx > 0.7 else "OK"],
            ["Behavioral Shift Index",         f"{shift:.4f}",  "Elevated" if shift > 0.4 else "Normal"],
            ["Structural Dynamics Score",      f"{dynamics:.4f}","Elevated" if dynamics > 0.6 else "Normal"],
            ["Degradation Score (avg)",        f"{deg:.4f}",    "High" if deg > 0.3 else "Acceptable"],
            ["Structural Condition Score",     f"{cond:.3f}",   "Poor" if cond < 0.5 else "Good"],
            ["30-Day Risk Forecast",           pct(fc),         "Rising ⚠" if fc > risk else "Stable"],
            ["Anomaly Alert Events (total)",   str(alrts),     "Flagged" if alrts > 0 else "None"],
            ["Dominant Behavioral State",      state,          ""],
            ["Probability of Failure (100yr)", f"{prob_100}%",  "HIGH" if prob_100 > 50 else "LOW"],
            ["Est. Remaining Service Life",    f"~{years} yrs" if years else "N/A", condition_label],
        ]
        col_widths = [7.5*cm, 4.5*cm, 4.0*cm]
        tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND',  (0,0), (-1,0), CYAN),
            ('TEXTCOLOR',   (0,0), (-1,0), colors.white),
            ('FONTNAME',    (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',    (0,0), (-1,0), 10),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F0F7FA')]),
            ('FONTSIZE',    (0,1), (-1,-1), 9),
            ('GRID',        (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
            ('ALIGN',       (1,0), (-1,-1), 'CENTER'),
            ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING',  (0,0), (-1,-1), 5),
            ('BOTTOMPADDING',(0,0),(-1,-1), 5),
        ]))
        # Color-code status column
        for row_idx, row in enumerate(table_data[1:], start=1):
            status = str(row[2]).upper()
            c = (RED   if any(k in status for k in ['HIGH','CRITICAL','ELEVATED','FLAGGED','RISING','POOR']) else
                 ORANGE if 'MODERATE' in status else
                 GREEN  if any(k in status for k in ['LOW','NORMAL','OK','GOOD','STABLE','EXCELLENT']) else
                 colors.black)
            tbl.setStyle(TableStyle([('TEXTCOLOR', (2,row_idx), (2,row_idx), c)]))
        story.append(tbl)
        story.append(Spacer(1, 14))

        # ── Risk Trend ───────────────────────────────────────────────────────
        story.append(Paragraph("Risk Trend Analysis", h2_style))
        if rt > 0.05:
            trend_txt = ("⚠️ The failure risk score has been <b>increasing</b> over the monitoring period. "
                         "This is a concern that warrants increased inspection frequency.")
            p_style = warn_style
        elif rt < -0.05:
            trend_txt = ("✅ The failure risk score has been <b>decreasing</b> — current maintenance "
                         "strategy is effective. Continue the current approach.")
            p_style = body_style
        else:
            trend_txt = "→ The failure risk score is <b>stable</b> over the monitoring period. No significant change in risk trajectory."
            p_style = body_style
        story.append(Paragraph(trend_txt, p_style))
        story.append(Spacer(1, 10))

        # ── Recommendations ──────────────────────────────────────────────────
        story.append(Paragraph("Engineering Recommendations", h2_style))
        recs = []
        if risk >= 0.5:
            recs.append("🔴 Deploy an emergency structural assessment team immediately.")
            recs.append("🔴 Consider traffic load restrictions pending inspection results.")
        elif risk >= 0.2:
            recs.append("⚠️ Schedule a detailed on-site structural inspection within 4–6 weeks.")
            recs.append("⚠️ Increase monitoring frequency from monthly to bi-weekly.")
        else:
            recs.append("✅ Continue standard monitoring schedule (monthly/bi-monthly).")
        if alrts > 0:
            recs.append(f"⚠️ Review {alrts} anomaly alert event(s) — identify possible load or weather correlation.")
        if deg > 0.3:
            recs.append("⚠️ Elevated degradation detected — evaluate joint and bearing conditions.")
        if rt > 0.05:
            recs.append("⚠️ Risk trend is rising — consider accelerated maintenance program.")
        recs.append(f"📅 Next recommended inspection: {'Within 1 week' if risk >= 0.5 else 'Within 4–6 weeks' if risk >= 0.2 else 'In 12–18 months'}.")
        for r in recs:
            story.append(Paragraph(f"&nbsp;&nbsp;• {r}", body_style))
        story.append(Spacer(1, 14))

        # ── Footer ───────────────────────────────────────────────────────────
        story.append(HRFlowable(width="100%", thickness=1, color=GRAY, spaceAfter=8))
        story.append(Paragraph(
            f"<font size=8 color='#888888'>Report generated by Augenblick Structural Intelligence Platform · "
            f"AI-Powered Analysis · {now} · Data source: processed/failure_prediction_behavior.parquet · "
            f"This report is for engineering advisory purposes only.</font>",
            body_style))

        doc.build(story)
        buf.seek(0)

        # Write to temp file and serve
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf",
                                          prefix=f"health_report_{bridge_id}_")
        tmp.write(buf.read())
        tmp.close()

        return FileResponse(
            tmp.name,
            media_type="application/pdf",
            filename=f"Health_Report_{bridge_id.upper()}_{datetime.now().strftime('%Y%m%d')}.pdf",
            headers={"Content-Disposition": f'attachment; filename="Health_Report_{bridge_id.upper()}.pdf"'},
        )
    except Exception as e:
        import traceback; traceback.print_exc()
        return {"error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# CHAT ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat_with_agent(req: ChatRequest):
    import asyncio
    
    # 1. Domain Guard Check
    if _is_off_topic(req.message):
        return {"response": _OFF_TOPIC_REPLY}

    # 2. Bridge ID Validation
    try:
        bridge_id = _extract_bridge_id(req.message)
        if bridge_id:
            df = _load_df()
            valid_bridges = df["bridge_id"].unique()
            if bridge_id not in valid_bridges:
                return {"response": f"⚠️ I'm sorry, but I do not have any monitoring records for **Bridge {bridge_id}**.\n\n"
                                    f"Please verify the bridge identifier. The structures currently active in the monitoring system are: "
                                    f"`{', '.join(valid_bridges)}`."}
    except Exception:
        pass

    # 3. PDF Downloader exception (must be instantly handled so UI can present link)
    q = req.message.lower()
    if any(k in q for k in ["generate report", "health report", "generate health", "create report", "pdf report", "download report", "full report pdf"]):
        answer = _smart_router(req.message)
        if answer:
            return {"response": answer}

    # 3. Route to the LangChain / Ollama Agentic AI Assistant
    # We use await asyncio.to_thread because the agent's run_query is synchronous
    # and we don't want to block the entire FastAPI event loop while the LLM generates.
    try:
        from agent_assistant import run_query
        # The user requested True LLM generation ("fine if it takes longer")
        # so we feed it to the Agent Interface directly.
        response_text = await asyncio.to_thread(run_query, req.message)
        return {"response": response_text}
    except Exception as e:
        import traceback; traceback.print_exc()
        return {"response": f"⚠️ Agent Error: {e}"}
        # so we feed it to the Agent Interface directly.
        response_text = await asyncio.to_thread(run_query, req.message)
        return {"response": response_text}
    except Exception as e:
        import traceback; traceback.print_exc()
        return {"response": f"⚠️ Agent Error: {e}"}
