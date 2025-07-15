import os
import yaml
from datetime import datetime
from main.backend import load_toas

def test_load_toas():
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "config.yaml"))
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    files_dir = os.path.abspath(config["paths"]["files_dir"])
    logs_dir = os.path.abspath(os.path.join(config["paths"]["logs_dir"], "load_toas"))
    os.makedirs(logs_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = os.path.join(logs_dir, f"log_load_toas_{timestamp}.txt")
    log_lines = []

    tim_path = os.path.join(files_dir, "psr04.tim")

    try:
        assert os.path.exists(tim_path), f"Archivo .tim no encontrado: {tim_path}"
        log_lines.append("Archivo .tim encontrado correctamente.")

        mjds, toas = load_toas(tim_path, return_also_mjds=True)

        assert toas is not None, "El objeto TOAs retornado es None."
        assert hasattr(toas, "ntoas"), "El objeto TOAs no tiene el atributo 'ntoas'."
        assert toas.ntoas > 0, "No se cargaron TOAs desde el archivo."

        log_lines.append(f"Se cargaron {toas.ntoas} TOAs.")
        log_lines.append("La función load_toas pasó la prueba unitaria.")

    except AssertionError as e:
        log_lines.append(str(e))
        raise

    finally:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(log_lines))
