import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { ProcessingJob } from '../../types';

interface ProcessingState {
  jobs: ProcessingJob[];
  currentJob: ProcessingJob | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: ProcessingState = {
  jobs: [],
  currentJob: null,
  isLoading: false,
  error: null,
};

const processingSlice = createSlice({
  name: 'processing',
  initialState,
  reducers: {
    setJobs: (state, action: PayloadAction<ProcessingJob[]>) => {
      state.jobs = action.payload;
    },
    addJob: (state, action: PayloadAction<ProcessingJob>) => {
      state.jobs.push(action.payload);
    },
    updateJob: (state, action: PayloadAction<ProcessingJob>) => {
      const index = state.jobs.findIndex(job => job.id === action.payload.id);
      if (index !== -1) {
        state.jobs[index] = action.payload;
      }
    },
    setCurrentJob: (state, action: PayloadAction<ProcessingJob | null>) => {
      state.currentJob = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
  },
});

export const { setJobs, addJob, updateJob, setCurrentJob, setLoading, setError } = processingSlice.actions;
export default processingSlice.reducer;