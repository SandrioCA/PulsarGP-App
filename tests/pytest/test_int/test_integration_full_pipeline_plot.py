import os
import yaml
import matplotlib.pyplot as plt
from datetime import datetime
from main.backend import load_toas, compute_residuals, plot_residuals

def test_integration_full_pipeline_plot():
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "config.yaml"))
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    files_dir = os.path.abspath(config["paths"]["files_dir"])
    logs_dir = os.path.abspath(os.path.join(config["paths"]["logs_dir"], "test_integration_full_pipeline_plot"))
    plots_dir = os.path.abspath(os.path.join(config["paths"]["plots_dir"], "test_integration_full_pipeline_plot"))

    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = os.path.join(logs_dir, f"log_full_pipeline_plot_{timestamp}.txt")
    plot_path = os.path.join(plots_dir, f"plot_residuals_{timestamp}.png")

    log_lines = []

    try:
        tim_path = os.path.join(files_dir, "psr04.tim")
        par_path = os.path.join(files_dir, "psr04.par")

        assert os.path.exists(tim_path), f"Archivo .tim no encontrado: {tim_path}"
        assert os.path.exists(par_path), f"Archivo .par no encontrado: {par_path}"
        log_lines.append("✔ Archivos de entrada encontrados.")

        mjds, toas = load_toas(tim_path, return_also_mjds=True)
        residuals = compute_residuals(par_path, toas)
        model = residuals.model

        plot_residuals(residuals, model, show=False, save_path=plot_path)
        assert os.path.exists(plot_path), "El archivo de la gráfica no fue generado."

        log_lines.append("Prueba de integración completa: gráfico generado con éxito.")
    except Exception as e:
        log_lines.append(f"Error durante la prueba de integración: {str(e)}")
        raise
    finally:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(log_lines))
