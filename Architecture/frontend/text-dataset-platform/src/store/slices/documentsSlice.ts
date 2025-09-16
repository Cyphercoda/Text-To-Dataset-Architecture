import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Document, ApiResponse } from '../../types';

interface DocumentsState {
  documents: Document[];
  currentDocument: Document | null;
  isLoading: boolean;
  uploadProgress: Record<string, number>;
  error: string | null;
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

const initialState: DocumentsState = {
  documents: [],
  currentDocument: null,
  isLoading: false,
  uploadProgress: {},
  error: null,
  pagination: {
    page: 1,
    limit: 20,
    total: 0,
    totalPages: 0,
  },
};

export const fetchDocuments = createAsyncThunk(
  'documents/fetchDocuments',
  async (params: { page?: number; limit?: number; status?: string; dateRange?: string }) => {
    const queryParams = new URLSearchParams();
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.limit) queryParams.append('limit', params.limit.toString());
    if (params.status) queryParams.append('status', params.status);
    if (params.dateRange) queryParams.append('date_range', params.dateRange);

    const response = await fetch(`/api/v1/documents/list?${queryParams}`);
    const data: ApiResponse<Document[]> = await response.json();
    
    if (!data.success) {
      throw new Error(data.error?.message || 'Failed to fetch documents');
    }
    
    return { documents: data.data || [], pagination: data.pagination };
  }
);

export const uploadDocument = createAsyncThunk(
  'documents/upload',
  async (file: File, { dispatch }) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch('/api/v1/documents/upload', {
      method: 'POST',
      body: formData,
    });
    
    const data: ApiResponse<{ upload_id: string; document_ids: string[]; processing_started: boolean }> = await response.json();
    
    if (!data.success || !data.data) {
      throw new Error(data.error?.message || 'Upload failed');
    }
    
    return data.data;
  }
);

export const deleteDocument = createAsyncThunk(
  'documents/delete',
  async (documentId: string) => {
    const response = await fetch(`/api/v1/documents/${documentId}`, {
      method: 'DELETE',
    });
    
    const data: ApiResponse<{ success: boolean; cleanup_scheduled: boolean }> = await response.json();
    
    if (!data.success) {
      throw new Error(data.error?.message || 'Delete failed');
    }
    
    return documentId;
  }
);

const documentsSlice = createSlice({
  name: 'documents',
  initialState,
  reducers: {
    setCurrentDocument: (state, action: PayloadAction<Document | null>) => {
      state.currentDocument = action.payload;
    },
    updateUploadProgress: (state, action: PayloadAction<{ documentId: string; progress: number }>) => {
      state.uploadProgress[action.payload.documentId] = action.payload.progress;
    },
    updateDocumentStatus: (state, action: PayloadAction<{ documentId: string; status: Document['status']; progress?: number }>) => {
      const document = state.documents.find(doc => doc.id === action.payload.documentId);
      if (document) {
        document.status = action.payload.status;
        if (action.payload.progress !== undefined) {
          document.processingStage.progress = action.payload.progress;
        }
      }
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchDocuments.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchDocuments.fulfilled, (state, action) => {
        state.isLoading = false;
        state.documents = action.payload.documents;
        if (action.payload.pagination) {
          state.pagination = action.payload.pagination;
        }
      })
      .addCase(fetchDocuments.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch documents';
      })
      
      .addCase(uploadDocument.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(uploadDocument.fulfilled, (state) => {
        state.isLoading = false;
      })
      .addCase(uploadDocument.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Upload failed';
      })
      
      .addCase(deleteDocument.fulfilled, (state, action) => {
        state.documents = state.documents.filter(doc => doc.id !== action.payload);
      });
  },
});

export const { setCurrentDocument, updateUploadProgress, updateDocumentStatus, clearError } = documentsSlice.actions;
export default documentsSlice.reducer;