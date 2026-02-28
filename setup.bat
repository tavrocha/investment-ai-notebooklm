@echo off
chcp 65001 > nul
echo.
echo ============================================================
echo   Dashboard de Investimentos — Instalação
echo   Autor: Vinícius Tavares Rocha
echo ============================================================
echo.

:: Verifica Python
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado.
    echo Instale em: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python encontrado.
echo.

:: Instala dependências
echo [INFO] Instalando dependencias...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas.
echo.

:: Cria .env se não existir
if not exist .env (
    echo [INFO] Criando arquivo .env de exemplo...
    copy .env.example .env > nul
    echo [OK] Arquivo .env criado.
    echo.
    echo [ATENCAO] Edite o arquivo .env e adicione suas chaves de API!
    echo           Sem as chaves, o modulo de IA nao funcionara.
    echo           As funcoes de grafico e carteira funcionam sem chaves.
) else (
    echo [OK] Arquivo .env ja existe.
)

echo.
echo ============================================================
echo   Instalacao concluida!
echo   Execute: python app-investimento.py
echo ============================================================
echo.
pause