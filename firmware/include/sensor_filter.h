// =============================================================================
// ROLLIQ Firmware — sensor_filter.h
// Low-pass filter using Exponential Moving Average (EMA).
//
// Theory:  y[n] = α · x[n] + (1 − α) · y[n−1]
//
// A small α (e.g. 0.1) yields heavy smoothing — good for removing jitter
// from accelerometer/gyroscope data while retaining slow postural changes.
// The effective cutoff frequency is:
//     f_c = α · f_s / (2π)   (first-order approximation)
// At α = 0.1 and f_s = 50 Hz → f_c ≈ 0.8 Hz.
// =============================================================================
#ifndef SENSOR_FILTER_H
#define SENSOR_FILTER_H

#include <cmath>

// -----------------------------------------------------------------------------
// Single-axis exponential moving average filter
// -----------------------------------------------------------------------------
struct EMAFilter {
    float alpha;        // Smoothing coefficient ∈ (0, 1]
    float value;        // Current filtered output
    bool  initialised;  // First-sample flag

    // Construct with a given alpha (default uses config value).
    explicit EMAFilter(float a = 0.1f)
        : alpha(a), value(0.0f), initialised(false) {}

    // Reset filter state so the next input is treated as the first sample.
    void reset() {
        value       = 0.0f;
        initialised = false;
    }

    // Feed a new raw sample and return the filtered output.
    float update(float raw) {
        if (!initialised) {
            // Seed the filter with the first reading to avoid a long ramp-up.
            value       = raw;
            initialised = true;
        } else {
            value = alpha * raw + (1.0f - alpha) * value;
        }
        return value;
    }
};

// -----------------------------------------------------------------------------
// Six-axis filter bank — one EMA per axis
// -----------------------------------------------------------------------------
struct SixAxisFilter {
    EMAFilter ax, ay, az;
    EMAFilter gx, gy, gz;

    explicit SixAxisFilter(float a = 0.1f)
        : ax(a), ay(a), az(a), gx(a), gy(a), gz(a) {}

    void reset() {
        ax.reset(); ay.reset(); az.reset();
        gx.reset(); gy.reset(); gz.reset();
    }

    void setAlpha(float a) {
        ax.alpha = a; ay.alpha = a; az.alpha = a;
        gx.alpha = a; gy.alpha = a; gz.alpha = a;
    }
};

#endif // SENSOR_FILTER_H
