# ROLLIQ: Hardware Integration & Classroom Demonstration Guide

Low-Cost Wearable Edge-Intelligence System for Quantifying Human Bed-Mobility Patterns.

---

## 1. Hardware Architecture & Electrical Schematics

The ROLLIQ wearable sensing node is designed for positioning around the user's torso (via elastic thoracic strap).

### Components Bill of Materials (BOM)
- **Microcontroller**: ESP32 NodeMCU (30-pin, CP2102/CH340 USB)
- **Inertial Measurement Unit**: MPU6050 (6-axis accelerometer + gyroscope)
- **Wiring**: 4-wire Female-to-Female jumper ribbon (10–15 cm)
- **Power**: 5V Micro-USB cable or 3.7V LiPo battery via regulator

### Electrical Connections Table

| MPU6050 Pin | ESP32 Pin | Function | Notes |
|:---|:---|:---|:---|
| **VCC** | **3.3V** | Power Supply | ⚠️ Do NOT connect to 5V (protects ESP32 GPIO) |
| **GND** | **GND** | System Ground | Common reference ground |
| **SDA** | **GPIO 21** | I2C Data | Hardware I2C data bus (pull-up internal) |
| **SCL** | **GPIO 22** | I2C Clock | Hardware I2C clock line (400 kHz Fast-Mode) |
| **AD0** | **GND** | I2C Address Select | Address 0x68 (default) |
| **INT** | *Unconnected* | Data-Ready Interrupt | Polling at 50 Hz via micros() |

---

## 2. Signal Processing & Kinematics Architecture

### Accelerometer Full-Scale Range
- Configured to **±2g** ($16384 \text{ LSB/g}$).
- Optimal sensitivity for subtle postural settling without clipping bed-mobility movements.

### Gyroscope Full-Scale Range
- Configured to **±250°/s** ($131 \text{ LSB/(°/s)}$).
- Provides maximum resolution for natural turning angular velocity ($30\text{–}120\text{°/s}$).

### Exponential Moving Average (EMA) Low-Pass Filter
$$y[n] = \alpha \cdot x[n] + (1 - \alpha) \cdot y[n-1]$$
- Configured $\alpha = 0.10$ at $f_s = 50\text{ Hz}$.
- Cutoff frequency $f_c \approx 0.85\text{ Hz}$, effectively eliminating bed spring vibration and sensor jitter while faithfully transmitting voluntary gross body rolling.

### Orientation Estimation: Complementary Filter
$$\theta_{roll}[n] = 0.98 \cdot (\theta_{roll}[n-1] + \omega_x \cdot \Delta t) + 0.02 \cdot \arctan2(a_y, a_z)$$
$$\theta_{pitch}[n] = 0.98 \cdot (\theta_{pitch}[n-1] + \omega_y \cdot \Delta t) + 0.02 \cdot \arctan2(-a_x, \sqrt{a_y^2 + a_z^2})$$
- 98% weighting on gyroscope integration provides rapid, smooth response during dynamic rolling.
- 2% gravity vector anchor cancels long-term gyroscope bias drift during prolonged rest.

---

## 3. Firmware Flashing Guide

### Method A: PlatformIO (Recommended)
1. Open `rolliq/firmware` in VS Code with PlatformIO extension installed.
2. Edit `include/config.h` to specify your local Wi-Fi SSID, password, and your PC's IP address:
   ```cpp
   #define WIFI_SSID "Your_WiFi_Network"
   #define WIFI_PASSWORD "Your_Password"
   #define SERVER_HOST "192.168.1.100" // PC running backend
   #define SERVER_PORT 8000
   ```
3. Connect ESP32 via USB.
4. Click **PlatformIO: Upload** (`pio run -t upload`) and **Monitor** (`pio device monitor`).
5. Observe calibration printout and 50 Hz transmission loop.

### Method B: Arduino IDE
1. Install **ESP32 by Espressif Systems** via Boards Manager.
2. Install **ArduinoJson** (v6.x) via Library Manager.
3. Open `firmware/src/main.cpp`.
4. Select board: `ESP32 Dev Module`.
5. Upload to board.

---

## 4. Complete Step-by-Step Classroom Demonstration Script

Follow this sequence for an end-to-end presentation:

### Step 1: Launch Backend and Frontend
Double click `start_all.bat` in the `rolliq` directory.
- Backend runs at `http://localhost:8000`
- Frontend runs at `http://localhost:3000`

### Step 2: User Cohort & Baseline Inspection
1. Navigate to **User Profiles** (`/users`).
2. Notice the pre-seeded clinical subject **"Eleanor Vance (Demo)"**, age group **Elderly**.
3. Point out that Eleanor already has 4 completed sessions logged over two weeks, establishing a personalized baseline profile.
4. Navigate to **Mobility Analytics** (`/analytics`) to show:
   - Baseline Transition Duration: ~2.8s
   - Baseline Smoothness (Jerk): ~2.6
   - Bilateral turning symmetry chart and RMI history.

