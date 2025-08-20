import logging

def configure_logging():
    """
    Configura logging básico para todo o projeto
    """
    logging.basicConfig(
        level = logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )