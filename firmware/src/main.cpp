// =============================================================================
// ROLLIQ Firmware — main.cpp
// Complete implementation of all modules for the bed-mobility monitoring
// system running on ESP32 + MPU6050.
//
// Architecture overview:
//   1.  setup() — serial, LED, WiFi, I2C, MPU6050 init + calibration, WDT.
//   2.  loop()  — hard-timed at SAMPLING_FREQ_HZ:
//       a.  Read raw 6-axis data from MPU6050.
//       b.  Apply gyro bias correction + scale to physical units.
//       c.  Apply per-axis EMA low-pass filter.
//       d.  Compute roll/pitch via complementary filter.
//       e.  Push into send buffer.
//       f.  When buffer is full → batch-send to backend (HTTP or WS).
//       g.  Maintain WiFi connection + status LED.
//       h.  Feed watchdog.
// =============================================================================

#include <Arduino.h>
#include <Wire.h>
#include <esp_task_wdt.h>

#include "config.h"
#include "sensor_filter.h"
#include "mpu6050_handler.h"
#include "wifi_manager.h"
#include "data_sender.h"

// *****************************************************************************
// ██  MPU6050Handler  —  FULL IMPLEMENTATION
// *****************************************************************************

// ---------------------------------------------------------------------------
// Constructor
// ---------------------------------------------------------------------------
MPU6050Handler::MPU6050Handler()
    : _roll(0.0f), _pitch(0.0f),
      _orientationInitialised(false), _lastOrientationUs(0),
      _filter(LPF_ALPHA)
{
    _cal  = {0, 0, 0, 0, 0, 0, false};
    _health = {0, 0, 0, true};
}

// ---------------------------------------------------------------------------
// begin() — power-on, verify, configure MPU6050
// ---------------------------------------------------------------------------
bool MPU6050Handler::begin() {
    // Start I2C with configured pins and clock speed.
    Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
    Wire.setClock(I2C_CLOCK_HZ);
    delay(100);  // Let the bus stabilise after power-on.

    // Wake the MPU6050 — clear the SLEEP bit in PWR_MGMT_1.
    // Also select PLL with X-axis gyro reference (CLKSEL = 1) for better
    // clock stability than the internal 8 MHz oscillator.
    if (!writeRegister(MPU6050_REG_PWR_MGMT_1, 0x01)) {
        Serial.println(F("[MPU] ERROR: Cannot write PWR_MGMT_1"));
        return false;
    }
    delay(100);

    // Verify sensor identity.
    if (!verifySensor()) {
        return false;
    }

    // ---- Configure sample-rate divider ----
    // Internal sample rate (with DLPF enabled) is 1 kHz.
    // Divider = (1000 / desired_Hz) − 1 = 19 for 50 Hz.
    writeRegister(MPU6050_REG_SMPLRT_DIV, (uint8_t)(1000 / SAMPLING_FREQ_HZ - 1));

    // ---- Digital Low-Pass Filter (DLPF) ----
    // CONFIG register DLPF_CFG = 3 → bandwidth ~44 Hz accel, ~42 Hz gyro.
    // This is a hardware anti-aliasing filter before our software EMA.
    writeRegister(MPU6050_REG_CONFIG, 0x03);

    // ---- Full-scale ranges ----
    // Gyro:  FS_SEL = 0 → ±250 °/s  (highest resolution for slow movement).
    writeRegister(MPU6050_REG_GYRO_CONFIG,  (GYRO_FS_SEL  << 3));
    // Accel: AFS_SEL = 0 → ±2 g.
    writeRegister(MPU6050_REG_ACCEL_CONFIG, (ACCEL_FS_SEL << 3));

    // Reset filter state.
    _filter.reset();
    _orientationInitialised = false;

    // Initialise health tracker.
    _health.consecutive_fails = 0;
    _health.last_good_read_ms = millis();
    _health.last_reset_ms     = 0;
    _health.healthy           = true;

    Serial.println(F("[MPU] Initialisation complete."));
    return true;
}

// ---------------------------------------------------------------------------
// verifySensor() — WHO_AM_I register check
// ---------------------------------------------------------------------------
bool MPU6050Handler::verifySensor() {
    uint8_t whoAmI = readRegister(MPU6050_REG_WHO_AM_I);
    if (whoAmI != MPU6050_WHO_AM_I_VAL) {
        Serial.printf("[MPU] WHO_AM_I mismatch: got 0x%02X, expected 0x%02X\n",
                      whoAmI, MPU6050_WHO_AM_I_VAL);
        return false;
    }
    Serial.println(F("[MPU] WHO_AM_I verified OK."));
    return true;
}

