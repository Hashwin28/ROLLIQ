// =============================================================================
// ROLLIQ Firmware — mpu6050_handler.h
// MPU6050 driver: initialisation, calibration, reading, health monitoring.
// =============================================================================
#ifndef MPU6050_HANDLER_H
#define MPU6050_HANDLER_H

#include <Wire.h>
#include <cstdint>
#include "config.h"
#include "sensor_filter.h"

// -----------------------------------------------------------------------------
// Sensor data structure — one timestamped reading
// -----------------------------------------------------------------------------
struct SensorData {
    unsigned long timestamp_ms;     // millis() at acquisition time

    // Raw values (LSB integers straight from registers)
    int16_t raw_ax, raw_ay, raw_az;
    int16_t raw_gx, raw_gy, raw_gz;

    // Physical-unit values after bias correction + scaling
    float ax_g, ay_g, az_g;        // Acceleration in g
    float gx_dps, gy_dps, gz_dps;  // Angular rate in °/s

    // Filtered physical values (after EMA low-pass)
    float filt_ax, filt_ay, filt_az;
    float filt_gx, filt_gy, filt_gz;

    // Orientation estimates from complementary filter (degrees)
    float roll, pitch;

    // Health flag for this sample
    bool valid;
};

// -----------------------------------------------------------------------------
// Calibration offsets — computed at startup while the sensor is stationary
// -----------------------------------------------------------------------------
struct CalibrationData {
    float accel_offset_x, accel_offset_y, accel_offset_z;
    float gyro_offset_x,  gyro_offset_y,  gyro_offset_z;
    bool  calibrated;
};

// -----------------------------------------------------------------------------
// Sensor health tracker
// -----------------------------------------------------------------------------
struct SensorHealth {
    uint32_t      consecutive_fails;
    unsigned long last_good_read_ms;
    unsigned long last_reset_ms;
    bool          healthy;
};

// -----------------------------------------------------------------------------
// MPU6050 Handler class
// -----------------------------------------------------------------------------
class MPU6050Handler {
public:
    MPU6050Handler();

    // Initialise I2C bus and MPU6050 registers.  Returns true on success.
    bool begin();

    // Verify the sensor is present and responsive (WHO_AM_I check).
    bool verifySensor();

    // Run stationary calibration (sensor must be still and level).
    // Collects CALIBRATION_SAMPLES samples, computes bias offsets.
    bool calibrate();

    // Read a single 6-axis sample, apply corrections, filter, and estimate
    // orientation.  Returns true if the read succeeded.
    bool readSensor(SensorData &out);

    // Get current health status.
    const SensorHealth& getHealth() const { return _health; }

    // Get calibration data.
    const CalibrationData& getCalibration() const { return _cal; }

    // Attempt a soft reset of the sensor (power-cycle via PWR_MGMT_1).
    bool softReset();

private:
    // Low-level register helpers
    bool    writeRegister(uint8_t reg, uint8_t val);
    uint8_t readRegister(uint8_t reg);
    bool    readRegisters(uint8_t startReg, uint8_t *buffer, uint8_t count);

    // Read raw 14 bytes (accel + temp + gyro) in one burst.
    bool readRaw6Axis(int16_t &ax, int16_t &ay, int16_t &az,
                      int16_t &gx, int16_t &gy, int16_t &gz);

    // Orientation estimation state
    float _roll, _pitch;
    bool  _orientationInitialised;
    unsigned long _lastOrientationUs;

    CalibrationData _cal;
    SensorHealth    _health;
    SixAxisFilter   _filter;
};

#endif // MPU6050_HANDLER_H
