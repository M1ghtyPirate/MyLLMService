from fastapi import FastAPI
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_endpoint: str
    api_key: str