// ---------------------------------------------------------------------------
// calibrate() — stationary calibration
//
// The sensor must be resting flat and still.  We collect CALIBRATION_SAMPLES
// readings, average them, and store the offsets.
//
// For the accelerometer we expect (0, 0, +1 g) at rest, so we subtract the
// mean and then add 1 g back on the Z axis.
//
// For the gyroscope we expect (0, 0, 0), so the mean is the bias.
// ---------------------------------------------------------------------------
bool MPU6050Handler::calibrate() {
    Serial.println(F("[MPU] Starting calibration — keep sensor STILL and LEVEL..."));

    double sumAx = 0, sumAy = 0, sumAz = 0;
    double sumGx = 0, sumGy = 0, sumGz = 0;
    uint32_t goodSamples = 0;

    for (uint32_t i = 0; i < CALIBRATION_SAMPLES; ++i) {
        int16_t ax, ay, az, gx, gy, gz;
        if (readRaw6Axis(ax, ay, az, gx, gy, gz)) {
            sumAx += ax;
            sumAy += ay;
            sumAz += az;
            sumGx += gx;
            sumGy += gy;
            sumGz += gz;
            ++goodSamples;
        }
        delay(SAMPLE_PERIOD_MS);  // Maintain sampling cadence.

        // Print progress every 100 samples.
        if ((i + 1) % 100 == 0) {
            Serial.printf("[MPU] Calibration %u / %u\n", i + 1,
                          (uint32_t)CALIBRATION_SAMPLES);
        }
    }

    if (goodSamples < CALIBRATION_SAMPLES / 2) {
        Serial.println(F("[MPU] Calibration FAILED — too many bad reads."));
        return false;
    }

    // Compute mean offsets in raw LSB units.
    _cal.accel_offset_x = (float)(sumAx / goodSamples);
    _cal.accel_offset_y = (float)(sumAy / goodSamples);
    // Z-axis at rest reads ~ +ACCEL_SENSITIVITY (1 g).  We want the offset
    // such that (raw − offset) / sensitivity = 0 for X/Y and 1 for Z.
    _cal.accel_offset_z = (float)(sumAz / goodSamples) - ACCEL_SENSITIVITY;

    _cal.gyro_offset_x  = (float)(sumGx / goodSamples);
    _cal.gyro_offset_y  = (float)(sumGy / goodSamples);
    _cal.gyro_offset_z  = (float)(sumGz / goodSamples);
    _cal.calibrated     = true;

    Serial.println(F("[MPU] Calibration complete."));
    Serial.printf("  Accel offsets (LSB): X=%.1f  Y=%.1f  Z=%.1f\n",
                  _cal.accel_offset_x, _cal.accel_offset_y, _cal.accel_offset_z);
    Serial.printf("  Gyro  offsets (LSB): X=%.1f  Y=%.1f  Z=%.1f\n",
                  _cal.gyro_offset_x, _cal.gyro_offset_y, _cal.gyro_offset_z);
    return true;
}

