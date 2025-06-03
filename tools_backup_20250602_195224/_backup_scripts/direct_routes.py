#!/usr/bin/env python3
"""
Rutas directas para acceso garantizado sin dependencias
Este archivo se carga antes de MongoDB y otras dependencias
para asegurar acceso incluso si hay errores en la aplicación principal
"""

import os
from flask import Flask, send_from_directory, session, redirect, request, jsonify, url_for

def register_direct_routes(app):
    """Registra rutas de acceso garantizado antes de cargar otros componentes"""
    
    # ================================================================
    # ACCESO SUPER-SIMPLE EN LA RAÍZ: FUNCIONA EN TODOS LOS ENTORNOS
    # ================================================================
    
    # Ruta en la raíz para fácil acceso
    @app.route('/admin-login')
    def admin_login_root():
        """Página de acceso admin - accesible desde la raíz"""
        return send_from_directory('static', 'admin_login.html')
    
    # Bypass directo para admin por defecto
    @app.route('/direct_admin')
    def direct_admin():
        """Bypass directo como admin por defecto"""
        try:
            # Limpiar cualquier sesión anterior
            session.clear()
            
            # Datos de admin por defecto
            session.permanent = True
            session['user_id'] = '680bc20aa170ac7fe8e58bec'
            session['email'] = 'admin@example.com'
            session['username'] = 'administrator'
            session['role'] = 'admin'
            session['logged_in'] = True
            session.modified = True
            
            print("ACCESO GARANTIZADO: Admin Por Defecto")
            return redirect('/admin/')
        except Exception as e:
            print(f"ERROR en direct_admin: {e}")
            # Incluso en caso de error, redirigir al admin
            return redirect('/admin/')
    
    # Bypass para ED Frutos
    @app.route('/direct_admin_edf')
    def direct_admin_edf():
        """Bypass directo como ED Frutos"""
        try:
            # Limpiar cualquier sesión anterior
            session.clear()
            
            # Datos de ED Frutos
            session.permanent = True
            session['user_id'] = '67ed5c96300befce1d631c44'
            session['email'] = 'edfrutos@gmail.com'
            session['username'] = 'edefrutos'
            session['role'] = 'admin'
            session['logged_in'] = True
            session.modified = True
            
            print("ACCESO GARANTIZADO: ED Frutos")
            return redirect('/admin/')
        except Exception as e:
            print(f"ERROR en direct_admin_edf: {e}")
            # Incluso en caso de error, redirigir al admin
            return redirect('/admin/')
    
    # RUTA DE EMERGENCIA SIN DEPENDENCIAS
    @app.route('/emergency_admin')
    def emergency_admin():
        """Acceso de emergencia que bypasea todo el sistema"""
        try:
            # Código más simple posible
            session.clear()
            session['user_id'] = '680bc20aa170ac7fe8e58bec'
            session['role'] = 'admin'
            return redirect('/admin/')
        except:
            # En caso de error, mostrar un mensaje
            return '''<html><body style="font-family: sans-serif; padding: 20px; text-align: center">
                <h1>Error de sesión</h1>
                <p>Intenta acceder directamente a <a href="/admin/">/admin/</a></p>
                </body></html>'''
