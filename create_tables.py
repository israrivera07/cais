import psycopg2

def create_tables():
    conn = psycopg2.connect(
        dbname='your_dbname',        # Reemplaza con el nombre de tu base de datos
        user='your_user',            # Reemplaza con tu usuario de PostgreSQL
        password='your_password',    # Reemplaza con tu contraseña de PostgreSQL
        host='localhost',
        port='5432'
    )
    cur = conn.cursor()
    
    # Crear tabla de usuarios
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL
    );
    ''')
    
    # Insertar roles de ejemplo
    cur.execute('''
    INSERT INTO users (username, password, role)
    VALUES
    ('supervisor', 'super_secure_password', 'Supervisor'),
    ('medico1', 'super_secure_password', 'Medico1'),
    ('paciente1', 'super_secure_password', 'Paciente1')
    ON CONFLICT (username) DO NOTHING;
    ''')
    
    conn.commit()
    cur.close()
    conn.close()

if __name__ == '__main__':
    create_tables()