// ---------------------------------------------------------------------------
// readSensor() — read, correct, filter, estimate orientation
// ---------------------------------------------------------------------------
bool MPU6050Handler::readSensor(SensorData &out) {
    out.valid = false;

    // --- 1. Read raw 6-axis data ---
    if (!readRaw6Axis(out.raw_ax, out.raw_ay, out.raw_az,
                      out.raw_gx, out.raw_gy, out.raw_gz)) {
        _health.consecutive_fails++;
        if (_health.consecutive_fails >= MAX_CONSECUTIVE_FAILS) {
            _health.healthy = false;
            // Attempt soft reset if cooldown has elapsed.
            if (millis() - _health.last_reset_ms > SENSOR_RESET_COOLDOWN_MS) {
                Serial.println(F("[MPU] Too many failures — attempting soft reset."));
                softReset();
            }
        }
        return false;
    }

    // Successful read — update health.
    _health.consecutive_fails = 0;
    _health.last_good_read_ms = millis();
    _health.healthy           = true;

    out.timestamp_ms = millis();

    // --- 2. Apply calibration bias correction and convert to physical units ---
    // Subtract the calibration bias (in raw LSB) then divide by sensitivity.
    out.ax_g   = ((float)out.raw_ax - _cal.accel_offset_x) / ACCEL_SENSITIVITY;
    out.ay_g   = ((float)out.raw_ay - _cal.accel_offset_y) / ACCEL_SENSITIVITY;
    out.az_g   = ((float)out.raw_az - _cal.accel_offset_z) / ACCEL_SENSITIVITY;

    out.gx_dps = ((float)out.raw_gx - _cal.gyro_offset_x)  / GYRO_SENSITIVITY;
    out.gy_dps = ((float)out.raw_gy - _cal.gyro_offset_y)  / GYRO_SENSITIVITY;
    out.gz_dps = ((float)out.raw_gz - _cal.gyro_offset_z)  / GYRO_SENSITIVITY;

    // --- 3. Apply low-pass EMA filter to each axis ---
    out.filt_ax = _filter.ax.update(out.ax_g);
    out.filt_ay = _filter.ay.update(out.ay_g);
    out.filt_az = _filter.az.update(out.az_g);
    out.filt_gx = _filter.gx.update(out.gx_dps);
    out.filt_gy = _filter.gy.update(out.gy_dps);
    out.filt_gz = _filter.gz.update(out.gz_dps);

    // --- 4. Complementary filter for orientation (roll & pitch) ---
    //
    // The accelerometer gives a noisy but drift-free gravity reference:
    //   roll_acc  = atan2(ay, az)
    //   pitch_acc = atan2(−ax, √(ay² + az²))
    //
    // The gyroscope gives smooth short-term rates but drifts over time.
    //
    // Complementary filter fuses both:
    //   angle = α · (angle + gyro · dt) + (1 − α) · accel_angle
    //
    // With α = 0.98, short-term noise is suppressed while long-term drift
    // is bounded by the accelerometer.

    unsigned long nowUs = micros();
    if (!_orientationInitialised) {
        // Seed orientation from accelerometer alone on first sample.
        _roll  = atan2f(out.filt_ay, out.filt_az) * 180.0f / M_PI;
        _pitch = atan2f(-out.filt_ax,
                        sqrtf(out.filt_ay * out.filt_ay +
                              out.filt_az * out.filt_az)) * 180.0f / M_PI;
        _orientationInitialised = true;
        _lastOrientationUs      = nowUs;
    } else {
        float dt = (float)(nowUs - _lastOrientationUs) / 1000000.0f;
        _lastOrientationUs = nowUs;

        // Clamp dt to avoid spikes if there was a long pause.
        if (dt > 0.1f) dt = 0.1f;

        // Accelerometer-derived angles.
        float rollAcc  = atan2f(out.filt_ay, out.filt_az) * 180.0f / M_PI;
        float pitchAcc = atan2f(-out.filt_ax,
                                sqrtf(out.filt_ay * out.filt_ay +
                                      out.filt_az * out.filt_az)) * 180.0f / M_PI;

        // Fuse: gyro integration + accelerometer correction.
        _roll  = COMP_FILTER_ALPHA * (_roll  + out.filt_gx * dt) +
                 (1.0f - COMP_FILTER_ALPHA) * rollAcc;
        _pitch = COMP_FILTER_ALPHA * (_pitch + out.filt_gy * dt) +
                 (1.0f - COMP_FILTER_ALPHA) * pitchAcc;
    }

    out.roll  = _roll;
    out.pitch = _pitch;
    out.valid = true;
    return true;
}

// ---------------------------------------------------------------------------
// softReset() — cycle the sensor through sleep and re-init
// ---------------------------------------------------------------------------
bool MPU6050Handler::softReset() {
    _health.last_reset_ms = millis();
    Serial.println(F("[MPU] Soft-resetting sensor..."));

    // Write DEVICE_RESET bit (bit 7) of PWR_MGMT_1.
    writeRegister(MPU6050_REG_PWR_MGMT_1, 0x80);
    delay(150);

    // Re-initialise.
    bool ok = begin();
    if (ok && _cal.calibrated) {
        // Restore previous calibration (don't force user to hold still again).
        Serial.println(F("[MPU] Re-applied previous calibration offsets."));
    }
    _filter.reset();
    _orientationInitialised = false;
    return ok;
}

