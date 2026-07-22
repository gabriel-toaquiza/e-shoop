import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # DEBUG apagado por defecto (producción). Para desarrollo: FLASK_DEBUG=1 en el .env
    debug = os.getenv('FLASK_DEBUG', '0') == '1'
    app.run(host=os.getenv('HOST', '127.0.0.1'),
            port=int(os.getenv('PORT', '5000')),
            debug=debug)
