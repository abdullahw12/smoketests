# app/main.py
import logging
from probe import run_probe
logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for more detailed logs
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Ensures logs are printed to console
    ]
)

if __name__ == "__main__":
    logging.info("Starting probe microservice...")
    run_probe()
