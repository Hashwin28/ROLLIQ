# ROLLIQ — Smart Bed-Mobility and Recovery Monitoring System

<p align="center">
  <strong>Low-cost wearable edge-intelligence for quantifying human bed-mobility patterns</strong>
</p>

---

## Overview

ROLLIQ captures, analyses, and quantifies human bed-mobility patterns using an ESP32 + MPU6050 wearable sensor positioned around the user's torso. It detects rolling movements, postural transitions, and generates personalized mobility analytics.

> **Note:** ROLLIQ is an experimental engineering prototype. It is not a clinically validated diagnostic or medical decision-making system.

## Architecture

```
┌──────────────┐     HTTP/WS      ┌──────────────┐     HTTP      ┌──────────────┐
│   ESP32 +    │ ───────────────▶ │   FastAPI     │ ◀──────────▶ │    React     │
│   MPU6050    │   Sensor Data    │   Backend     │   REST API   │   Frontend   │
│  (Wearable)  │                  │  + SQLite DB  │   + WS       │  (Vite+TS)   │
└──────────────┘                  └──────────────┘               └──────────────┘
                                        │
                                  ┌─────┴─────┐
                                  │ Simulation │
                                  │  Engine    │
                                  └───────────┘
```

## Features

- **Real-time sensor monitoring** — Live accelerometer and gyroscope visualization
- **Movement classification** — Detects rolls, turns, sit-up/lie-down transitions
- **Posture detection** — Supine, lateral, prone, sitting with hysteresis
- **ROLLIQ Mobility Index (RMI)** — Personalized composite mobility score
- **Personal baseline tracking** — Individual movement baselines with deviation detection
- **Recovery analytics** — Session-over-session trend analysis
- **Simulation mode** — 10 predefined scenarios for demo without hardware
- **Alert system** — Configurable alerts for prolonged posture, baseline deviations
- **Multi-user support** — Independent profiles with isolated data

## Hardware Requirements

| Component | Description |
|-----------|-------------|
| ESP32 NodeMCU | 30-pin development board |
| MPU6050 | 6-axis accelerometer + gyroscope breakout |
| Jumper wires | 4× female-to-female |
| USB cable | Micro-USB for ESP32 |

### Wiring Diagram

```
MPU6050          ESP32
────────         ─────
VCC     ───────▶ 3.3V
GND     ───────▶ GND
SDA     ───────▶ GPIO 21
SCL     ───────▶ GPIO 22
INT     ───────  (not connected)
```

> **⚠️ Warning:** Connect VCC to 3.3V, not 5V. The ESP32 GPIO pins are not 5V tolerant.

## Quick Start

### Prerequisites

- **Node.js** ≥ 18.x
- **Python** ≥ 3.10
- **npm** ≥ 9.x
- **pip** (Python package manager)
- (Optional) **PlatformIO** for ESP32 firmware upload

### 1. Clone and Navigate

```bash
cd rolliq
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
python main.py
```

The backend runs at `http://localhost:8000`.

API documentation is available at `http://localhost:8000/docs`.

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:3000`.

### 4. ESP32 Firmware (Optional)

Requires [PlatformIO](https://platformio.org/).

```bash
cd firmware
# Edit include/config.h with your WiFi credentials and backend IP
pio run --target upload
pio device monitor
```

### 5. Using Simulation Mode

If no ESP32 hardware is available:

1. Open the app at `http://localhost:3000`
2. Create a user profile
3. Navigate to **Live Monitoring**
4. Click **Simulation Mode** in the sidebar
5. Select a scenario (e.g., "Normal Rolling")
6. Start the simulation
7. Watch real-time sensor data, posture detection, and movement classification

## Simulation Scenarios

| # | Scenario | Description |
|---|----------|-------------|
| 1 | Normal Rolling | Periodic left-right rolls with pauses |
| 2 | Left-Right Turning | Alternating turns with rest periods |
| 3 | Supine to Sitting | Multiple sit-up transitions |
| 4 | Sitting to Supine | Multiple lie-down transitions |
| 5 | Minor Movements | Small adjustments, no full transitions |
| 6 | Prolonged Immobility | Mostly static, very rare movement |
| 7 | Irregular Movement | Varied timing and mixed types |
| 8 | Sensor Disconnect | Normal data then simulated disconnection |
| 9 | Noisy Signals | High noise overlay on normal movements |
| 10 | Incomplete Transition | Movements that start but don't complete |

