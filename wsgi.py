"""
WSGI entry point para Gunicorn en producción.
"""
from run import app

if __name__ == "__main__":
    app.run()



