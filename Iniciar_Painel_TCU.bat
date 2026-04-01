@echo off
title Painel de Auditoria Contábil - TCU
color 09

echo =======================================================
echo     INICIANDO O PAINEL DE AUDITORIA CONTABIL (IA)
echo =======================================================
echo.
echo Aguarde alguns segundos enquanto o servidor carrega...
echo.
echo DICA: Para desligar o sistema depois de usar, basta 
echo fechar esta janela preta.
echo =======================================================
echo.

:: 1. Ativa o ambiente virtual exclusivo deste projeto
call ".venv\Scripts\activate.bat"

:: 2. Inicia o servidor do Streamlit
python -m streamlit run 03_dashboard_tcu.py

:: 3. Pausa caso de algum erro (para a janela nao fechar muito rapido)
pause