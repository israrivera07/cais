import streamlit as st
import pandas as pd
from datetime import datetime 
from datetime import time as time_module
import time 
from utils.auth import (
    authenticate_user, create_user, get_real_name, 
    get_patients_of_medico, get_all_medicos, create_appointment, 
    get_appointments, get_patient_appointments, get_all_patients_of_medico, 
    get_all_medical_appointments, delete_medico, delete_patient, delete_appointment, get_patient_questions, add_question, get_medico_id_from_database, obtener_estado_formulario, guardar_respuesta_formulario, actualizar_estado_formulario,
    obtener_respuestas_formulario_por_rol
)
import asyncio
from io import BytesIO
from PIL import Image
import base64
import matplotlib.pyplot as plt
from chatbot.chatbot import get_answer

# Configuración inicial de la página
st.set_page_config(page_title="CAIS - CARE AI SYSTEM", page_icon=":hospital:", layout="wide")

# Añadir esto después de los imports:
st.markdown("""
    <style>
        /* Fuentes y colores generales */
        body {
            font-family: 'Arial', sans-serif;
            color: #333;
        }
        /* Tarjetas */
        .card {
            background: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        /* Botones principales */
        .stButton>button {
            background-color: #0077B6;
            color: white;
            border-radius: 5px;
        }
    </style>
""", unsafe_allow_html=True)


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

                    st.rerun()
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
    """Escribe el texto de manera progresiva"""
    placeholder.markdown("")  # Limpiar primero
    full_response = ""
    for chunk in text.split():
        full_response += chunk + " "
        placeholder.markdown(f"""
            <div style='background: #f0f2f6; color: #333; border-radius: 10px 10px 10px 0; padding: 10px; margin: 5px 0;'>
                {full_response}
            </div>
        """, unsafe_allow_html=True)
        time.sleep(delay)
    return full_response

def chatbot_interface():
    st.title("Chatbot del paciente")
    st.write("Bienvenido a nuestro asistente médico virtual. Aquí puedes hacer preguntas relacionadas con tu salud y obtener respuestas inmediatas. Estoy especializado en hernia inguinal, apendicectomía, colecistectomía y cirugía coloproctológica.")
    
    # Inicializar la sesión si no existe
    if "history" not in st.session_state:
        st.session_state.history = []
    if "short_term_memory" not in st.session_state:
        st.session_state.short_term_memory = []
    if "first_interaction" not in st.session_state:
        st.session_state.first_interaction = True

    # Mostrar el historial de preguntas en la barra lateral
    with st.sidebar:
        st.write("### Historial de Preguntas")
        for message in st.session_state.history:
            if message['sender'] == 'Usuario':
                st.write(f"**{message['sender']}:** {message['text']}")

    # Preguntas sugeridas solo en la primera interacción
    if st.session_state.first_interaction:
        suggested_questions = [
            "¿Cuáles son los síntomas de una hernia inguinal?",
            "¿Cuándo es necesaria una apendicectomía?",
            "¿Qué cuidados postoperatorios debo tener después de una colecistectomía?",
            "¿Qué es la cirugía coloproctológica?"
        ]
        
        with st.expander("¿Necesitas ayuda? Prueba estas preguntas:"):
            for question in suggested_questions:
                if st.button(question, key=f"suggested_{question}"):
                    process_user_input(question)
                    st.session_state.first_interaction = False
                    st.rerun()

    # Mostrar historial de conversación
    for message in st.session_state.history:
        if message['sender'] == "Usuario":
            with st.chat_message("user", avatar="👤"):
                st.markdown(f"""
                    <div style='background: #0077B6; color: white; border-radius: 10px 10px 0 10px; padding: 10px; margin: 5px 0;'>
                        {message['text']}
                    </div>
                """, unsafe_allow_html=True)
        else:
            with st.chat_message("assistant", avatar="logo_cais.png"):
                st.markdown(f"""
                    <div style='background: #f0f2f6; color: #333; border-radius: 10px 10px 10px 0; padding: 10px; margin: 5px 0;'>
                        {message['text']}
                    </div>
                """, unsafe_allow_html=True)

    # Entrada del usuario
    user_input = st.chat_input("Escribe tu mensaje:")
    if user_input:
        if st.session_state.first_interaction:
            st.session_state.first_interaction = False
        process_user_input(user_input)

