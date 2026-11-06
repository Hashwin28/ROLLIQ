// =============================================================================
// ROLLIQ Firmware — wifi_manager.h
// WiFi connection management with auto-reconnect and exponential backoff.
// =============================================================================
#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <WiFi.h>
#include "config.h"

// -----------------------------------------------------------------------------
// Connection states
// -----------------------------------------------------------------------------
enum class WiFiState : uint8_t {
    DISCONNECTED,
    CONNECTING,
    CONNECTED,
    RECONNECTING
};

// -----------------------------------------------------------------------------
// WiFi Manager class
// -----------------------------------------------------------------------------
class WiFiManager {
public:
    WiFiManager();

    // Start the WiFi connection process (blocking up to WIFI_CONNECT_TIMEOUT_MS
    // on the first call).  Returns true if connected.
    bool begin();

    // Non-blocking check — call every loop iteration.
    // Handles reconnection with exponential backoff.
    void update();

    // Current state accessors
    WiFiState getState()  const { return _state; }
    bool      isConnected() const { return _state == WiFiState::CONNECTED; }
    int32_t   getRSSI()   const { return WiFi.RSSI(); }
    String    getIP()     const { return WiFi.localIP().toString(); }

    // Returns the LED half-period (ms) matching the current state.
    uint16_t getLEDBlinkInterval() const;

private:
    WiFiState     _state;
    unsigned long _lastAttemptMs;
    unsigned long _backoffMs;
    uint8_t       _retryCount;

    void startConnection();
};

#endif // WIFI_MANAGER_H
