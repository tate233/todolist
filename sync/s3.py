"""S3 sync backend (requires the optional 'boto3' dependency).

Import-safe without boto3; ``is_available`` reports dependency presence.
"""
from typing import List, Tuple

from sync.base import SyncBackend


def is_available() -> bool:
    try:
        import boto3  # noqa: F401,PLC0415
    except ImportError:
        return False
    return True


class S3Backend(SyncBackend):
    def __init__(self, bucket: str, prefix: str = "smartnotes/", **client_kwargs):
        if not is_available():
            raise RuntimeError("S3 后端需要安装 boto3")
        import boto3  # noqa: PLC0415
        self.bucket = bucket
        self.prefix = prefix
        self.client = boto3.client("s3", **client_kwargs)

    def _key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    def upload(self, key: str, data: bytes, mtime: float) -> None:
        self.client.put_object(Bucket=self.bucket, Key=self._key(key), Body=data,
                               Metadata={"mtime": str(mtime)})

    def download(self, key: str) -> Tuple[bytes, float]:
        from botocore.exceptions import ClientError  # noqa: PLC0415
        try:
            obj = self.client.get_object(Bucket=self.bucket, Key=self._key(key))
        except ClientError as e:
            raise KeyError(key) from e
        return obj["Body"].read(), float(obj.get("Metadata", {}).get("mtime", -1.0))

    def list_keys(self) -> List[str]:
        resp = self.client.list_objects_v2(Bucket=self.bucket, Prefix=self.prefix)
        return [o["Key"][len(self.prefix):] for o in resp.get("Contents", [])]

    def get_mtime(self, key: str) -> float:
        from botocore.exceptions import ClientError  # noqa: PLC0415
        try:
            head = self.client.head_object(Bucket=self.bucket, Key=self._key(key))
        except ClientError:
            return -1.0
        return float(head.get("Metadata", {}).get("mtime", -1.0))