def process_user_input(user_input):
    """Procesa la entrada del usuario y gestiona la respuesta del chatbot."""
    st.session_state.short_term_memory.append(user_input)
    st.session_state.history.append({'sender': 'Usuario', 'text': user_input})
    
    # Mostrar input del usuario
    with st.chat_message("user", avatar="👤"):
        st.markdown(f"""
            <div style='background: #0077B6; color: white; border-radius: 10px 10px 0 10px; padding: 10px; margin: 5px 0;'>
                {user_input}
            </div>
        """, unsafe_allow_html=True)
    
    # Generar y mostrar respuesta
    with st.chat_message("assistant", avatar="⚕️"):
        response_placeholder = st.empty()
        with st.spinner("El asistente está pensando..."):
            response = asyncio.run(get_answer(user_input, st.session_state.short_term_memory))
            full_response = write_progressively(response, response_placeholder)
    
    st.session_state.history.append({'sender': 'Chatbot', 'text': full_response})
    st.session_state.short_term_memory.append(full_response)

    if len(st.session_state.short_term_memory) > 5:
        st.session_state.short_term_memory.pop(0)

    if "medico_id" in st.session_state and st.session_state.medico_id:
        add_question(st.session_state.username, st.session_state.medico_id, user_input, full_response)
        print(f"Pregunta añadida a la base de datos: {user_input} -> {full_response}")
    else:
        st.error("Error: No se ha asignado medico_id al paciente.")
    
    st.rerun()


