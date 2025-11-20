#!/usr/bin/env python
"""
Script de prueba para ver si el servidor responde
"""

from waitress import serve
from flask import Flask

test_app = Flask(__name__)

@test_app.route('/')
def hello():
    return "✅ Server is working!"

if __name__ == "__main__":
    print("🚀 Iniciando servidor de prueba en http://localhost:5002")
    serve(test_app, host='localhost', port=5002)
