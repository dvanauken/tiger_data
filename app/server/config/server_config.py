from dataclasses import dataclass

@dataclass
class ServerConfig:
    ftp_host: str = 'ftp2.census.gov'
    https_host: str = 'www2.census.gov'
    base_path: str = '/geo/tiger/TIGER2023'

