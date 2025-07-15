import os
import yaml
from datetime import datetime
from main.backend import load_toas, compute_residuals, plot_residuals

def test_plot_residuals():
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "config.yaml"))
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    files_dir = os.path.abspath(config["paths"]["files_dir"])
    logs_dir = os.path.abspath(os.path.join(config["paths"]["logs_dir"], "plot_residuals"))
    plots_dir = os.path.abspath(os.path.join(config["paths"]["plots_dir"], "plot_residuals"))

    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = os.path.join(logs_dir, f"log_plot_residuals_{timestamp}.txt")
    plot_path = os.path.join(plots_dir, f"residual_plot_{timestamp}.png")

    log_lines = []

    tim_path = os.path.join(files_dir, "psr04.tim")
    par_path = os.path.join(files_dir, "psr04.par")

    try:
        assert os.path.exists(tim_path), f"Archivo .tim no encontrado: {tim_path}"
        assert os.path.exists(par_path), f"Archivo .par no encontrado: {par_path}"
        log_lines.append("Archivos de entrada encontrados.")

        toas = load_toas(tim_path, return_also_mjds=False)
        residuals = compute_residuals(par_path, toas)

        plot_residuals(residuals, residuals.model, show=False, save_path=plot_path)

        assert os.path.exists(plot_path), "✘ El gráfico de residuos no fue guardado correctamente."
        log_lines.append(f"El gráfico fue generado y guardado en {plot_path}.")
        log_lines.append("La función plot_residuals pasó la prueba unitaria.")

    except AssertionError as e:
        log_lines.append(str(e))
        raise

    finally:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(log_lines))
