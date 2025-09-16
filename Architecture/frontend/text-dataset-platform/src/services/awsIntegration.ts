/**
 * AWS Services Direct Integration
 * Direct browser-to-AWS service communication for optimal performance
 */

import { CognitoIdentityProvider } from '@aws-sdk/client-cognito-identity-provider';
import { S3Client, PutObjectCommand, GetObjectCommand } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { CloudWatchEmbeddableApi } from '@aws-sdk/client-cloudwatch-embedded-metrics';

// AWS Configuration
const AWS_CONFIG = {
  region: process.env.REACT_APP_AWS_REGION || 'us-east-1',
  cognito: {
    userPoolId: process.env.REACT_APP_COGNITO_USER_POOL_ID!,
    clientId: process.env.REACT_APP_COGNITO_CLIENT_ID!,
    identityPoolId: process.env.REACT_APP_COGNITO_IDENTITY_POOL_ID!,
  },
  s3: {
    bucket: process.env.REACT_APP_S3_UPLOAD_BUCKET!,
    region: process.env.REACT_APP_S3_REGION || 'us-east-1',
  },
};

/**
 * Cognito Authentication Service
 */
export class CognitoAuthService {
  private cognitoClient: CognitoIdentityProvider;

  constructor() {
    this.cognitoClient = new CognitoIdentityProvider({
      region: AWS_CONFIG.region,
    });
  }

  /**
   * Authenticate user with Cognito
   */
  async signIn(email: string, password: string, mfaCode?: string) {
    try {
      const response = await this.cognitoClient.initiateAuth({
        AuthFlow: 'USER_PASSWORD_AUTH',
        ClientId: AWS_CONFIG.cognito.clientId,
        AuthParameters: {
          USERNAME: email,
          PASSWORD: password,
        },
      });

      if (response.ChallengeName === 'SOFTWARE_TOKEN_MFA' && mfaCode) {
        const mfaResponse = await this.cognitoClient.respondToAuthChallenge({
          ClientId: AWS_CONFIG.cognito.clientId,
          ChallengeName: 'SOFTWARE_TOKEN_MFA',
          Session: response.Session,
          ChallengeResponses: {
            SOFTWARE_TOKEN_MFA_CODE: mfaCode,
            USERNAME: email,
          },
        });
        return mfaResponse.AuthenticationResult;
      }

      return response.AuthenticationResult;
    } catch (error) {
      console.error('Cognito sign-in error:', error);
      throw error;
    }
  }

  /**
   * Sign up new user
   */
  async signUp(email: string, password: string, name: string) {
    try {
      const response = await this.cognitoClient.signUp({
        ClientId: AWS_CONFIG.cognito.clientId,
        Username: email,
        Password: password,
        UserAttributes: [
          { Name: 'email', Value: email },
          { Name: 'name', Value: name },
        ],
      });
      return response;
    } catch (error) {
      console.error('Cognito sign-up error:', error);
      throw error;
    }
  }

  /**
   * Confirm email verification
   */
  async confirmSignUp(email: string, confirmationCode: string) {
    try {
      return await this.cognitoClient.confirmSignUp({
        ClientId: AWS_CONFIG.cognito.clientId,
        Username: email,
        ConfirmationCode: confirmationCode,
      });
    } catch (error) {
      console.error('Cognito confirm sign-up error:', error);
      throw error;
    }
  }

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string) {
    try {
      const response = await this.cognitoClient.initiateAuth({
        AuthFlow: 'REFRESH_TOKEN_AUTH',
        ClientId: AWS_CONFIG.cognito.clientId,
        AuthParameters: {
          REFRESH_TOKEN: refreshToken,
        },
      });
      return response.AuthenticationResult;
    } catch (error) {
      console.error('Token refresh error:', error);
      throw error;
    }
  }

  /**
   * Get user information
   */
  async getCurrentUser(accessToken: string) {
    try {
      return await this.cognitoClient.getUser({
        AccessToken: accessToken,
      });
    } catch (error) {
      console.error('Get user error:', error);
      throw error;
    }
  }

  /**
   * Sign out user
   */
  async signOut(accessToken: string) {
    try {
      return await this.cognitoClient.globalSignOut({
        AccessToken: accessToken,
      });
    } catch (error) {
      console.error('Sign out error:', error);
      throw error;
    }
  }
}

