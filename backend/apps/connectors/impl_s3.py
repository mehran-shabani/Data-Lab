"""S3/MinIO connector implementation (read-only for MVP)."""

import logging
from typing import Any
from uuid import UUID

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from .base import Connector
from .resilience import circuit_breaker_decorator, with_retry

logger = logging.getLogger(__name__)


class S3Connector(Connector):
    """S3/MinIO connector with ping and sample operations (read-only)."""

    def __init__(self, conf: dict[str, Any], org_id: UUID, ds_id: UUID):
        super().__init__(conf, org_id, ds_id)
        self._endpoint = conf["endpoint"]
        self._region = conf.get("region", "us-east-1")
        self._bucket = conf["bucket"]
        self._access_key = conf["access_key"]
        self._secret_key = conf["secret_key"]
        self._use_path_style = conf.get("use_path_style", False)
        self._timeout = conf.get("timeout_ms", 4000) / 1000.0
        self._client = None

    def _get_client(self):
        """Get or create S3 client."""
        if self._client is None:
            config = Config(
                signature_version='s3v4',
                s3={'addressing_style': 'path' if self._use_path_style else 'virtual'},
                connect_timeout=self._timeout,
                read_timeout=self._timeout,
            )
            
            self._client = boto3.client(
                's3',
                endpoint_url=self._endpoint,
                aws_access_key_id=self._access_key,
                aws_secret_access_key=self._secret_key,
                region_name=self._region,
                config=config,
            )
        return self._client

    @circuit_breaker_decorator
    @with_retry(retries=2, base_ms=250, max_ms=2000)
    async def ping(self) -> tuple[bool, str]:
        """Test S3 connectivity with head_bucket.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            client = self._get_client()
            client.head_bucket(Bucket=self._bucket)
            return True, f"S3 bucket '{self._bucket}' accessible"
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.warning(f"S3 ping failed for ds_id={self.ds_id}: {error_code}")
            return False, f"S3 error: {error_code} - {str(e)}"
        except BotoCoreError as e:
            logger.warning(f"S3 ping failed for ds_id={self.ds_id}: {e}")
            return False, f"Connection failed: {str(e)}"
        except Exception as e:
            logger.warning(f"S3 ping failed for ds_id={self.ds_id}: {e}")
            return False, f"Unexpected error: {str(e)}"

    @circuit_breaker_decorator
    @with_retry(retries=1, base_ms=250, max_ms=1000)
    async def sample(self, params: dict[str, Any]) -> Any:
        """List objects in S3 bucket (read-only sample).
        
        Args:
            params: Should contain:
                - prefix: Object prefix filter (optional)
                - max_keys: Maximum objects to list (default: 5, max: 20)
                
        Returns:
            List of objects
        """
        try:
            client = self._get_client()
            
            prefix = params.get("prefix", "")
            max_keys = min(params.get("max_keys", 5), 20)  # Cap for safety
            
            response = client.list_objects_v2(
                Bucket=self._bucket,
                Prefix=prefix,
                MaxKeys=max_keys,
            )
            
            objects = []
            for obj in response.get("Contents", []):
                objects.append({
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat(),
                    "etag": obj.get("ETag", ""),
                })
            
            return {
                "ok": True,
                "bucket": self._bucket,
                "prefix": prefix,
                "count": len(objects),
                "objects": objects,
                "truncated": response.get("IsTruncated", False),
            }
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.warning(f"S3 sample failed for ds_id={self.ds_id}: {error_code}")
            return {"ok": False, "error": f"S3 error: {error_code}"}
        except BotoCoreError as e:
            logger.warning(f"S3 sample failed for ds_id={self.ds_id}: {e}")
            return {"ok": False, "error": str(e)}
        except Exception as e:
            logger.warning(f"S3 sample failed for ds_id={self.ds_id}: {e}")
            return {"ok": False, "error": str(e)}

    async def close(self) -> None:
        """Close S3 client (boto3 handles connection pooling)."""
        self._client = None
