# 🔥 FireVision AI — AI Fire Detection & Smart Home Safety System

**FireVision AI** is an AI-powered fire and smoke detection system designed for Smart Home applications.

The system combines **AI Computer Vision**, **Raspberry Pi**, environmental sensors, and smart-home actuators to detect potential fire hazards and automatically perform safety actions.

The AI model:

```text
FireVisionAI.pt
```

analyzes real-time camera images to detect **fire and smoke**, while the Raspberry Pi collects environmental data and controls connected safety devices.

---

## 🎯 Project Overview

FireVision AI combines two types of monitoring:

**AI Vision Detection**

* 🔥 Fire detection
* 💨 Smoke detection
* 🎥 Real-time camera monitoring

**Environmental Monitoring**

* 🌡 Temperature monitoring
* 💧 Humidity monitoring

When a dangerous condition is detected, the Raspberry Pi can automatically control:

* 🚪 Servo motor for opening/closing doors
* 🔊 Speaker for voice/alarm warnings
* 🚨 Warning lights
* 🌀 Ventilation fan
* 📷 Camera monitoring
* 📡 Smart Home / IoT notifications

---

# 🏠 System Architecture

```text
                         ┌──────────────────┐
                         │      CAMERA      │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  FireVision AI   │
                         │ FireVisionAI.pt  │
                         └────────┬─────────┘
                                  │
                         Fire / Smoke
                           Detection
                                  │
                                  ▼
┌─────────────────┐      ┌──────────────────┐
│ Temperature &   │─────►│   RASPBERRY PI   │
│ Humidity Sensor │      │ Main Controller  │
└─────────────────┘      └────────┬─────────┘
                                  │
             ┌────────────────────┼────────────────────┐
             │                    │                    │
             ▼                    ▼                    ▼
       ┌───────────┐        ┌───────────┐       ┌───────────┐
       │   SERVO   │        │  SPEAKER  │       │ WARNING   │
       │   DOOR    │        │   ALARM   │       │   LIGHT   │
       └───────────┘        └───────────┘       └───────────┘
             │
             │                    ┌───────────┐
             └───────────────────►│    FAN    │
                                  └───────────┘
```

---

# 🧠 FireVision AI Model

The AI model is stored in:

```text
FireVisionAI.pt
```

The model is used to process images from the camera and identify signs of fire or smoke.

Basic AI pipeline:

```text
Camera
   │
   ▼
Capture Frame
   │
   ▼
FireVisionAI.pt
   │
   ▼
Fire / Smoke Detection
   │
   ▼
Raspberry Pi Decision System
```

The AI model acts as one source of information for the safety system.

Environmental sensor readings can provide additional information before an automated response is triggered.

---

# 🍓 Raspberry Pi

The **Raspberry Pi** acts as the central controller of the entire system.

It is responsible for:

* Running FireVision AI
* Reading camera frames
* Reading temperature
* Reading humidity
* Processing AI detection results
* Making automation decisions
* Controlling servo motors
* Controlling warning lights
* Controlling the speaker
* Controlling the ventilation fan
* Communicating with Smart Home / IoT systems

Conceptually:

```text
                Raspberry Pi
                     │
        ┌────────────┼─────────────┐
        │            │             │
      INPUT       PROCESS        OUTPUT
        │            │             │
    Camera       FireVision       Servo
 Temperature       AI             Speaker
  Humidity       Decision          Light
                                 Fan
```

---

# 🌡 Temperature & Humidity Sensor

The temperature and humidity sensor continuously monitors environmental conditions.

Example values:

```text
Temperature: 32°C
Humidity: 58%
```

These measurements can be combined with AI detection results.

For example:

```text
AI detects smoke
        +
Temperature increases
        │
        ▼
Higher-confidence warning condition
```

This reduces reliance on a single source of information.

---

# 🚪 Servo Door Control

A servo motor can be connected to a prototype door mechanism.

Example automation:

```text
NORMAL
   │
   ▼
Door operates normally

FIRE ALERT
   │
   ▼
Raspberry Pi
   │
   ▼
Servo
   │
   ▼
Move door to configured emergency position
```

The exact emergency door behavior must be configured according to the physical prototype and applicable fire-safety requirements.

---

# 🔊 Speaker Warning System

The Raspberry Pi can activate a speaker when a fire warning is triggered.

Example warning:

```text
⚠️ WARNING!

Fire or smoke has been detected.

Please check the area and follow the emergency procedure.
```

Different warning levels can also be implemented:

```text
LEVEL 0 → Normal

LEVEL 1 → Possible smoke detected
          Warning notification

LEVEL 2 → Fire / smoke risk
          Warning light + speaker

LEVEL 3 → Confirmed emergency condition
          Alarm + configured emergency automation
```

---

# 🚨 Warning Light

Warning LEDs or lamps provide visual status information.

