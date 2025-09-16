import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Dataset } from '../../types';

interface DatasetsState {
  datasets: Dataset[];
  currentDataset: Dataset | null;
  isLoading: boolean;
  error: string | null;
  generationProgress: Record<string, number>;
}

const initialState: DatasetsState = {
  datasets: [],
  currentDataset: null,
  isLoading: false,
  error: null,
  generationProgress: {},
};

const datasetsSlice = createSlice({
  name: 'datasets',
  initialState,
  reducers: {
    setDatasets: (state, action: PayloadAction<Dataset[]>) => {
      state.datasets = action.payload;
    },
    addDataset: (state, action: PayloadAction<Dataset>) => {
      state.datasets.push(action.payload);
    },
    updateDataset: (state, action: PayloadAction<Dataset>) => {
      const index = state.datasets.findIndex(dataset => dataset.id === action.payload.id);
      if (index !== -1) {
        state.datasets[index] = action.payload;
      }
    },
    removeDataset: (state, action: PayloadAction<string>) => {
      state.datasets = state.datasets.filter(dataset => dataset.id !== action.payload);
    },
    setCurrentDataset: (state, action: PayloadAction<Dataset | null>) => {
      state.currentDataset = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setGenerationProgress: (state, action: PayloadAction<{ datasetId: string; progress: number }>) => {
      state.generationProgress[action.payload.datasetId] = action.payload.progress;
    },
  },
});

export const {
  setDatasets,
  addDataset,
  updateDataset,
  removeDataset,
  setCurrentDataset,
  setLoading,
  setError,
  setGenerationProgress,
} = datasetsSlice.actions;

export default datasetsSlice.reducer;