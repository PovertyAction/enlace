"""Enlace - Extract and harmonize data from development economics research papers."""

import logging

__version__ = "0.1.0"

# Create the base 'enlace' logger at package import time
# This ensures all child loggers (enlace.extractor, enlace.cli, etc.) properly inherit
# from the 'enlace' logger instead of the root logger
_base_logger = logging.getLogger("enlace")
