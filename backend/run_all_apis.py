import os
import signal
import subprocess
import time
from typing import Dict

MICROSERVICES = [
    {"name": "admin", "path": "admin", "module": "main", "port": 8000},
    {"name": "apprenti", "path": "apprenti", "module": "main", "port": 8001},
    {"name": "maitre", "path": "maitre", "module": "main", "port": 8002},
    {"name": "tuteur", "path": "tuteur", "module": "main", "port": 8003},
    {"name": "coordonatrice", "path": "coordonatrice", "module": "main", "port": 8004},
    {"name": "auth", "path": "auth", "module": "main", "port": 8005},
    {"name": "responsable_cursus", "path": "responsable_cursus", "module": "main", "port": 8006},
    {"name": "ecole", "path": "ecole", "module": "main", "port": 8007},
    {"name": "entreprise", "path": "entreprise", "module": "main", "port": 8008},
    {"name": "responsableformation", "path": "responsableformation", "module": "main", "port": 8009},
]

processes: Dict[str, subprocess.Popen] = {}


def run_uvicorn(service):
    name = service["name"]
    path = service["path"]
    module = service["module"]
    port = service["port"]

    cmd = [
        "uvicorn",
        f"{module}:app",
        "--reload",
        "--port",
        str(port),
    ]

    env = os.environ.copy()
    env["APP_PORT"] = str(port)

    try:
        proc = subprocess.Popen(cmd, cwd=path, env=env)
        processes[name] = proc
        print(f"-> {name} lancé sur http://localhost:{port}/{name}/docs")
    except FileNotFoundError:
        print(f"!! Dossier manquant : {path}")


def stop_processes():
    for name, proc in processes.items():
        if proc.poll() is not None:
            continue
        print(f"Arrêt de {name}...")
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


def main():
    print("Démarrage des microservices...\n")
    try:
        for service in MICROSERVICES:
            run_uvicorn(service)
            time.sleep(0.5)

        print("\nInterfaces disponibles :")
        for service in MICROSERVICES:
            port = service["port"]
            name = service["name"]
            if name in processes:
                print(f"   - {name} : http://localhost:{port}/{name}/docs")

        print("\nAppuyez sur Ctrl+C pour arrêter tous les services.")

        while any(proc.poll() is None for proc in processes.values()):
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nInterruption détectée, arrêt des services...")
    finally:
        stop_processes()


if __name__ == "__main__":
    main()
