import os
from dataclasses import dataclass

import boto3
from botocore.config import Config


@dataclass(frozen=True)
class StorageConfig:
    access_key_id: str
    secret_access_key: str
    endpoint_url: str | None
    region_name: str | None
    bucket_name: str
    force_path_style: bool
    presign_expires_seconds: int


def _get_env(name: str, fallback: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is not None and value != "":
        return value
    return fallback


def get_storage_config() -> StorageConfig:
    access_key_id = _get_env("S3_ACCESS_KEY_ID", _get_env("ACCESS_KEY_ID"))
    secret_access_key = _get_env("S3_SECRET_ACCESS_KEY", _get_env("SECRET_ACCESS_KEY"))
    bucket_name = _get_env("S3_BUCKET", _get_env("BUCKET"))
    if not access_key_id or not secret_access_key or not bucket_name:
        raise RuntimeError("Missing S3 credentials or bucket configuration.")

    endpoint_url = _get_env("S3_ENDPOINT", _get_env("ENDPOINT"))
    region_name = _get_env("S3_REGION", _get_env("REGION"))
    force_path_style = _get_env("S3_FORCE_PATH_STYLE", "false").lower() == "true"
    presign_expires_seconds = int(_get_env("S3_PRESIGN_EXPIRES", "3600"))

    return StorageConfig(
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        endpoint_url=endpoint_url,
        region_name=region_name,
        bucket_name=bucket_name,
        force_path_style=force_path_style,
        presign_expires_seconds=presign_expires_seconds,
    )


def get_s3_client(config: StorageConfig):
    s3_config = Config(s3={"addressing_style": "path"} if config.force_path_style else {})
    return boto3.client(
        "s3",
        aws_access_key_id=config.access_key_id,
        aws_secret_access_key=config.secret_access_key,
        region_name=config.region_name,
        endpoint_url=config.endpoint_url,
        config=s3_config,
    )


def get_bucket_name(config: StorageConfig) -> str:
    return config.bucket_name


def presign_get_url(client, bucket: str, key: str, expires_in: int) -> str:
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_in,
    )
