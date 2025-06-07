from PyInstaller.utils.hooks import collect_all

def hook(hook_api):
    packages = ['pydrive2', 'pymongo', 'boto3', 'dns']  # Cambiado 'dnspython' a 'dns' que es el nombre correcto
    for package in packages:
        try:
            datas, binaries, hiddenimports = collect_all(package)
            hook_api.add_datas(datas)
            hook_api.add_binaries(binaries)
            hook_api.add_imports(*hiddenimports)
        except Exception as e:
            print(f"[WARNING] Error procesando {package}: {str(e)}")