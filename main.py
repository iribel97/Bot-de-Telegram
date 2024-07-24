#Importar el conector de la bd
import mysql.connector
#Importar el telebot
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime

# Conexión a la base de datos
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            user='root',
            password='root',
            host='localhost',
            database='bot'
        )
        return connection
    except mysql.connector.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None


#Conexion con el bot
TOKEN = '7455687188:AAEQsUC6ENXGXb93V55PmNAfZp75AC-E1CU'
bot = telebot.TeleBot(TOKEN)

# Función para mostrar los botones iniciales
def show_initial_buttons(chat_id):
    markup = ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    btn_add_task = KeyboardButton('/Agregar')
    btn_list_tasks = KeyboardButton('/Mostrar')
    btn_edit_task = KeyboardButton('/Editar')
    btn_delete_task = KeyboardButton('/Eliminar')
    markup.add(btn_add_task, btn_list_tasks, btn_edit_task, btn_delete_task)
    bot.send_message(chat_id,'Selecciona una opción:', reply_markup=markup)


#Creacion de comandos simples como `/start`
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute('INSERT IGNORE INTO users (id, username, first_name, last_name) VALUES (%s, %s, %s, %s)', 
                       (user.id, user.username, user.first_name, user.last_name))
        conn.commit()
        cursor.close()
        conn.close()

    bot.send_message(message.chat.id, f'Hola {user.first_name}! Soy tu agenda bot. ¿Qué te gustaría hacer?')
    show_initial_buttons(message.chat.id)


# Manejar la descripción de la tarea
def handle_task_description(message):
    user_id = message.from_user.id
    task_description = message.text
    bot.send_message(message.chat.id, 'Por favor, proporciona una fecha de vencimiento para la tarea (formato: YYYY-MM-DD).')
    bot.register_next_step_handler(message, handle_task_due_date, task_description)
         

# Manejar la fecha de vencimiento de la tarea
def handle_task_due_date(message, task_description):
    user_id = message.from_user.id
    try:
        task_due_date = datetime.strptime(message.text, '%Y-%m-%d')
    except ValueError:
        bot.send_message(message.chat.id, 'Formato de fecha no válido. Por favor, proporciona la fecha en el formato YYYY-MM-DD.')
        bot.register_next_step_handler(message, handle_task_due_date, task_description)
        return

    # Obtener la fecha actual
    current_date = datetime.now()
    
    # Comparar la fecha ingresada con la fecha actual
    if task_due_date < current_date:
        bot.send_message(message.chat.id, 'La fecha de vencimiento no puede ser menor a la fecha actual. Por favor, proporciona una fecha válida.')
        bot.register_next_step_handler(message, handle_task_due_date, task_description)
        return
    
    #Comparar que la fecha ingresada no sea mayor a 2090
    if task_due_date.year > 2090:
        bot.send_message(message.chat.id, 'La fecha de vencimiento no puede ser mayor al año 2090. Por favor, proporciona una fecha válida.')
        bot.register_next_step_handler(message, handle_task_due_date, task_description)
        return

    conn = get_db_connection()


    if conn:
        #Traer todos los task del usuario
        cursor = conn.cursor()
        query = """
            SELECT t.descript, t.due_date, s.name
            FROM tasks t
            JOIN task_status s ON t.status_id = s.id
            WHERE t.user_id = %s
            """
        cursor.execute(query, (user_id,))
        tasks = cursor.fetchall()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO tasks (user_id, descript, due_date, num_task_user) VALUES (%s, %s, %s, %s)', (user_id, task_description, task_due_date, tasks.__len__()+1))
        conn.commit()
        cursor.close()
        conn.close()

    bot.send_message(message.chat.id, '¡Tarea agregada!')

# Comando /add para agregar tareas
@bot.message_handler(commands=['Agregar'])
def add_task(message):
    bot.send_message(message.chat.id, 'Por favor, proporciona una descripción de la tarea.')
    bot.register_next_step_handler(message, handle_task_description)

