@echo off
title Dashboard de Investimentos

:: Vai para a pasta onde o .bat está
cd /d "%~dp0"

:: Verifica se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado.
    echo Instale em: https://www.python.org/downloads/
    echo Marque a opcao "Add Python to PATH" durante a instalacao.
    pause
    exit /b
)

:: Instala dependencias se necessario
echo Verificando dependencias...
pip install yfinance matplotlib numpy --quiet

:: Roda o dashboard
echo Iniciando dashboard...
python app-investimento.py

:: Se der erro, mostra a mensagem
if errorlevel 1 (
    echo.
    echo [ERRO] Algo deu errado. Veja a mensagem acima.
    pause
)