def medico_interface():
    # Cargar el logo
    logo = Image.open("logoCAIS.png")
    
    # Convertir la imagen a base64
    buffered = BytesIO()
    logo.save(buffered, format="PNG")
    logo_base64 = base64.b64encode(buffered.getvalue()).decode()

    # Título de la interfaz
    st.title("Interfaz del Médico")

    # Sidebar con logo y menú de opciones
    with st.sidebar:
        logo_html = f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="data:image/png;base64,{logo_base64}" style="border-radius: 10px; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1); width: 100px;">
        </div>
        """
        st.markdown(logo_html, unsafe_allow_html=True)
        st.write("CAIS - Care AI System")
        option = st.selectbox(
            "FUNCIONES DE MÉDICO", 
            ["Dashboard", "Crear Paciente", "Ver Pacientes", "Gestionar Citas", "Eliminar Citas", "Eliminar Paciente", "Ver Historial de Preguntas", "Formulario de Satisfacción"]
        )

    # Pantalla de inicio o dashboard
    if option == "Dashboard":
        st.subheader(f"Bienvenido, {st.session_state.username} 👋")
        st.write("""
            Esta es la interfaz principal de médico. Aquí puedes realizar las siguientes acciones:
            - **Crear Paciente**: Registra un nuevo paciente en el sistema.
            - **Ver Pacientes**: Visualiza y gestiona tu lista de pacientes.
            - **Gestionar Citas**: Programa y administra tus citas con los pacientes.
            - **Eliminar Citas**: Cancela citas programadas.
            - **Eliminar Paciente**: Retira a un paciente de tu lista.
            - **Ver Historial de Preguntas**: Consulta las preguntas y respuestas de tus pacientes.
            - **Formulario de Satisfacción**: Completa un formulario para ayudar a mejorar el sistema.
        """)
        
    # Funcionalidades específicas del médico
    elif option == "Crear Paciente":
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
                st.rerun()
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
                st.rerun()
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
            questions = get_patient_questions(selected_patient_username, st.session_state.username)
            if questions:
                for question in questions:
                    st.write(f"**Pregunta:** {question['question']}")
                    st.write(f"**Respuesta:** {question['answer']}")
                    st.write("---")
            else:
                st.write("No hay preguntas registradas para este paciente.")
        else:
            st.error("Por favor, selecciona un paciente")

    elif option == "Formulario de Satisfacción":
        st.write("### Formulario de Satisfacción")
        formulario_satisfaccion()

    # Colocar el botón de cerrar sesión en la parte inferior del sidebar
    with st.sidebar:
        st.write("---")
        if st.button("Cerrar sesión"):
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.history = []
            st.session_state.short_term_memory = []
            st.session_state.medico_id = None
            st.rerun()

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

    # Estado inicial para mostrar el dashboard de bienvenida
    if 'supervisor_dashboard' not in st.session_state:
        st.session_state.supervisor_dashboard = True  # Controla si está en el dashboard inicial

    # Mostrar la bienvenida del supervisor en el dashboard inicial
    if st.session_state.supervisor_dashboard:
        st.subheader(f"Bienvenido, {st.session_state.username}")
        st.write("Como supervisor, puedes realizar las siguientes funciones en el sistema CAIS:")
        st.markdown("""
            - **Crear Médico**: Agrega un nuevo médico al sistema.
            - **Eliminar Médico**: Elimina médicos registrados.
            - **Ver Citas Médicas**: Consulta las citas programadas de cada médico.
            - **Ver Respuestas de Formularios**: Revisa las respuestas de satisfacción proporcionadas por los pacientes y médicos.
        """)
        st.write("Selecciona una opción del menú lateral para empezar.")
    
    # Barra lateral de opciones
    with st.sidebar:
        logo_html = f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="data:image/png;base64,{logo_base64}" style="border-radius: 10px; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1); width: 100px;">
        </div>
        """
        st.markdown(logo_html, unsafe_allow_html=True)
        st.write("CAIS - Care AI System")
        option = st.selectbox("FUNCIONES DE SUPERVISOR", ["Dashboard", "Crear Médico", "Eliminar Médico", "Ver Citas Médicas", "Ver Respuestas de Formularios"])

    # Ocultar el dashboard si se selecciona alguna otra opción
    if option != "Dashboard":
        st.session_state.supervisor_dashboard = False

    # Definir funcionalidades según la opción seleccionada
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
                st.rerun()
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

    elif option == "Ver Respuestas de Formularios":
        st.write("### Respuestas de Formularios de Pacientes y Médicos")

        # Obtener respuestas de formularios por rol
        respuestas_pacientes = obtener_respuestas_formulario_por_rol('paciente')
        respuestas_medicos = obtener_respuestas_formulario_por_rol('medico')

        # Mostrar respuestas de pacientes
        st.subheader("Respuestas de Pacientes")
        if respuestas_pacientes:
            df_pacientes = pd.DataFrame(respuestas_pacientes)
            st.dataframe(df_pacientes)

            # Calcular y mostrar las medias de las valoraciones
            media_satisfaccion_pacientes = df_pacientes['satisfaccion'].mean()
            media_funcionalidad_pacientes = df_pacientes['funcionalidad'].mean()
            media_usabilidad_pacientes = df_pacientes['usabilidad'].mean()

            st.write(f"Media de Satisfacción: {media_satisfaccion_pacientes:.2f}")
            st.write(f"Media de Funcionalidad: {media_funcionalidad_pacientes:.2f}")
            st.write(f"Media de Usabilidad: {media_usabilidad_pacientes:.2f}")

            # Crear gráfico de barras para pacientes
            st.subheader("Gráfico de Medias de Pacientes")
            valores_pacientes = [media_satisfaccion_pacientes, media_funcionalidad_pacientes, media_usabilidad_pacientes]
            etiquetas = ['Satisfacción', 'Funcionalidad', 'Usabilidad']

            fig, ax = plt.subplots()
            ax.bar(etiquetas, valores_pacientes, color=['blue', 'orange', 'green'])
            ax.set_ylabel('Media')
            ax.set_title('Medias de Valoraciones de Pacientes')
            st.pyplot(fig)
        else:
            st.write("No hay respuestas de formularios de pacientes.")

        # Mostrar respuestas de médicos
        st.subheader("Respuestas de Médicos")
        if respuestas_medicos:
            df_medicos = pd.DataFrame(respuestas_medicos)
            st.dataframe(df_medicos)

            # Calcular y mostrar las medias de las valoraciones
            media_satisfaccion_medicos = df_medicos['satisfaccion'].mean()
            media_funcionalidad_medicos = df_medicos['funcionalidad'].mean()
            media_usabilidad_medicos = df_medicos['usabilidad'].mean()

            st.write(f"Media de Satisfacción: {media_satisfaccion_medicos:.2f}")
            st.write(f"Media de Funcionalidad: {media_funcionalidad_medicos:.2f}")
            st.write(f"Media de Usabilidad: {media_usabilidad_medicos:.2f}")

            # Crear gráfico de barras para médicos
            st.subheader("Gráfico de Medias de Médicos")
            valores_medicos = [media_satisfaccion_medicos, media_funcionalidad_medicos, media_usabilidad_medicos]
            etiquetas_medicos = ['Satisfacción', 'Funcionalidad', 'Usabilidad']

            fig, ax = plt.subplots()
            ax.bar(etiquetas_medicos, valores_medicos, color=['blue', 'orange', 'green'])
            ax.set_ylabel('Media')
            ax.set_title('Medias de Valoraciones de Médicos')
            st.pyplot(fig)
        else:
            st.write("No hay respuestas de formularios de médicos.")

    # Botón de cerrar sesión en la barra lateral
    with st.sidebar:
        st.write("---")
        if st.button("Cerrar sesión"):
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.history = []
            st.session_state.short_term_memory = []
            st.session_state.supervisor_dashboard = True
            st.rerun()


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
        options = ["Dashboard", "Chatbot", "Ver Citas", "Ver Historial de Preguntas", "Formulario de Satisfacción"]
        
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
        st.markdown("""
                <h1 style='
                    text-align: center; 
                    color: #06bcbf;  /* Verde más oscuro/médico */
                    font-family: 'Roboto', sans-serif;
                    font-size: 2em;  /* Más compacto */
                    margin: 10px 0 5px 0;
                    padding: 8px;
                    background-color: #E8F5E9;  /* Fondo verde claro */
                    border-radius: 8px;
                    border-left: 4px solid #06bcbf;
                '>Bienvenido a <strong>CAIS</strong></h1>
                
                <p style='
                    text-align: center;
                    color: #026c6e;
                    font-family: 'Roboto', sans-serif;
                    margin-bottom: 20px;
                '>Care AI System</p>
            """, unsafe_allow_html=True)

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
                st.rerun()
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
                st.rerun()
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
                st.rerun()
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
            st.markdown(f"""<div style='background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px;'>
                        <h2 style='color: #0077B6; text-align: center;'>👤 {real_name}</h2>
                        </div>""", unsafe_allow_html=True)

        # Recuadro para el nombre del médico asignado
        with col2:
            st.markdown(f"""<div style='background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px;'>
                        <h3 style='text-align: center; color: #555;'>⚕️Médico Asignado: {medico_name}</h3>
                        </div>""", unsafe_allow_html=True)

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
    
    elif st.session_state.option == "Formulario de Satisfacción":
        st.write("### Formulario de Satisfacción")
        formulario_satisfaccion()

    # Colocar el botón de cerrar sesión en la parte inferior del sidebar
    with st.sidebar:
        st.write("---")
        if st.button("Cerrar sesión"):
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.history = []
            st.session_state.short_term_memory = []
            st.session_state.medico_id = None
            st.rerun()