// ---------------------------------------------------------------------------
// I2C register helpers
// ---------------------------------------------------------------------------
bool MPU6050Handler::writeRegister(uint8_t reg, uint8_t val) {
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(reg);
    Wire.write(val);
    return (Wire.endTransmission() == 0);
}

uint8_t MPU6050Handler::readRegister(uint8_t reg) {
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(reg);
    if (Wire.endTransmission(false) != 0) return 0x00;
    Wire.requestFrom((uint8_t)MPU6050_ADDR, (uint8_t)1);
    if (Wire.available()) return Wire.read();
    return 0x00;
}

bool MPU6050Handler::readRegisters(uint8_t startReg, uint8_t *buffer,
                                   uint8_t count) {
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(startReg);
    if (Wire.endTransmission(false) != 0) return false;
    uint8_t received = Wire.requestFrom((uint8_t)MPU6050_ADDR, count);
    if (received != count) return false;
    for (uint8_t i = 0; i < count; ++i) {
        buffer[i] = Wire.read();
    }
    return true;
}

// ---------------------------------------------------------------------------
// readRaw6Axis() — burst-read accel + temp + gyro (14 bytes starting 0x3B)
// ---------------------------------------------------------------------------
bool MPU6050Handler::readRaw6Axis(int16_t &ax, int16_t &ay, int16_t &az,
                                  int16_t &gx, int16_t &gy, int16_t &gz) {
    uint8_t buf[14];
    if (!readRegisters(MPU6050_REG_ACCEL_XOUT_H, buf, 14)) {
        return false;
    }
    // Registers are big-endian: high byte first.
    ax = (int16_t)((buf[0]  << 8) | buf[1]);
    ay = (int16_t)((buf[2]  << 8) | buf[3]);
    az = (int16_t)((buf[4]  << 8) | buf[5]);
    // buf[6..7] = temperature — skipped.
    gx = (int16_t)((buf[8]  << 8) | buf[9]);
    gy = (int16_t)((buf[10] << 8) | buf[11]);
    gz = (int16_t)((buf[12] << 8) | buf[13]);
    return true;
}


// *****************************************************************************
// ██  WiFiManager  —  FULL IMPLEMENTATION
// *****************************************************************************

WiFiManager::WiFiManager()
    : _state(WiFiState::DISCONNECTED),
      _lastAttemptMs(0), _backoffMs(WIFI_RECONNECT_MIN_MS), _retryCount(0)
{}

void WiFiManager::startConnection() {
    WiFi.mode(WIFI_STA);
    WiFi.setAutoReconnect(false);  // We manage reconnection ourselves.
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    _state         = WiFiState::CONNECTING;
    _lastAttemptMs = millis();
    Serial.printf("[WiFi] Connecting to \"%s\"...\n", WIFI_SSID);
}

bool WiFiManager::begin() {
    startConnection();

    // Block until connected or timeout.
    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED &&
           millis() - start < WIFI_CONNECT_TIMEOUT_MS) {
        delay(250);
        Serial.print('.');
    }
    Serial.println();

    if (WiFi.status() == WL_CONNECTED) {
        _state      = WiFiState::CONNECTED;
        _backoffMs  = WIFI_RECONNECT_MIN_MS;
        _retryCount = 0;
        Serial.printf("[WiFi] Connected — IP: %s  RSSI: %d dBm\n",
                      WiFi.localIP().toString().c_str(), WiFi.RSSI());
        return true;
    }

    Serial.println(F("[WiFi] Initial connection FAILED — will keep retrying."));
    _state = WiFiState::DISCONNECTED;
    return false;
}

