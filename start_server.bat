@echo off
title AtmoSync - Micro-Climate Arbitrage Analytics Server
echo Starting AtmoSync Backend Server on http://127.0.0.1:8050 ...
python "%~dp0backend\app.py"
pause
