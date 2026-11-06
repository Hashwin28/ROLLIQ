// =============================================================================
// ROLLIQ Firmware — data_sender.h
// Sends buffered sensor data to the backend via HTTP POST (JSON array)
// or optionally via WebSocket.
// =============================================================================
#ifndef DATA_SENDER_H
#define DATA_SENDER_H

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <WebSocketsClient.h>
#include "config.h"
#include "mpu6050_handler.h"

// -----------------------------------------------------------------------------
// Data Sender class
// -----------------------------------------------------------------------------
class DataSender {
public:
    DataSender();

    // Initialise HTTP / WebSocket client.
    void begin();

    // Buffer a single sensor reading.  Returns true if the buffer is now full
    // and should be flushed.
    bool bufferReading(const SensorData &data, bool sensorHealthy,
                       float samplingRate);

    // Flush the buffer — send all buffered readings to the backend.
    // Returns true on successful transmission.
    bool flush();

    // Number of readings currently buffered.
    uint16_t bufferedCount() const { return _bufferIndex; }

    // Total packets sent since boot.
    uint32_t packetsSent() const { return _packetSeq; }

    // Non-blocking WebSocket event loop (call every iteration when WS is used).
    void loop();

private:
    // Internal buffer
    SensorData _buffer[DATA_BUFFER_SIZE];
    bool       _healthFlags[DATA_BUFFER_SIZE];
    float      _sampleRates[DATA_BUFFER_SIZE];
    uint16_t   _bufferIndex;
    uint32_t   _packetSeq;

    // HTTP helpers
    bool sendHTTP();

    // WebSocket helpers
    WebSocketsClient _ws;
    bool             _wsConnected;
    bool             _useWebSocket;

    bool sendWebSocket();
    void initWebSocket();

    // Build the JSON document for the current buffer contents.
    void buildJSON(DynamicJsonDocument &doc);

    // WebSocket event callback (static + instance pointer trick)
    static DataSender *_instance;
    static void wsEventCallback(WStype_t type, uint8_t *payload, size_t length);
    void        handleWSEvent(WStype_t type, uint8_t *payload, size_t length);
};

#endif // DATA_SENDER_H