# Comando /list para listar tareas
@bot.message_handler(commands=['Mostrar'])
def list_tasks(message):
    user_id = message.from_user.id

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = """
        SELECT t.descript, t.due_date, s.name
        FROM tasks t
        JOIN task_status s ON t.status_id = s.id
        WHERE t.user_id = %s
        """
        cursor.execute(query, (user_id,))
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()

        if tasks:
            pending_tasks = []
            in_progress_tasks = []
            completed_tasks = []

            for task in tasks:
                description, due_date, status_name = task
                if status_name.lower() == 'pendiente':
                    pending_tasks.append(f"{description} - {due_date.strftime('%Y-%m-%d')}")
                elif status_name.lower() == 'en progreso':
                    in_progress_tasks.append(f"{description} - {due_date.strftime('%Y-%m-%d')}")
                elif status_name.lower() == 'realizada':
                    completed_tasks.append(f"{description} - {due_date.strftime('%Y-%m-%d')}")

            response = "*TAREAS PENDIENTES*\n--------------------------------------------------\n"
            if pending_tasks:
                response += '\n'.join(pending_tasks) + '\n'
            else:
                response += "No tienes tareas pendientes.\n"

            response += "\n*TAREAS EN PROGRESO*\n--------------------------------------------------\n"
            if in_progress_tasks:
                response += '\n'.join(in_progress_tasks) + '\n'
            else:
                response += "No tienes tareas en progreso.\n"

            response += "\n*TAREAS REALIZADAS*\n--------------------------------------------------\n"
            if completed_tasks:
                response += '\n'.join(completed_tasks) + '\n'
            else:
                response += "No tienes tareas realizadas.\n"
        else:
            response = 'No tienes tareas registradas.'

        bot.reply_to(message, response, parse_mode='Markdown')
    else:
        bot.reply_to(message, 'Error al conectar a la base de datos.')

# Comando /edit para editar tareas
@bot.message_handler(commands=['Editar'])
def select_task_to_edit(message):
    user_id = message.from_user.id

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = """
        SELECT t.id, t.num_task_user, t.descript, s.name
        FROM tasks t
        JOIN task_status s ON t.status_id = s.id
        WHERE t.user_id = %s
        """
        cursor.execute(query, (user_id,))
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()

        if tasks:
            response = "Selecciona el número de la tarea que deseas editar:\n"
            for task in tasks:
                task_id, num_task_user ,description, status_name = task
                response += f"{num_task_user}. {description} - {status_name}\n"

            msg = bot.reply_to(message, response)
            bot.register_next_step_handler(msg, ask_edit_choice)
        else:
            bot.reply_to(message, 'No tienes tareas registradas.')
    else:
        bot.reply_to(message, 'Error al conectar a la base de datos.')

def ask_edit_choice(message):
    try:
        task_id = int(message.text)
        markup = ReplyKeyboardMarkup(row_width=3, one_time_keyboard=True, resize_keyboard=True)
        btn_edit_description = KeyboardButton('Editar Descripción')
        btn_edit_status = KeyboardButton('Editar Estado')
        btn_edit_due_date = KeyboardButton('Editar Fecha de Entrega')
        btn_cancel = KeyboardButton('Cancelar')
        markup.add(btn_edit_description, btn_edit_status, btn_edit_due_date, btn_cancel)
        
        msg = bot.reply_to(message, "¿Qué deseas editar?", reply_markup=markup)
        bot.register_next_step_handler(msg, lambda msg: handle_edit_choice(msg, task_id))
    except ValueError:
        bot.reply_to(message, 'Entrada inválida. Por favor, ingresa un número de tarea válido.')

