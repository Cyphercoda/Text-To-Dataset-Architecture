import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { AnalysisResults } from '../../types';

interface AnalysisState {
  results: Record<string, AnalysisResults>;
  currentAnalysis: AnalysisResults | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: AnalysisState = {
  results: {},
  currentAnalysis: null,
  isLoading: false,
  error: null,
};

const analysisSlice = createSlice({
  name: 'analysis',
  initialState,
  reducers: {
    setAnalysisResults: (state, action: PayloadAction<{ documentId: string; results: AnalysisResults }>) => {
      state.results[action.payload.documentId] = action.payload.results;
    },
    setCurrentAnalysis: (state, action: PayloadAction<AnalysisResults | null>) => {
      state.currentAnalysis = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    clearResults: (state) => {
      state.results = {};
      state.currentAnalysis = null;
    },
  },
});

export const { setAnalysisResults, setCurrentAnalysis, setLoading, setError, clearResults } = analysisSlice.actions;
export default analysisSlice.reducer;