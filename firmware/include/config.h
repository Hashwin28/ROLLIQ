// =============================================================================
// ROLLIQ Firmware — config.h
// System-wide configuration for the bed-mobility monitoring system.
// =============================================================================
#ifndef CONFIG_H
#define CONFIG_H

#include <cstdint>

// -----------------------------------------------------------------------------
// Device Identity
// -----------------------------------------------------------------------------
#define DEVICE_ID               "ROLLIQ-001"
#define FIRMWARE_VERSION        "1.0.0"

// -----------------------------------------------------------------------------
// WiFi Configuration
// Change these to match your network before flashing.
// -----------------------------------------------------------------------------
#define WIFI_SSID               "ROLLIQ_NET"
#define WIFI_PASSWORD           "rolliq2024"
#define WIFI_CONNECT_TIMEOUT_MS 15000           // Initial connection timeout
#define WIFI_RECONNECT_MIN_MS   1000            // Exponential backoff base
#define WIFI_RECONNECT_MAX_MS   60000           // Backoff ceiling

// -----------------------------------------------------------------------------
// Backend Server
// -----------------------------------------------------------------------------
#define SERVER_IP               "192.168.1.100"
#define SERVER_PORT             8080
#define HTTP_ENDPOINT           "/api/sensor/data"
#define WS_ENDPOINT             "/ws/sensor"
#define HTTP_TIMEOUT_MS         5000

// When true the firmware tries WebSocket first; falls back to HTTP POST.
#define USE_WEBSOCKET           false

// -----------------------------------------------------------------------------
// Sampling & Timing
// -----------------------------------------------------------------------------
// 50 Hz → 20 ms per sample.  This is a good balance between temporal
// resolution for human movement analysis and ESP32 processing budget.
#define SAMPLING_FREQ_HZ        50
#define SAMPLE_PERIOD_US        (1000000UL / SAMPLING_FREQ_HZ)  // 20 000 µs
#define SAMPLE_PERIOD_MS        (1000UL / SAMPLING_FREQ_HZ)     // 20 ms

// -----------------------------------------------------------------------------
// I2C Bus — MPU6050
// -----------------------------------------------------------------------------
// ESP32 default I2C0: SDA = GPIO 21, SCL = GPIO 22.
// MPU6050 address is 0x68 when AD0 is low; 0x69 when AD0 is high.
#define I2C_SDA_PIN             21
#define I2C_SCL_PIN             22
#define I2C_CLOCK_HZ            400000          // 400 kHz fast-mode
#define MPU6050_ADDR            0x68

// -----------------------------------------------------------------------------
// MPU6050 Register Map (subset used by this firmware)
// -----------------------------------------------------------------------------
#define MPU6050_REG_WHO_AM_I        0x75
#define MPU6050_REG_PWR_MGMT_1      0x6B
#define MPU6050_REG_PWR_MGMT_2      0x6C
#define MPU6050_REG_SMPLRT_DIV      0x19
#define MPU6050_REG_CONFIG          0x1A
#define MPU6050_REG_GYRO_CONFIG     0x1B
#define MPU6050_REG_ACCEL_CONFIG    0x1C
#define MPU6050_REG_ACCEL_XOUT_H    0x3B
#define MPU6050_REG_SIGNAL_PATH_RST 0x68
#define MPU6050_WHO_AM_I_VAL        0x68        // Expected response

// Full-scale range selections ---
// Accelerometer: ±2 g  → sensitivity 16384 LSB/g
// Gyroscope:     ±250 °/s → sensitivity 131 LSB/(°/s)
// These low ranges maximise resolution for subtle bed movements.
#define ACCEL_FS_SEL            0               // 0 = ±2 g
#define GYRO_FS_SEL             0               // 0 = ±250 °/s
#define ACCEL_SENSITIVITY       16384.0f        // LSB per g
#define GYRO_SENSITIVITY        131.0f          // LSB per °/s

// -----------------------------------------------------------------------------
// Calibration
// -----------------------------------------------------------------------------
// Number of samples averaged during the stationary calibration routine.
// At 50 Hz this takes ~20 s — long enough to average out noise.
#define CALIBRATION_SAMPLES     1000

// Static offsets (set to 0; replaced at runtime by calibration routine).
#define ACCEL_OFFSET_X          0
#define ACCEL_OFFSET_Y          0
#define ACCEL_OFFSET_Z          0
#define GYRO_OFFSET_X           0
#define GYRO_OFFSET_Y          0
#define GYRO_OFFSET_Z           0

// -----------------------------------------------------------------------------
// Signal Processing
// -----------------------------------------------------------------------------
// Exponential Moving Average (low-pass) filter coefficient.
// α = 0.1 → cutoff ≈ 0.8 Hz at 50 Hz sampling.  Human voluntary trunk
// movement is typically < 2 Hz; this aggressively smooths high-frequency
// vibration while preserving postural change information.
#define LPF_ALPHA               0.1f

// Complementary filter coefficient for orientation estimation.
// We trust the gyroscope for short-term (fast) changes and the accelerometer
// for long-term (gravity) reference.  α = 0.98 means 98 % gyro + 2 % accel.
#define COMP_FILTER_ALPHA       0.98f

// -----------------------------------------------------------------------------
// Data Buffering & Transmission
// -----------------------------------------------------------------------------
// Number of sensor readings to buffer before sending a batch HTTP POST.
// 50 samples at 50 Hz → one POST per second.
#define DATA_BUFFER_SIZE        50

// Maximum JSON payload size (bytes).  Each sample ≈ 200 B of JSON;
// 50 × 200 = 10 000 + envelope overhead → 12 kB is comfortable.
#define JSON_DOC_SIZE           12288

// -----------------------------------------------------------------------------
// Sensor Health Monitoring
// -----------------------------------------------------------------------------
// If the sensor produces this many consecutive failed reads we declare it
// unhealthy and attempt a soft reset.
#define MAX_CONSECUTIVE_FAILS   10
#define SENSOR_RESET_COOLDOWN_MS 5000

// -----------------------------------------------------------------------------
// Status LED
// -----------------------------------------------------------------------------
// On-board LED on most ESP32 DevKit boards is GPIO 2.
#define STATUS_LED_PIN          2

// Blink patterns (half-period in ms):
#define LED_BLINK_WIFI_CONNECTING   250     // Fast blink — connecting
#define LED_BLINK_WIFI_CONNECTED    1000    // Slow blink — connected, idle
#define LED_BLINK_SENDING           100     // Very fast — transmitting
#define LED_BLINK_ERROR             50      // Ultra-fast — error state

// -----------------------------------------------------------------------------
// Watchdog
// -----------------------------------------------------------------------------
#define WDT_TIMEOUT_SEC         10              // Hardware watchdog timeout

#endif // CONFIG_H
