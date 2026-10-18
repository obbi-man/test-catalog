"""Хранилище изображений (S3/MinIO). boto3 синхронный, поэтому вызовы уходят в thread pool."""
import asyncio
from typing import Iterator, Protocol

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.config import Settings


class Storage(Protocol):
    async def put(self, key: str, data: bytes, content_type: str) -> None: ...
    def open(self, key: str) -> tuple[Iterator[bytes], str]: ...
    async def ping(self) -> None: ...


class S3Storage:
    def __init__(self, settings: Settings):
        self.bucket = settings.s3_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        await asyncio.to_thread(
            self.client.put_object,
            Bucket=self.bucket, Key=key, Body=data, ContentType=content_type,
        )

    def open(self, key: str) -> tuple[Iterator[bytes], str]:
        """Возвращает (итератор чанков, content_type). Бросает KeyError, если объекта нет."""
        try:
            obj = self.client.get_object(Bucket=self.bucket, Key=key)
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
                raise KeyError(key) from e
            raise
        return obj["Body"].iter_chunks(64 * 1024), obj.get("ContentType", "application/octet-stream")

    async def ping(self) -> None:
        await asyncio.to_thread(self.client.head_bucket, Bucket=self.bucket)
