# e-Shop — Tienda de Manualidades

Tienda en línea de manualidades (totebags, cuadros, decoración) desarrollada con **Flask**, como proyecto de la materia *Diseño y Creación de Páginas Web*.

## Integrantes
- Gabriel Toaquiza
- Juan Pacheco
- Angelo Navarrete

## Tecnologías
- Python + Flask
- Flask-SQLAlchemy + Flask-Migrate (base de datos)
- Flask-Login (autenticación) · Flask-WTF (formularios)
- MySQL / MariaDB · Bootstrap 5

## Requisitos previos
- Python 3.x
- MySQL o MariaDB (por ejemplo con XAMPP)
- Git

## Instalación

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/gabriel-toaquiza/e-shoop.git
   cd e-shoop
   ```

2. Crear y activar el entorno virtual:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/Mac:
   source .venv/bin/activate
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Crear el archivo `.env` en la raíz:
   ```
   SECRET_KEY=una-clave-secreta
   DB_USER=ecommerce_user
   DB_PASSWORD=123456
   DB_HOST=localhost
   DB_NAME=ecommerce_db
   ```

5. Crear la base de datos en MySQL:
   ```sql
   CREATE DATABASE ecommerce_db;
   CREATE USER 'ecommerce_user'@'localhost' IDENTIFIED BY '123456';
   GRANT ALL PRIVILEGES ON ecommerce_db.* TO 'ecommerce_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

6. Aplicar las migraciones:
   ```bash
   flask --app run db upgrade
   ```

7. (Opcional) Cargar datos de prueba:
   ```bash
   python seed.py
   ```

8. Ejecutar la aplicación:
   ```bash
   python run.py
   ```
   Abrir: http://127.0.0.1:5000/

## Usuarios de prueba (seed)
- **Admin:** admin@tienda.com / admin123
- **Cliente:** juan@email.com / cliente123