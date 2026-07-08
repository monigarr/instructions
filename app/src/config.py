"""Application configuration."""

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ocr_provider: str = "tesseract"
    azure_document_intelligence_endpoint: str = ""
    azure_document_intelligence_key: str = ""
    strict_warning: bool = True
    ocr_confidence_threshold: float = 0.55
    ocr_timeout_seconds: float = 4.0
    max_upload_bytes: int = 10_485_760
    batch_concurrency: int = 6
    batch_persist: bool = False
    batch_persist_dir: str = "./data/batches"
    latency_warn_ms: float = 5000.0
    latency_gate_enabled: bool = False
    preprocess_imperfect: bool = False
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    use_factory_graph: bool = False
    rag_enabled: bool = False
    chroma_persist_dir: str = "./data/chroma"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if "PORT" in os.environ:
            self.api_port = int(os.environ["PORT"])

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def azure_configured(self) -> bool:
        return bool(self.azure_document_intelligence_endpoint and self.azure_document_intelligence_key)


settings = Settings()
