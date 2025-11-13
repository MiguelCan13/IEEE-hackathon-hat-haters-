/*
 * ESP32 WiFi Servo Controller
 * 
 * Receives servo position commands over WiFi and controls a 180-degree servo
 * 
 * Hardware:
 * - ESP32 (NodeMCU-32S)
 * - 180-degree servo motor
 * - Servo connected to GPIO 14 (or change SERVO_PIN)
 * 
 * API:
 * POST /servo - Set servo position
 *   JSON: {"position": 0-180}
 * GET /status - Get current status
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

// WiFi credentials
const char* ssid = "GatewayAtCollegeStation_SS";
const char* password = "13RHV5D47MGABLWC";

// Servo pin
#define SERVO_PIN 14

// Create servo object
Servo myServo;

// Web server on port 80
WebServer server(80);

// Current servo position
int currentPosition = 90;  // Start at center

// Last command time (for safety timeout)
unsigned long lastCommandTime = 0;
const unsigned long COMMAND_TIMEOUT = 5000;  // 5 seconds

// Forward declarations
void handleServoCommand();
void handleStatus();
void handleNotFound();
void setServoPosition(int position);

void setup() {
    Serial.begin(115200);
    Serial.println("\n\n=================================");
    Serial.println("ESP32 WiFi Servo Controller");
    Serial.println("=================================");
    
    // Initialize servo
    Serial.println("\nInitializing servo...");
    myServo.attach(SERVO_PIN);
    myServo.write(90);  // Start at center position
    Serial.println("✓ Servo initialized at 90°");
    
    // Connect to WiFi
    Serial.print("\nConnecting to WiFi: ");
    Serial.println(ssid);
    
    WiFi.begin(ssid, password);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n✓ WiFi Connected!");
        Serial.print("IP Address: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println("\n✗ WiFi Connection Failed!");
        Serial.println("Please check your credentials and try again.");
    }
    
    // Setup web server routes
    server.on("/servo", HTTP_POST, handleServoCommand);
    server.on("/status", HTTP_GET, handleStatus);
    server.onNotFound(handleNotFound);
    
    // Start server
    server.begin();
    Serial.println("\n✓ Web server started");
    Serial.println("=================================");
    Serial.println("Ready to receive servo commands!");
    Serial.println("=================================\n");
    
    lastCommandTime = millis();
}

void loop() {
    // Handle web server requests
    server.handleClient();
    
    // Safety timeout - return to center if no commands for a while
    if (millis() - lastCommandTime > COMMAND_TIMEOUT) {
        if (currentPosition != 90) {
            Serial.println("⚠️  Command timeout - returning to center");
            setServoPosition(90);
        }
        lastCommandTime = millis();
    }
}

void handleServoCommand() {
    // Check if request has a body
    if (!server.hasArg("plain")) {
        server.send(400, "text/plain", "Missing request body");
        return;
    }
    
    // Parse JSON
    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, server.arg("plain"));
    
    if (error) {
        Serial.print("JSON parse error: ");
        Serial.println(error.c_str());
        server.send(400, "text/plain", "Invalid JSON");
        return;
    }
    
    // Get position from JSON
    if (!doc.containsKey("position")) {
        server.send(400, "text/plain", "Missing 'position' field");
        return;
    }
    
    int position = doc["position"];
    
    // Validate position (0-180)
    if (position < 0 || position > 180) {
        server.send(400, "text/plain", "Position must be 0-180");
        return;
    }
    
    // Set servo position
    setServoPosition(position);
    
    // Update last command time
    lastCommandTime = millis();
    
    // Send success response
    JsonDocument response;
    response["status"] = "ok";
    response["position"] = currentPosition;
    
    String responseJson;
    serializeJson(response, responseJson);
    
    server.send(200, "application/json", responseJson);
    
    Serial.print("✓ Servo position: ");
    Serial.print(currentPosition);
    Serial.println("°");
}

void handleStatus() {
    JsonDocument doc;
    doc["status"] = "ok";
    doc["position"] = currentPosition;
    doc["uptime"] = millis();
    doc["wifi_strength"] = WiFi.RSSI();
    
    String json;
    serializeJson(doc, json);
    
    server.send(200, "application/json", json);
}

void handleNotFound() {
    String message = "ESP32 Servo Controller\n\n";
    message += "Available endpoints:\n";
    message += "POST /servo - Set servo position (JSON: {\"position\": 0-180})\n";
    message += "GET /status - Get current status\n\n";
    message += "Current position: " + String(currentPosition) + "°\n";
    
    server.send(404, "text/plain", message);
}

void setServoPosition(int position) {
    // Clamp to valid range
    position = constrain(position, 0, 180);
    
    // Write to servo
    myServo.write(position);
    currentPosition = position;
}
