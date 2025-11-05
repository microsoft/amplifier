# Embedded Sensor Demo Project

Firmware for a temperature/humidity sensor with display and WiFi reporting.

## Context

This project represents embedded hardware integration where:
- Requirements must be clear before hardware is manufactured
- Changes are expensive (firmware flashing, hardware recalls)
- Comprehensive documentation is mandatory
- Testing must be thorough before deployment

**Perfect for: `waterfall` profile (Phased Sequential Development)**

## Project Constraints

- **Hardware**: Custom PCB with STM32 microcontroller, DHT22 sensor, OLED display
- **Deployment**: 1000 units will be manufactured
- **Updates**: OTA firmware updates possible but expensive
- **Timeline**: 3 months to production
- **Cost of Change**: Hardware changes cost $50k in retooling

## Complete Requirements

Must be fully specified upfront:

### Functional Requirements
1. Read temperature/humidity from DHT22 sensor every 30 seconds
2. Display current readings on OLED screen
3. Connect to WiFi and POST readings to cloud endpoint
4. Store last 100 readings in flash memory
5. LED indicators for: power, sensor read, WiFi transmit, error

### Non-Functional Requirements
1. Battery life: 6 months on 2x AA batteries
2. Operating temp: -20°C to 60°C
3. Accuracy: ±0.5°C, ±2% RH
4. Response time: < 2s for display update
5. WiFi: WPA2-PSK, retry logic for failures

### Interfaces
- I2C for sensor communication
- SPI for display
- UART for debugging
- GPIO for LED control

## Why Waterfall?

Changes after manufacturing are catastrophic. We must:
1. Gather complete requirements
2. Design comprehensive system architecture
3. Specify all interfaces and protocols
4. Implement according to spec
5. Test exhaustively
6. Deploy with confidence

This is a perfect use case for phase-gated development with comprehensive upfront planning.
