from fastapi import FastAPI
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_access_token_endpoint: str
    api_endpoint: str
    authorization_key: str
