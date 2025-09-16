"""
AWS CloudWatch service for monitoring and logging
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config

from app.core.config import settings

logger = logging.getLogger(__name__)


class CloudWatchService:
    """AWS CloudWatch service for metrics and logs"""
    
    def __init__(self):
        # Configure boto3 with retry settings
        config = Config(
            region_name=settings.AWS_REGION,
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )
        
        try:
            # CloudWatch client for metrics
            self.cloudwatch = boto3.client(
                'cloudwatch',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                config=config
            )
            
            # CloudWatch Logs client
            self.logs_client = boto3.client(
                'logs',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                config=config
            )
            
            # Application namespace
            self.namespace = "TextDatasetAPI"
            
            # Ensure log group exists
            self.log_group_name = f"/aws/application/{settings.APP_NAME}"
            self._ensure_log_group_exists()
            
            logger.info("CloudWatch service initialized successfully")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize CloudWatch service: {e}")
            raise
    
    def _ensure_log_group_exists(self):
        """Ensure log group exists"""
        try:
            self.logs_client.create_log_group(
                logGroupName=self.log_group_name,
                tags={
                    'Application': settings.APP_NAME,
                    'Environment': settings.ENVIRONMENT
                }
            )
            logger.info(f"Created log group: {self.log_group_name}")
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                logger.warning(f"Failed to create log group: {e}")
    
    def put_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = 'Count',
        dimensions: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Put custom metric to CloudWatch
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Metric unit (Count, Bytes, Seconds, etc.)
            dimensions: Metric dimensions
            timestamp: Metric timestamp
            
        Returns:
            Success status
        """
        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit
            }
            
            if dimensions:
                metric_data['Dimensions'] = [
                    {'Name': k, 'Value': v} for k, v in dimensions.items()
                ]
            
            if timestamp:
                metric_data['Timestamp'] = timestamp
            
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[metric_data]
            )
            
            logger.debug(f"Put metric: {metric_name} = {value} {unit}")
            return True
        
        except ClientError as e:
            logger.error(f"Failed to put metric: {e}")
            return False
    
    def put_metrics_batch(self, metrics: List[Dict[str, Any]]) -> bool:
        """
        Put multiple metrics to CloudWatch
        
        Args:
            metrics: List of metric data dictionaries
            
        Returns:
            Success status
        """
        try:
            # CloudWatch supports up to 20 metrics per call
            batch_size = 20
            
            for i in range(0, len(metrics), batch_size):
                batch = metrics[i:i + batch_size]
                
                metric_data = []
                for metric in batch:
                    data = {
                        'MetricName': metric['name'],
                        'Value': metric['value'],
                        'Unit': metric.get('unit', 'Count')
                    }
                    
                    if 'dimensions' in metric and metric['dimensions']:
                        data['Dimensions'] = [
                            {'Name': k, 'Value': v} 
                            for k, v in metric['dimensions'].items()
                        ]
                    
                    if 'timestamp' in metric and metric['timestamp']:
                        data['Timestamp'] = metric['timestamp']
                    
                    metric_data.append(data)
                
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=metric_data
                )
            
            logger.info(f"Put {len(metrics)} metrics in batches")
            return True
        
        except ClientError as e:
            logger.error(f"Failed to put metrics batch: {e}")
            return False
    
    def get_metric_statistics(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        period: int = 300,
        statistics: List[str] = None,
        dimensions: Optional[Dict[str, str]] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get metric statistics from CloudWatch
        
        Args:
            metric_name: Name of the metric
            start_time: Start time for data
            end_time: End time for data
            period: Period in seconds
            statistics: Statistics to retrieve (Average, Sum, Maximum, etc.)
            dimensions: Metric dimensions
            
        Returns:
            List of metric data points
        """
        try:
            if not statistics:
                statistics = ['Average', 'Sum', 'Maximum', 'Minimum']
            
            kwargs = {
                'Namespace': self.namespace,
                'MetricName': metric_name,
                'StartTime': start_time,
                'EndTime': end_time,
                'Period': period,
                'Statistics': statistics
            }
            
            if dimensions:
                kwargs['Dimensions'] = [
                    {'Name': k, 'Value': v} for k, v in dimensions.items()
                ]
            
            response = self.cloudwatch.get_metric_statistics(**kwargs)
            
            # Sort by timestamp
            datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
            
            return datapoints
        
        except ClientError as e:
            logger.error(f"Failed to get metric statistics: {e}")
            return None
    
    def create_alarm(
        self,
        alarm_name: str,
        metric_name: str,
        comparison_operator: str,
        threshold: float,
        evaluation_periods: int = 2,
        statistic: str = 'Average',
        period: int = 300,
        dimensions: Optional[Dict[str, str]] = None,
        alarm_actions: Optional[List[str]] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        Create CloudWatch alarm
        
        Args:
            alarm_name: Name of the alarm
            metric_name: Name of the metric to monitor
            comparison_operator: Comparison operator (GreaterThanThreshold, etc.)
            threshold: Alarm threshold value
            evaluation_periods: Number of periods to evaluate
            statistic: Statistic to use
            period: Period in seconds
            dimensions: Metric dimensions
            alarm_actions: List of actions to take when alarm triggers
            description: Alarm description
            
        Returns:
            Success status
        """
        try:
            kwargs = {
                'AlarmName': alarm_name,
                'MetricName': metric_name,
                'Namespace': self.namespace,
                'Statistic': statistic,
                'Period': period,
                'EvaluationPeriods': evaluation_periods,
                'Threshold': threshold,
                'ComparisonOperator': comparison_operator
            }
            
            if dimensions:
                kwargs['Dimensions'] = [
                    {'Name': k, 'Value': v} for k, v in dimensions.items()
                ]
            
            if alarm_actions:
                kwargs['AlarmActions'] = alarm_actions
            
            if description:
                kwargs['AlarmDescription'] = description
            
            self.cloudwatch.put_metric_alarm(**kwargs)
            
            logger.info(f"Created alarm: {alarm_name}")
            return True
        
        except ClientError as e:
            logger.error(f"Failed to create alarm: {e}")
            return False
    
    def send_log_event(
        self,
        log_stream: str,
        message: str,
        timestamp: Optional[datetime] = None,
        level: str = 'INFO'
    ) -> bool:
        """
        Send log event to CloudWatch Logs
        
        Args:
            log_stream: Name of the log stream
            message: Log message
            timestamp: Log timestamp
            level: Log level
            
        Returns:
            Success status
        """
        try:
            # Ensure log stream exists
            self._ensure_log_stream_exists(log_stream)
            
            if not timestamp:
                timestamp = datetime.utcnow()
            
            # Format message
            formatted_message = json.dumps({
                'timestamp': timestamp.isoformat(),
                'level': level,
                'message': message,
                'application': settings.APP_NAME,
                'environment': settings.ENVIRONMENT
            })
            
            log_event = {
                'timestamp': int(timestamp.timestamp() * 1000),
                'message': formatted_message
            }
            
            self.logs_client.put_log_events(
                logGroupName=self.log_group_name,
                logStreamName=log_stream,
                logEvents=[log_event]
            )
            
            return True
        
        except ClientError as e:
            logger.error(f"Failed to send log event: {e}")
            return False
    
    def _ensure_log_stream_exists(self, log_stream: str):
        """Ensure log stream exists"""
        try:
            self.logs_client.create_log_stream(
                logGroupName=self.log_group_name,
                logStreamName=log_stream
            )
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                logger.warning(f"Failed to create log stream: {e}")
    
    def get_log_events(
        self,
        log_stream: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get log events from CloudWatch Logs
        
        Args:
            log_stream: Name of the log stream
            start_time: Start time for logs
            end_time: End time for logs
            limit: Maximum number of events
            
        Returns:
            List of log events
        """
        try:
            kwargs = {
                'logGroupName': self.log_group_name,
                'logStreamName': log_stream,
                'limit': limit
            }
            
            if start_time:
                kwargs['startTime'] = int(start_time.timestamp() * 1000)
            
            if end_time:
                kwargs['endTime'] = int(end_time.timestamp() * 1000)
            
            response = self.logs_client.get_log_events(**kwargs)
            
            return response.get('events', [])
        
        except ClientError as e:
            logger.error(f"Failed to get log events: {e}")
            return []
    
    # Application-specific metric methods
    def record_api_request(self, endpoint: str, method: str, status_code: int, duration: float):
        """Record API request metrics"""
        dimensions = {
            'Endpoint': endpoint,
            'Method': method,
            'StatusCode': str(status_code)
        }
        
        # Request count
        self.put_metric('APIRequests', 1, 'Count', dimensions)
        
        # Response time
        self.put_metric('APIResponseTime', duration, 'Seconds', dimensions)
        
        # Error count for non-2xx responses
        if status_code >= 400:
            self.put_metric('APIErrors', 1, 'Count', dimensions)
    
    def record_document_processing(self, success: bool, duration: float, file_size: int):
        """Record document processing metrics"""
        dimensions = {'Status': 'Success' if success else 'Failed'}
        
        # Processing count
        self.put_metric('DocumentProcessing', 1, 'Count', dimensions)
        
        # Processing time
        self.put_metric('ProcessingTime', duration, 'Seconds', dimensions)
        
        # File size processed
        self.put_metric('ProcessedFileSize', file_size, 'Bytes', dimensions)
    
    def record_user_activity(self, activity_type: str, user_id: Optional[str] = None):
        """Record user activity metrics"""
        dimensions = {'ActivityType': activity_type}
        
        if user_id:
            dimensions['UserID'] = user_id
        
        self.put_metric('UserActivity', 1, 'Count', dimensions)
    
    def record_system_health(self, cpu_usage: float, memory_usage: float, disk_usage: float):
        """Record system health metrics"""
        metrics = [
            {'name': 'CPUUsage', 'value': cpu_usage, 'unit': 'Percent'},
            {'name': 'MemoryUsage', 'value': memory_usage, 'unit': 'Percent'},
            {'name': 'DiskUsage', 'value': disk_usage, 'unit': 'Percent'}
        ]
        
        self.put_metrics_batch(metrics)
    
    def record_database_metrics(self, connection_count: int, query_time: float, query_type: str):
        """Record database metrics"""
        dimensions = {'QueryType': query_type}
        
        # Database connections
        self.put_metric('DatabaseConnections', connection_count, 'Count')
        
        # Query time
        self.put_metric('DatabaseQueryTime', query_time, 'Seconds', dimensions)
    
    def record_celery_task_metrics(self, task_name: str, success: bool, duration: float):
        """Record Celery task metrics"""
        dimensions = {
            'TaskName': task_name,
            'Status': 'Success' if success else 'Failed'
        }
        
        # Task count
        self.put_metric('CeleryTasks', 1, 'Count', dimensions)
        
        # Task duration
        self.put_metric('CeleryTaskDuration', duration, 'Seconds', dimensions)
    
    def create_standard_alarms(self):
        """Create standard application alarms"""
        alarms = [
            {
                'name': 'HighAPIErrorRate',
                'metric': 'APIErrors',
                'threshold': 10,
                'comparison': 'GreaterThanThreshold',
                'description': 'High API error rate detected'
            },
            {
                'name': 'SlowAPIResponse',
                'metric': 'APIResponseTime',
                'threshold': 5.0,
                'comparison': 'GreaterThanThreshold',
                'statistic': 'Average',
                'description': 'Slow API response times detected'
            },
            {
                'name': 'ProcessingFailures',
                'metric': 'DocumentProcessing',
                'threshold': 5,
                'comparison': 'GreaterThanThreshold',
                'dimensions': {'Status': 'Failed'},
                'description': 'High document processing failure rate'
            }
        ]
        
        for alarm in alarms:
            self.create_alarm(
                alarm_name=alarm['name'],
                metric_name=alarm['metric'],
                comparison_operator=alarm['comparison'],
                threshold=alarm['threshold'],
                statistic=alarm.get('statistic', 'Sum'),
                dimensions=alarm.get('dimensions'),
                description=alarm.get('description')
            )


# Global instance
cloudwatch_service = CloudWatchService()