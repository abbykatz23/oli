# Inky Art Display — Setup & Reflash Guide

Raspberry Pi + Pimoroni Inky Impression (Spectra/e640) + Art Institute of Chicago API

Displays a random public-domain artwork daily. Includes a simple Flask web UI for manual refresh.

---

## Hardware

- **Display:** Pimoroni Inky Impression — **Spectra 6 / e640 variant**
  - Correct driver: `from inky.inky_e640 import Inky`
  - ⚠️ Using `inky_uc8159` or `Inky7Colour` will silently fail with no display update — those are for the *older* board variant.
  - Resolution: 600×400
- **Pi:** (fill in model — e.g. Pi 5 / Pi Zero WH)
- **Username set during imaging:** `oli` (or whatever you set — **this must match every path below**)

---

## Fresh Reflash — Full Setup Steps

### 1. Flash the SD card
Use Raspberry Pi Imager → Raspberry Pi OS Lite (32/64-bit as appropriate).
Before writing, click the gear icon:
- Enable SSH
- Set username + password
- Enter WiFi SSID/password (use the **recipient's** WiFi if known ahead of time, or your own temporarily — see WiFi Transfer section below)
- If their network is hidden, add `scan_ssid=1` handling (see below)

### 2. First boot & SSH in
```bash
ssh <username>@<pi-ip>
```
Find the IP via `arp -a` (Mac/Windows) if `<hostname>.local` doesn't resolve.

### 3. Install system dependencies
```bash
sudo apt update
sudo apt install -y python3-pip python3-numpy python3-pil i2c-tools git libopenblas0
```
⚠️ **`libopenblas0` is critical and easy to miss.** Without it, numpy fails with:
```
ImportError: libopenblas.so.0: cannot open shared object file
```
This cost significant debugging time last round — install it up front.

### 4. Clone this repo
```bash
git clone https://github.com/abbykatz23/oli.git
cd oli
```

### 5. Set up the virtual environment
The Pimoroni install script **requires** a venv (it will refuse to run without one):
```bash
python3 -m venv --system-site-packages ~/.venv
source ~/.venv/bin/activate
```
`--system-site-packages` is important — lets the venv see globally installed packages.

### 6. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 7. Run Pimoroni's Inky install script
```bash
git clone https://github.com/pimoroni/inky
cd inky
./install.sh
```
- Say **yes** to copying examples (useful for testing the display independently).
- This configures SPI/I2C overlays in `/boot/firmware/config.txt` automatically.

### 8. Reboot
```bash
sudo reboot
```

### 9. Test the display manually
```bash
source ~/.venv/bin/activate
python3 ~/oli/display_art.py
```
You should see console output selecting an artwork and "Image sent to display."

---

## Known Gotchas From Last Build (avoid repeating these)

1. **Hardcoded `pi` username** — the original script/service files had `/home/pi/...` hardcoded from the first (Chase) build. If cloning for a new user, **grep for stale paths first**:
   ```bash
   grep -rn "pi" ~/oli/*.py ~/oli/*.service
   ```
   Replace any `/home/pi/` with `/home/<actual-username>/`.

2. **numpy/libopenblas failure** — see step 3 above. Fixed by installing `libopenblas0` at the OS level (not fixable via pip/requirements.txt alone, since it's a system library).

3. **systemd service using system Python instead of venv** — if `ExecStart=/usr/bin/python3 ...` is used instead of the venv's interpreter, Flask (or other venv-only packages) won't be found. Always point `ExecStart` at `~/.venv/bin/python3`.

4. **Flask not in original dependency list** — needed for `web.py` but wasn't installed in the base setup. Now included in `requirements.txt`.

---

## Cron Job (daily refresh)

```bash
crontab -e
```
Add:
```
0 8 * * * /home/<username>/.venv/bin/python3 /home/<username>/oli/display_art.py >> /home/<username>/cron.log 2>&1
@reboot sleep 60 && /home/<username>/.venv/bin/python3 /home/<username>/oli/display_art.py >> /home/<username>/cron.log 2>&1
```
- First line: refreshes daily at 8am.
- Second line: refreshes ~60 seconds after boot (gives WiFi time to connect first).

To test without waiting until 8am, temporarily change the schedule to a couple minutes ahead, save, wait, then check:
```bash
cat ~/cron.log
```

---

## Web UI (Flask refresh button)

Service file: `/etc/systemd/system/oli-web.service`

```ini
[Unit]
Description=Oli's Inky art display web UI
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=<username>
WorkingDirectory=/home/<username>/oli
ExecStart=/home/<username>/.venv/bin/python3 /home/<username>/oli/web.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Install/enable:
```bash
sudo cp oli-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now oli-web
```

Check status:
```bash
systemctl status oli-web
journalctl -u oli-web -n 50 --no-pager   # full error logs if it fails
```

Access from a browser on the same network: `http://<pi-ip>:5000`

---

## WiFi Transfer (moving the Pi to a different network before gifting)

**Best method — no monitor/keyboard needed:**

Option A — Ethernet:
1. Plug Pi into recipient's router via Ethernet
2. Boot it, find its new IP via `arp -a` from a laptop on the same network
3. SSH in, then:
   ```bash
   sudo raspi-config
   ```
   → System Options → Wireless LAN → enter their SSID/password
4. Reboot, unplug Ethernet — it should now be on their WiFi

Option B — Pre-configure before leaving home (if you have their WiFi info in advance):
Edit `wpa_supplicant.conf` on the SD card's boot partition directly from a card reader, so it auto-connects on first boot at their place. Add `scan_ssid=1` if their network is hidden:
```
network={
    ssid="TheirNetworkName"
    psk="theirpassword"
    scan_ssid=1
}
```

---

## Verifying Everything Works End-to-End

After any reflash or WiFi transfer, test the full chain:
1. Power cycle the Pi (proper shutdown preferred: `sudo shutdown -h now`, then unplug)
2. Wait ~90 seconds + the 60-second cron delay
3. Confirm:
   - [ ] Display shows a new artwork
   - [ ] `cat ~/cron.log` shows a fresh successful entry
   - [ ] `http://<pi-ip>:5000` loads and the refresh button works
   - [ ] `systemctl status oli-web` shows `active (running)`
