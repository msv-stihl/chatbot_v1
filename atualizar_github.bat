@echo off
cd /d C:\Users\manserv\OneDrive - MANSERV\Área de Trabalho\Projetos_Wesley\chatbot\backend
git pull
git add dados.json
git commit -m "Atualização automática de dados"
git push origin main
