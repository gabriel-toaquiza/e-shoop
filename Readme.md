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

> El archivo `.env.example` contiene la plantilla de todas las variables. Cópialo como `.env` y rellénalo.

## Usuarios de prueba (seed)
- **Admin:** admin@tienda.com / admin123
- **Cliente:** juan@email.com / cliente123

## Despliegue en producción

En producción **no** se usa `python run.py` (es el servidor de desarrollo). Se usa un
servidor WSGI real y se apaga el modo debug.

### 1. Variables de entorno del servidor
En el `.env` del servidor:
```
FLASK_DEBUG=0
FLASK_ENV=production
SECRET_KEY=<clave-fuerte-generada>
SESSION_COOKIE_SECURE=1        # solo si el sitio usa HTTPS
DB_USER=...  DB_PASSWORD=...  DB_HOST=...  DB_NAME=...
```
Genera una clave fuerte:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Instalar dependencias y migrar
```bash
pip install -r requirements.txt
flask --app run db upgrade
```

### 3. Levantar con un servidor WSGI

**Linux / Mac (Gunicorn):**
```bash
gunicorn -w 4 -b 0.0.0.0:8000 run:app
```
`run:app` = el objeto `app` dentro de `run.py`. `-w 4` = 4 procesos de trabajo.

**Windows (Waitress)** — Gunicorn no funciona en Windows:
```bash
waitress-serve --listen=0.0.0.0:8000 run:app
```

Para producción real, delante del servidor WSGI se suele poner **Nginx** como proxy
inverso (sirve los archivos estáticos y gestiona HTTPS).