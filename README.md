# 🎮 Multi-Militia: Python Edition

![Multi-Militia Header](./docs/images/header.png)

**Multi-Militia** is a high-octane, 2D side-scrolling multiplayer shooter built as a modern tribute to the legendary *Mini Militia*. Experience intense combat with jetpack physics, a massive arsenal of weapons, and seamless local or online multiplayer action.

---

## ✨ Key Features

*   **🚀 Jetpack Combat**: Master the art of aerial warfare with gravity-defying jetpack mechanics.
*   **🔫 Massive Arsenal**: Choose from over 15+ weapons including Assault Rifles (AK-47, M4), SMGs (Uzi, MP5), Snipers, Shotguns, and futuristic tech like the PHASR Laser and EMP Gun.
*   **👥 Local & Online Multiplayer**: 
    *   **Local**: Play with up to 4 players on a single machine using keyboard and gamepads.
    *   **Online**: Connect with friends across the globe using a simple 4-digit room code system powered by Node.js and Socket.io.
*   **🌍 Dynamic Maps**: Explore diverse battlegrounds with layered parallax backgrounds, strategic platforms, and interactive hazards.
*   **📈 Tactical HUD**: Real-time tracking of Health, Shield, Fuel, and Ammo, plus a global Kill Feed and Scoreboard.
*   **💥 High Fidelity**: Blood particles, smoke trails, muzzle flashes, and explosive effects for a premium combat experience.

---

## 🛠️ Installation & Setup

### 1. Prerequisites
Ensure you have the following installed:
- **Python 3.8+**
- **Node.js** (for online multiplayer hosting)

### 2. Install Dependencies
Run the following commands in your terminal:

```bash
# Install Python libraries
pip install pygame python-socketio requests

# Install Node.js dependencies
npm install
```

### 3. Launching the Game
**For Online Mode:**
1. Start the signaling server:
   ```bash
   node server.js
   ```
2. Launch the game client:
   ```bash
   python game.py
   ```

**For Local Play:**
Simply run:
```bash
python game.py
```

---

## 🕹️ Controls

Multi-Militia supports up to 4 players simultaneously.

| Action | Player 1 (KBM) | Player 2 (Keyboard) | Player 3 (Alt-KB) | Player 4 (Alt-KB) |
| :--- | :--- | :--- | :--- | :--- |
| **Move** | `A` / `D` | `←` / `→` | `J` / `L` | `F` / `H` |
| **Jetpack** | `W` / `Space` | `↑` | `I` | `T` |
| **Aim** | Mouse | `I` / `K` | `U` / `O` | `R` / `Y` |
| **Shoot** | Left Click | `Numpad 0` | `P` | `V` |
| **Grenade** | `G` | `Numpad .` | `M` | `B` |
| **Reload** | `R` | `Numpad /` | `N` | `X` |
| **Switch** | `Q` | `Right Shift` | `,` | `Z` |

---

## 🔫 Weapons Selection

![Weapons](./docs/images/weapons.png)

| Category | Weapons | Special Features |
| :--- | :--- | :--- |
| **Assault** | AK-47, M4, XM8 | Reliable, balanced damage and fire rate. |
| **SMG** | Uzi, MP5, Tec-9 | High fire rate, Tec-9 features dual-wield. |
| **Sniper** | Barrett | Long range, extreme damage, slow fire rate. |
| **Shotgun** | Super 90 | High spread, devastating at close range. |
| **Special** | Rocket, EMP, PHASR | Explosives, stunning shocks, and laser beams. |
| **Handguns** | Magnum, Deagle | High precision, Deagle features dual-wield. |

---

## 🔧 Technical Overview

- **Core Engine**: Built using `Pygame` for robust 2D physics and rendering.
- **Networking**: `python-socketio` (Client) and `Socket.io` (Server) provide low-latency event relaying.
- **State Management**: Dedicated systems for handling game cycles (Menu, Playing, Game Over, etc.).
- **Map System**: procedurally defined platforms and spawns with multi-layered parallax background generation.

---

## 📜 Credits
Developed with passion by the **Multi-Militia Team**. Inspired by the classic Mini Militia experience.

---
