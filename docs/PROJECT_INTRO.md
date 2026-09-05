# GERT Project Detailed Introduction (Beginner-Friendly)

## 📖 Table of Contents
1. [What is this project?](#what-is-this-project)
2. [Why do we need this project?](#why-do-we-need-this-project)
3. [What can this project do?](#what-can-this-project-do)
4. [Technical Architecture (Simple Understanding)](#technical-architecture-simple-understanding)
5. [Project Structure](#project-structure)
6. [How to Use](#how-to-use)
7. [Core Features Explained](#core-features-explained)
8. [Technology Stack](#technology-stack)
9. [Project Highlights](#project-highlights)

---

## 🎯 What is this project?

**GERT (Grid Extreme Risk Toolkit)** is a **power grid extreme risk prediction system**.

### Understanding with a real-life example:

Imagine:
- **During the hottest summer days**, everyone turns on their air conditioners, causing electricity demand to surge
- **During the coldest winter days**, heating equipment runs at full capacity, also causing demand to surge
- If **power generation capacity is insufficient**, **blackouts occur**

**Problems with traditional forecasting**:
- Only predicts "average electricity demand"
- But during extreme weather, actual demand far exceeds the average
- Result: Forecast says "sufficient capacity", but blackouts happen anyway

**GERT's approach**:
- Not only predicts the average, but also predicts the "worst-case scenario" (1% probability extreme events)
- If the worst case exceeds generation capacity, it **provides early warning**
- Helps grid operators **prepare in advance** to avoid blackouts

---

## ❓ Why do we need this project?

### Real-world case: 2021 Texas Winter Storm

- **What happened**: Extreme cold caused electricity demand to surge while power generation equipment failed
- **Result**: Massive blackouts affecting millions of people, causing huge economic losses
- **Problem**: Traditional forecasting systems failed to provide early warnings

### GERT's value

1. **Early warning**: Predicts extreme risks hours or even days in advance
2. **Risk quantification**: Quantifies risk levels using a 0-100 score
3. **Visualization**: Intuitively displays risks using charts
4. **Decision support**: Helps operators make correct decisions

---

## 🚀 What can this project do?

### 1. **Real-time Risk Monitoring (Live Monitor)**

**Features**:
- Displays current grid risk level (LOW / MODERATE / HIGH / EXTREME)
- Shows 24-hour electricity demand forecast using charts
- Displays "worst-case scenario" (P99) and "average scenario" (P50)
- If the red line (P99) approaches or exceeds the green line (generation capacity), the system highlights warnings in red

**Interface**:
- Left side: Map showing regional status
- Right side: Time series chart (Fan Chart)
- Top: Key metric cards (risk score, load, capacity margin)

---

### 2. **Scenario Laboratory (Scenario Lab)**

**Features**:
- Simulates extreme weather: extreme cold, heat waves, no wind/no sunlight
- Adjust parameters like temperature and wind speed to see how risk changes
- System explains "why risk increased" (e.g., temperature drops → heating demand increases → risk rises)

**Use cases**:
- "What would the risk be if temperature drops to -10°C tomorrow?"
- "What happens if wind speed drops to 0, reducing solar generation?"

---

### 3. **Historical Event Replay (Event Replay)**

**Features**:
- Replays historical events like the 2021 Texas winter storm
- Shows hourly data: load, capacity, forecast, risk score
- Displays "control room logs": when the system warned about risks

**Value**:
- Validates system accuracy
- Learn from historical experience
- Improve prediction models

---

### 4. **Model Benchmarking (Benchmarks)**

**Features**:
- Compares accuracy between traditional models and GERT
- Uses calibration charts to verify "when we say 99%, it really is 99%"
- Displays Pinball Loss (prediction error)

**Value**:
- Proves GERT is more accurate than traditional methods
- Builds trust

---

## 🏗 Technical Architecture (Simple Understanding)

### Overall Architecture

```
┌─────────────────┐
│  User Browser   │  ← The interface you see
└────────┬────────┘
         │ HTTP Request
         ▼
┌─────────────────┐
│  Next.js Frontend│  ← Displays charts, handles interactions
└────────┬────────┘
         │ API Calls
         ▼
┌─────────────────┐
│ FastAPI Backend │  ← Calculates predictions, assesses risks
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌──────┐  ┌──────┐
│Database│ │External│  ← Stores history, fetches weather data
│        │ │  API   │
└──────┘  └──────┘
```

### Frontend-Backend Separation

**Frontend (Next.js)**:
- Responsibilities: Display interface, handle user interactions, call backend APIs
- Technologies: React, TypeScript, Tailwind CSS, Recharts

**Backend (FastAPI)**:
- Responsibilities: Calculate predictions, assess risks, and store data
- Technologies: Python, FastAPI, SQLAlchemy, Pydantic

**Database (SQLite/PostgreSQL)**:
- Responsibilities: Store prediction history, alert records, load data

---

## 📁 Project Structure

### Frontend Files (`app/`, `components/`, `lib/`)

```
app/
├── page.tsx              # Homepage (Live Monitor)
├── scenario/page.tsx      # Scenario Laboratory
├── benchmark/page.tsx     # Model Benchmarking
├── events/polar-vortex/   # Event Replay
└── layout.tsx            # Global Layout

components/
├── Sidebar.tsx            # Left navigation bar
├── Charts.tsx             # Chart components
├── GridMap.tsx           # Map component
├── Toast.tsx              # Error notification component
└── ui.tsx                 # Common UI components

lib/
├── api.ts                 # API call wrapper
└── types.ts               # TypeScript type definitions
```

### Backend Files (`api/`, `services/`, `models/`, etc.)

```
api/
├── routes.py              # API routes (endpoint definitions)
├── schemas.py             # Data models (request/response formats)
├── validators.py          # Input validation
└── app.py                 # FastAPI application entry point

services/
├── risk_service.py        # Risk prediction service
├── scenario_service.py    # Scenario analysis service
└── region.py              # Region configuration

models/
├── stub.py                # Mock model (for demos)
├── real_adapter.py        # Real model adapter
└── quantiles.py           # Quantile processing

data/
├── ercot.py               # ERCOT data adapter
├── caiso.py               # CAISO data adapter
└── factory.py             # Data adapter factory

db/
├── models.py              # Database models
├── repository.py          # Data access layer
└── connection.py          # Database connection

alerts/
├── manager.py             # Alert manager
├── channels.py            # Notification channels (Email/SMS/Webhook)
└── config.py              # Alert configuration
```

---

## 🎮 How to Use

### 1. Start the Project

```bash
# Method 1: Use startup script (recommended)
./start.sh

# Method 2: Manual startup
# Terminal 1: Start backend
source .venv/bin/activate
python main.py

# Terminal 2: Start frontend
npm run dev
```

### 2. Access the Interface

- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs

### 3. Usage Flow

1. **View real-time risk**:
   - Open the homepage (Live Monitor)
   - View current risk level and prediction charts
   - Click "Refresh Model" to update data

2. **Test scenarios**:
   - Switch to "Scenario Lab"
   - Drag temperature/wind speed sliders
   - Click "Apply Scenario" to see impact

3. **View history**:
   - Switch to "Event Replay"
   - View 2021 winter storm replay

---

## 🔍 Core Features Explained

### 1. Quantile Regression

**What are quantiles?**
- P50: 50% probability of not exceeding this value (median)
- P90: 90% probability of not exceeding this value
- P99: 99% probability of not exceeding this value (extreme case)

**Why use quantiles?**
- Traditional methods only predict the average (P50)
- But during extreme weather, actual values may far exceed the average
- Quantile regression can predict the "worst-case scenario"

**Code locations**:
- `models/quantiles.py`: Quantile processing
- `features/weather.py`: Feature engineering

---

### 2. Risk Scoring

**Scoring rules**:
```
Risk Score = f(Capacity Margin)
Capacity Margin = Generation Capacity - P99 Load

If Capacity Margin < 0: Risk Score = 100 (EXTREME)
If Capacity Margin < 500 MW: Risk Score = 90 (HIGH)
If Capacity Margin < 2000 MW: Risk Score = 75 (HIGH)
If Capacity Margin < 5000 MW: Risk Score = 40 (MODERATE)
Otherwise: Risk Score = 0 (LOW)
```

**Code location**:
- `risk/scoring.py`: Risk scoring logic

---

### 3. Real Data Integration

**Data sources**:
- **ERCOT** (Texas Grid)
- **CAISO** (California Grid)
- **PJM** (Pennsylvania-New Jersey-Maryland)
- **NYISO** (New York Grid)

**Data adapters**:
- Each ISO has different API formats
- Adapters unify data formats
- Automatic adapter selection

**Code locations**:
- `data/`: Data adapters
- `api/routes.py`: `/load/current` endpoint

---

### 4. Alert Notification System

**Notification channels**:
- **Email** (SMTP)
- **SMS** (Twilio)
- **Webhook** (Slack/Discord/DingTalk)

**Trigger conditions**:
- Risk level escalation (LOW → MODERATE → HIGH → EXTREME)
- Risk score exceeds threshold (default HIGH=90, EXTREME=95)
- Rate limiting: Maximum one alert per 15 minutes

**Code locations**:
- `alerts/manager.py`: Alert manager
- `alerts/channels.py`: Notification channels

---

### 5. Data Persistence

**Stored content**:
- **predictions**: Prediction history
- **alerts**: Alert history
- **grid_loads**: Load history

**Use cases**:
- Backtest model accuracy
- Analyze historical trends
- Audit and compliance

**Code locations**:
- `db/models.py`: Database models
- `db/repository.py`: Data access layer

---

## 🛠 Technology Stack

### Frontend Technologies

| Technology | Purpose | Why Choose |
|------------|---------|------------|
| **Next.js** | React Framework | Server-side rendering, routing, performance optimization |
| **TypeScript** | Type System | Reduces errors, improves code quality |
| **Tailwind CSS** | Styling Framework | Rapid development, responsive design |
| **Recharts** | Chart Library | Powerful features, easy customization |
| **Lucide React** | Icon Library | Rich icons, consistent style |

### Backend Technologies

| Technology | Purpose | Why Choose |
|------------|---------|------------|
| **FastAPI** | Web Framework | High performance, auto documentation, type validation |
| **Python** | Programming Language | Scientific computing, numerical modeling, rich ecosystem |
| **SQLAlchemy** | ORM | Database operations, connection pooling, migrations |
| **Pydantic** | Data Validation | Type safety, automatic validation |
| **httpx** | HTTP Client | Async, good performance |

### Database

| Technology | Purpose | Why Choose |
|------------|---------|------------|
| **SQLite** | Development DB | No installation needed, lightweight |
| **PostgreSQL** | Production DB | Powerful features, good performance |

---

## ✨ Project Highlights

### 1. **High Engineering Standards**

- ✅ **Modular Design**: Clear code layering (API, Service, Model)
- ✅ **Type Safety**: TypeScript + Pydantic
- ✅ **Error Handling**: Comprehensive error handling and user notifications
- ✅ **Input Validation**: Strict parameter validation
- ✅ **Database Optimization**: Connection pooling, transaction management

### 2. **Complete Functionality**

- ✅ **Real Data Integration**: Supports multiple ISO data sources
- ✅ **Alert System**: Multi-channel notifications
- ✅ **Data Persistence**: Historical data storage

### 3. **Great User Experience**

- ✅ **Control Room Style**: Professional interface design
- ✅ **Real-time Feedback**: Loading states, error notifications
- ✅ **Smooth Interactions**: Responsive design, animation effects
- ✅ **Clear Information**: Data source indicators, trend indicators

### 4. **Highly Extensible**

- ✅ **Adapter Pattern**: Easy to add new data sources
- ✅ **Plugin Design**: Easy to add new features
- ✅ **Configuration**: Environment variable configuration
- ✅ **Complete Documentation**: Code comments, usage documentation

---

## 📊 Project Statistics

- **Code Volume**:
  - Python: ~4,182 lines
  - TypeScript/TSX: ~9,254 lines
  - Total: ~13,436 lines

- **Module Count**:
  - Backend modules: 15+
  - Frontend components: 10+
  - API endpoints: 10+

- **Features**:
  - 5 main pages
  - 4 data adapters
  - 3 notification channels
  - 3 database tables

---

## 🎓 Learning Value

### For Beginners

1. **Full-stack Development**: Learn frontend-backend separation architecture
2. **API Design**: Learn RESTful API design
3. **Data Visualization**: Learn chart rendering
4. **Database Operations**: Learn ORM usage
5. **Error Handling**: Learn exception handling best practices

### For Advanced Learners

1. **Architecture Design**: Learn layered architecture, adapter pattern
2. **Performance Optimization**: Learn connection pooling, caching
3. **Engineering Practices**: Learn code organization, testing, documentation
4. **Business Understanding**: Learn grid operations, risk prediction

---

## 🚀 Next Steps for Learning

1. **Deepen Algorithm Understanding**:
   - Quantile regression principles
   - Risk scoring algorithms
   - Feature engineering

2. **Extend Features**:
   - Add more data sources
   - Implement real-time data push (WebSocket)
   - Add more visualizations

3. **Optimize Performance**:
   - Add caching layer
   - Optimize database queries
   - Frontend performance optimization

4. **Deploy to Production**:
   - Docker containerization
   - CI/CD automation
   - Production environment configuration

---

## 📝 Summary

**GERT is**:
- ✅ A **professional** power grid risk prediction system
- ✅ A **complete** full-stack project (Frontend + Backend + Database)
- ✅ **Well-engineered** code structure (modular, type-safe, error handling)
- ✅ **Practical** features (real data, alerts, persistence)
- ✅ **User-friendly** interface (control room style, smooth interactions)

**Suitable for**:
- Learning full-stack development
- Learning data visualization
- Learning API design
- Learning engineering practices
- Showcasing as a portfolio project

---

## 📚 Related Documentation

- **Deployment Guide**: `DEPLOYMENT.md`
- **Real Data Integration**: `docs/REAL_DATA_SETUP.md`
- **Improvement Suggestions**: `docs/IMPROVEMENTS.md`
- **API Documentation**: http://localhost:8000/docs (after starting the server)

---

**Happy learning! If you have questions, check the code comments or documentation anytime.** 🎉
