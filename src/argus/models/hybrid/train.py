"""Training script: fit SEIR + residual on a cassette, save weights to MLflow."""
def train_on_series(series: np.ndarray, save_path: Path = None):
    ...
from argus.models.registry import log_run

def train_and_log(series, run_name="hybrid_default"):
    from argus.models.hybrid.hybrid_model import HybridDetector
    detector = HybridDetector(epochs=80)
    detector.fit(series)
    log_run(
        run_name=run_name,
        params={"epochs": 80, "n_weeks": len(series)},
        metrics={"final_residual_std": detector.residual_std},
    )
