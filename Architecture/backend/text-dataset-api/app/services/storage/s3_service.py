"""
AWS S3 service for file storage and management
"""

import logging
from typing import Dict, List, Any, Optional, BinaryIO
from datetime import datetime, timedelta
from urllib.parse import urlparse
import mimetypes
import hashlib

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config

from app.core.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """AWS S3 service for file operations"""
    
    def __init__(self):
        # Configure boto3 with retry and timeout settings
        config = Config(
            region_name=settings.AWS_REGION,
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            max_pool_connections=50,
            connect_timeout=10,
            read_timeout=30
        )
        
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                config=config
            )
            
            self.s3_resource = boto3.resource(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                config=config
            )
            
            # Verify credentials by listing buckets
            self.s3_client.list_buckets()
            logger.info("S3 service initialized successfully")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize S3 service: {e}")
            raise
    
    def upload_file(
        self, 
        file_obj: BinaryIO,
        bucket: str,
        key: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload file to S3
        
        Args:
            file_obj: File object to upload
            bucket: S3 bucket name
            key: S3 object key
            content_type: MIME content type
            metadata: File metadata
            tags: File tags
            
        Returns:
            Upload result with file info
        """
        try:
            # Read file content
            file_obj.seek(0)
            file_content = file_obj.read()
            file_size = len(file_content)
            
            # Calculate content hash
            content_hash = hashlib.md5(file_content).hexdigest()
            
            # Determine content type
            if not content_type:
                content_type, _ = mimetypes.guess_type(key)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # Prepare metadata
            upload_metadata = {
                'uploaded-by': 'text-dataset-api',
                'upload-timestamp': datetime.utcnow().isoformat(),
                'content-hash': content_hash,
                'file-size': str(file_size)
            }
            
            if metadata:
                upload_metadata.update(metadata)
            
            # Reset file pointer
            file_obj.seek(0)
            
            # Upload file
            extra_args = {
                'ContentType': content_type,
                'Metadata': upload_metadata,
                'ServerSideEncryption': 'AES256'
            }
            
            if tags:
                # Convert tags to TagSet format
                tag_set = [{'Key': k, 'Value': v} for k, v in tags.items()]
                extra_args['Tagging'] = '&'.join([f"{tag['Key']}={tag['Value']}" for tag in tag_set])
            
            self.s3_client.upload_fileobj(
                file_obj,
                bucket,
                key,
                ExtraArgs=extra_args
            )
            
            # Generate file URL
            file_url = f"https://{bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
            
            logger.info(f"File uploaded successfully: {bucket}/{key}")
            
            return {
                'success': True,
                'bucket': bucket,
                'key': key,
                'file_size': file_size,
                'content_type': content_type,
                'content_hash': content_hash,
                'file_url': file_url,
                'metadata': upload_metadata,
                'uploaded_at': datetime.utcnow().isoformat()
            }
        
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            return {
                'success': False,
                'error': f"S3 error ({error_code}): {error_message}",
                'error_code': error_code
            }
        
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def download_file(self, bucket: str, key: str) -> bytes:
        """
        Download file from S3
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            File content as bytes
        """
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read()
            
            logger.info(f"File downloaded successfully: {bucket}/{key}")
            return content
        
        except ClientError as e:
            logger.error(f"S3 download failed: {e}")
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise FileNotFoundError(f"File not found: {bucket}/{key}")
            raise Exception(f"S3 error ({error_code}): {e.response['Error']['Message']}")
        
        except Exception as e:
            logger.error(f"File download failed: {e}")
            raise
    
    def delete_file(self, bucket: str, key: str) -> bool:
        """
        Delete file from S3
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            Success status
        """
        try:
            self.s3_client.delete_object(Bucket=bucket, Key=key)
            logger.info(f"File deleted successfully: {bucket}/{key}")
            return True
        
        except ClientError as e:
            logger.error(f"S3 delete failed: {e}")
            return False
        
        except Exception as e:
            logger.error(f"File deletion failed: {e}")
            return False
    
    def list_files(
        self, 
        bucket: str,
        prefix: Optional[str] = None,
        max_keys: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        List files in S3 bucket
        
        Args:
            bucket: S3 bucket name
            prefix: Key prefix filter
            max_keys: Maximum number of keys to return
            
        Returns:
            List of file information
        """
        try:
            kwargs = {
                'Bucket': bucket,
                'MaxKeys': max_keys
            }
            
            if prefix:
                kwargs['Prefix'] = prefix
            
            response = self.s3_client.list_objects_v2(**kwargs)
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'etag': obj['ETag'].strip('"'),
                    'storage_class': obj.get('StorageClass', 'STANDARD')
                })
            
            logger.info(f"Listed {len(files)} files from {bucket}")
            return files
        
        except ClientError as e:
            logger.error(f"S3 list failed: {e}")
            return []
        
        except Exception as e:
            logger.error(f"File listing failed: {e}")
            return []
    
    def get_file_metadata(self, bucket: str, key: str) -> Optional[Dict[str, Any]]:
        """
        Get file metadata from S3
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            File metadata or None if not found
        """
        try:
            response = self.s3_client.head_object(Bucket=bucket, Key=key)
            
            metadata = {
                'content_length': response['ContentLength'],
                'content_type': response.get('ContentType'),
                'last_modified': response['LastModified'].isoformat(),
                'etag': response['ETag'].strip('"'),
                'metadata': response.get('Metadata', {}),
                'server_side_encryption': response.get('ServerSideEncryption'),
                'storage_class': response.get('StorageClass', 'STANDARD')
            }
            
            return metadata
        
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            logger.error(f"Failed to get file metadata: {e}")
            return None
        
        except Exception as e:
            logger.error(f"Failed to get file metadata: {e}")
            return None
    
    def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        expiration: int = 3600,
        method: str = 'get_object'
    ) -> Optional[str]:
        """
        Generate presigned URL for S3 object
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            expiration: URL expiration in seconds
            method: S3 method (get_object, put_object, etc.)
            
        Returns:
            Presigned URL or None if failed
        """
        try:
            url = self.s3_client.generate_presigned_url(
                method,
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expiration
            )
            
            logger.info(f"Generated presigned URL for {bucket}/{key}")
            return url
        
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None
    
    def generate_upload_presigned_url(
        self,
        bucket: str,
        key: str,
        content_type: Optional[str] = None,
        expiration: int = 3600
    ) -> Optional[Dict[str, Any]]:
        """
        Generate presigned POST URL for file upload
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            content_type: File content type
            expiration: URL expiration in seconds
            
        Returns:
            Presigned POST data or None if failed
        """
        try:
            conditions = [
                {"bucket": bucket},
                ["starts-with", "$key", key]
            ]
            
            fields = {"key": key}
            
            if content_type:
                conditions.append({"Content-Type": content_type})
                fields["Content-Type"] = content_type
            
            response = self.s3_client.generate_presigned_post(
                Bucket=bucket,
                Key=key,
                Fields=fields,
                Conditions=conditions,
                ExpiresIn=expiration
            )
            
            logger.info(f"Generated presigned POST URL for {bucket}/{key}")
            return response
        
        except ClientError as e:
            logger.error(f"Failed to generate presigned POST URL: {e}")
            return None
    
    def copy_file(
        self,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Copy file within S3
        
        Args:
            source_bucket: Source bucket name
            source_key: Source object key
            dest_bucket: Destination bucket name
            dest_key: Destination object key
            metadata: Optional new metadata
            
        Returns:
            Success status
        """
        try:
            copy_source = {'Bucket': source_bucket, 'Key': source_key}
            
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata
                extra_args['MetadataDirective'] = 'REPLACE'
            
            self.s3_client.copy(copy_source, dest_bucket, dest_key, ExtraArgs=extra_args)
            
            logger.info(f"File copied: {source_bucket}/{source_key} -> {dest_bucket}/{dest_key}")
            return True
        
        except ClientError as e:
            logger.error(f"S3 copy failed: {e}")
            return False
        
        except Exception as e:
            logger.error(f"File copy failed: {e}")
            return False
    
    def create_multipart_upload(
        self,
        bucket: str,
        key: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """
        Create multipart upload for large files
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            content_type: File content type
            metadata: File metadata
            
        Returns:
            Upload ID or None if failed
        """
        try:
            kwargs = {'Bucket': bucket, 'Key': key}
            
            if content_type:
                kwargs['ContentType'] = content_type
            
            if metadata:
                kwargs['Metadata'] = metadata
            
            response = self.s3_client.create_multipart_upload(**kwargs)
            upload_id = response['UploadId']
            
            logger.info(f"Created multipart upload: {bucket}/{key} (ID: {upload_id})")
            return upload_id
        
        except ClientError as e:
            logger.error(f"Failed to create multipart upload: {e}")
            return None
    
    def upload_part(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        part_number: int,
        data: bytes
    ) -> Optional[str]:
        """
        Upload part for multipart upload
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            upload_id: Multipart upload ID
            part_number: Part number (1-based)
            data: Part data
            
        Returns:
            Part ETag or None if failed
        """
        try:
            response = self.s3_client.upload_part(
                Bucket=bucket,
                Key=key,
                PartNumber=part_number,
                UploadId=upload_id,
                Body=data
            )
            
            etag = response['ETag']
            logger.debug(f"Uploaded part {part_number} for {bucket}/{key}")
            return etag
        
        except ClientError as e:
            logger.error(f"Failed to upload part {part_number}: {e}")
            return None
    
    def complete_multipart_upload(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        parts: List[Dict[str, Any]]
    ) -> bool:
        """
        Complete multipart upload
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            upload_id: Multipart upload ID
            parts: List of parts with PartNumber and ETag
            
        Returns:
            Success status
        """
        try:
            self.s3_client.complete_multipart_upload(
                Bucket=bucket,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )
            
            logger.info(f"Completed multipart upload: {bucket}/{key}")
            return True
        
        except ClientError as e:
            logger.error(f"Failed to complete multipart upload: {e}")
            return False
    
    def abort_multipart_upload(self, bucket: str, key: str, upload_id: str) -> bool:
        """
        Abort multipart upload
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            upload_id: Multipart upload ID
            
        Returns:
            Success status
        """
        try:
            self.s3_client.abort_multipart_upload(
                Bucket=bucket,
                Key=key,
                UploadId=upload_id
            )
            
            logger.info(f"Aborted multipart upload: {bucket}/{key}")
            return True
        
        except ClientError as e:
            logger.error(f"Failed to abort multipart upload: {e}")
            return False


# Global instance
s3_service = S3Service()