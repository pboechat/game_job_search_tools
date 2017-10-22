@echo off

if exist venv (
    echo venv directory already exist.
    pause
    exit /b 0
)

where virtualenv.exe >nul 2>nul
if %errorlevel%==1 (
    echo installing virtualenv...
    pip install virtualenv
)

virtualenv.exe venv

call .\venv\Scripts\activate.bat

python -m pip install -U pip

pip3 install -e .

pause