def handle_edit_choice(message, task_id):
    choice = message.text

    if choice == 'Editar Descripción':
        msg = bot.reply_to(message, "Ingresa la nueva descripción:")
        bot.register_next_step_handler(msg, lambda msg: update_task_description(msg, task_id))
    elif choice == 'Editar Estado':
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM task_status")
            statuses = cursor.fetchall()
            cursor.close()
            conn.close()

            status_buttons = [KeyboardButton(status[0]) for status in statuses]
            markup = ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True, resize_keyboard=True)
            markup.add(*status_buttons)

            msg = bot.reply_to(message, "Selecciona el nuevo estado:", reply_markup=markup)
            bot.register_next_step_handler(msg, lambda msg: update_task_status(msg, task_id))
    elif choice == 'Editar Fecha de Entrega':
        msg = bot.reply_to(message, "Ingresa la nueva fecha de entrega (formato YYYY-MM-DD):")
        bot.register_next_step_handler(msg, lambda msg: update_task_due_date(msg, task_id))
    elif choice == 'Cancelar':
        show_initial_buttons(message.chat.id)
    else:
        bot.reply_to(message, 'Opción inválida. Por favor, selecciona "Editar Descripción", "Editar Estado", "Editar Fecha de Entrega" o "Cancelar".')

def update_task_description(message, task_id):
    new_description = message.text

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = "UPDATE tasks SET descript = %s WHERE id = %s"
        cursor.execute(query, (new_description, task_id))
        conn.commit()
        cursor.close()
        conn.close()

        bot.reply_to(message, "La descripción de la tarea ha sido actualizada.")
        show_initial_buttons(message.chat.id)
    else:
        bot.reply_to(message, 'Error al conectar a la base de datos.')

def update_task_status(message, task_id):
    new_status = message.text

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = "SELECT id FROM task_status WHERE name = %s"
        cursor.execute(query, (new_status,))
        status_id = cursor.fetchone()
        
        if status_id:
            query = "UPDATE tasks SET status_id = %s WHERE id = %s"
            cursor.execute(query, (status_id[0], task_id))
            conn.commit()
            bot.reply_to(message, "El estado de la tarea ha sido actualizado.")
        else:
            bot.reply_to(message, "Estado no válido.")
        
        cursor.close()
        conn.close()
        show_initial_buttons(message.chat.id)
    else:
        bot.reply_to(message, 'Error al conectar a la base de datos.')

def update_task_due_date(message, task_id):
    new_due_date_str = message.text
    try:
        new_due_date = datetime.strptime(new_due_date_str, '%Y-%m-%d')

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            query = "UPDATE tasks SET due_date = %s WHERE id = %s"
            cursor.execute(query, (new_due_date, task_id))
            conn.commit()
            cursor.close()
            conn.close()

            bot.reply_to(message, "La fecha de entrega de la tarea ha sido actualizada.")
            show_initial_buttons(message.chat.id)
        else:
            bot.reply_to(message, 'Error al conectar a la base de datos.')
    except ValueError:
        bot.reply_to(message, "Formato de fecha inválido. Por favor, usa el formato YYYY-MM-DD.")

# Comando /delete para eliminar tareas
@bot.message_handler(commands=['Eliminar'])
def select_task_to_delete(message):
    user_id = message.from_user.id

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = """
        SELECT t.id, t.descript, s.name
        FROM tasks t
        JOIN task_status s ON t.status_id = s.id
        WHERE t.user_id = %s
        """
        cursor.execute(query, (user_id,))
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()

        if tasks:
            response = "Selecciona el número de la tarea que deseas eliminar:\n"
            for task in tasks:
                task_id, description, status_name = task
                response += f"{task_id}. {description} - {status_name}\n"

            msg = bot.reply_to(message, response)
            bot.register_next_step_handler(msg, delete_task)
        else:
            bot.reply_to(message, 'No tienes tareas registradas.')
    else:
        bot.reply_to(message, 'Error al conectar a la base de datos.')

def delete_task(message):
    try:
        task_id = int(message.text)

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            query = "DELETE FROM tasks WHERE id = %s"
            cursor.execute(query, (task_id,))
            conn.commit()
            cursor.close()
            conn.close()

            bot.reply_to(message, "Tarea eliminada.")
            show_initial_buttons(message.chat.id)
        else:
            bot.reply_to(message, 'Error al conectar a la base de datos.')
    except ValueError:
        bot.reply_to(message, 'Entrada inválida. Por favor, ingresa un número de tarea válido.')


# Iniciar el bot
if __name__ == "__main__":
    bot.polling(none_stop=True)