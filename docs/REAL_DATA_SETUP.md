# Real Data Integration Guide

## Overview

GERT now supports integration with real grid data, including:
1. **Real Load Data**: Fetch real-time load from ISOs like ERCOT, CAISO, PJM, NYISO
2. **Alert Notification System**: Automatically send email/SMS/Webhook notifications when risk exceeds thresholds
3. **Database Persistence**: Automatically save all prediction and alert history to database

---

## 1. Real Data Integration

### Data Source Adapters

The system has implemented data adapters for the following ISOs:
- `ERCOTAdapter`: Texas grid
- `CAISOAdapter`: California grid
- `PJMAdapter`: Pennsylvania-New Jersey-Maryland grid
- `NYISOAdapter`: New York grid

### Usage

Data adapters are automatically selected based on region:
```python
from data.factory import get_data_adapter

adapter = get_data_adapter("ERCOT_NORTH")
load_data = await adapter.fetch_current_load("ERCOT_NORTH")
```

### API Endpoints

**Get Current Load**:
```
GET /load/current?region=ERCOT_NORTH
```

Returns:
```json
{
  "region": "ERCOT_NORTH",
  "current_load_mw": 45000.0,
  "capacity_mw": 65000.0,
  "utilization_percent": 69.2,
  "timestamp": "2024-02-16T18:00:00",
  "data_source": "real_time"
}
```

**Prediction Endpoint Automatically Uses Real Data**:
The prediction endpoint automatically attempts to fetch real load data and marks the data source in `diagnostics`:
- `data_source: "real_time"` - Real data was used
- `data_source: "simulated"` - Simulated data was used (fallback when API fails)

---

## 2. Alert Notification System

### Configure Environment Variables

Configure in `.env` file:

```bash
# Alert thresholds (risk score)
ALERT_LOW_THRESHOLD=40.0
ALERT_MODERATE_THRESHOLD=75.0
ALERT_HIGH_THRESHOLD=90.0
ALERT_EXTREME_THRESHOLD=95.0

# Minimum alert interval (minutes, prevent spam)
ALERT_MIN_INTERVAL_MINUTES=15

# ===== Email Notifications =====
ALERT_EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com
EMAIL_TO=operator1@example.com,operator2@example.com

# ===== SMS Notifications (Twilio) =====
ALERT_SMS_ENABLED=false
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890
SMS_TO_NUMBERS=+1234567890,+0987654321

# ===== Webhook Notifications (Slack/Discord/DingTalk) =====
ALERT_WEBHOOK_ENABLED=true
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
WEBHOOK_SECRET=optional_secret
```

### Alert Trigger Conditions

The system will send alerts in the following situations:
1. **Risk Level Escalation**: LOW → MODERATE → HIGH → EXTREME
2. **Risk Score Exceeds Threshold**: Reaches configured threshold (default HIGH=90, EXTREME=95)
3. **Spam Prevention**: Maximum one alert per 15 minutes for the same risk level

### Alert Content Example

**Email/SMS**:
```
GERT Risk Alert - HIGH Risk Detected

Region: ERCOT_NORTH
Risk Level: HIGH
Risk Score: 92.5/100

Load Forecast:
  P99 Extreme Load: 58.50 GW
  Available Capacity: 65.00 GW
  Margin: 6.50 GW (TIGHT)

Timestamp: 2024-02-16 18:00:00 UTC

Action Required:
  - Monitor grid conditions closely
  - Prepare contingency reserves
  - Consider demand response activation
```

---

## 3. Database Persistence

### Database Configuration

**Development Environment (SQLite, default)**:
```bash
# No configuration needed, automatically uses SQLite
DATABASE_URL=sqlite:///./gert.db
```

**Production Environment (PostgreSQL)**:
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/gert
```

### Database Table Structure

**predictions**: Prediction history
- Stores complete information for each prediction (weather, load, risk score, etc.)
- Used for backtesting and model optimization

**alerts**: Alert history
- Records all sent alerts
- Includes notification channels and success status

**grid_loads**: Load history
- Stores real load data fetched from ISO APIs
- Used for analyzing load patterns

### API Endpoints

**Query Prediction History**:
```
GET /predictions/history?region=ERCOT_NORTH&limit=100
```

**Query Alert History**:
```
GET /alerts/history?region=ERCOT_NORTH&limit=50
```

### Initialize Database

Database tables are automatically created when the application starts. You can also manually initialize:

```python
from db.connection import init_db
init_db()
```

---

## 4. Complete Deployment Example

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

Create `.env` file:
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/gert

# Alert System
ALERT_EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-password
EMAIL_FROM=your-email@gmail.com
EMAIL_TO=operator@example.com

ALERT_WEBHOOK_ENABLED=true
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK
```

### Step 3: Start Application

```bash
python main.py
```

Or using uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Step 4: Verify

1. **Check Database**: Visit `/health` endpoint, confirm database is initialized
2. **Test Prediction**: Send prediction request, check if `diagnostics.data_source` is `real_time`
3. **Test Alert**: Trigger high-risk scenario, check if notification is received

---

## 5. Troubleshooting

### Real Data Fetch Failure

- **Check Network**: Ensure server can access ISO APIs
- **View Logs**: Check error messages in `logger.warning`
- **Fallback Mechanism**: System automatically falls back to simulated data, service will not be interrupted

### Alerts Not Sent

- **Check Configuration**: Confirm `ALERT_*_ENABLED=true` and credentials are correct
- **Check Thresholds**: Confirm risk score reaches configured threshold
- **Check Interval**: Confirm not within 15-minute cooldown period
- **View Logs**: Check records in `alerts` table

### Database Errors

- **Check Connection**: Confirm `DATABASE_URL` is correct
- **Check Permissions**: Ensure database user has permission to create tables
- **SQLite Permissions**: Ensure application has write permission for `gert.db`

---

## 6. Future Optimization Directions

1. **More Complete ISO API Integration**: Implement complete OASIS/PJM API queries
2. **Historical Data Backfill**: Download historical CSV from ISOs and import to database
3. **Prediction Accuracy Analysis**: Compare predictions vs actual load, calculate errors
4. **Customizable Alert Rules**: Allow users to customize thresholds and notification channels
5. **Data Visualization**: Display prediction history and alert trends in frontend
