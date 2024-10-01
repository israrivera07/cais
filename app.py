import streamlit as st
import pandas as pd
from datetime import datetime 
from datetime import time as time_module
import time 
from utils.auth import (
    authenticate_user, create_user, get_real_name, 
    get_patients_of_medico, get_all_medicos, create_appointment, 
    get_appointments, get_patient_appointments, get_all_patients_of_medico, 
    get_all_medical_appointments, delete_medico, delete_patient, delete_appointment, get_patient_questions, add_question, get_medico_id_from_database
)
import asyncio
from chatbot.chatbot import get_answer

# Inicializar session_state si no está presente
if 'username' not in st.session_state:
    st.session_state.username = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'history' not in st.session_state:
    st.session_state.history = []
if 'short_term_memory' not in st.session_state:
    st.session_state.short_term_memory = []
if 'medico_counter' not in st.session_state:
    st.session_state.medico_counter = 1  # Inicializar el contador de médicos
if 'medico_id' not in st.session_state:
    st.session_state.medico_id = None  # Inicializar medico_id

def main():
    if st.session_state.username:
        st.success(f"Has iniciado sesión como: {st.session_state.username}")

        if st.session_state.role == "paciente":
            st.write(f"Bienvenido {get_real_name(st.session_state.username)}!")
            st.session_state.medico_id = get_medico_id_for_patient(st.session_state.username)  # Asignar medico_id al paciente
            paciente_interface()

        elif st.session_state.role == "medico":
            st.write("Bienvenido Médico!")
            medico_interface()

        elif st.session_state.role == "supervisor":
            st.write("Bienvenido Supervisor!")
            supervisor_interface()

        else:
            st.write("Rol desconocido")
    else:
        show_login_form()

from PIL import Image
import base64
from io import BytesIO

def show_login_form():
    # Cargar el logo
    logo = Image.open("logoCAIS.png")
    
    # Convertir la imagen a base64
    buffered = BytesIO()
    logo.save(buffered, format="PNG")
    logo_base64 = base64.b64encode(buffered.getvalue()).decode()

    # HTML y CSS para centrar la imagen y agregar sombra
    logo_html = f"""
    <div style="display: flex; justify-content: center; align-items: center; height: 200px;">
        <img src="data:image/png;base64,{logo_base64}" style="border-radius: 10px; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1); width: 200px;">
    </div>
    """

    # Mostrar la imagen centrada con sombra
    st.markdown(logo_html, unsafe_allow_html=True)

    # HTML y CSS para el título
    title_html = """
    <h1 style="text-align: center; font-size: 50px; font-weight: bold; color: white; margin-top: 20px; margin-bottom: 20px;">
        CAIS - Care AI System (DEMO)
    </h1>
    """
    st.markdown(title_html, unsafe_allow_html=True)

    # Crear un contenedor en Streamlit para el formulario
    with st.container():
        st.write("")
        st.write("")
        # Configurar el formulario
        with st.form(key='login_form', clear_on_submit=True):
            st.write("INICIAR SESIÓN")
            username = st.text_input("Nombre de usuario", placeholder="Introduce tu nombre de usuario")
            password = st.text_input("Contraseña", type="password", placeholder="Introduce tu contraseña")
            
            # Botón de enviar formulario
            submit_button = st.form_submit_button("Iniciar sesión")
            st.write('</div>', unsafe_allow_html=True)
            
            if submit_button:
                user, role = authenticate_user(username, password)
                if user:
                    st.session_state.username = user
                    st.session_state.role = role
                    # Mostrar pantalla de carga
                    show_loading_screen()

                    st.experimental_rerun()
                else:
                    st.error("Nombre de usuario o contraseña incorrectos")

def show_loading_screen():
    st.write("Iniciando sesión...")

    # Barra de progreso
    progress_bar = st.progress(0)
    for i in range(100):
        time.sleep(0.01)  # Ajustar la velocidad de la barra de progreso
        progress_bar.progress(i + 1)

    st.success("¡Inicio de sesión exitoso!")