## Project Structure

```
rolliq/
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── main.py                    # FastAPI application entry
│   ├── config.py                  # Configuration and thresholds
│   ├── database.py                # SQLAlchemy setup
│   ├── models.py                  # ORM models
│   ├── schemas.py                 # Pydantic schemas
│   ├── routers/                   # API route handlers
│   │   ├── sensor.py              # Sensor data ingestion
│   │   ├── sessions.py            # Session management
│   │   ├── users.py               # User profiles
│   │   ├── devices.py             # Device management
│   │   ├── analytics.py           # Analytics queries
│   │   ├── alerts.py              # Alert management
│   │   └── simulation.py          # Simulation control
│   ├── services/                  # Business logic
│   │   ├── movement_classifier.py # Movement event classification
│   │   ├── posture_detector.py    # Posture detection with hysteresis
│   │   ├── rmi_calculator.py      # Mobility Index calculation
│   │   ├── baseline_engine.py     # Personal baseline management
│   │   ├── signal_processor.py    # Signal filtering and quality
│   │   ├── alert_service.py       # Alert generation
│   │   └── simulation_engine.py   # Simulated sensor data
│   ├── websocket/
│   │   └── manager.py             # WebSocket connection management
│   └── tests/                     # Automated tests
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── App.tsx                # Router and layout
│   │   ├── api/                   # API client and WebSocket
│   │   ├── components/            # Reusable UI components
│   │   ├── hooks/                 # Custom React hooks
│   │   ├── pages/                 # Application pages
│   │   ├── store/                 # State management
│   │   └── types/                 # TypeScript interfaces
│   └── public/
└── firmware/
    ├── platformio.ini
    ├── src/
    │   └── main.cpp               # ESP32 firmware
    └── include/
        ├── config.h               # Hardware configuration
        ├── mpu6050_handler.h       # Sensor interface
        ├── wifi_manager.h          # WiFi management
        ├── data_sender.h           # HTTP/WS data transmission
        └── sensor_filter.h         # Signal filtering
```

## API Documentation

Once the backend is running, visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/users` | Create user profile |
| POST | `/api/sessions` | Start monitoring session |
| POST | `/api/sensor/data` | Ingest sensor readings |
| WS | `/ws/sensor/{session_id}` | Real-time sensor stream |
| GET | `/api/sessions/{id}/movements` | List detected movements |
| GET | `/api/analytics/rmi-history/{user_id}` | RMI trend data |
| POST | `/api/simulation/start` | Start simulation |

## ROLLIQ Mobility Index (RMI)

The RMI is a composite score (0–100) combining:

| Component | Weight | Measures |
|-----------|--------|----------|
| Duration | 20% | Transition time vs. optimal range |
| Smoothness | 20% | Movement jerk (lower = smoother) |
| Velocity | 15% | Angular velocity profile |
| Stability | 15% | Post-transition steadiness |
| Completion | 15% | Successful movement ratio |
| Consistency | 15% | Repeatability across attempts |

> The RMI is an experimental engineering metric, not a clinically validated score.

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, Vite, TypeScript, Tailwind CSS, Framer Motion, Recharts, Lucide |
| Backend | Python, FastAPI, Uvicorn, Pydantic, SQLAlchemy |
| Database | SQLite |
| Signal Processing | NumPy, SciPy, scikit-learn |
| Hardware | ESP32, MPU6050, Arduino framework |
| Communication | REST API, WebSocket |

## Development

### Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ROLLIQ_DB_URL` | `sqlite:///./rolliq.db` | Database connection |
| `ROLLIQ_SAMPLING_RATE` | `50` | Expected sensor Hz |
| `ROLLIQ_HOST` | `0.0.0.0` | Backend host |
| `ROLLIQ_PORT` | `8000` | Backend port |

## License

This project is for educational and research purposes.

## Disclaimer

ROLLIQ is an experimental prototype designed for engineering demonstration and educational use. It is not a medical device and should not be used for clinical diagnosis, treatment decisions, or medical monitoring. All mobility scores and analytics are experimental engineering metrics.
