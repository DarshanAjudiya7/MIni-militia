# 🎮 Multi-Militia — Python & Node.js Edition

A real-time multiplayer 2D shooter, built as a tribute to the classic Mini Militia. This project features high-intensity combat, jetpack mechanics, and support for both local and online multiplayer sessions.

---

## 🚀 Quick Start

### 1. Requirements
- **Python 3.x**
- **Node.js** (for the signaling server)
- **Pygame** and **Python-SocketIO** libraries

### 2. Installation
First, install the necessary dependencies:

```bash
# Install Python libraries
pip install pygame python-socketio requests

# Install Node.js dependencies
npm install
```

### 3. Running the Game
To play the game, follow these steps in order:

**A. Start the Server (for Online Mode):**
```bash
node server.js
```

**B. Launch the Client:**
```bash
python game.py
```

---

## 🕹️ Controls

### Player 1 (Mouse & Keyboard)
*   **Move**: `A` / `D`
*   **Jetpack**: `W` / `Space`
*   **Aim**: Mouse Cursor
*   **Shoot**: Left Click
*   **Grenade**: `G`
*   **Reload**: `R`
*   **Switch Weapon**: `Q`
*   **Respawn**: `Enter`

### Player 2 (Alternative Keyboard)
*   **Move**: `Left` / `Right` Arrow Keys
*   **Jetpack**: `Up` Arrow Key
*   **Aim**: `I` / `J` / `K` / `L` Keys
*   **Shoot**: `Numpad 0` / `Right Ctrl`
*   **Grenade**: `Numpad .`
*   **Reload**: `Numpad /`
*   **Switch Weapon**: `Right Shift`

---

## 🏗️ Technical Architecture

The project consists of two main components:

### 1. Client (`game.py`)
Developed using **Pygame**, the client handles:
- **Game Engine**: Physics (gravity, jetpack), collision detection, and character rendering.
- **State Management**: Handling HUD, Timer, Scoreboard, and Kill Feed.
- **Networking**: Using `python-socketio` to connect to the Node.js server for real-time synchronization.

### 2. Server (`server.js`)
Developed using **Node.js** and **Socket.io**, the server acts as a signaling orchestrator:
- **Room Management**: Allows players to create and join private rooms using passcodes.
- **Data Relay**: Forwards position, shooting, and damage events between players in the same room.
- **Connection Handling**: Manages player IDs and cleanup upon disconnection.

---

## 🛠️ Combat System

- **Weapons**: Includes AK-47, M4, Sniper, Shotgun, Rocket Launcher, and futuristic weapons like PHASR.
- **Dynamic Physics**: Every bullet has its own speed, spread, and travel physics.
- **Hit Detection**: Accurate rectangle-to-point collision for player hits.
- **Jetpack Fuel**: Limited fuel that recharges automatically while standing on the ground.
- **Power-ups**: Collect Health Packs and Shields scattered across the map.

---

## 📋 Features
- [x] **Smooth Character Animations**: Walking, aiming, and jetpack particle effects.
- [x] **Parallax Backgrounds**: Multi-layered backgrounds for enhanced depth.
- [x] **Real-time Online Mode**: Play with friends using a simple 4-digit room code.
- [x] **Full Kill Feed**: Tracks who killed whom and with what weapon.
- [x] **Weapon Classes**: Multiple initial loadouts (Assault, SMG, Sniper, Special).

---

Built with ❤️ by the Multi-Militia Development Team.
