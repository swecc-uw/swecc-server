import os

import boto3


class S3Client:
    instance = None

    def __init__(self):
        if S3Client.instance._initialized:
            return

        self.access_key_id = os.environ.get("AWS_ACCESS_KEY_ID", None)
        self.secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY", None)

        if not self.access_key_id or not self.secret_access_key:
            raise ValueError("AWS credentials not found")

        self.client = boto3.client(
            "s3",
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
        )

        self._initialized = True

    def __new__(cls):
        if cls.instance is None:
            cls.instance = super(S3Client, cls).__new__(cls)
            cls.instance._initialized = False
        return cls.instance

    def get_presigned_url(self, bucket, key, expiration=3600):
        return self.client.generate_presigned_url(
            ClientMethod="put_object",
            Params={"Bucket": bucket, "Key": key, "ContentType": "application/pdf"},
            ExpiresIn=expiration,
        )
