# Primer Bot en Telegram

Se realiza un bot basico que va a gestionarse como agenda

## Configuración
1. Clona este repositorio poniendo en la terminal bash `git clone https://github.com/iribel97/Bot-de-Telegram.git`
2. Instala las dependencias 
3. Crea un bot en Telegram por medio de BotFather para optener un token.
4. Reemplaza 'TOKEN' en 'main.py' con tu token
5. Ejecutar el bot usando `python main.py`
6. Crear una base de datos y edita los parametros de la funcion `get_db_connection()` de `main.py`


## Dependencias
* `pip install pyTelegramBotAPI`
* `pip install mysql-connector-python`

## Funcionalidades
- Agregar un evento
- Eliminar un evento
- Editar un evento
- Mostrar eventos agendados