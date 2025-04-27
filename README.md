
# 📸 Dashcam RTSP Relay for Storm Chasing Rigs

A lightweight Python + FFmpeg script to **connect**, **keep alive**, and **re-broadcast** video from dashcams that only allow single-client Wi-Fi access.

Designed for **mobile field use** (storm chasing, scientific expeditions, automotive testing) with **Raspberry Pi** deployment in mind.

---

## 🌪️ Features

- 📡 Connects to dashcam over Wi-Fi using RTSP
- 🎥 Verifies real video is flowing before launching
- 🔁 Auto-reconnects on Wi-Fi drops or dashcam reboot
- 🚀 Launches FFmpeg to relay the live feed to other devices
- 🔥 Extremely lightweight (no GUI needed)
- 🛜 Stable for unattended deployments
- 🛠️ Fully systemd-ready for autostart on Raspberry Pi

---

## ⚙️ Requirements

- Python 3.7+
- ffmpeg installed (`sudo apt install ffmpeg`)
- Raspberry Pi OS or similar Debian-based Linux
- Dashcam that serves RTSP streams (e.g., HiSilicon-based cameras)

---

## 🛠️ Setup

1. **Clone the Repository**

```bash
git clone https://github.com/Speexvocon/dashcam-relay.git
cd dashcam-relay
```

2. **Install Requirements**

Install ffmpeg if not already present:

```bash
sudo apt update
sudo apt install ffmpeg
```

3. **Edit Configuration**

Edit `dashcam_streamer.py` to match your camera IP and stream path if necessary:

```python
DASHCAM_IP = '192.168.0.1'
DASHCAM_RTSP_URL = f'rtsp://{DASHCAM_IP}:554/livestream/1'
```

4. **Make the Script Executable**

```bash
chmod +x dashcam_streamer.py
```

---

## 🚀 Running Manually

Simply run:

```bash
python3 dashcam_streamer.py
```

The script will:
- Connect to your dashcam
- Maintain the session
- Relay the video to `rtsp://<pi-ip>:8554/stream`

You can then view it from VLC, ffplay, or OBS Studio!

---

## 🛜 Autostart at Boot (Systemd Service)

1. **Create a service file:**

```bash
sudo nano /etc/systemd/system/dashcam-relay.service
```

2. **Paste:**

```ini
[Unit]
Description=Dashcam RTSP Relay Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/dashcam_streamer.py
Restart=always
RestartSec=5
User=pi
WorkingDirectory=/home/pi

[Install]
WantedBy=multi-user.target
```

3. **Enable the service:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable dashcam-relay
sudo systemctl start dashcam-relay
```

---

## 📸 Accessing the Stream

After successful startup, you can view the rebroadcasted stream at:

```
rtsp://<your-pi-ip>:8554/stream
```

Examples:
- Open with **VLC**: Media → Open Network Stream
- Open with **ffplay**:
  ```bash
  ffplay rtsp://<your-pi-ip>:8554/stream
  ```

## 📄 License

MIT License  
© 2025 [Speexvocon]
