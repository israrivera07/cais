import psycopg2
from datetime import datetime
from psycopg2 import sql

def get_db_connection():
    return psycopg2.connect(
        dbname="mydatabase",
        user="postgres",
        password="isra7303",
        host="7.tcp.eu.ngrok.io",  # Cambia localhost por la URL de ngrok
        port="10932",               # Cambia el puerto por el que te ha dado ngrok
        options='-c client_encoding=UTF8'
    )


def authenticate_user(username, password):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, password, role FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    conn.close()
    
    if user and password == user[1]:
        return user[0], user[2]
    else:
        return None, None

def create_user(username, email, name, password, role, medico_id=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, email, name, password, role, medico_id) VALUES (%s, %s, %s, %s, %s, %s)",
        (username, email, name, password, role, medico_id)
    )
    conn.commit()
    conn.close()

def get_real_name(username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM users WHERE username = %s", (username,))
    real_name = cur.fetchone()[0]
    conn.close()
    return real_name

def create_medico(username, email, name, password):
    medico_id = f"med{get_next_medico_id()}"
    create_user(username, email, name, password, 'medico', medico_id)

def get_next_medico_id():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT MAX(CAST(SUBSTR(medico_id, 4) AS INTEGER)) FROM users WHERE medico_id LIKE 'med%'")
    max_id = cur.fetchone()[0]
    conn.close()
    return max_id + 1 if max_id else 1

def get_patients_of_medico(medico_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM users WHERE medico_id = %s", (medico_id,))
    patients = cur.fetchall()
    conn.close()
    return [patient[0] for patient in patients]

def get_all_medicos():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT users.username, users.name, COUNT(patients.username) as patient_count
        FROM users
        LEFT JOIN users as patients ON users.username = patients.medico_id
        WHERE users.role = 'medico'
        GROUP BY users.username, users.name
    """)
    medicos = cursor.fetchall()
    
    conn.close()
    return medicos

def create_appointment(medico_username, patient_username, appointment_date, appointment_time):
    conn = get_db_connection()  # Usa la función get_db_connection para evitar duplicación de código
    cur = conn.cursor()
    
    # Insertar cita en la base de datos
    cur.execute(
        "INSERT INTO appointments (medico_username, patient_username, appointment_date, hora) VALUES (%s, %s, %s, %s)",
        (medico_username, patient_username, appointment_date, appointment_time)
    )
    conn.commit()
    conn.close()


def get_appointments(medico_username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT patient_username, appointment_date, hora
        FROM appointments
        WHERE medico_username = %s
    """, (medico_username,))
    appointments = cur.fetchall()
    conn.close()
    return [{'patient_username': a[0], 'appointment_date': a[1], 'hora': a[2]} for a in appointments]


def get_patient_appointments(patient_username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT medico_username, appointment_date, hora
        FROM appointments
        WHERE patient_username = %s
    """, (patient_username,))
    appointments = cur.fetchall()
    conn.close()
    return [{'medico_username': a[0], 'appointment_date': a[1], 'hora': a[2]} for a in appointments]

def get_all_patients_of_medico(medico_username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT username, name 
        FROM users 
        WHERE medico_id = %s AND role = 'paciente'
    """, (medico_username,))
    patients = cur.fetchall()
    conn.close()
    return patients  # Devolver una lista de tuplas (username, name)


def get_all_medical_appointments():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT medico_username, patient_username, appointment_date, hora
        FROM appointments
    """)
    appointments = cur.fetchall()
    conn.close()
    return [{'medico_username': a[0], 'patient_username': a[1], 'appointment_date': a[2], 'hora': a[3]} for a in appointments]



def delete_medico(medico_username):
    """Elimina un médico, todos sus pacientes y todas las citas asociadas"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Comenzar una transacción
        cursor.execute('BEGIN')

        # Eliminar todas las citas del médico
        cursor.execute("DELETE FROM appointments WHERE medico_username = %s", (medico_username,))

        # Eliminar todas las citas de los pacientes del médico
        cursor.execute("DELETE FROM appointments WHERE patient_username IN (SELECT username FROM users WHERE medico_id = %s)", (medico_username,))

        # Eliminar todos los pacientes del médico
        cursor.execute("DELETE FROM users WHERE role = 'paciente' AND medico_id = %s", (medico_username,))

        # Eliminar al médico
        cursor.execute("DELETE FROM users WHERE role = 'medico' AND username = %s", (medico_username,))

        # Confirmar la transacción
        conn.commit()

        print(f"Médico {medico_username} y todos sus pacientes y citas han sido eliminados con éxito.")

    except Exception as e:
        # Deshacer la transacción en caso de error
        conn.rollback()
        print(f"Error al eliminar al médico {medico_username}: {e}")

    finally:
        cursor.close()
        conn.close()



def delete_patient(patient_username):
    """Elimina un paciente y todas sus citas asociadas"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Comenzar una transacción
        cursor.execute('BEGIN')

        # Eliminar todas las citas del paciente
        cursor.execute("DELETE FROM appointments WHERE patient_username = %s", (patient_username,))

        # Eliminar al paciente
        cursor.execute("DELETE FROM users WHERE role = 'paciente' AND username = %s", (patient_username,))

        # Confirmar la transacción
        conn.commit()

        print(f"Paciente {patient_username} y todas sus citas han sido eliminados con éxito.")

    except Exception as e:
        # Deshacer la transacción en caso de error
        conn.rollback()
        print(f"Error al eliminar al paciente {patient_username}: {e}")

    finally:
        cursor.close()
        conn.close()

def delete_appointment(medico_username, patient_username, appointment_date, appointment_time):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if appointment_time:
            cur.execute(
                "DELETE FROM appointments WHERE medico_username = %s AND patient_username = %s AND appointment_date = %s AND hora = %s",
                (medico_username, patient_username, appointment_date, appointment_time)
            )
        else:
            cur.execute(
                "DELETE FROM appointments WHERE medico_username = %s AND patient_username = %s AND appointment_date = %s AND hora IS NULL",
                (medico_username, patient_username, appointment_date)
            )
        conn.commit()
        print(f"Cita eliminada con éxito.")
    except Exception as e:
        conn.rollback()
        print(f"Error al eliminar la cita: {e}")
    finally:
        conn.close()


def add_question(patient_username, medico_username, question, answer):
    try:
        print(f"Intentando añadir pregunta. Paciente: {patient_username}, Médico: {medico_username}, Pregunta: {question}, Respuesta: {answer}")
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            "INSERT INTO questions (patient_username, medico_username, question, answer, timestamp) VALUES (%s, %s, %s, %s, NOW())",
            (patient_username, medico_username, question, answer)
        )
        conn.commit()
        cur.close()
        conn.close()
        
        print("Pregunta y respuesta añadidas correctamente.")
        
    except Exception as e:
        print(f"Error al añadir pregunta: {e}")




def get_patient_questions(patient_username, medico_username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT question, answer, timestamp FROM questions WHERE patient_username = %s AND medico_username = %s ORDER BY timestamp",
        (patient_username, medico_username)
    )
    questions = cur.fetchall()
    conn.close()
    return [{'question': q[0], 'answer': q[1], 'timestamp': q[2]} for q in questions]

def get_medico_id_from_database(patient_username):
    # Lógica para conectarse a la base de datos y obtener el medico_id del paciente
    # Por ejemplo:
    connection = get_db_connection()
    query = "SELECT medico_id FROM users WHERE username = %s"
    cursor = connection.cursor()
    cursor.execute(query, (patient_username,))
    result = cursor.fetchone()
    cursor.close()
    connection.close()

    if result:
        return result[0]  # Devuelve el medico_id
    else:
        return None


def obtener_estado_formulario(usuario):
    conn = get_db_connection()
    """
    Verifica en la base de datos si el usuario ya ha completado el formulario.
    Retorna True si el formulario ha sido completado, de lo contrario False.
    """
    try:
        with conn.cursor() as cur:
            query = sql.SQL("SELECT formulario FROM public.users WHERE username = %s")
            cur.execute(query, (usuario,))
            result = cur.fetchone()
            return result[0] if result else False  # Devuelve el valor booleano de 'formulario' o False si no se encuentra el usuario
    except Exception as e:
        print(f"Error al verificar el estado del formulario: {e}")
        return False

def guardar_respuesta_formulario(usuario, rol, satisfaccion, funcionalidad, usabilidad, mejoras):
    """
    Inserta la respuesta del formulario en la tabla respuestasformulario.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            query = sql.SQL("""
                INSERT INTO public.respuestasformulario (username, role, satisfaccion, funcionalidad, usabilidad, mejoras, fecha)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """)
            cur.execute(query, (usuario, rol, satisfaccion, funcionalidad, usabilidad, mejoras))
            conn.commit()
            print("Formulario guardado con éxito.")
    except Exception as e:
        print(f"Error al guardar el formulario: {e}")
        conn.rollback()

def actualizar_estado_formulario(usuario):
    """
    Actualiza el estado del formulario en la tabla de usuarios a True, indicando que el formulario ha sido completado.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            query = sql.SQL("UPDATE public.users SET formulario = TRUE WHERE username = %s")
            cur.execute(query, (usuario,))
            conn.commit()
            print("Estado de formulario actualizado exitosamente.")
    except Exception as e:
        print(f"Error al actualizar el estado del formulario: {e}")
        conn.rollback()


# Función para obtener respuestas de formulario por rol
def obtener_respuestas_formulario_por_rol(rol):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT satisfaccion, funcionalidad, usabilidad, mejoras
            FROM respuestasformulario
            WHERE role = %s
        """, (rol,))
        respuestas = cursor.fetchall()
    conn.close()
    return [{"satisfaccion": r[0], "funcionalidad": r[1], "usabilidad": r[2], "mejoras": r[3]} for r in respuestas]
















