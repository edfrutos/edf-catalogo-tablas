"""Comprobaciones estáticas del empaquetado para la Mac App Store (packaging/mas)."""

import ast
import pathlib
import plistlib
import re
import shutil
import subprocess

import pytest
import yaml

RAIZ = pathlib.Path(__file__).resolve().parents[1]
MAS = RAIZ / "packaging" / "mas"
WORKFLOW = RAIZ / ".github" / "workflows" / "build_macos_mas.yml"


def _plist(nombre):
    with open(MAS / nombre, "rb") as f:
        return plistlib.load(f)


def test_entitlements_principales_activan_sandbox_y_red():
    ent = _plist("entitlements-mas.plist")
    assert ent["com.apple.security.app-sandbox"] is True
    assert ent["com.apple.security.network.client"] is True
    assert ent["com.apple.security.network.server"] is True
    assert ent["com.apple.security.files.user-selected.read-write"] is True


def test_entitlements_sin_excepciones_de_hardened_runtime():
    # La firma de la tienda no usa Hardened Runtime: las excepciones cs.* sobran
    for nombre in ("entitlements-mas.plist", "entitlements-mas-child.plist"):
        assert not [k for k in _plist(nombre) if k.startswith("com.apple.security.cs.")]


def test_entitlements_no_fijan_identificadores_del_equipo():
    # Se añaden en sign_and_package.sh a partir del perfil embebido
    ent = _plist("entitlements-mas.plist")
    assert "com.apple.application-identifier" not in ent
    assert "com.apple.developer.team-identifier" not in ent


def test_entitlements_hijos_heredan_el_sandbox():
    ent = _plist("entitlements-mas-child.plist")
    assert ent == {
        "com.apple.security.app-sandbox": True,
        "com.apple.security.inherit": True,
    }


def test_entitlements_developer_id_no_se_tocan():
    ent = plistlib.loads((RAIZ / "entitlements.plist").read_bytes())
    assert "com.apple.security.app-sandbox" not in ent
    assert ent["com.apple.security.cs.disable-library-validation"] is True


def test_spec_mas_compila_y_no_firma_ni_comprime():
    src = (MAS / "TablaTeca_mas.spec").read_text(encoding="utf-8")
    ast.parse(src)
    assert "upx=True" not in src
    assert "console=False" in src
    assert "exclude_binaries=True" in src
    assert 'bundle_identifier="com.edefrutos.tablateca"' in src
    assert "codesign_identity=None" in src
    assert "entitlements_file=None" in src
    assert "MAS_BUILD_NUMBER" in src and "MAS_MARKETING_VERSION" in src
    assert 'LSApplicationCategoryType' in src
    # Apple (90869): una app solo arm64 necesita un mínimo de macOS >= 12.0
    assert '"LSMinimumSystemVersion": "12.0"' in src


def test_script_de_firma_sintaxis_y_buenas_practicas():
    script = MAS / "sign_and_package.sh"
    src = script.read_text(encoding="utf-8")
    subprocess.run(["bash", "-n", str(script)], check=True)
    assert "set -Eeuo pipefail" in src
    # Nunca firmar con --deep: solo se usa para verificar
    for linea in src.splitlines():
        if "--deep" in linea:
            assert "codesign --verify" in linea
    assert "--entitlements" in src
    assert "embedded.provisionprofile" in src
    # compatible con bash 3.2 (macOS)
    assert "mapfile" not in src and "readarray" not in src
    assert "declare -A" not in src


@pytest.mark.skipif(shutil.which("shellcheck") is None, reason="shellcheck no instalado")
def test_script_de_firma_pasa_shellcheck():
    subprocess.run(["shellcheck", "-S", "warning", str(MAS / "sign_and_package.sh")], check=True)


@pytest.fixture(scope="module")
def wf():
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def test_workflow_mas_filtra_rutas_y_no_toca_el_de_developer_id(wf):
    triggers = wf.get(True) or wf["on"]  # PyYAML interpreta "on" como True
    for evento in ("push", "pull_request"):
        assert "packaging/mas/**" in triggers[evento]["paths"]
    assert "workflow_dispatch" in triggers
    assert wf["name"] != "Build macOS App v2.0"


def test_workflow_mas_secretos_solo_fuera_de_pull_request(wf):
    pasos = wf["jobs"]["build-mas"]["steps"]
    con_secretos = [p for p in pasos if "secrets." in yaml.dump(p)]
    assert con_secretos
    for paso in con_secretos:
        assert "!= 'pull_request'" in paso.get("if", ""), paso["name"]


def test_workflow_mas_pr_firma_ad_hoc_y_limpia_llavero(wf):
    pasos = {p["name"]: p for p in wf["jobs"]["build-mas"]["steps"]}
    adhoc = pasos["Ad hoc sign and package (solo comprobación)"]
    assert adhoc["if"] == "github.event_name == 'pull_request'"
    assert adhoc["env"]["MAS_AD_HOC"] == "1"
    limpieza = pasos["Clean up keychain and profile"]
    assert limpieza["if"].startswith("always()")
    assert pasos["Validate package with App Store Connect"]["continue-on-error"] is True


def test_workflow_mas_usa_numero_de_ejecucion_como_build(wf):
    pasos = {p["name"]: p for p in wf["jobs"]["build-mas"]["steps"]}
    assert pasos["Build app (PyInstaller, onedir)"]["env"]["MAS_BUILD_NUMBER"] == "${{ github.run_number }}"
    assert re.fullmatch(r"\d+(\.\d+){0,2}", wf["env"]["MAS_MARKETING_VERSION"])


def _chunks_icns(ruta):
    datos = ruta.read_bytes()
    assert datos[:4] == b"icns"
    assert int.from_bytes(datos[4:8], "big") == len(datos)
    i, tipos = 8, {}
    while i < len(datos):
        tipo = datos[i:i + 4].decode()
        largo = int.from_bytes(datos[i + 4:i + 8], "big")
        tipos[tipo] = datos[i + 8:i + largo]
        i += largo
    return tipos


def test_icono_icns_incluye_512_y_512_2x_en_png():
    # La tienda exige 512x512 y 512x512@2x en el .icns
    tipos = _chunks_icns(RAIZ / "edf_developer.icns")
    for t in ("ic09", "ic10"):
        assert tipos[t][:8] == b"\x89PNG\r\n\x1a\n", t


def test_icono_maestro_1024_con_esquinas_transparentes():
    from PIL import Image

    im = Image.open(RAIZ / "icons" / "TablaTeca_1024.png").convert("RGBA")
    assert im.size == (1024, 1024)
    assert im.getpixel((0, 0))[3] == 0 and im.getpixel((1023, 1023))[3] == 0
    assert im.getpixel((512, 512))[3] == 255