def write_progressively(text, placeholder, delay=0.05):
    """Escribe el texto de manera progresiva en el placeholder."""
    for i in range(len(text) + 1):
        placeholder.markdown(f"<div style='background-color: #e8f5e9; color: black; padding: 10px; border-radius: 5px; margin-bottom: 5px;'><strong>Chatbot:</strong> {text[:i]}</div>", unsafe_allow_html=True)
        time.sleep(delay)
    placeholder.markdown(f"<div style='background-color: #e8f5e9; color: black; padding: 10px; border-radius: 5px; margin-bottom: 5px;'><strong>Chatbot:</strong> {text}</div>", unsafe_allow_html=True)  # Asegúrate de mostrar el texto completo al final

def chatbot_interface():
    st.title("Chatbot del paciente")
    st.write("Bienvenido a nuestro asistente médico virtual. Aquí puedes hacer preguntas relacionadas con tu salud y obtener respuestas inmediatas. Estoy especializado en hernia inguinal, apendicectomía, colecistectomía y cirugía coloproctológica.")
    st.write("### Conversación")

    # Crear un contenedor para la conversación
    conversation_placeholder = st.container()

    # Mostrar el historial de preguntas en la barra lateral
    with st.sidebar:
        st.write("### Historial de Preguntas")
        for message in st.session_state.history:
            if message['sender'] == 'Usuario':
                st.write(f"**{message['sender']}:** {message['text']}")


    # Preguntas sugeridas
    suggested_questions = [
        "¿Cuáles son los síntomas de una hernia inguinal?",
        "¿Cuándo es necesaria una apendicectomía?",
        "¿Qué cuidados postoperatorios debo tener después de una colecistectomía?",
        "¿Qué es la cirugía coloproctológica?"
    ]
    
    # Mostrar preguntas sugeridas si aún no se ha hecho ninguna pregunta
    if len(st.session_state.history) == 0:
        st.write("### Preguntas Sugeridas")
        cols = st.columns(4)
        for i, question in enumerate(suggested_questions):
            if cols[i].button(question):
                user_input = question
                st.session_state.short_term_memory.append(user_input)
                st.session_state.history.append({'sender': 'Usuario', 'text': user_input})

                # Mostrar la pregunta del usuario en el contenedor de conversación
                with conversation_placeholder:
                    st.markdown(f"<div style='background-color: #e1f5fe; color: black; padding: 10px; border-radius: 5px; margin-bottom: 5px;'><strong>Usuario:</strong> {user_input}</div>", unsafe_allow_html=True)
                
                # Obtener la respuesta del chatbot
                response = asyncio.run(get_answer(user_input, st.session_state.short_term_memory))

                # Mostrar la respuesta del chatbot de manera progresiva
                with conversation_placeholder:
                    write_progressively(response, st.empty())
                
                # Añadir la respuesta del chatbot al historial
                st.session_state.history.append({'sender': 'Chatbot', 'text': response})
                st.session_state.short_term_memory.append(response)

                # Mantener un máximo de 5 elementos en la memoria a corto plazo
                if len(st.session_state.short_term_memory) > 5:
                    st.session_state.short_term_memory.pop(0)

                # Verificar si medico_id está presente antes de intentar añadir la pregunta y respuesta a la base de datos
                if st.session_state.medico_id:
                    # Añadir la pregunta y respuesta a la base de datos
                    add_question(st.session_state.username, st.session_state.medico_id, user_input, response)
                else:
                    st.error("Error: No se ha asignado medico_id al paciente.")

                # Volver a cargar la aplicación para reflejar los cambios
                st.experimental_rerun()
    
    # Mostrar el historial de la conversación
    with conversation_placeholder:
        for message in st.session_state.history:
            if message['sender'] == 'Usuario':
                st.markdown(f"<div style='background-color: #e1f5fe; color: black; padding: 10px; border-radius: 5px; margin-bottom: 5px;'><strong>{message['sender']}:</strong> {message['text']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='background-color: #e8f5e9; color: black; padding: 10px; border-radius: 5px; margin-bottom: 5px;'><strong>{message['sender']}:</strong> {message['text']}</div>", unsafe_allow_html=True)

    user_input = st.text_input("Escribe tu mensaje:")

    if st.button("Enviar") and user_input:
        # Añadir la pregunta del usuario al historial
        st.session_state.short_term_memory.append(user_input)
        st.session_state.history.append({'sender': 'Usuario', 'text': user_input})

        # Mostrar la pregunta del usuario en el contenedor de conversación
        with conversation_placeholder:
            st.markdown(f"<div style='background-color: #e1f5fe; color: black; padding: 10px; border-radius: 5px; margin-bottom: 5px;'><strong>Usuario:</strong> {user_input}</div>", unsafe_allow_html=True)
        
        # Obtener la respuesta del chatbot
        response = asyncio.run(get_answer(user_input, st.session_state.short_term_memory))
        
        # Mostrar la respuesta del chatbot de manera progresiva
        with conversation_placeholder:
            write_progressively(response, st.empty())
        
        # Añadir la respuesta del chatbot al historial
        st.session_state.history.append({'sender': 'Chatbot', 'text': response})
        st.session_state.short_term_memory.append(response)

        # Mantener un máximo de 5 elementos en la memoria a corto plazo
        if len(st.session_state.short_term_memory) > 5:
            st.session_state.short_term_memory.pop(0)

        # Verificar si medico_id está presente antes de intentar añadir la pregunta y respuesta a la base de datos
        if st.session_state.medico_id:
            # Añadir la pregunta y respuesta a la base de datos
            add_question(st.session_state.username, st.session_state.medico_id, user_input, response)
        else:
            st.error("Error: No se ha asignado medico_id al paciente.")

        # Volver a cargar la aplicación para reflejar los cambios
        st.experimental_rerun()


