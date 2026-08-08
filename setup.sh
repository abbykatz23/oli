#!/bin/bash
sudo apt update && sudo apt install -y \
  python3-pip python3-numpy python3-pil i2c-tools git libopenblas0

python3 -m venv --system-site-packages ~/.venv
source ~/.venv/bin/activate
pip install -r requirements.txt

git clone https://github.com/pimoroni/inky
cd inky && ./install.sh