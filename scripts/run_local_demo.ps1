Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PWD'; uvicorn app.model_service:app --host 0.0.0.0 --port 8001" -WindowStyle Hidden
Start-Sleep -Seconds 5
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PWD'; uvicorn app.gateway:app --host 0.0.0.0 --port 8000" -WindowStyle Hidden
Start-Sleep -Seconds 3
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PWD'; python -m http.server 8080 --directory frontend" -WindowStyle Hidden

