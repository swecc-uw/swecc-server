import os
import boto3


class S3Client:
    instance = None

    # Don't use outside of this class
    def __init__(self):
        self.access_key_id = os.environ.get("AWS_ACCESS_KEY_ID", None)
        self.secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY", None)

        if not self.access_key_id or not self.secret_access_key:
            raise ValueError("AWS credentials not found")

        self.client = boto3.client(
            "s3",
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
        )

    @classmethod
    def get_instance(cls):
        if not cls.instance:
            cls.instance = S3Client()
        return cls.instance

    def get_presigned_url(self, bucket, key, expiration=3600):
        return self.client.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expiration,
        )
