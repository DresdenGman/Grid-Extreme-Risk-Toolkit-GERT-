# Grid Extreme Risk Toolkit (GERT)

GERT is a probabilistic risk assessment platform designed to identify, quantify, and visualize extreme tail risks in power grid operations. Unlike traditional forecasting tools that focus on the "average" (P50) outcome, GERT utilizes Quantile Regression to model the 1% (P99) extreme scenarios that lead to blackouts and infrastructure failure.

## 🚀 Features

- **Probabilistic Forecasting**: Visualizes uncertainty using Fan Charts, displaying P50, P90, P95, and P99 load quantiles.
- **Risk Quantification**: Converts complex grid data into a normalized Risk Score (0-100) and actionable Status Levels (Low to Extreme).
- **Scenario Stress Testing**: A "What-If" laboratory allowing operators to simulate extreme weather events (e.g., Polar Vortex, Heat Waves) and observe immediate grid impacts.
- **Historical Event Replay**: Step-by-step playback of historical grid failures (e.g., 2021 Winter Storm) to understand risk evolution.
- **AI-Augmented Analysis**: Integrated Generative AI to provide natural language explanations of risk drivers and recommend mitigation actions.
- **Model Benchmarking**: Transparency tools including Reliability Diagrams and Pinball Loss metrics to validate model accuracy.

## 📸 Interface Preview

### 1. Risk Dashboard (Live Monitor)
Real-time visualization of Load vs. Capacity with probabilistic "Fan Charts" showing P50, P90, and P99 tail risks.
![Dashboard Screenshot](./docs/images/dashboard.png)
*Above: The dashboard showing an "Extreme" risk event where P99 load exceeds capacity.*

### 2. Scenario Stress Lab
Interactive "What-If" analysis. Users can adjust temperature (-20°C) and wind speeds to see immediate impacts on grid stability.
![Scenario Lab Screenshot](./docs/images/scenario.png)

### 3. Historical Event Playback
Step-by-step replay of the 2021 Winter Storm, showing how GERT predicts failure hours before the blackout.
![Event Playback Screenshot](./docs/images/event.png)

## 🛠 Tech Stack

**Frontend**
- **Framework**: Next.js 14 (React 18)
- **Styling**: Tailwind CSS
- **Visualization**: Recharts (Composed Charts, Area Charts), Custom SVG Maps
- **Icons**: Lucide React

**Backend**
- **Framework**: FastAPI (Python)
- **Data Processing**: NumPy, Pydantic
- **AI Integration**: Google GenAI SDK (Gemini Models)
- **Rate Limiting**: Slowapi

## 🏗 Architecture

The system follows a decoupled architecture:
1.  **FastAPI Backend**: Handles statistical modeling, risk logic execution, and AI orchestration. It exposes a JSON API.
2.  **Next.js Frontend**: Consumes the API to render interactive dashboards and visualizations.

## 🚦 Getting Started

### Prerequisites
- Node.js 18+
- Python 3.9+

### Installation & Run

The project includes a startup script to launch both the backend and frontend services.

```bash
# 1. Install dependencies (First run only)
npm install
pip install -r requirements.txt

# 2. Start the application
./start.sh
```

- **Frontend**: Accessible at `http://localhost:3000`
- **Backend API Docs**: Accessible at `http://localhost:8000/docs`

## 🧠 Methodology

**Why Quantile Regression?**
Grid reliability relies on understanding the "tail risk"—the low-probability, high-impact events. Standard regression models (OLS) predict the mean, often underestimating the volatility seen during extreme weather. GERT predicts specific quantiles (e.g., the 99th percentile), providing a statistical upper bound for load demand that helps operators plan reserves more effectively.

**Risk Scoring**
The Risk Score is a function of the **Capacity Margin** (Available Generation - P99 Load).
- **Score 100**: P99 Load exceeds Capacity (Blackout likely).
- **Score 0**: Ample reserves available.

## 📄 License
MIT