### Step 3: Live Telemetry & Simulation Demo
1. Navigate to **Live Monitor** (`/monitor`).
2. In the left panel, notice the **Sensor Simulator** panel with 10 scenarios.
3. Select **"Normal Rolling"** scenario and click **Start Simulation**.
4. Observe the live stream:
   - The **Torso Orientation Silhouette** smoothly tilts from Supine to Left Lateral to Right Lateral.
   - The **Real-Time Accelerometer Chart** displays the tri-axial gravity transitions.
   - The **Real-Time Gyroscope Chart** displays the bell-curve rotational angular velocity pulses.
   - The **Signal Integrity** meter reflects 50 Hz stream stability.
5. Watch the **Detected Movement Sequence** log new classified movements (`left_roll`, `right_roll`) in real-time!

### Step 4: Scenario Variations
1. Switch scenario to **"Supine-to-Sitting Transition"**:
   - Notice the pitch axis elevation ($a_x$ elevates to $+0.88\text{g}$) and posture switches to **Sitting Upright**.
2. Switch scenario to **"Sensor Disconnection"**:
   - Observe the system trigger a **"Sensor Stream Interrupted"** notification alert after 10s without packets.
3. Switch scenario to **"Noisy Signals"**:
   - Observe signal integrity meter degrade and filter smoothing in action.

### Step 5: Finalize Session & Analyze Movement Depth
1. Click **Finalize / Stop Session**.
2. Observe the calculated **ROLLIQ Mobility Index (RMI)** update on the Dashboard (`/`).
3. Click any logged movement event to open **Individual Movement Analysis** (`/movement/:id`):
   - Review the raw acceleration and gyroscope waveforms.
   - Review the kinematic jerk score, peak angular velocity, and the **Classifier Decision Criteria** explaining exactly why the event was classified.

### Step 6: Review Personal Baseline Shift
1. Navigate back to **Mobility Analytics** (`/analytics`).
2. Inspect the **Personal Baseline Deviation Profile** table:
   - Notice the exact z-score deviations ($\sigma$) and whether changes indicate normal variation or a notable shift requiring attention.

---

## 5. Engineering Architecture & Directory Structure

```
rolliq/
├── start_all.bat                  # One-click startup for both services
├── run_backend.bat                # Standalone FastAPI launcher
├── run_frontend.bat               # Standalone Vite launcher
├── README.md                      # Overview and API documentation
├── HARDWARE_AND_DEMO_GUIDE.md     # Wiring, kinematics, and presentation guide
├── backend/
│   ├── main.py                    # FastAPI application & static mount
│   ├── config.py                  # Thresholds, weights & sampling rates
│   ├── database.py                # Async SQLite SQLAlchemy session factory
│   ├── models.py                  # Relational ORM entities
│   ├── schemas.py                 # Pydantic validation contracts
│   ├── seed_demo_data.py          # Clinical demo profile & baseline seeder
│   ├── routers/                   # REST & WebSocket route handlers
│   │   ├── sensor.py              # 50 Hz telemetry ingestion & WebSocket
│   │   ├── sessions.py            # Session lifecycle & movement query
│   │   ├── users.py               # Multi-user profile management
│   │   ├── devices.py             # ESP32 hardware registration & calibration
│   │   ├── analytics.py           # Recovery trends & baseline comparisons
│   │   ├── alerts.py              # Alert notifications & caregiver read-status
│   │   └── simulation.py          # 10-scenario simulation controller
│   ├── services/                  # Core algorithms
│   │   ├── signal_processor.py    # Butterworth LPF, quality & orientation
│   │   ├── posture_detector.py    # Gravity decomposition & hysteresis
│   │   ├── movement_classifier.py # Dynamic threshold & kinematic segmentation
│   │   ├── rmi_calculator.py      # ROLLIQ Mobility Index (6-component score)
│   │   ├── baseline_engine.py     # Personal baseline & z-score deviations
│   │   ├── alert_service.py       # Prolonged posture & anomaly alerts
│   │   └── simulation_engine.py   # Realistic 10-scenario 50 Hz IMU generator
│   └── tests/                     # 16 automated tests (all passing)
│       ├── test_classification.py
│       ├── test_rmi.py
│       ├── test_baseline.py
│       ├── test_simulation.py
│       └── test_api.py
├── frontend/
│   ├── src/
│   │   ├── App.tsx                # Client-side router & layout
│   │   ├── main.tsx               # Root entry
│   │   ├── index.css              # Midnight navy design tokens & styles
│   │   ├── types/index.ts         # Strict TypeScript domain interfaces
│   │   ├── store/appStore.tsx     # Context & reducer state management
│   │   ├── api/                   # REST client & WebSocket manager
│   │   ├── components/            # Reusable UI widgets & charts
│   │   └── pages/                 # 7 complete application views
│   └── dist/                      # Pre-compiled high-performance bundle
└── firmware/
    ├── platformio.ini             # ESP32 build specifications
    ├── include/                   # Driver headers, WiFi manager & filters
    └── src/main.cpp               # 50 Hz real-time telemetry loop
```
