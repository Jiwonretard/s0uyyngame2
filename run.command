#!/bin/zsh
cd "$(dirname "$0")"
if ! python3 -c "import pygame" >/dev/null 2>&1; then
  echo "Pygame이 없어 설치를 시작합니다."
  python3 -m pip install -r requirements.txt || exit 1
fi
python3 main.py

