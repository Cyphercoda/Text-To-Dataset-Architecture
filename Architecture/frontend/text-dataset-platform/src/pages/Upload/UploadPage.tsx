/**
 * Upload Page Component
 * Document upload interface with drag & drop, progress tracking, and batch operations
 */

import React, { useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useDropzone } from 'react-dropzone';
import toast from 'react-hot-toast';

// Components
import { OptimizedCard } from '../../components/optimization/PerformanceOptimized';
import LoadingSpinner from '../../components/ui/LoadingSpinner';
import ProgressBar from '../../components/ui/ProgressBar';
import FilePreview from '../../components/upload/FilePreview';
import ProcessingConfig from '../../components/upload/ProcessingConfig';
import UploadHistory from '../../components/upload/UploadHistory';

// Hooks and Services
import { useS3Upload } from '../../services/awsIntegration';
import { useProcessingStore } from '../../stores/realTimeStore';
import { uploadAPI } from '../../services/api/upload';

// Types
import { UploadFile, ProcessingConfig as ProcessingConfigType } from '../../types';

// Icons
import {
  CloudArrowUpIcon,
  DocumentTextIcon,
  XMarkIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';

interface UploadState {
  files: UploadFile[];
  isUploading: boolean;
  uploadProgress: Record<string, number>;
  config: ProcessingConfigType;
  showAdvancedConfig: boolean;
}

const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { uploadFile, uploadProgress, isUploading } = useS3Upload();
  const { addJob } = useProcessingStore();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [state, setState] = useState<UploadState>({
    files: [],
    isUploading: false,
    uploadProgress: {},
    config: {
      outputFormat: 'json',
      qualityLevel: 'high',
      enableNER: true,
      enableSentiment: true,
      enableClassification: true,
      batchSize: 10,
      language: 'auto',
      customInstructions: '',
    },
    showAdvancedConfig: false,
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: uploadAPI.uploadDocuments,
    onSuccess: (data) => {
      toast.success('Documents uploaded successfully!');
      
      // Add processing jobs to store
      data.jobs?.forEach(job => addJob(job));
      
      // Clear files and redirect
      setState(prev => ({ ...prev, files: [] }));
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      
      // Navigate to dashboard to see processing progress
      navigate('/dashboard');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Upload failed');
    },
  });

  // Dropzone configuration
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'application/rtf': ['.rtf'],
    },
    maxSize: 50 * 1024 * 1024, // 50MB
    maxFiles: 20,
    onDrop: handleFileDrop,
    onDropRejected: handleDropRejected,
  });

  // Handle file drop
  function handleFileDrop(acceptedFiles: File[]) {
    const newFiles: UploadFile[] = acceptedFiles.map(file => ({
      id: `${file.name}-${Date.now()}-${Math.random()}`,
      file,
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'pending',
      progress: 0,
      error: null,
    }));

    setState(prev => ({
      ...prev,
      files: [...prev.files, ...newFiles],
    }));
  }

  // Handle rejected files
  function handleDropRejected(rejectedFiles: any[]) {
    rejectedFiles.forEach(({ file, errors }) => {
      const errorMessage = errors.map((e: any) => e.message).join(', ');
      toast.error(`${file.name}: ${errorMessage}`);
    });
  }

  // Remove file from list
  const removeFile = useCallback((fileId: string) => {
    setState(prev => ({
      ...prev,
      files: prev.files.filter(f => f.id !== fileId),
    }));
  }, []);

  // Update processing config
  const updateConfig = useCallback((newConfig: Partial<ProcessingConfigType>) => {
    setState(prev => ({
      ...prev,
      config: { ...prev.config, ...newConfig },
    }));
  }, []);

  // Start upload process
  const startUpload = async () => {
    if (state.files.length === 0) {
      toast.error('Please select files to upload');
      return;
    }

    setState(prev => ({ ...prev, isUploading: true }));

    try {
      // Update file statuses to uploading
      setState(prev => ({
        ...prev,
        files: prev.files.map(f => ({ ...f, status: 'uploading' })),
      }));

      const uploadPromises = state.files.map(async (uploadFile) => {
        try {
          // Upload to S3 and get key
          const s3Key = await uploadFile(uploadFile.file, 'user-id'); // Replace with actual user ID
          
          // Update file status
          setState(prev => ({
            ...prev,
            files: prev.files.map(f =>
              f.id === uploadFile.id
                ? { ...f, status: 'uploaded', s3Key }
                : f
            ),
          }));

          return {
            name: uploadFile.name,
            s3Key,
            size: uploadFile.size,
            type: uploadFile.type,
          };
        } catch (error) {
          setState(prev => ({
            ...prev,
            files: prev.files.map(f =>
              f.id === uploadFile.id
                ? { ...f, status: 'error', error: (error as Error).message }
                : f
            ),
          }));
          throw error;
        }
      });

      const uploadedFiles = await Promise.all(uploadPromises);

      // Start processing
      await uploadMutation.mutateAsync({
        files: uploadedFiles,
        config: state.config,
      });

    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setState(prev => ({ ...prev, isUploading: false }));
    }
  };

  // Clear all files
  const clearFiles = () => {
    setState(prev => ({ ...prev, files: [] }));
  };

  // Get upload statistics
  const uploadStats = {
    total: state.files.length,
    pending: state.files.filter(f => f.status === 'pending').length,
    uploading: state.files.filter(f => f.status === 'uploading').length,
    completed: state.files.filter(f => f.status === 'uploaded').length,
    failed: state.files.filter(f => f.status === 'error').length,
    totalSize: state.files.reduce((sum, f) => sum + f.size, 0),
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Upload Documents</h1>
          <p className="text-gray-600 mt-2">
            Upload your text documents to convert them into training-ready datasets
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Upload Area */}
          <div className="lg:col-span-2 space-y-6">
            {/* Drag & Drop Zone */}
            <OptimizedCard title="Select Files" className="h-64">
              <div
                {...getRootProps()}
                className={`h-full border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                  isDragActive
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <input {...getInputProps()} ref={fileInputRef} />
                
                <CloudArrowUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                
                {isDragActive ? (
                  <p className="text-lg text-blue-600">Drop files here...</p>
                ) : (
                  <>
                    <p className="text-lg text-gray-600 mb-2">
                      Drag & drop files here, or click to select
                    </p>
                    <p className="text-sm text-gray-500">
                      Supports PDF, DOC, DOCX, TXT, MD, RTF (max 50MB each)
                    </p>
                  </>
                )}
              </div>
            </OptimizedCard>

            {/* File List */}
            {state.files.length > 0 && (
              <OptimizedCard 
                title={`Selected Files (${state.files.length})`}
                className="max-h-96 overflow-y-auto"
              >
                <div className="space-y-2">
                  {state.files.map((file) => (
                    <FilePreview
                      key={file.id}
                      file={file}
                      onRemove={() => removeFile(file.id)}
                    />
                  ))}
                </div>
                
                {/* Upload Controls */}
                <div className="flex justify-between items-center mt-6 pt-4 border-t">
                  <div className="text-sm text-gray-600">
                    Total: {(uploadStats.totalSize / (1024 * 1024)).toFixed(1)} MB
                  </div>
                  
                  <div className="flex space-x-3">
                    <button
                      onClick={clearFiles}
                      disabled={state.isUploading}
                      className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
                    >
                      Clear All
                    </button>
                    
                    <button
                      onClick={startUpload}
                      disabled={state.isUploading || uploadMutation.isPending}
                      className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center"
                    >
                      {state.isUploading || uploadMutation.isPending ? (
                        <>
                          <LoadingSpinner size="sm" className="mr-2" />
                          Uploading...
                        </>
                      ) : (
                        'Start Upload'
                      )}
                    </button>
                  </div>
                </div>
              </OptimizedCard>
            )}

            {/* Upload Progress */}
            {(state.isUploading || uploadMutation.isPending) && (
              <OptimizedCard title="Upload Progress">
                <div className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="text-gray-500">Total</div>
                      <div className="font-medium">{uploadStats.total}</div>
                    </div>
                    <div>
                      <div className="text-gray-500">Completed</div>
                      <div className="font-medium text-green-600">{uploadStats.completed}</div>
                    </div>
                    <div>
                      <div className="text-gray-500">Uploading</div>
                      <div className="font-medium text-blue-600">{uploadStats.uploading}</div>
                    </div>
                    <div>
                      <div className="text-gray-500">Failed</div>
                      <div className="font-medium text-red-600">{uploadStats.failed}</div>
                    </div>
                  </div>
                  
                  <ProgressBar
                    progress={(uploadStats.completed / uploadStats.total) * 100}
                    className="w-full"
                  />
                </div>
              </OptimizedCard>
            )}
          </div>

          {/* Configuration Panel */}
          <div className="space-y-6">
            {/* Processing Configuration */}
            <ProcessingConfig
              config={state.config}
              onChange={updateConfig}
              showAdvanced={state.showAdvancedConfig}
              onToggleAdvanced={() =>
                setState(prev => ({
                  ...prev,
                  showAdvancedConfig: !prev.showAdvancedConfig,
                }))
              }
            />

            {/* Upload History */}
            <UploadHistory />
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadPage;