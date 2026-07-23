<div align="center">

# 🛍️ Verova — Tienda de Manualidades

**Tienda en línea de artesanías hechas a mano** (tote bags, cuadros de cuentas, velas, cunas nido y decoración de interiores), desarrollada con **Flask** como proyecto de la materia *Diseño y Creación de Páginas Web* — Universidad Politécnica Salesiana.

</div>

---

## 📑 Índice

- [Descripción](#-descripción)
- [Características](#-características)
- [Tecnologías](#-tecnologías)
- [Arquitectura del proyecto](#-arquitectura-del-proyecto)
- [Modelo de datos](#-modelo-de-datos)
- [Instalación y puesta en marcha](#-instalación-y-puesta-en-marcha)
- [Variables de entorno](#-variables-de-entorno)
- [Usuarios de prueba](#-usuarios-de-prueba)
- [Flujo de compra y pago](#-flujo-de-compra-y-pago)
- [Panel de administración](#-panel-de-administración)
- [Despliegue en producción](#-despliegue-en-producción)
- [Equipo](#-equipo)

---

## 📖 Descripción

Verova es un **e-commerce completo** que permite a los clientes explorar un catálogo de productos artesanales, personalizar piezas, gestionar un carrito y favoritos, y realizar pedidos con **pago por transferencia bancaria verificada**. Incluye además un **panel de administración** para gestionar categorías, productos, clientes y pedidos.

El proyecto está construido siguiendo el **patrón application factory** de Flask, con la lógica separada en *blueprints* y una base de datos relacional gestionada mediante migraciones.

---

## ✨ Características

### Cara pública (cliente)
- **Catálogo** con página de inicio, tienda con **búsqueda y filtro por categoría**, y paginación.
- **Detalle de producto** con galería de imágenes (portada + hasta 4 adicionales) y productos relacionados.
- **Productos personalizables**: el cliente escribe especificaciones (color, medidas, texto a bordar…) antes de añadir al carrito, según las instrucciones que define el administrador.
- **Carrito de compras** basado en sesión, con soporte para líneas independientes (un mismo producto con distintas personalizaciones se agrupa por separado) y control de stock.
- **Favoritos** que funcionan tanto para usuarios anónimos (guardados en sesión) como registrados (guardados en base de datos), fusionándose al iniciar sesión.
- **Autenticación** de usuarios (registro, inicio y cierre de sesión) con validación de correo único y cédula ecuatoriana.
- **Historial de pedidos** ("Mis pedidos") con línea de tiempo del estado.
- Páginas informativas: **Nosotros, Contacto** (con formulario y preguntas frecuentes), **Términos y condiciones** y **Política de privacidad**.

### Panel de administración
- **Dashboard** con métricas: ventas totales, pedidos, clientes, pedidos por verificar, alertas de inventario (bajo stock) y últimos pedidos.
- **CRUD de categorías y productos** con carga de imágenes, filtros de búsqueda y eliminación con confirmación.
- **Gestión de clientes** (activar / desactivar cuentas).
- **Gestión de pedidos**: verificación de comprobantes de pago, avance de estados, cancelación y eliminación, con **reposición automática de stock**.

### Transversal
- Protección **CSRF** en todos los formularios.
- Contraseñas **hasheadas** (nunca en texto plano).
- Manejo de dinero con **`Decimal`** para evitar errores de redondeo.
- Comprobantes de pago guardados en **carpeta privada** (fuera de `static/`), servidos solo al dueño del pedido o al administrador.
- Páginas de error personalizadas (403, 404, 413, 500).
- Descuento de stock **atómico** (a prueba de condiciones de carrera).

---

## 🧰 Tecnologías

| Categoría | Herramientas |
|---|---|
| **Lenguaje** | Python 3.12+ |
| **Framework** | Flask 3 (application factory + blueprints) |
| **Base de datos** | MySQL / MariaDB (vía PyMySQL) |
| **ORM y migraciones** | SQLAlchemy 2 · Flask-SQLAlchemy · Flask-Migrate (Alembic) |
| **Autenticación** | Flask-Login |
| **Formularios y seguridad** | Flask-WTF · WTForms · CSRFProtect |
| **Frontend** | Jinja2 · Bootstrap 5 · Bootstrap Icons · Google Fonts (Marcellus + Poppins) |
| **Servidor WSGI** | Gunicorn (Linux) · Waitress (Windows) |
| **Configuración** | python-dotenv |

---

## 🏗️ Arquitectura del proyecto

```
e-shoop/
├── app/
│   ├── __init__.py            # Application factory: registra extensiones, blueprints y context processors
│   ├── config.py              # Configuración (BD, seguridad, datos bancarios)
│   ├── estados.py             # Estados de pedido centralizados (etiquetas, colores, flujo)
│   ├── errores.py             # Manejadores de errores HTTP (403/404/413/500)
│   ├── utils.py               # Utilidades compartidas (redirecciones seguras)
│   │
│   ├── models/                # Modelos de datos (una tabla por archivo)
│   │   ├── usuario.py
│   │   ├── categoria.py
│   │   ├── producto.py
│   │   └── pedido.py          # Pedido + DetallePedido
│   │
│   ├── blueprints/
│   │   ├── public/            # Rutas de cara al cliente
│   │   │   ├── routes.py
│   │   │   ├── carrito_utils.py   # Lógica del carrito en sesión
│   │   │   └── pagos_utils.py     # Validación de cédula y comprobantes
│   │   ├── auth/              # Registro, login, logout
│   │   │   ├── routes.py
│   │   │   └── forms.py
│   │   └── admin/            # Panel de administración (rutas divididas por área)
│   │       ├── routes.py          # Agregador
│   │       ├── rutas_dashboard.py
│   │       ├── rutas_categorias.py
│   │       ├── rutas_productos.py
│   │       ├── rutas_clientes.py
│   │       ├── rutas_pedidos.py
│   │       ├── helpers.py         # Constantes y utilidades de imagen
│   │       ├── forms.py
│   │       └── decorators.py      # @admin_requerido
│   │
│   ├── templates/            # Plantillas Jinja2 (public / admin / auth / partials / errores)
│   └── static/              # CSS y estructura de imágenes (marca, banners, productos, etc.)
│
├── migrations/              # Migraciones de Alembic
├── run.py                   # Punto de entrada (objeto `app` para el WSGI)
├── seed.py                  # Datos de prueba iniciales
├── requirements.txt
├── .env.example             # Plantilla de variables de entorno
└── README.md
```

---

## 🗄️ Modelo de datos

| Tabla | Descripción | Campos destacados |
|---|---|---|
| **usuarios** | Clientes y administradores | `email` (único), `password` (hash), `rol` (cliente/admin), `activo` |
| **categorias** | Categorías del catálogo | `nombre` (único), `imagen`, `activa` |
| **productos** | Artículos a la venta | `precio` (Decimal), `stock`, `imagen` + `imagenes` (galería), `personalizable`, `instrucciones_personalizacion` |
| **pedidos** | Pedidos realizados | `estado`, `total`, datos de entrega (`nombre_receptor`, `cedula`, `direccion`), `comprobante` |
| **detalle_pedido** | Líneas de cada pedido | `cantidad`, `precio_unitario`, `especificaciones` |
| **favoritos** | Relación N–M usuario ↔ producto | (tabla de asociación) |

**Relaciones principales:** un usuario tiene muchos pedidos; una categoría tiene muchos productos; un pedido tiene muchas líneas de detalle; usuarios y productos se relacionan mediante favoritos.

**Estados de un pedido:**
`en_verificacion` → `pagado` → `enviado` → `entregado`, más `rechazado` (comprobante inválido) y `cancelado`.

---

## 🚀 Instalación y puesta en marcha

### Requisitos previos
- **Python 3.12 o superior**
- **MySQL / MariaDB** (por ejemplo, mediante [XAMPP](https://www.apachefriends.org/))
- **Git**

### Pasos

**1. Clonar el repositorio**
```bash
git clone https://github.com/gabriel-toaquiza/e-shoop.git
cd e-shoop
```

**2. Crear y activar el entorno virtual**
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux / Mac:
source venv/bin/activate
```

**3. Instalar dependencias**
```bash
pip install -r requirements.txt
```

**4. Configurar las variables de entorno**

Copia la plantilla y edita los valores:
```bash
# Windows:   copy .env.example .env
# Linux/Mac: cp .env.example .env
```
> Consulta la sección [Variables de entorno](#-variables-de-entorno) para el detalle de cada valor.

**5. Crear la base de datos en MySQL**
```sql
CREATE DATABASE ecommerce_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ecommerce_user'@'localhost' IDENTIFIED BY '123456';
GRANT ALL PRIVILEGES ON ecommerce_db.* TO 'ecommerce_user'@'localhost';
FLUSH PRIVILEGES;
```

**6. Aplicar las migraciones** (crea todas las tablas)
```bash
flask --app run db upgrade
```

**7. (Opcional) Cargar datos de prueba**
```bash
python seed.py
```

**8. Ejecutar la aplicación**
```bash
python run.py
```
Abrir en el navegador: **http://127.0.0.1:5000/**

> 💡 Para desarrollo con recarga automática, asegúrate de tener `FLASK_DEBUG=1` en tu `.env`.

---

## 🔐 Variables de entorno

Todas las variables se definen en el archivo `.env` (nunca se sube al repositorio). La plantilla completa está en **`.env.example`**.

| Variable | Descripción | Ejemplo |
|---|---|---|
| `SECRET_KEY` | Clave para firmar sesiones y cookies. **Obligatoria en producción.** | `a1b2c3...` |
| `DB_USER` / `DB_PASSWORD` | Credenciales de MySQL | `ecommerce_user` / `123456` |
| `DB_HOST` / `DB_NAME` | Host y nombre de la base de datos | `localhost` / `ecommerce_db` |
| `FLASK_DEBUG` | `1` en desarrollo, `0` en producción | `1` |
| `HOST` / `PORT` | Dirección y puerto (opcionales) | `127.0.0.1` / `5000` |
| `SESSION_COOKIE_SECURE` | `1` para enviar cookies solo por HTTPS | `0` |

> Genera una clave segura con:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

También se configuran en `app/config.py` los **datos bancarios** para el pago por transferencia (`DATOS_BANCARIOS`); reemplaza los valores placeholder por los reales.

---

## 👥 Usuarios de prueba

Tras ejecutar `python seed.py`:

| Rol | Correo | Contraseña |
|---|---|---|
| **Administrador** | `admin@tienda.com` | `admin123` |
| **Cliente** | `juan@email.com` | `cliente123` |

---

## 💳 Flujo de compra y pago

Como no se utiliza una pasarela de pagos, el flujo es por **transferencia bancaria con verificación manual**:

1. El cliente añade productos al carrito (indicando especificaciones si el producto es personalizable).
2. En el **checkout** ingresa sus datos de entrega (nombre, cédula validada, dirección) y **sube el comprobante de la transferencia** — obligatorio para crear el pedido.
3. El pedido nace en estado **`En verificación`**. El stock **no** se descuenta todavía.
4. El **administrador** revisa el comprobante:
   - ✅ **Confirma el pago** → el pedido pasa a `Pagado` y el stock se descuenta de forma atómica.
   - ❌ **Rechaza el comprobante** → el pedido pasa a `Rechazado` y el cliente puede subir otro.
5. A partir de `Pagado`, el administrador avanza el pedido por `Enviado` → `Entregado`.

> Los comprobantes se almacenan en una **carpeta privada** y solo pueden verlos el dueño del pedido o un administrador.

---

## 🛠️ Panel de administración

Accesible en **`/admin/dashboard`** (requiere una cuenta con rol `admin`). Presenta una interfaz de tipo *dashboard* con barra lateral de navegación:

- **Panel**: métricas generales y alertas de inventario.
- **Pedidos**: listado con filtro por estado, verificación de pagos y gestión de estados.
- **Productos** y **Categorías**: CRUD completo con imágenes y filtros de búsqueda.
- **Clientes**: activar o desactivar cuentas.

---

## 🌐 Despliegue en producción

En producción **no** se usa `python run.py` (es el servidor de desarrollo). Se emplea un servidor WSGI real con el modo *debug* desactivado.

**1. Variables de entorno del servidor** (`.env`):
```
FLASK_DEBUG=0
SECRET_KEY=<clave-fuerte-generada>
SESSION_COOKIE_SECURE=1        # solo si el sitio usa HTTPS
DB_USER=...  DB_PASSWORD=...  DB_HOST=...  DB_NAME=...
```

**2. Instalar dependencias y aplicar migraciones:**
```bash
pip install -r requirements.txt
flask --app run db upgrade
```

**3. Levantar con un servidor WSGI:**

- **Linux / Mac (Gunicorn):**
  ```bash
  gunicorn -w 4 -b 0.0.0.0:8000 run:app
  ```
- **Windows (Waitress)** — Gunicorn no funciona en Windows:
  ```bash
  waitress-serve --listen=0.0.0.0:8000 run:app
  ```

Para producción real, se recomienda un **proxy inverso (Nginx)** delante del servidor WSGI para servir archivos estáticos y gestionar HTTPS.

---

## 👨‍💻 Equipo

Proyecto desarrollado para la materia **Diseño y Creación de Páginas Web** (2026) — Universidad Politécnica Salesiana.

| Integrante | Correo |
|---|---|
| **Gabriel Toaquiza** | gtoaquizac@est.ups.edu.ec |
| **Juan Pacheco** | jpachecon1@est.ups.edu.ec |
| **Angelo Navarrete** | anavarretev2@est.ups.edu.ec |

---

<div align="center">
<sub>Hecho con 🧶 y Flask · Verova 2026</sub>
</div>