def medico_interface():
    # Cargar el logo
    logo = Image.open("logoCAIS.png")
    
    # Convertir la imagen a base64
    buffered = BytesIO()
    logo.save(buffered, format="PNG")
    logo_base64 = base64.b64encode(buffered.getvalue()).decode()


    st.title("Interfaz del Médico")
    
    with st.sidebar:
        logo_html = f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="data:image/png;base64,{logo_base64}" style="border-radius: 10px; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1); width: 100px;">
        </div>
        """
        st.markdown(logo_html, unsafe_allow_html=True)
        st.write("CAIS - Care AI System")
        option = st.selectbox("FUNCIONES DE MÉDICO", ["Crear Paciente", "Ver Pacientes", "Gestionar Citas", "Eliminar Citas", "Eliminar Paciente", "Ver Historial de Preguntas"])
    
    if option == "Crear Paciente":
        with st.form(key='create_patient_form'):
            st.write("CREAR PACIENTE")
            username = st.text_input("Nombre de usuario")
            email = st.text_input("Email")
            name = st.text_input("Nombre real")
            password = st.text_input("Contraseña", type="password")

            if st.form_submit_button("Crear paciente"):
                if username and email and name and password:
                    create_user(username, email, name, password, role="paciente", medico_id=st.session_state.username)
                    st.success("Paciente creado con éxito")
                else:
                    st.error("Por favor, rellena todos los campos")

    elif option == "Ver Pacientes":
        st.write("### Lista de Pacientes")
        patients = get_patients_of_medico(st.session_state.username)
        for patient in patients:
            st.write(f"- {patient}")

    elif option == "Gestionar Citas":
        st.write("### Gestionar Citas")

        patients = get_all_patients_of_medico(st.session_state.username)
        patient_options = [f"{name} ({username})" for username, name in patients]
        selected_patient = st.selectbox("Selecciona un paciente", patient_options)

        # Extraer el nombre de usuario del paciente seleccionado
        selected_patient_username = selected_patient.split(' (')[1].strip(')')

        appointment_date = st.date_input("Selecciona la fecha de la cita", min_value=datetime.today())
        appointment_time = st.time_input("Selecciona la hora de la cita", value=time_module(9, 0))  # Hora predeterminada de 09:00

        if st.button("Guardar Cita"):
            if selected_patient_username and appointment_date and appointment_time:
                create_appointment(st.session_state.username, selected_patient_username, appointment_date, appointment_time)
                st.success("Cita creada con éxito")
            else:
                st.error("Por favor, selecciona un paciente, una fecha y una hora")

        st.write("### Mis Citas")
        appointments = get_appointments(st.session_state.username)
        if appointments:
            for appointment in appointments:
                st.write(f"Paciente: {appointment['patient_username']} - Fecha: {appointment['appointment_date']} - Hora: {appointment['hora']}")
        else:
            st.write("No tienes citas programadas.")
            
    elif option == "Eliminar Citas":
        st.write("### Eliminar Citas")

        appointments = get_appointments(st.session_state.username)
        if appointments:
            appointment_options = [f"{appointment['patient_username']} - {appointment['appointment_date']} - {appointment['hora']}" for appointment in appointments]
            selected_appointment = st.selectbox("Selecciona una cita", appointment_options)
            
            if st.button("Eliminar Cita"):
                selected_patient_username, appointment_date, appointment_time_str = selected_appointment.split(' - ')
                
                if appointment_time_str != 'None':
                    appointment_time = datetime.strptime(appointment_time_str, '%H:%M:%S').time()
                else:
                    appointment_time = None
                    
                delete_appointment(st.session_state.username, selected_patient_username, appointment_date, appointment_time)
                st.success("Cita eliminada con éxito.")
                st.experimental_rerun()
        else:
            st.write("No tienes citas programadas.")

    elif option == "Eliminar Paciente":
        st.write("### Eliminar Paciente")

        patients = get_all_patients_of_medico(st.session_state.username)
        patient_options = [f"{name} ({username})" for username, name in patients]
        patient_to_delete = st.selectbox("Selecciona un paciente para eliminar", patient_options)

        # Extraer el nombre de usuario del paciente seleccionado
        patient_to_delete_username = patient_to_delete.split(' (')[1].strip(')')

        if st.button("Eliminar Paciente"):
            if patient_to_delete_username:
                delete_patient(patient_to_delete_username)
                st.success(f"Paciente {patient_to_delete_username} ha sido eliminado con éxito.")
                st.experimental_rerun()
            else:
                st.error("Por favor, selecciona un paciente para eliminar")

    elif option == "Ver Historial de Preguntas":
        st.write("### Historial de Preguntas de Pacientes")
        patients = get_all_patients_of_medico(st.session_state.username)
        patient_options = [f"{name} ({username})" for username, name in patients]
        selected_patient = st.selectbox("Selecciona un paciente", patient_options)

        # Extraer el nombre de usuario del paciente seleccionado
        selected_patient_username = selected_patient.split(' (')[1].strip(')')

        if selected_patient_username:
            questions = get_patient_questions(selected_patient_username, st.session_state.username)  # Proporcionar ambos argumentos
            if questions:
                for question in questions:
                    st.write(f"**Pregunta:** {question['question']}")
                    st.write(f"**Respuesta:** {question['answer']}")
                    st.write("---")
            else:
                st.write("No hay preguntas registradas para este paciente.")
        else:
            st.error("Por favor, selecciona un paciente")

    # Colocar el botón de cerrar sesión en la parte inferior del sidebar
    with st.sidebar:
        st.write("---")
        if st.button("Cerrar sesión"):
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.history = []
            st.session_state.short_term_memory = []
            st.session_state.medico_id = None
            st.experimental_rerun()

def supervisor_interface():
    # Cargar el logo
    logo = Image.open("logoCAIS.png")
    
    # Convertir la imagen a base64
    buffered = BytesIO()
    logo.save(buffered, format="PNG")
    logo_base64 = base64.b64encode(buffered.getvalue()).decode()

    st.title("Interfaz del Supervisor")
    medicos = get_all_medicos()

    # Usar una lista de opciones para selección
    medico_options = [medico[0] for medico in medicos]  # Solo los nombres de usuario de los médicos

    with st.sidebar:
        logo_html = f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="data:image/png;base64,{logo_base64}" style="border-radius: 10px; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1); width: 100px;">
        </div>
        """
        st.markdown(logo_html, unsafe_allow_html=True)
        st.write("CAIS - Care AI System")
        option = st.selectbox("FUNCIONES DE SUPERVISOR", ["Crear Médico", "Eliminar Médico", "Ver Citas Médicas"])

    if option == "Crear Médico":
        with st.form(key='create_medico_form'):
            st.write("CREAR MÉDICO")
            username = st.text_input("Nombre de usuario")
            email = st.text_input("Email")
            name = st.text_input("Nombre real")
            password = st.text_input("Contraseña", type="password")

            if st.form_submit_button("Crear médico"):
                if username and email and name and password:
                    create_user(username, email, name, password, role="medico")
                    st.success("Médico creado con éxito")
                else:
                    st.error("Por favor, rellena todos los campos")

    elif option == "Eliminar Médico":
        st.write("### Eliminar Médico")
        medico_to_delete = st.selectbox("Selecciona un médico para eliminar", medico_options)

        if st.button("Eliminar Médico"):
            if medico_to_delete:
                delete_medico(medico_to_delete)
                st.success(f"Médico {medico_to_delete} ha sido eliminado con éxito.")
                st.experimental_rerun()
            else:
                st.error("Por favor, selecciona un médico para eliminar")

    elif option == "Ver Citas Médicas":
        st.write("### Citas Médicas")
        selected_medico_username = st.selectbox("Selecciona un médico", medico_options)

        if selected_medico_username:
            appointments = get_appointments(selected_medico_username)
            if appointments:
                for appointment in appointments:
                    st.write(f"Paciente: {appointment['patient_username']} - Fecha: {appointment['appointment_date']} - Hora: {appointment['hora']}")
            else:
                st.write("No hay citas programadas para este médico.")
        else:
            st.error("Por favor, selecciona un médico")

    # Colocar el botón de cerrar sesión en la parte inferior del sidebar
    with st.sidebar:
        st.write("---")
        if st.button("Cerrar sesión"):
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.history = []
            st.session_state.short_term_memory = []
            st.session_state.medico_id = None
            st.experimental_rerun()


