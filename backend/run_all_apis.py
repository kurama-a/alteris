import subprocess
import socket
import time
import os

MICROSERVICES = [
    {"name": "apprenti", "path": "apprenti", "module": "main"},
    {"name": "tuteur", "path": "tuteur", "module": "main"},
    {"name": "maitre", "path": "maitre", "module": "main"},
    {"name": "coordonatrice", "path": "coordonatrice", "module": "main"},
    {"name": "auth", "path": "auth", "module": "main"},
    {"name": "admin", "path": "admin", "module": "main"},
    {"name": "responsable_cursus", "path": "responsable_cursus", "module": "main"},
    {"name": "entreprise_externe", "path": "entreprise-externe", "module": "main"},
    {"name": "ecole", "path": "ecole", "module": "main"},
]   

processes = []
service_ports = {}

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def run_uvicorn(service):
    name = service["name"]
    path = service["path"]
    module = service["module"]
    port = find_free_port()

    cmd = [
        "uvicorn",
        f"{module}:app",
        "--reload",
        "--port", str(port)
        # ❌ PAS de --root-path ici
    ]

    try:
        proc = subprocess.Popen(cmd, cwd=path)
        processes.append(proc)
        service_ports[name] = port
        print(f"🚀 {name} lancé sur http://localhost:{port}/{name}/docs")
    except FileNotFoundError:
        print(f"❌ Dossier manquant : {path}")

print("🔧 Lancement des microservices...\n")

for service in MICROSERVICES:
    run_uvicorn(service)
    time.sleep(0.5)

print("\n🌐 Interfaces disponibles :")
for name, port in service_ports.items():
    print(f"   🔹 {name} : http://localhost:{port}/{name}/docs")