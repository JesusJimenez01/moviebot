# moviebot
Chatbot creado con Rasa para complementar mi proyecto de final de grado

## Tutorial:
Activar entorno virtual (en windows usar antes Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass)
```bash
pip install rasa
pip install fuzzywuzzy
pip install python-dotenv
```

Abrir 2 consolas:
  Consola 1 -> Primero usar el comando `rasa train` y luego `rasa run actions` (Esto monta el servidor de las acciones personalizadas)
  Consola 2 -> Usar el comando `rasa shell` para probar en local o `rasa run --enable-api --cors "*"` para habilitar la api
