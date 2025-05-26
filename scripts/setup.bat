@echo off
echo 🏈 EsporteSocial - Setup Windows
echo ================================

REM Verificar se Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python nao encontrado. Instale Python 3.8+ 
    pause
    exit /b 1
)

echo ✅ Python encontrado

REM Criar ambiente virtual
if not exist venv (
    echo 📦 Criando ambiente virtual...
    python -m venv venv
)

REM Ativar ambiente virtual
echo 🔧 Ativando ambiente virtual...
call venv\Scripts\activate.bat

REM Instalar dependencias
echo 📋 Instalando dependencias...
pip install --upgrade pip
pip install -r requirements.txt

REM Criar arquivo .env se nao existir
if not exist .env (
    echo ⚙️ Criando arquivo .env...
    copy .env.example .env
    echo 📝 Configure suas chaves de API no arquivo .env!
)

echo.
echo 🎉 Setup concluido!
echo.
echo 📋 Proximos passos:
echo 1. Configure suas chaves de API no arquivo .env
echo 2. Execute: venv\Scripts\activate.bat
echo 3. Execute: python run.py
echo.
pause