/**
 * S3 Direct Upload Service
 */
export class S3UploadService {
  private s3Client: S3Client;

  constructor() {
    this.s3Client = new S3Client({
      region: AWS_CONFIG.s3.region,
    });
  }

  /**
   * Generate presigned URL for direct upload
   */
  async getPresignedUploadUrl(
    fileName: string, 
    fileType: string, 
    userId: string,
    expiresIn: number = 3600
  ): Promise<{ uploadUrl: string; key: string }> {
    const key = `uploads/${userId}/${Date.now()}-${fileName}`;
    
    try {
      const command = new PutObjectCommand({
        Bucket: AWS_CONFIG.s3.bucket,
        Key: key,
        ContentType: fileType,
        Metadata: {
          userId,
          uploadedAt: new Date().toISOString(),
        },
      });

      const uploadUrl = await getSignedUrl(this.s3Client, command, { 
        expiresIn 
      });

      return { uploadUrl, key };
    } catch (error) {
      console.error('Error generating presigned URL:', error);
      throw error;
    }
  }

  /**
   * Upload file directly to S3 with progress tracking
   */
  async uploadFile(
    file: File,
    presignedUrl: string,
    onProgress?: (progress: number) => void
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      // Track upload progress
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const progress = (event.loaded / event.total) * 100;
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          resolve();
        } else {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Upload failed'));
      });

      xhr.open('PUT', presignedUrl);
      xhr.setRequestHeader('Content-Type', file.type);
      xhr.send(file);
    });
  }

  /**
   * Multi-part upload for large files
   */
  async uploadLargeFile(
    file: File,
    userId: string,
    chunkSize: number = 5 * 1024 * 1024, // 5MB chunks
    onProgress?: (progress: number) => void
  ): Promise<string> {
    const totalChunks = Math.ceil(file.size / chunkSize);
    const uploadId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const key = `uploads/${userId}/large/${uploadId}-${file.name}`;

    try {
      // Upload chunks in parallel with concurrency limit
      const maxConcurrency = 3;
      const chunks: Promise<void>[] = [];
      
      for (let i = 0; i < totalChunks; i++) {
        const start = i * chunkSize;
        const end = Math.min(start + chunkSize, file.size);
        const chunk = file.slice(start, end);
        
        const chunkPromise = this.uploadChunk(chunk, key, i + 1);
        chunks.push(chunkPromise);

        // Limit concurrency
        if (chunks.length >= maxConcurrency || i === totalChunks - 1) {
          await Promise.all(chunks);
          chunks.length = 0; // Clear array
          
          if (onProgress) {
            const progress = ((i + 1) / totalChunks) * 100;
            onProgress(progress);
          }
        }
      }

      return key;
    } catch (error) {
      console.error('Large file upload error:', error);
      throw error;
    }
  }

  /**
   * Upload individual chunk
   */
  private async uploadChunk(chunk: Blob, key: string, partNumber: number): Promise<void> {
    const chunkKey = `${key}.part${partNumber}`;
    
    const command = new PutObjectCommand({
      Bucket: AWS_CONFIG.s3.bucket,
      Key: chunkKey,
      Body: chunk,
    });

    try {
      await this.s3Client.send(command);
    } catch (error) {
      console.error(`Chunk ${partNumber} upload failed:`, error);
      throw error;
    }
  }
}

/**
 * CloudWatch Embedded Metrics Service
 */