void WiFiManager::update() {
    switch (_state) {
        case WiFiState::CONNECTED:
            if (WiFi.status() != WL_CONNECTED) {
                Serial.println(F("[WiFi] Connection lost!"));
                _state     = WiFiState::RECONNECTING;
                _backoffMs = WIFI_RECONNECT_MIN_MS;
                _retryCount = 0;
            }
            break;

        case WiFiState::DISCONNECTED:
        case WiFiState::RECONNECTING:
            if (millis() - _lastAttemptMs >= _backoffMs) {
                Serial.printf("[WiFi] Reconnect attempt #%u (backoff %lu ms)\n",
                              _retryCount + 1, _backoffMs);
                WiFi.disconnect(true);
                delay(50);
                startConnection();
                _state = WiFiState::CONNECTING;
            }
            break;

        case WiFiState::CONNECTING:
            if (WiFi.status() == WL_CONNECTED) {
                _state      = WiFiState::CONNECTED;
                _backoffMs  = WIFI_RECONNECT_MIN_MS;
                _retryCount = 0;
                Serial.printf("[WiFi] Reconnected — IP: %s\n",
                              WiFi.localIP().toString().c_str());
            } else if (millis() - _lastAttemptMs >= WIFI_CONNECT_TIMEOUT_MS) {
                // Timed out — back off and retry later.
                _retryCount++;
                _state     = WiFiState::RECONNECTING;
                // Exponential backoff: double each time, cap at max.
                _backoffMs = min(_backoffMs * 2, (unsigned long)WIFI_RECONNECT_MAX_MS);
                _lastAttemptMs = millis();
            }
            break;
    }
}

uint16_t WiFiManager::getLEDBlinkInterval() const {
    switch (_state) {
        case WiFiState::CONNECTING:
        case WiFiState::RECONNECTING:
            return LED_BLINK_WIFI_CONNECTING;
        case WiFiState::CONNECTED:
            return LED_BLINK_WIFI_CONNECTED;
        case WiFiState::DISCONNECTED:
        default:
            return LED_BLINK_ERROR;
    }
}


// *****************************************************************************
// ██  DataSender  —  FULL IMPLEMENTATION
// *****************************************************************************

DataSender *DataSender::_instance = nullptr;

DataSender::DataSender()
    : _bufferIndex(0), _packetSeq(0),
      _wsConnected(false), _useWebSocket(USE_WEBSOCKET)
{
    _instance = this;
}

void DataSender::begin() {
    if (_useWebSocket) {
        initWebSocket();
    }
}

void DataSender::initWebSocket() {
    _ws.begin(SERVER_IP, SERVER_PORT, WS_ENDPOINT);
    _ws.onEvent(wsEventCallback);
    _ws.setReconnectInterval(5000);
    Serial.println(F("[WS] WebSocket client initialised."));
}

void DataSender::wsEventCallback(WStype_t type, uint8_t *payload, size_t length) {
    if (_instance) {
        _instance->handleWSEvent(type, payload, length);
    }
}

void DataSender::handleWSEvent(WStype_t type, uint8_t *payload, size_t length) {
    switch (type) {
        case WStype_DISCONNECTED:
            _wsConnected = false;
            Serial.println(F("[WS] Disconnected."));
            break;
        case WStype_CONNECTED:
            _wsConnected = true;
            Serial.printf("[WS] Connected to ws://%s:%d%s\n",
                          SERVER_IP, SERVER_PORT, WS_ENDPOINT);
            break;
        case WStype_TEXT:
            // Server acknowledgement or command — log it.
            Serial.printf("[WS] Received: %s\n", payload);
            break;
        case WStype_ERROR:
            Serial.println(F("[WS] Error event."));
            break;
        default:
            break;
    }
}

void DataSender::loop() {
    if (_useWebSocket) {
        _ws.loop();
    }
}

bool DataSender::bufferReading(const SensorData &data, bool sensorHealthy,
                                float samplingRate) {
    if (_bufferIndex >= DATA_BUFFER_SIZE) {
        // Buffer overflow protection — discard oldest by flushing first.
        Serial.println(F("[TX] Buffer overflow — auto-flushing."));
        flush();
    }
    _buffer[_bufferIndex]      = data;
    _healthFlags[_bufferIndex] = sensorHealthy;
    _sampleRates[_bufferIndex] = samplingRate;
    _bufferIndex++;
    return (_bufferIndex >= DATA_BUFFER_SIZE);
}

bool DataSender::flush() {
    if (_bufferIndex == 0) return true;  // Nothing to send.

    bool ok = false;
    if (_useWebSocket && _wsConnected) {
        ok = sendWebSocket();
    }
    if (!ok) {
        // Fall back to HTTP if WS failed or is disabled.
        ok = sendHTTP();
    }

    if (ok) {
        _packetSeq++;
        _bufferIndex = 0;
        Serial.printf("[TX] Batch #%u sent (%u readings).\n",
                      _packetSeq, DATA_BUFFER_SIZE);
    } else {
        Serial.println(F("[TX] Send FAILED — data remains in buffer."));
    }
    return ok;
}

