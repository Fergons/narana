"""Logging utilities for pipeline runs"""
import logging
from pathlib import Path
import datetime
from typing import Tuple

def setup_pipeline_logger(
    pipeline_name: str,
    run_id: str,
    base_dir: str = "runs",
    log_level: int = logging.DEBUG
) -> Tuple[logging.Logger, Path]:
    """Setup logging for a pipeline run
    
    Args:
        pipeline_name: Name of the pipeline (e.g., "character", "plot")
        run_id: Unique identifier for this run (e.g., book_id)
        base_dir: Base directory for all runs
        log_level: Logging level for file handler
        
    Returns:
        Tuple of (logger, run_directory_path)
    """
    # Create runs directory if it doesn't exist
    runs_dir = Path(base_dir)
    runs_dir.mkdir(exist_ok=True)
    
    # Create pipeline-specific directory
    pipeline_dir = runs_dir / pipeline_name
    pipeline_dir.mkdir(exist_ok=True)
    
    # Create run-specific directory with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = pipeline_dir / f"{run_id}_{timestamp}"
    run_dir.mkdir(exist_ok=True)
    
    # Configure logger
    logger = logging.getLogger(f"{pipeline_name}.{run_id}")
    logger.setLevel(log_level)
    
    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-12s | %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)-8s | %(message)s'
    )
    
    # File handler - detailed logging
    file_handler = logging.FileHandler(run_dir / "pipeline.log")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)
    
    # Console handler - important info only
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger, run_dir

class PipelineLogger:
    """Context manager for pipeline logging"""
    
    def __init__(
        self,
        pipeline_name: str,
        run_id: str,
        base_dir: str = "runs",
        log_level: int = logging.DEBUG
    ):
        self.pipeline_name = pipeline_name
        self.run_id = run_id
        self.base_dir = base_dir
        self.log_level = log_level
        self.logger = None
        self.run_dir = None
        
    def __enter__(self):
        self.logger, self.run_dir = setup_pipeline_logger(
            self.pipeline_name,
            self.run_id,
            self.base_dir,
            self.log_level
        )
        return self.logger, self.run_dir
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Clean up handlers
        if self.logger:
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler) 