def get_medico_id_for_patient(patient_username):
    # Suponiendo que existe una función para obtener el medico_id para un paciente
    # Aquí puedes reemplazar la función ficticia con la que realmente obtienes el medico_id
    medico_id = get_medico_id_from_database(patient_username)
    return medico_id


def paciente_interface():
    # Cargar el logo
    logo = Image.open("logoCAIS.png")
    
    # Convertir la imagen a base64
    buffered = BytesIO()
    logo.save(buffered, format="PNG")
    logo_base64 = base64.b64encode(buffered.getvalue()).decode()

    # Sidebar con logo y opciones generales
    with st.sidebar:
        logo_html = f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="data:image/png;base64,{logo_base64}" style="border-radius: 10px; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1); width: 100px;">
        </div>
        """
        st.markdown(logo_html, unsafe_allow_html=True)
        st.write("CAIS - Care AI System")

        # Definir las opciones de funcionalidad
        options = ["Dashboard", "Chatbot", "Ver Citas", "Ver Historial de Preguntas"]
        
        # Manejar el valor por defecto del selectbox
        option = st.selectbox(
            "FUNCIONES DE PACIENTE",
            options,
            index=options.index(st.session_state.get("option", "Dashboard"))
        )
        st.session_state.option = option

    # Mostrar bienvenida inicial
    if st.session_state.get("first_login", True):
        st.session_state.option = None
        st.markdown("<h1 style='text-align: center; color: #4CAF50;'>Bienvenido!</h1>", unsafe_allow_html=True)

        # Botones de bienvenida
        col1, col2, col3 = st.columns(3)

        with col1:
            card_html = """
            <div style="padding: 20px; border-radius: 10px; background-color: #f9f9f9; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1); text-align: center;">
                <img src="https://cdn-icons-png.flaticon.com/512/4712/4712027.png" style="width: 70px;">
                <h3 style="color: #333;">Chatbot</h3>
                <p style="color: #666;">Habla con nuestro asistente virtual</p>
            </div>
            """
            if st.button("Ir al Chatbot"):
                st.session_state.option = "Chatbot"
                st.session_state.first_login = False
                st.experimental_rerun()
                st.markdown(card_html, unsafe_allow_html=True)

        with col2:
            card_html = """
            <div style="padding: 20px; border-radius: 10px; background-color: #f9f9f9; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1); text-align: center;">
                <img src="https://cdn-icons-png.flaticon.com/512/2983/2983687.png" style="width: 70px;">
                <h3 style="color: #333;">Ver Citas</h3>
                <p style="color: #666;">Consulta tus próximas citas médicas</p>
            </div>
            """
            if st.button("Ir a Ver Citas"):
                st.session_state.option = "Ver Citas"
                st.session_state.first_login = False
                st.experimental_rerun()
                st.markdown(card_html, unsafe_allow_html=True)

        with col3:
            card_html = """
            <div style="padding: 20px; border-radius: 10px; background-color: #f9f9f9; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1); text-align: center;">
                <img src="https://cdn-icons-png.flaticon.com/512/2921/2921222.png" style="width: 70px;">
                <h3 style="color: #333;">Historial</h3>
                <p style="color: #666;">Revisa tus preguntas anteriores</p>
            </div>
            """
            if st.button("Ir al Historial de Preguntas"):
                st.session_state.option = "Ver Historial de Preguntas"
                st.session_state.first_login = False
                st.experimental_rerun()
                st.markdown(card_html, unsafe_allow_html=True)

    # Dashboard refinado
    if st.session_state.option == "Dashboard" or not st.session_state.get("option"):
        # Establecer opción por defecto al dashboard
        st.session_state.option = "Dashboard"

        # Obtener nombre real del paciente
        real_name = get_real_name(st.session_state.username)

        # Obtener ID del médico asignado al paciente
        medico_id = get_medico_id_from_database(st.session_state.username)

        # Obtener el nombre del médico
        medico_name = get_real_name(medico_id) if medico_id else "No asignado"

        # Recuadros estéticos
        col1, col2 = st.columns(2)

        # Recuadro para el nombre del paciente
        with col1:
            st.markdown(f"<div style='background-color:#E8F5E9; padding: 10px; border-radius: 5px;'>"
                        f"<h2 style='text-align: center; color: #4CAF50;'>Paciente: {real_name}</h2>"
                        f"</div>", unsafe_allow_html=True)

        # Recuadro para el nombre del médico asignado
        with col2:
            st.markdown(f"<div style='background-color:#E8F5E9; padding: 10px; border-radius: 5px;'>"
                        f"<h3 style='text-align: center; color: #4CAF50;'>Médico Asignado: {medico_name}</h3>"
                        f"</div>", unsafe_allow_html=True)

        # Obtener las preguntas del paciente
        questions = get_patient_questions(st.session_state.username, medico_id)
        last_five_questions = questions[-5:] if questions else []

        # Recuadro con scroll para las preguntas
        st.markdown("<h3 style='text-align: center;'>Últimas 5 preguntas:</h3>", unsafe_allow_html=True)
        with st.expander("Ver Preguntas"):
            for q in last_five_questions:
                st.write(f"**Pregunta:** {q['question']}")
                st.write(f"*Fecha:* {q['timestamp']}")
                st.write("---")

    # Opciones funcionales del paciente
    elif st.session_state.option == "Chatbot":
        st.write("### Chatbot")
        st.session_state.medico_id = get_medico_id_from_database(st.session_state.username)
        if not st.session_state.medico_id:
            st.error("No se pudo encontrar el médico asignado para el paciente.")
        else:
            chatbot_interface()
    
    elif st.session_state.option == "Ver Citas":
        st.write("### Mis Citas")
        appointments = get_patient_appointments(st.session_state.username)
        if appointments:
            for appointment in appointments:
                st.write(f"Doctor: {appointment['medico_username']} - Fecha: {appointment['appointment_date']} - Hora: {appointment['hora']}")
        else:
            st.write("No tienes citas programadas.")
    
    elif st.session_state.option == "Ver Historial de Preguntas":
        st.write("### Historial de Preguntas")
        questions = get_patient_questions(st.session_state.username, st.session_state.medico_id)
        if questions:
            for question in questions:
                st.write(f"**Pregunta:** {question['question']}")
                st.write(f"**Respuesta:** {question['answer']}")
                st.write("---")
        else:
            st.write("No hay preguntas registradas.")

    # Colocar el botón de cerrar sesión en la parte inferior del sidebar
    with st.sidebar:
        st.write("---")
        if st.button("Cerrar sesión"):
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.history = []
            st.session_state.short_term_memory = []
            st.session_state.medico_id = None
            st.experimental_rerun()


if __name__ == "__main__":
    main()



































