// ---------------------------------------------------------------------------
// buildJSON() — serialise the buffer into a JSON document
// ---------------------------------------------------------------------------
void DataSender::buildJSON(DynamicJsonDocument &doc) {
    doc["device_id"]       = DEVICE_ID;
    doc["firmware"]        = FIRMWARE_VERSION;
    doc["packet_sequence"] = _packetSeq;
    doc["batch_size"]      = _bufferIndex;

    JsonArray readings = doc.createNestedArray("readings");
    for (uint16_t i = 0; i < _bufferIndex; ++i) {
        JsonObject r = readings.createNestedObject();
        r["ts"]    = _buffer[i].timestamp_ms;
        r["ax"]    = serialized(String(_buffer[i].filt_ax, 4));
        r["ay"]    = serialized(String(_buffer[i].filt_ay, 4));
        r["az"]    = serialized(String(_buffer[i].filt_az, 4));
        r["gx"]    = serialized(String(_buffer[i].filt_gx, 4));
        r["gy"]    = serialized(String(_buffer[i].filt_gy, 4));
        r["gz"]    = serialized(String(_buffer[i].filt_gz, 4));
        r["roll"]  = serialized(String(_buffer[i].roll,  2));
        r["pitch"] = serialized(String(_buffer[i].pitch, 2));
        r["health"]        = _healthFlags[i] ? "OK" : "DEGRADED";
        r["sampling_rate"] = serialized(String(_sampleRates[i], 1));
    }
}

// ---------------------------------------------------------------------------
// sendHTTP() — POST the JSON payload to the backend
// ---------------------------------------------------------------------------
bool DataSender::sendHTTP() {
    HTTPClient http;
    String url = String("http://") + SERVER_IP + ":" + String(SERVER_PORT) +
                 HTTP_ENDPOINT;

    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(HTTP_TIMEOUT_MS);

    DynamicJsonDocument doc(JSON_DOC_SIZE);
    buildJSON(doc);

    String payload;
    serializeJson(doc, payload);

    int httpCode = http.POST(payload);
    bool success = (httpCode >= 200 && httpCode < 300);

    if (!success) {
        Serial.printf("[HTTP] POST failed — code %d\n", httpCode);
        if (httpCode < 0) {
            Serial.printf("[HTTP] Error: %s\n", http.errorToString(httpCode).c_str());
        }
    }

    http.end();
    return success;
}

// ---------------------------------------------------------------------------
// sendWebSocket() — push the JSON payload over the active WS connection
// ---------------------------------------------------------------------------
bool DataSender::sendWebSocket() {
    if (!_wsConnected) return false;

    DynamicJsonDocument doc(JSON_DOC_SIZE);
    buildJSON(doc);

    String payload;
    serializeJson(doc, payload);

    bool ok = _ws.sendTXT(payload);
    if (!ok) {
        Serial.println(F("[WS] sendTXT failed."));
    }
    return ok;
}


// *****************************************************************************
// ██  GLOBAL OBJECTS & STATE
// *****************************************************************************

static MPU6050Handler  mpu;
static WiFiManager     wifi;
static DataSender      sender;

// Timing
static unsigned long lastSampleUs   = 0;
static unsigned long loopCount      = 0;
static float         measuredRateHz = (float)SAMPLING_FREQ_HZ;

// LED state
static unsigned long lastLEDToggleMs = 0;
static bool          ledState        = false;

// Rate measurement
static unsigned long rateWindowStart = 0;
static uint32_t      rateWindowCount = 0;


// *****************************************************************************
// ██  STATUS LED HELPER
// *****************************************************************************

static void updateStatusLED(uint16_t intervalMs) {
    if (millis() - lastLEDToggleMs >= intervalMs) {
        ledState = !ledState;
        digitalWrite(STATUS_LED_PIN, ledState ? HIGH : LOW);
        lastLEDToggleMs = millis();
    }
}


// *****************************************************************************
// ██  SETUP
// *****************************************************************************

