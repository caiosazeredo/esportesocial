@echo off
echo 🏈 Iniciando EsporteSocial...

REM Ativar ambiente virtual
call venv\Scripts\activate.bat

REM Verificar se .env existe
if not exist .env (
    echo ❌ Arquivo .env nao encontrado!
    echo 🔧 Execute setup.bat primeiro
    pause
    exit /b 1
)

REM Executar aplicacao
python run.py

pause
