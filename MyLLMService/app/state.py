from __future__ import annotations

import time

from gigachat.models.auth import AccessToken
import requests

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List
from uuid import uuid4
from xml.etree.ElementInclude import include

from pydantic import Tag

from app.config import settings
from app.config.settings import Settings

from .models import JokeRequest, JokeResponse

from gigachat import GigaChat


@dataclass(slots=True)
class AppState:
    jokes: List[JokeResponse] = field(default_factory=list)
    access_token: AccessToken = field(default_factory=lambda: AccessToken(
            access_token="",
            expires_at=int(time.time()),
        )
    )
    settings = Settings()

    def normalize_tags(self, tags: List[str]) -> List[str]:
        normalized_tags: List[str] = []
        for tag in tags or []:
            normalized_tag = (tag or "").strip().lower()
            if len(normalized_tag) == 0 or normalized_tag in normalized_tags:
                continue
            normalized_tags.append(normalized_tag)
        normalized_tags.sort()
        return normalized_tags

    def get_access_token(self) -> str:
        if self.access_token.expires_at > time.time():
            return self.access_token.access_token

        giga_chat_auth = GigaChat(
            base_url=self.settings.api_access_token_endpoint,
            credentials=self.settings.authorization_key,
            verify_ssl_certs=False,
        )
        response = giga_chat_auth.get_token()
        print(f'Auth response: <{response}>')
        self.access_token = response
        return self.access_token.access_token

    def create_joke(self, tags: List[str]) -> JokeResponse:

        giga_chat = GigaChat(
            base_url=self.settings.api_endpoint,
            model="GigaChat-2",
            access_token=self.get_access_token(),
            verify_ssl_certs=False,
        )
        print(f'Token: <{self.get_access_token()}>')
        response = giga_chat.chat(f'Ты - заслуженный артист РСФСР, писатель-юморист и бессменный резидент кривого зеркала. '
            + f'Придумай уморительный анекдот, затрагивающий следующие темы: {", ".join(tags)}. '
            + f'Формат ответа - строка "<Название анекдота>|<Текст анекдота>".'
            + f'Ограничения: название анектода - от 1 до 100 символов, не содержит символ "|"; текст анекдота - от 1 до 5000 символов, не содержит символ "|".')
        print(response)
        title, text = response.choices[0].message.content.split('|')
        
        joke = JokeResponse(
            tags=tags,
            title=title.strip(),
            text=text.strip(),
            created_at=datetime.now(timezone.utc),
        )

        self.jokes.append(joke)
        return joke

    def get_joke(self, tags: List[str]) -> JokeResponse | None:
        normalized_tags = self.normalize_tags(tags)
        
        for joke in self.jokes:
            if len(joke.tags) != len(normalized_tags):
                continue
            for i, tag in enumerate(joke.tags):
                if tag != normalized_tags[i]:
                    break
            else:
                return joke
        return self.create_joke(normalized_tags)