void setup() {
    // --- Serial ---
    Serial.begin(115200);
    while (!Serial && millis() < 3000) { /* wait up to 3 s for USB-CDC */ }
    Serial.println();
    Serial.println(F("============================================="));
    Serial.println(F("  ROLLIQ — Bed-Mobility Monitoring System"));
    Serial.printf ("  Firmware %s | Device %s\n", FIRMWARE_VERSION, DEVICE_ID);
    Serial.println(F("============================================="));

    // --- Status LED ---
    pinMode(STATUS_LED_PIN, OUTPUT);
    digitalWrite(STATUS_LED_PIN, LOW);

    // --- WiFi ---
    wifi.begin();  // Blocking attempt; continues even if it fails.

    // --- MPU6050 ---
    Serial.println(F("[INIT] Initialising MPU6050..."));
    if (!mpu.begin()) {
        Serial.println(F("[INIT] FATAL: MPU6050 init failed. Halting."));
        // Rapid-blink LED forever to signal hardware fault.
        while (true) {
            digitalWrite(STATUS_LED_PIN, !digitalRead(STATUS_LED_PIN));
            delay(LED_BLINK_ERROR);
        }
    }

    // --- Calibration ---
    if (!mpu.calibrate()) {
        Serial.println(F("[INIT] WARNING: Calibration failed — using zero offsets."));
    }

    // --- Data Sender ---
    sender.begin();

    // --- Watchdog Timer ---
    // The ESP-IDF task watchdog protects against infinite loops or hangs.
    esp_task_wdt_init(WDT_TIMEOUT_SEC, true);  // true = panic on timeout
    esp_task_wdt_add(NULL);                     // Subscribe the loopTask

    // --- Timing ---
    lastSampleUs    = micros();
    rateWindowStart = millis();
    rateWindowCount = 0;

    Serial.println(F("[INIT] Setup complete. Entering main loop."));
    Serial.printf ("[INIT] Sampling at %d Hz (period %lu µs)\n",
                   SAMPLING_FREQ_HZ, (unsigned long)SAMPLE_PERIOD_US);
}


// *****************************************************************************
// ██  MAIN LOOP — hard-timed at SAMPLING_FREQ_HZ
// *****************************************************************************

void loop() {
    // Feed the hardware watchdog every iteration.
    esp_task_wdt_reset();

    // --- Timing gate: wait until one sample period has elapsed ---
    unsigned long nowUs = micros();
    if ((nowUs - lastSampleUs) < SAMPLE_PERIOD_US) {
        // Yield remaining time to WiFi / RTOS tasks.
        // Using delayMicroseconds would busy-wait; delay(1) lets FreeRTOS
        // schedule background WiFi processing.
        if ((nowUs - lastSampleUs) < (SAMPLE_PERIOD_US - 1000)) {
            delay(1);
        }
        return;
    }
    lastSampleUs = nowUs;
    loopCount++;

    // --- 1. WiFi housekeeping (non-blocking) ---
    wifi.update();
    sender.loop();  // WebSocket event pump

    // --- 2. Read + process sensor data ---
    SensorData sample;
    bool readOk = mpu.readSensor(sample);

    if (readOk) {
        // --- 3. Buffer the reading ---
        bool bufferFull = sender.bufferReading(
            sample,
            mpu.getHealth().healthy,
            measuredRateHz
        );

        // --- 4. If buffer full, send batch ---
        if (bufferFull && wifi.isConnected()) {
            sender.flush();
        }
    }

    // --- 5. Measure actual sampling rate ---
    rateWindowCount++;
    unsigned long rateElapsed = millis() - rateWindowStart;
    if (rateElapsed >= 1000) {
        measuredRateHz  = (float)rateWindowCount * 1000.0f / (float)rateElapsed;
        rateWindowCount = 0;
        rateWindowStart = millis();

        // Periodic status line every second.
        Serial.printf("[LOOP] Rate: %.1f Hz | WiFi: %s | Buf: %u/%u | "
                      "Pkts: %u | Health: %s\n",
                      measuredRateHz,
                      wifi.isConnected() ? "OK" : "DOWN",
                      sender.bufferedCount(), (uint16_t)DATA_BUFFER_SIZE,
                      sender.packetsSent(),
                      mpu.getHealth().healthy ? "OK" : "DEGRADED");
    }

    // --- 6. Status LED ---
    // Override blink rate when actively sending data.
    uint16_t ledInterval = wifi.getLEDBlinkInterval();
    if (!mpu.getHealth().healthy) {
        ledInterval = LED_BLINK_ERROR;
    }
    updateStatusLED(ledInterval);
}