def formulario_satisfaccion():
    # Obtener el rol y estado del formulario del usuario
    usuario = st.session_state.username
    rol = st.session_state.role
    
    # Verificar si el formulario ya fue completado en la sesión o en la base de datos
    formulario_completado = st.session_state.get("formulario_completado", False) or obtener_estado_formulario(usuario)

    if formulario_completado:
        st.write("Formulario ya respondido. ¡Muchas gracias!")
    else:
        st.write(f"Formulario de satisfacción para {rol.capitalize()}")

        # Formulario de satisfacción
        with st.form("Formulario de Satisfacción"):
            satisfaccion = st.slider("¿Cómo calificarías tu satisfacción general?", 1, 5, 3)
            funcionalidad = st.slider("¿Cómo calificarías la funcionalidad de la app?", 1, 5, 3)
            usabilidad = st.slider("¿Cómo calificarías la usabilidad de la app?", 1, 5, 3)
            mejoras = st.text_area("¿Tienes alguna sugerencia de mejora?", "")
            submit_button = st.form_submit_button("Enviar")

            if submit_button:
                # Almacenar la respuesta en la base de datos
                guardar_respuesta_formulario(usuario, rol, satisfaccion, funcionalidad, usabilidad, mejoras)
                actualizar_estado_formulario(usuario)

                # Marcar el formulario como completado en la sesión actual
                st.session_state["formulario_completado"] = True
                st.toast("¡Gracias por tu feedback!", icon="👏")



if __name__ == "__main__":
    main()



































































