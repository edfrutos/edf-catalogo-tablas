import requests
from bs4 import BeautifulSoup

# Configura aquí los datos de acceso
BASE_URL = 'https://edefrutos2025.xyz'
LOGIN_URL = f'{BASE_URL}/login'
DASHBOARD_USER_URL = f'{BASE_URL}/dashboard_user'
DASHBOARD_ADMIN_URL = f'{BASE_URL}/admin/'

# Credenciales de prueba
USUARIOS = [
    {
        'tipo': 'usuario',
        'login_input': 'alberto@yahoo.com',  # Cambia por un usuario real
        'password': '34Maf15si$',              # Cambia por la contraseña real
        'dashboard_url': DASHBOARD_USER_URL
    },
    {
        'tipo': 'admin',
        'login_input': 'edfrutos@gmail.com',    # Cambia por un admin real
        'password': '34Maf15si$',                # Cambia por la contraseña real
        'dashboard_url': DASHBOARD_ADMIN_URL
    }
]

def test_login(usuario):
    session = requests.Session()
    # Obtener el token CSRF si existe
    resp = session.get(LOGIN_URL, verify=False)
    soup = BeautifulSoup(resp.text, 'html.parser')
    csrf_token = ''
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    if csrf_input:
        csrf_token = csrf_input['value']
    
    data = {
        'login_input': usuario['login_input'],
        'password': usuario['password'],
    }
    if csrf_token:
        data['csrf_token'] = csrf_token
    
    # Enviar POST de login
    resp = session.post(LOGIN_URL, data=data, verify=False, allow_redirects=True)
    print(f"\n[{usuario['tipo'].upper()}] Intento de login para: {usuario['login_input']}")
    print(f"Status code tras login: {resp.status_code}")
    if 'dashboard' in resp.url or 'admin' in resp.url:
        print(f"Redirigido correctamente a: {resp.url}")
    else:
        print(f"No se redirigió al dashboard. URL final: {resp.url}")
    if 'Bienvenido' in resp.text or 'Panel' in resp.text:
        print("Login exitoso (texto de bienvenida encontrado)")
    elif 'contraseña incorrectos' in resp.text or 'Credenciales inválidas' in resp.text:
        print("Login fallido: usuario o contraseña incorrectos")
    else:
        print("No se pudo determinar el resultado del login. Revisa la respuesta HTML.")
    # Probar acceso directo al dashboard
    resp2 = session.get(usuario['dashboard_url'], verify=False)
    print(f"Status code acceso dashboard: {resp2.status_code}")
    if resp2.status_code == 200:
        print("Acceso al dashboard OK")
    else:
        print("No se pudo acceder al dashboard tras login")

if __name__ == '__main__':
    for usuario in USUARIOS:
        test_login(usuario) 