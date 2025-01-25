from dataclasses import dataclass

@dataclass
class ProcessingConfig:
    base_tolerance: float = 0.005
    output_dir: str = "./tiger_processed"
    parallel_downloads: int = 4
    max_retries: int = 3
    timeout: int = 300