For example:

| System State     | Warning                   |
| ---------------- | ------------------------- |
| Normal           | System operating normally |
| AI detection     | Visual warning            |
| High temperature | Temperature warning       |
| Fire alert       | Emergency warning light   |

The exact LED colors and flashing patterns can be configured depending on the hardware.

---

# 🌀 Ventilation Fan

A fan can be controlled through the Raspberry Pi using an appropriate relay or driver circuit.

Example logic:

```text
Temperature exceeds configured threshold
                │
                ▼
          Turn ventilation fan ON
```

The fan can be used for normal temperature/ventilation control.

> During a real fire event, automatically operating ventilation can affect smoke and fire behavior. Fire-response fan control should therefore follow the building's fire-safety design rather than simply turning the fan on whenever fire is detected.

---

# 🚨 Detection Logic

A simple decision system can combine AI and sensor data:

```text
                  CAMERA
                     │
                     ▼
               FireVision AI
                     │
             Fire / Smoke?
                     │
                     ▼
              Raspberry Pi
                     ▲
                     │
          Temperature / Humidity
                     │
                  SENSOR
```

Possible logic:

```text
IF AI detects FIRE
        OR
   AI detects SMOKE
        OR
   temperature exceeds configured threshold

THEN

→ Trigger warning state
→ Activate warning light
→ Play speaker warning
→ Save detection event
→ Send Smart Home notification
```

More critical automated actions should use additional validation and appropriate safety rules.

---

# 🔄 Complete System Workflow

```text
START
  │
  ▼
Initialize Raspberry Pi
  │
  ├── Camera
  ├── AI Model
  ├── Temperature/Humidity Sensor
  ├── Servo
  ├── Speaker
  ├── Warning Light
  └── Fan
  │
  ▼
Read Camera + Sensors
  │
  ▼
Run FireVision AI
  │
  ▼
Analyze Detection
  │
  ├──── NORMAL ────► Continue Monitoring
  │
  └──── WARNING
          │
          ▼
     Raspberry Pi
          │
          ├──► Warning Light
          │
          ├──► Speaker Alarm
          │
          ├──► Servo Control
          │
          ├──► Fan Control according to configured safety logic
          │
          └──► Smart Home Notification
```

---

# 🧰 Hardware

Main hardware for the project:

* 🍓 Raspberry Pi
* 📷 USB Camera / Raspberry Pi Camera
* 🌡 Temperature & Humidity Sensor
* 🚪 Servo Motor
* 🔊 Speaker
* 🚨 LED / Warning Light
* 🌀 DC Fan
* ⚡ Relay / MOSFET driver module where required
* 🔌 External power supply where required
* Breadboard / PCB
* Jumper wires

---

# 📁 Project Structure

```text
FireVision-AI/
│
├── FireVisionAI.pt
├── README.md
├── requirements.txt
├── main.py
│
├── ai/
│   └── detector.py
│
├── sensors/
│   └── temperature_humidity.py
│
├── devices/
│   ├── servo.py
│   ├── speaker.py
│   ├── warning_light.py
│   └── fan.py
│
├── smart_home/
│   └── mqtt.py
│
└── config/
    └── settings.py
```

Separating AI, sensors, and device control makes the system easier to maintain and expand.

---

# 🔮 Future Development

Future versions of FireVision AI could support:

* 📱 Mobile notifications
* 🏠 Home Assistant
* 📡 MQTT
* 📷 Multiple cameras
* 🌡 Multiple environmental sensors
* 💨 Physical smoke/gas sensors
* ☁️ Cloud monitoring
* 📊 Web dashboard
* 📈 Temperature history
* 📹 Automatic event recording
* 🔋 Backup power monitoring
* 📲 Telegram notifications
* 🧠 Improved AI models

---

# ⚠️ Safety Notice

**FireVision AI is an experimental and educational Smart Home AI project.**

AI models and environmental sensors can produce false alarms or fail to detect dangerous conditions.

The project must **not replace certified smoke detectors, fire alarms, fire doors, or other required life-safety systems**.

Servo-controlled doors, fans, and other automated equipment can also introduce safety risks if configured incorrectly. Real-world deployment should follow applicable electrical, building, and fire-safety requirements.

---

# 🔥 FireVision AI

### AI Vision + Raspberry Pi + Sensors + Smart Home Automation

```text
         FIREVISION AI
               │
     ┌─────────┴─────────┐
     │                   │
 AI Detection         Sensors
     │                   │
     └─────────┬─────────┘
               ▼
          Raspberry Pi
               │
     ┌─────────┼──────────┐
     │         │          │
   Servo     Speaker     Light
     │
     └──────────── Fan

               ↓

       SMART HOME SAFETY
```

**Building an intelligent fire monitoring and warning system using AI, IoT, and Smart Home technologies.**