export class CloudWatchMetricsService {
  /**
   * Embed CloudWatch dashboard in React app
   */
  static embedDashboard(
    containerId: string,
    dashboardName: string,
    region: string = AWS_CONFIG.region
  ): void {
    const script = document.createElement('script');
    script.src = 'https://cloudwatchmetrics.aws.amazon.com/js/cloudwatch-metrics.js';
    script.onload = () => {
      // @ts-ignore - CloudWatch embedded API
      window.cloudwatchMetrics?.embedDashboard({
        containerId,
        dashboardName,
        region,
        height: '400px',
        width: '100%',
        autoRefresh: true,
        refreshInterval: 30000, // 30 seconds
      });
    };
    document.head.appendChild(script);
  }

  /**
   * Send custom metrics to CloudWatch
   */
  static async sendMetric(
    metricName: string,
    value: number,
    unit: string = 'Count',
    dimensions?: Record<string, string>
  ): Promise<void> {
    try {
      // Send via custom API endpoint that forwards to CloudWatch
      await fetch('/api/metrics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          metricName,
          value,
          unit,
          dimensions,
          timestamp: new Date().toISOString(),
        }),
      });
    } catch (error) {
      console.error('Failed to send custom metric:', error);
    }
  }
}

/**
 * X-Ray Client-Side Tracing Service
 */
export class XRayTracingService {
  private static traceId: string | null = null;

  /**
   * Start new trace
   */
  static startTrace(operation: string): string {
    const traceId = this.generateTraceId();
    this.traceId = traceId;
    
    // Send trace start to backend
    fetch('/api/trace/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        traceId,
        operation,
        timestamp: Date.now(),
        userAgent: navigator.userAgent,
        url: window.location.href,
      }),
    }).catch(console.error);

    return traceId;
  }

  /**
   * Add subsegment to current trace
   */
  static addSubsegment(name: string, metadata?: Record<string, any>): void {
    if (!this.traceId) return;

    fetch('/api/trace/subsegment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        traceId: this.traceId,
        name,
        timestamp: Date.now(),
        metadata,
      }),
    }).catch(console.error);
  }

  /**
   * End current trace
   */
  static endTrace(success: boolean = true, error?: string): void {
    if (!this.traceId) return;

    fetch('/api/trace/end', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        traceId: this.traceId,
        success,
        error,
        timestamp: Date.now(),
      }),
    }).catch(console.error);

    this.traceId = null;
  }

  private static generateTraceId(): string {
    return `1-${Math.floor(Date.now() / 1000).toString(16)}-${Math.random().toString(16).substr(2, 24)}`;
  }
}

// Export service instances
export const cognitoAuthService = new CognitoAuthService();
export const s3UploadService = new S3UploadService();

// React hooks for AWS integration
export const useCognitoAuth = () => {
  const [user, setUser] = React.useState(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const signIn = async (email: string, password: string, mfaCode?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await cognitoAuthService.signIn(email, password, mfaCode);
      const userInfo = await cognitoAuthService.getCurrentUser(result?.AccessToken!);
      setUser(userInfo);
      return result;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const signOut = async () => {
    setIsLoading(true);
    try {
      await cognitoAuthService.signOut(user?.AccessToken!);
      setUser(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return { user, isLoading, error, signIn, signOut };
};

export const useS3Upload = () => {
  const [uploadProgress, setUploadProgress] = React.useState<Record<string, number>>({});
  const [isUploading, setIsUploading] = React.useState(false);

  const uploadFile = async (file: File, userId: string) => {
    setIsUploading(true);
    const fileId = `${file.name}-${Date.now()}`;
    
    try {
      const { uploadUrl, key } = await s3UploadService.getPresignedUploadUrl(
        file.name,
        file.type,
        userId
      );

      await s3UploadService.uploadFile(file, uploadUrl, (progress) => {
        setUploadProgress(prev => ({ ...prev, [fileId]: progress }));
      });

      return key;
    } catch (error) {
      console.error('Upload failed:', error);
      throw error;
    } finally {
      setIsUploading(false);
      setUploadProgress(prev => {
        const updated = { ...prev };
        delete updated[fileId];
        return updated;
      });
    }
  };

  return { uploadFile, uploadProgress, isUploading };
};