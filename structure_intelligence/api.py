"""
api.py — AI Structural Monitoring Platform API
Serves real parquet data: sensor fusion, behaviour analysis, anomaly detection, risk prediction
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pandas as pd
import numpy as np
import os, math, io, tempfile
from datetime import datetime

app = FastAPI(title="AI Structural Monitoring API")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

BASE = os.path.join(os.path.dirname(__file__), "processed")

# ── Data loaders ──────────────────────────────────────────────────────────────
def clean(df: pd.DataFrame) -> pd.DataFrame:
    return df.replace([math.inf, -math.inf], None).where(pd.notnull(df), None)

def load_behaviour() -> pd.DataFrame:
    return pd.read_parquet(os.path.join(BASE, "behaviour_behavior.parquet"))

def load_risk() -> pd.DataFrame:
    return pd.read_parquet(os.path.join(BASE, "failure_prediction_behavior.parquet"))

def load_sensor() -> pd.DataFrame:
    return pd.read_parquet(os.path.join(BASE, "sensor_fusion.parquet"))

def load_digital_twin() -> pd.DataFrame:
    return pd.read_parquet(os.path.join(BASE, "digital_twin.parquet"))

def slim(df: pd.DataFrame, n: int = 200) -> pd.DataFrame:
    """Downsample to at most n rows for the API response."""
    if len(df) <= n:
        return df
    step = max(1, len(df) // n)
    return df.iloc[::step].head(n)

# ── Single-bridge constants ────────────────────────────────────────────────────
# Behaviour / anomaly parquet uses 'test_id'; we fix to 'test1'.
# Risk / failure parquet uses 'bridge_id'; we fix to 'B001'.
BEHAVIOUR_ID = "test1"
RISK_BRIDGE  = "B001"
BRIDGE_DISPLAY_NAME = "Bridge B001"

# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/api/bridges")
def get_bridges():
    """Return single bridge entry."""
    return {"bridges": [{"id": BEHAVIOUR_ID, "name": BRIDGE_DISPLAY_NAME}]}


@app.get("/api/sensor/{test_id}")
def get_sensor(test_id: str):
    """Multi-sensor data: rms, peak, frequency per channel."""
    try:
        df = load_behaviour()
        bdf = df[df["test_id"] == test_id] if test_id != "all" else df
        cols = ["time_start_s"] + [c for c in bdf.columns if "_g_rms" in c or "_g_dom_freq_hz" in c or "_g_kurtosis" in c]
        cols = [c for c in cols if c in bdf.columns]
        out = slim(bdf[cols].reset_index(drop=True))
        return {"data": clean(out).to_dict(orient="records")}
    except Exception as e:
        return {"data": [], "error": str(e)}


@app.get("/api/behaviour/{test_id}")
def get_behaviour(test_id: str):
    """Structural behaviour: shift index, dynamics score, cluster, anomaly, risk."""
    try:
        df = load_behaviour()
        bdf = df[df["test_id"] == test_id] if test_id != "all" else df
        cols = ["time_start_s", "Behavioral_Shift_Index", "Structural_Dynamics_Score",
                "Behavioral_State_Cluster", "Autoencoder_Anomaly_Score",
                "Anomaly_Alert_Flag", "Predicted_Risk_Score"]
        available = [c for c in cols if c in bdf.columns]
        out = slim(bdf[available].reset_index(drop=True))
        
        # Summary stats
        bsi = float(bdf["Behavioral_Shift_Index"].mean()) if "Behavioral_Shift_Index" in bdf else 0
        sds = float(bdf["Structural_Dynamics_Score"].mean()) if "Structural_Dynamics_Score" in bdf else 0
        cluster = int(bdf["Behavioral_State_Cluster"].mode()[0]) if "Behavioral_State_Cluster" in bdf else 0
        anomaly = float(bdf["Autoencoder_Anomaly_Score"].mean()) if "Autoencoder_Anomaly_Score" in bdf else 0
        risk = float(bdf["Predicted_Risk_Score"].mean()) if "Predicted_Risk_Score" in bdf else 0
        alerts = int(bdf["Anomaly_Alert_Flag"].sum()) if "Anomaly_Alert_Flag" in bdf else 0

        return {
            "data": clean(out).to_dict(orient="records"),
            "summary": {
                "behavioral_shift_index": round(bsi, 4),
                "structural_dynamics_score": round(sds, 4),
                "behavioral_state_cluster": cluster,
                "anomaly_score": round(anomaly, 4),
                "risk_score": round(risk, 4),
                "alert_count": alerts,
            }
        }
    except Exception as e:
        import traceback; traceback.print_exc()
        return {"data": [], "summary": {}, "error": str(e)}


@app.get("/api/anomaly/{test_id}")
def get_anomaly(test_id: str):
    """Anomaly detection: autoencoder scores from B001 failure prediction dataset."""
    try:
        df = load_risk()  # failure_prediction_behavior.parquet
        bdf = df[df["bridge_id"] == RISK_BRIDGE].copy()
        bdf = bdf.reset_index(drop=True)
        bdf["row_index"] = bdf.index  # use as time axis
        cols = ["row_index", "Autoencoder_Anomaly_Score", "Predicted_Risk_Score"]
        available = [c for c in cols if c in bdf.columns]
        out = slim(bdf[available].reset_index(drop=True))
        # Rename for chart compat
        out = out.rename(columns={"row_index": "time_start_s"})
        
        anomaly_mean = float(bdf["Autoencoder_Anomaly_Score"].mean()) if "Autoencoder_Anomaly_Score" in bdf else 0
        anomaly_max = float(bdf["Autoencoder_Anomaly_Score"].max()) if "Autoencoder_Anomaly_Score" in bdf else 0
        # Count readings above threshold as alerts
        alert_count = int((bdf["Autoencoder_Anomaly_Score"] > 0.5).sum()) if "Autoencoder_Anomaly_Score" in bdf else 0
        
        return {
            "data": clean(out).to_dict(orient="records"),
            "summary": {
                "anomaly_mean": round(anomaly_mean, 4),
                "anomaly_max": round(anomaly_max, 4),
                "alert_count": alert_count,
                "threshold": 0.5,
            }
        }
    except Exception as e:
        return {"data": [], "summary": {}, "error": str(e)}


@app.get("/api/risk/{test_id}")
def get_risk(test_id: str):
    """Failure risk prediction: risk score from B001 failure prediction dataset."""
    try:
        df = load_risk()  # failure_prediction_behavior.parquet
        bdf = df[df["bridge_id"] == RISK_BRIDGE].copy()
        bdf = bdf.reset_index(drop=True)
        bdf["row_index"] = bdf.index
        cols = ["row_index", "Predicted_Risk_Score", "Autoencoder_Anomaly_Score"]
        available = [c for c in cols if c in bdf.columns]
        out = slim(bdf[available].reset_index(drop=True))
        out = out.rename(columns={"row_index": "time_start_s"})
        
        # Also pull BSI from behaviour parquet for behaviour shift metric
        beh_df = load_behaviour()
        beh_b = beh_df[beh_df["test_id"] == BEHAVIOUR_ID]
        bsi = float(beh_b["Behavioral_Shift_Index"].mean()) if "Behavioral_Shift_Index" in beh_b.columns else 0

        risk_mean = float(bdf["Predicted_Risk_Score"].mean()) if "Predicted_Risk_Score" in bdf else 0
        risk_max = float(bdf["Predicted_Risk_Score"].max()) if "Predicted_Risk_Score" in bdf else 0
        
        if risk_mean < 0.2: level = "LOW"
        elif risk_mean < 0.4: level = "MODERATE"
        elif risk_mean < 0.6: level = "HIGH"
        else: level = "CRITICAL"
        
        # Add BSI column to chart data from behaviour parquet (aligned by index)
        # Just note it in summary for the frontend bars
        return {
            "data": clean(out).to_dict(orient="records"),
            "summary": {
                "risk_mean": round(risk_mean, 4),
                "risk_max": round(risk_max, 4),
                "risk_level": level,
                "risk_pct": round(risk_mean * 100, 1),
                "behavioral_shift": round(bsi, 4),
            }
        }
    except Exception as e:
        return {"data": [], "summary": {}, "error": str(e)}



@app.get("/api/digital-twin/summary")
def get_twin_summary():
    """Summary stats from digital twin parquet for the Digital Twin page."""
    try:
        df = load_digital_twin()
        recent = df.tail(500)
        cols_of_interest = [
            "Structural_Health_Index_SHI", "Deflection_mm", "Strain_microstrain",
            "Vibration_ms2", "Probability_of_Failure_PoF", "Temperature_C",
            "Wind_Speed_ms", "Vehicle_Load_tons", "Anomaly_Detection_Score",
            "Maintenance_Alert", "SHI_Predicted_24h_Ahead", "SHI_Predicted_30d_Ahead"
        ]
        available = [c for c in cols_of_interest if c in df.columns]
        out = slim(recent[available].reset_index(drop=True), 150)
        
        summary = {}
        for c in available:
            summary[c] = round(float(df[c].mean()), 4)
        
        return {"data": clean(out).to_dict(orient="records"), "summary": summary}
    except Exception as e:
        return {"data": [], "summary": {}, "error": str(e)}


@app.get("/api/health")  
def health():
    return {"status": "ok", "service": "AI Structural Monitoring API"}


# ── AI Conclusion Generator ───────────────────────────────────────────────────

def generate_behaviour_conclusion(bsi: float, sds: float, cluster: int, anomaly: float, risk: float, alerts: int) -> dict:
    cluster_labels = {0: "Normal Baseline", 1: "Active Load State", 2: "Altered Dynamics"}
    cluster_name = cluster_labels.get(cluster, "Unknown")

    status = "normal"
    lines = []

    if bsi > 0.5:
        lines.append(f"The structure is showing a HIGH behavioral shift index of {bsi:.3f}, indicating significant deviation from its baseline behavior pattern.")
        status = "critical"
    elif bsi > 0.35:
        lines.append(f"The behavioral shift index is ELEVATED at {bsi:.3f}, suggesting the structure is beginning to deviate from expected patterns.")
        status = "warning"
    else:
        lines.append(f"The structural behavioral shift index is NORMAL at {bsi:.3f}, confirming stable baseline operation.")

    if sds > 0.7:
        lines.append(f"Structural dynamics show CRITICAL vibration pattern changes (score: {sds:.3f}). Damping characteristics suggest possible material fatigue or joint loosening.")
        status = "critical"
    elif sds > 0.5:
        lines.append(f"The structural dynamics score of {sds:.3f} is moderately elevated. Vibration damping patterns are showing mild irregularities worth monitoring.")
        if status == "normal": status = "warning"
    else:
        lines.append(f"Vibration damping dynamics are healthy (score: {sds:.3f}), with no abnormal resonance patterns detected.")

    lines.append(f"The AI has classified this structure into behavioral state cluster: '{cluster_name}'.")

    if risk > 0.6:
        lines.append(f"AI-predicted failure risk is CRITICAL at {risk*100:.1f}%. Immediate structural inspection is strongly recommended.")
        status = "critical"
    elif risk > 0.4:
        lines.append(f"Predicted failure risk is HIGH at {risk*100:.1f}%. Increased monitoring frequency is advised.")
        if status == "normal": status = "warning"
    elif risk > 0.2:
        lines.append(f"Predicted failure risk is MODERATE at {risk*100:.1f}%. Continue routine monitoring protocols.")
    else:
        lines.append(f"Failure risk is LOW at {risk*100:.1f}%. Structure is operating within safe parameters.")

    if alerts > 0:
        lines.append(f"⚠ {alerts} anomaly alert event(s) were triggered during the monitoring window. Review anomaly logs for time-specific details.")

    conclusion = " ".join(lines)
    return {"conclusion": conclusion, "status": status}


def generate_anomaly_conclusion(anomaly_mean: float, anomaly_max: float, alert_count: int, threshold: float) -> dict:
    status = "normal"
    lines = []

    if anomaly_mean > 0.5:
        lines.append(f"The autoencoder reconstruction model has detected consistently HIGH anomaly patterns. The mean anomaly score of {anomaly_mean*100:.1f}% far exceeds the safety threshold of {threshold*100:.0f}%.")
        status = "critical"
    elif anomaly_mean > 0.3:
        lines.append(f"The AI autoencoder is reporting ELEVATED anomaly scores with a mean of {anomaly_mean*100:.1f}%. The structure's sensor patterns are deviating from their learned normal behavior.")
        status = "warning"
    else:
        lines.append(f"Anomaly detection is showing NORMAL results. The mean reconstruction error of {anomaly_mean*100:.1f}% is well below the {threshold*100:.0f}% threshold.")

    if anomaly_max > 0.7:
        lines.append(f"A PEAK anomaly spike of {anomaly_max*100:.1f}% was recorded — this indicates at least one time window where the structure exhibited severely abnormal sensor readings.")
        status = "critical"
    elif anomaly_max > threshold:
        lines.append(f"The peak anomaly score of {anomaly_max*100:.1f}% exceeded the detection threshold during at least one time window, triggering the alert system.")
        if status == "normal": status = "warning"
    else:
        lines.append(f"Peak anomaly readings of {anomaly_max*100:.1f}% remained within the safe threshold throughout the monitoring period.")

    if alert_count > 5:
        lines.append(f"A total of {alert_count} alert events were triggered — this frequency suggests recurring structural irregularities requiring immediate attention.")
        status = "critical"
    elif alert_count > 0:
        lines.append(f"{alert_count} alert event(s) were recorded. The autoencoder flagged specific time windows where sensor reconstruction error exceeded the AI anomaly threshold.")
        if status == "normal": status = "warning"
    else:
        lines.append("No anomaly alert events were triggered. The AI model confirms sustained normal structural behavior throughout the entire monitoring window.")

    conclusion = " ".join(lines)
    return {"conclusion": conclusion, "status": status}


def generate_risk_conclusion(risk_mean: float, risk_max: float, risk_level: str, bsi: float) -> dict:
    status = "normal"
    lines = []

    level_map = {"LOW": "normal", "MODERATE": "warning", "HIGH": "warning", "CRITICAL": "critical"}
    status = level_map.get(risk_level, "normal")

    if risk_level == "CRITICAL":
        lines.append(f"⚠ CRITICAL ALERT: The AI failure risk model has assessed an extremely high failure probability of {risk_mean*100:.1f}% for this structure. Immediate intervention is required.")
    elif risk_level == "HIGH":
        lines.append(f"The AI regression model predicts a HIGH failure risk of {risk_mean*100:.1f}%. The structure is under considerable stress and requires prompt inspection.")
    elif risk_level == "MODERATE":
        lines.append(f"The predicted failure risk is at a MODERATE level of {risk_mean*100:.1f}%. The structure merits increased monitoring but is not in immediate danger.")
    else:
        lines.append(f"The AI risk model reports a LOW failure probability of {risk_mean*100:.1f}%. The structure is performing well within all safety margins.")

    lines.append(f"The maximum instantaneous risk score reached {risk_max*100:.1f}% during the analysis window.")

    if bsi > 0.4:
        lines.append(f"The behavioral shift index of {bsi:.3f} is contributing significantly to the elevated risk score, indicating the structure is drifting away from learned safe operating patterns.")
    elif bsi > 0.25:
        lines.append(f"A moderate behavioral shift index of {bsi:.3f} was observed. This contributes to the current risk assessment and should be tracked over time.")
    else:
        lines.append(f"The behavioral shift index of {bsi:.3f} is within normal bounds, contributing minimal additional risk.")

    if risk_level in ("HIGH", "CRITICAL"):
        lines.append("Recommendation: Schedule a physical structural inspection and increase sensor polling frequency to continuous monitoring mode.")
    else:
        lines.append("Recommendation: Continue standard monitoring protocols. No immediate action required at this risk level.")

    conclusion = " ".join(lines)
    return {"conclusion": conclusion, "status": status}


def generate_digitaltwin_conclusion(traffic: int, temp: float, wind: float, stress: float, damaged: str, scenario: str = "Normal") -> dict:
    status = "normal"
    lines = []

    stress_label = "LOW" if stress < 30 else "MODERATE" if stress < 55 else "HIGH" if stress < 75 else "CRITICAL"
    level_map = {"LOW": "normal", "MODERATE": "warning", "HIGH": "warning", "CRITICAL": "critical"}
    status = level_map.get(stress_label, "normal")

    lines.append(f"The Digital Twin physics simulation is running under the '{scenario}' scenario with {traffic}% traffic load, {temp}°C ambient temperature, and {wind} km/h wind speed.")

    if stress_label == "CRITICAL":
        lines.append(f"⚠ CRITICAL structural stress index of {stress:.0f} detected. The combined load exceeds safe capacity thresholds. Structure is at high risk of material failure without immediate load reduction.")
    elif stress_label == "HIGH":
        lines.append(f"Structural stress index is HIGH at {stress:.0f}. The Euler-Bernoulli beam model predicts significant deflection and strain that may approach material yield limits.")
    elif stress_label == "MODERATE":
        lines.append(f"Stress index is MODERATE at {stress:.0f}. The bridge structure is handling the current load acceptably, though monitoring is recommended.")
    else:
        lines.append(f"Stress index is LOW at {stress:.0f}. The structure is operating comfortably within design safety margins under current conditions.")

    if damaged != "none":
        lines.append(f"⚠ Damage simulation is active on Pillar {damaged}. The physics model has redistributed loads to adjacent structural members, causing elevated stress concentrations. Real-world equivalent would require immediate shutdown and inspection.")
        status = "critical"

    if wind > 80:
        lines.append(f"Wind-induced flutter risk is significant at {wind} km/h. Aerodynamic resonance could trigger oscillation modes that standard damping systems may not fully suppress.")
    if abs(temp - 20) > 20:
        lines.append(f"Thermal expansion effects are notable at {temp}°C (a {abs(temp-20):.0f}°C deviation from reference). Material stress from thermal gradients has been factored into the simulation.")
    if traffic > 80:
        lines.append(f"Traffic load of {traffic}% represents a near-overload condition. Vehicle-induced dynamic loading is the primary stress contributor under current settings.")

    conclusion = " ".join(lines)
    return {"conclusion": conclusion, "status": status}


@app.get("/api/ai-conclusion/behaviour/{test_id}")
def conclusion_behaviour(test_id: str):
    try:
        df = load_behaviour()
        bdf = df[df["test_id"] == test_id] if test_id != "all" else df
        bsi = float(bdf["Behavioral_Shift_Index"].mean()) if "Behavioral_Shift_Index" in bdf else 0
        sds = float(bdf["Structural_Dynamics_Score"].mean()) if "Structural_Dynamics_Score" in bdf else 0
        cluster = int(bdf["Behavioral_State_Cluster"].mode()[0]) if "Behavioral_State_Cluster" in bdf else 0
        anomaly = float(bdf["Autoencoder_Anomaly_Score"].mean()) if "Autoencoder_Anomaly_Score" in bdf else 0
        risk = float(bdf["Predicted_Risk_Score"].mean()) if "Predicted_Risk_Score" in bdf else 0
        alerts = int(bdf["Anomaly_Alert_Flag"].sum()) if "Anomaly_Alert_Flag" in bdf else 0
        return generate_behaviour_conclusion(bsi, sds, cluster, anomaly, risk, alerts)
    except Exception as e:
        return {"conclusion": f"Unable to generate conclusion: {str(e)}", "status": "normal"}


@app.get("/api/ai-conclusion/anomaly/{test_id}")
def conclusion_anomaly(test_id: str):
    try:
        df = load_risk()  # failure_prediction_behavior.parquet
        bdf = df[df["bridge_id"] == RISK_BRIDGE]
        anomaly_mean = float(bdf["Autoencoder_Anomaly_Score"].mean()) if "Autoencoder_Anomaly_Score" in bdf.columns else 0
        anomaly_max = float(bdf["Autoencoder_Anomaly_Score"].max()) if "Autoencoder_Anomaly_Score" in bdf.columns else 0
        alert_count = int((bdf["Autoencoder_Anomaly_Score"] > 0.5).sum()) if "Autoencoder_Anomaly_Score" in bdf.columns else 0
        return generate_anomaly_conclusion(anomaly_mean, anomaly_max, alert_count, 0.5)
    except Exception as e:
        return {"conclusion": f"Unable to generate conclusion: {str(e)}", "status": "normal"}


@app.get("/api/ai-conclusion/risk/{test_id}")
def conclusion_risk(test_id: str):
    try:
        df = load_risk()  # failure_prediction_behavior.parquet
        bdf = df[df["bridge_id"] == RISK_BRIDGE]
        risk_mean = float(bdf["Predicted_Risk_Score"].mean()) if "Predicted_Risk_Score" in bdf.columns else 0
        risk_max = float(bdf["Predicted_Risk_Score"].max()) if "Predicted_Risk_Score" in bdf.columns else 0
        beh_df = load_behaviour()
        beh_b = beh_df[beh_df["test_id"] == BEHAVIOUR_ID]
        bsi = float(beh_b["Behavioral_Shift_Index"].mean()) if "Behavioral_Shift_Index" in beh_b.columns else 0
        if risk_mean < 0.2: level = "LOW"
        elif risk_mean < 0.4: level = "MODERATE"
        elif risk_mean < 0.6: level = "HIGH"
        else: level = "CRITICAL"
        return generate_risk_conclusion(risk_mean, risk_max, level, bsi)
    except Exception as e:
        return {"conclusion": f"Unable to generate conclusion: {str(e)}", "status": "normal"}


@app.post("/api/ai-conclusion/digital-twin")
def conclusion_digital_twin(body: dict):
    try:
        traffic = int(body.get("traffic", 40))
        temp = float(body.get("temp", 22))
        wind = float(body.get("wind", 20))
        stress = float(body.get("stress", 0))
        damaged = str(body.get("damaged", "none"))
        scenario = str(body.get("scenario", "Normal"))
        return generate_digitaltwin_conclusion(traffic, temp, wind, stress, damaged, scenario)
    except Exception as e:
        return {"conclusion": f"Unable to generate conclusion: {str(e)}", "status": "normal"}


# ── PDF Health Report ─────────────────────────────────────────────────────────

@app.get("/api/report/{bridge_id}")
def generate_report(bridge_id: str):
    """Generates and returns a professional PDF structural health report for Bridge B001."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, KeepTogether
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER

        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        # ── Load data ──────────────────────────────────────────────────────
        # Failure prediction parquet: bridge_id = B001
        fp_df = load_risk()
        fp    = fp_df[fp_df["bridge_id"] == RISK_BRIDGE]

        # Behaviour parquet: test_id = test1 (same physical bridge)
        beh_df = load_behaviour()
        beh    = beh_df[beh_df["test_id"] == BEHAVIOUR_ID]

        def col_mean(df, c):
            return float(df[c].mean()) if c in df.columns and len(df) > 0 else 0.0
        def col_max(df, c):
            return float(df[c].max()) if c in df.columns and len(df) > 0 else 0.0
        def col_sum(df, c):
            return int(df[c].sum()) if c in df.columns and len(df) > 0 else 0

        risk        = col_mean(fp,  "Predicted_Risk_Score")
        risk_max    = col_max(fp,   "Predicted_Risk_Score")
        anomaly     = col_mean(fp,  "Autoencoder_Anomaly_Score")
        anomaly_mx  = col_max(fp,   "Autoencoder_Anomaly_Score")
        deg         = col_mean(fp,  "degradation_score")
        cond        = col_mean(fp,  "structural_condition")
        fc          = col_mean(fp,  "forecast_score_next_30d")
        alerts      = col_sum(fp,   "Anomaly_Alert_Flag")
        temp_c      = col_mean(fp,  "temperature_c")
        wind_mps    = col_mean(fp,  "wind_speed_mps")
        fft_freq    = col_mean(fp,  "fft_peak_freq")

        # From behaviour parquet
        bsi         = col_mean(beh, "Behavioral_Shift_Index")
        sds         = col_mean(beh, "Structural_Dynamics_Score")
        cluster     = int(beh["Behavioral_State_Cluster"].mode()[0]) if "Behavioral_State_Cluster" in beh.columns and len(beh) > 0 else 0
        beh_anomaly = col_mean(beh, "Autoencoder_Anomaly_Score")
        beh_risk    = col_mean(beh, "Predicted_Risk_Score")
        beh_alerts  = col_sum(beh,  "Anomaly_Alert_Flag")

        # Risk trend: first vs last quarter
        rt = 0.0
        if "Predicted_Risk_Score" in fp.columns and len(fp) > 9:
            n = max(1, len(fp) // 4)
            first = float(fp["Predicted_Risk_Score"].iloc[:n].mean())
            last  = float(fp["Predicted_Risk_Score"].iloc[-n:].mean())
            rt = last - first

        # Derived
        state_map  = {0: "Normal Baseline", 1: "Active Load State", 2: "Altered Dynamics"}
        state      = state_map.get(cluster, "Unknown")
        cond_label = "Excellent" if risk < 0.2 else ("Fair" if risk < 0.5 else "Degraded")
        risk_flag  = "LOW ✓" if risk < 0.2 else ("MODERATE" if risk < 0.5 else "HIGH ⚠")

        # Estimate service life (simplified heuristic)
        annual_rate = max(0.001, risk * 0.02 + (rt * 0.005 if rt > 0 else 0))
        prob_100    = round(min((1 - (1 - annual_rate) ** 100) * 100, 99.9), 1)
        if deg > 0 and risk > 0:
            years = round(max(5, min(80, (1 - cond) / max(deg * 0.01, 0.001))))
        else:
            years = 50

        # ── PDF Builder ────────────────────────────────────────────────────
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        CYAN   = colors.HexColor('#006B8F')
        RED    = colors.HexColor('#CC2222')
        ORANGE = colors.HexColor('#CC6600')
        GREEN  = colors.HexColor('#006600')
        GRAY   = colors.HexColor('#444444')
        LTGRAY = colors.HexColor('#F4F7FA')

        title_style = ParagraphStyle('T', parent=styles['Title'],   fontSize=18, leading=24, textColor=CYAN, spaceAfter=4)
        sub_style   = ParagraphStyle('S', parent=styles['Normal'],  fontSize=9,  textColor=GRAY, spaceAfter=14)
        h2_style    = ParagraphStyle('H', parent=styles['Heading2'],fontSize=12, textColor=CYAN, spaceBefore=14, spaceAfter=5)
        body_style  = ParagraphStyle('B', parent=styles['Normal'],  fontSize=9,  leading=15, textColor=colors.black)
        warn_style  = ParagraphStyle('W', parent=styles['Normal'],  fontSize=9,  leading=15, textColor=RED)
        small_style = ParagraphStyle('Sm', parent=styles['Normal'], fontSize=7.5, textColor=GRAY)

        story = []

        # Header
        story.append(Paragraph("STRUCTURAL HEALTH INTELLIGENCE REPORT", title_style))
        story.append(Paragraph(
            f"Bridge: <b>B001</b> &nbsp;|&nbsp; Generated: {now} &nbsp;|&nbsp; AI Structural Monitoring Platform",
            sub_style))
        story.append(HRFlowable(width="100%", thickness=2, color=CYAN, spaceAfter=12))

        # Executive Summary
        story.append(Paragraph("Executive Summary", h2_style))
        if risk < 0.2:
            summary_txt = ("Bridge B001 is currently in <b>good structural health</b> with no immediate concerns. "
                           "All monitored parameters are within normal operational bounds.")
        elif risk < 0.5:
            summary_txt = ("Bridge B001 exhibits a <b>moderate risk profile</b>. "
                           "Elevated anomaly events have been recorded and a detailed inspection is recommended "
                           "within the next 4–6 weeks.")
        else:
            summary_txt = ("<b>⚠ Elevated risk indicators</b> detected for Bridge B001. "
                           "Immediate structural assessment is strongly recommended. "
                           "Consider temporary load restrictions pending engineering review.")
        story.append(Paragraph(
            f"{summary_txt} AI model estimates approximately <b>{years} years</b> of remaining service life "
            f"under current load and environmental conditions.", body_style))
        story.append(Spacer(1, 8))

        # Key Metrics Table
        story.append(Paragraph("Key Structural Metrics", h2_style))
        pct = lambda v: f"{round(v * 100, 1)}%"
        table_data = [
            ["Metric", "Value", "Status"],
            ["Avg Predicted Failure Risk",      pct(risk),       risk_flag],
            ["Peak Failure Risk (recorded)",    pct(risk_max),   "HIGH ⚠" if risk_max > 0.5 else "OK"],
            ["AI Anomaly Score (avg)",           pct(anomaly),    "ELEVATED" if anomaly > 0.3 else "Normal"],
            ["Peak Anomaly Spike",               pct(anomaly_mx), "HIGH ⚠" if anomaly_mx > 0.7 else "OK"],
            ["Behavioral Shift Index",           f"{bsi:.4f}",    "Elevated" if bsi > 0.4 else "Normal"],
            ["Structural Dynamics Score",        f"{sds:.4f}",    "Elevated" if sds > 0.6 else "Normal"],
            ["Degradation Score (avg)",          f"{deg:.4f}",    "High" if deg > 0.3 else "Acceptable"],
            ["Structural Condition Score",       f"{cond:.3f}",   "Poor" if cond < 0.5 else "Good"],
            ["30-Day Risk Forecast",             pct(fc),         "Rising ⚠" if fc > risk else "Stable"],
            ["Anomaly Alert Events (B001 raw)",  str(alerts),     "Flagged" if alerts > 0 else "None"],
            ["Anomaly Alert Events (behaviour)", str(beh_alerts), "Flagged" if beh_alerts > 0 else "None"],
            ["Avg Temperature (sensor)",         f"{temp_c:.1f}°C", "Normal"],
            ["Avg Wind Speed (sensor)",          f"{wind_mps:.2f} m/s", "Normal"],
            ["FFT Peak Frequency",               f"{fft_freq:.2f} Hz", "Normal"],
            ["Dominant Behavioral State",        state,           ""],
            ["Prob. Failure (100-yr horizon)",   f"{prob_100}%",  "HIGH" if prob_100 > 50 else "LOW"],
            ["Est. Remaining Service Life",      f"~{years} yrs", cond_label],
        ]
        col_w = [7.5*cm, 4.5*cm, 4.0*cm]
        tbl = Table(table_data, colWidths=col_w, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), CYAN),
            ('TEXTCOLOR',     (0,0), (-1,0), colors.white),
            ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0,0), (-1,0), 9),
            ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, LTGRAY]),
            ('FONTSIZE',      (0,1), (-1,-1), 8.5),
            ('GRID',          (0,0), (-1,-1), 0.4, colors.HexColor('#CCCCCC')),
            ('ALIGN',         (1,0), (-1,-1), 'CENTER'),
            ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING',    (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        for row_idx, row in enumerate(table_data[1:], start=1):
            status = str(row[2]).upper()
            c = (RED    if any(k in status for k in ['HIGH','CRITICAL','ELEVATED','FLAGGED','RISING','POOR']) else
                 ORANGE if 'MODERATE' in status else
                 GREEN  if any(k in status for k in ['LOW','NORMAL','OK','GOOD','STABLE','EXCELLENT','ACCEPTABLE']) else
                 colors.black)
            tbl.setStyle(TableStyle([('TEXTCOLOR', (2,row_idx), (2,row_idx), c),
                                     ('FONTNAME', (2,row_idx), (2,row_idx), 'Helvetica-Bold')]))
        story.append(tbl)
        story.append(Spacer(1, 12))

        # Risk Trend
        story.append(Paragraph("Risk Trend Analysis", h2_style))
        if rt > 0.03:
            tt = ("⚠ The failure risk score is <b>rising</b> over the observed monitoring period. "
                  "This trend warrants increased inspection frequency and proactive maintenance planning.")
            ps = warn_style
        elif rt < -0.03:
            tt = ("✅ The failure risk score is <b>declining</b> — current maintenance strategy is effective. "
                  "Continue the current approach and schedule the next review in 6 months.")
            ps = body_style
        else:
            tt = "→ The failure risk score is <b>stable</b> over the monitoring period. No significant change in risk trajectory."
            ps = body_style
        story.append(Paragraph(tt, ps))
        story.append(Spacer(1, 8))

        # Engineering Recommendations
        story.append(Paragraph("Engineering Recommendations", h2_style))
        recs = []
        if risk >= 0.5:
            recs.append("🔴 Deploy an emergency structural assessment team immediately.")
            recs.append("🔴 Consider traffic load restrictions pending inspection results.")
        elif risk >= 0.2:
            recs.append("⚠ Schedule a detailed on-site structural inspection within 4–6 weeks.")
            recs.append("⚠ Increase monitoring frequency from monthly to bi-weekly.")
        else:
            recs.append("✅ Continue standard monitoring schedule (monthly / bi-monthly).")
        if alerts > 0 or beh_alerts > 0:
            total_al = alerts + beh_alerts
            recs.append(f"⚠ Review {total_al} anomaly alert event(s) — investigate possible load or weather correlation.")
        if deg > 0.3:
            recs.append("⚠ Elevated degradation detected — evaluate joint and bearing conditions.")
        if bsi > 0.35:
            recs.append("⚠ Behavioral shift index is elevated — check for foundation settlement or load redistribution.")
        if rt > 0.03:
            recs.append("⚠ Risk trend is rising — consider an accelerated maintenance program.")
        next_insp = ("Within 1 week" if risk >= 0.5 else "Within 4–6 weeks" if risk >= 0.2 else "In 12–18 months")
        recs.append(f"📅 Next recommended inspection: {next_insp}.")
        for r_text in recs:
            story.append(Paragraph(f"\u00a0\u00a0• {r_text}", body_style))
        story.append(Spacer(1, 14))

        # Data Sources
        story.append(Paragraph("Data Sources & Methodology", h2_style))
        sources = [
            ["Dataset", "File", "Records"],
            ["Failure Prediction (B001)", "failure_prediction_behavior.parquet", "448 readings"],
            ["Structural Behaviour (test1)", "behaviour_behavior.parquet", "~300 windows"],
        ]
        src_tbl = Table(sources, colWidths=[5.5*cm, 7*cm, 4.5*cm])
        src_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), CYAN),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0,0), (-1,1), 8.5),
            ('FONTSIZE',   (0,1), (-1,-1), 8),
            ('GRID',       (0,0), (-1,-1), 0.4, colors.HexColor('#CCCCCC')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LTGRAY]),
            ('ALIGN',      (2,0), (-1,-1), 'CENTER'),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        story.append(src_tbl)
        story.append(Spacer(1, 14))

        # Footer
        story.append(HRFlowable(width="100%", thickness=1, color=GRAY, spaceAfter=6))
        story.append(Paragraph(
            f"Report generated by AI Structural Monitoring Platform · {now} · "
            f"Data source: real parquet sensor datasets · "
            f"This report is for engineering advisory purposes only and does not constitute a formal structural certification.",
            small_style))

        doc.build(story)
        buf.seek(0)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf",
                                          prefix=f"health_report_B001_")
        tmp.write(buf.read())
        tmp.close()

        report_date = datetime.now().strftime("%Y%m%d")
        return FileResponse(
            tmp.name,
            media_type="application/pdf",
            filename=f"Health_Report_B001_{report_date}.pdf",
            headers={"Content-Disposition": f'attachment; filename="Health_Report_B001_{report_date}.pdf"'},
        )
    except Exception as e:
        import traceback; traceback.print_exc()
        return {"error": str(e)}
