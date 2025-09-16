# Text-to-Dataset Platform Frontend

A comprehensive React TypeScript application for converting text documents into training-ready datasets for Large Language Model (LLM) development.

## 🚀 Features

### Core Functionality
- **User Authentication**: Secure login/register with MFA support
- **Document Management**: Upload, process, and manage text documents
- **Real-time Processing**: Live updates on document processing status
- **Advanced Analytics**: Interactive dashboards and visualizations
- **Dataset Generation**: Multiple export formats (JSON, CSV, Parquet, HuggingFace)
- **Quality Metrics**: Comprehensive quality scoring and validation

### Technical Features
- **Material-UI Design System**: Modern, responsive interface
- **Redux Toolkit**: Centralized state management
- **TypeScript**: Type-safe development
- **Real-time Updates**: WebSocket integration ready
- **Performance Optimized**: Code splitting and lazy loading
- **Dark/Light Theme**: User-configurable themes

## 🏗️ Architecture

### Module Structure
```
src/
├── modules/
│   ├── authentication/     # Login, register, user management
│   ├── dashboard/          # Analytics and overview
│   ├── documentManagement/ # File upload and processing
│   ├── analysis/           # NLP results visualization
│   ├── dataset/            # Dataset creation and export
│   └── support/            # Help and documentation
├── store/                  # Redux store and slices
├── types/                  # TypeScript type definitions
├── constants/              # Application constants
├── utils/                  # Utility functions
└── components/common/      # Shared components
```

## 📦 Available Scripts

### `npm start`
Runs the app in development mode at [http://localhost:3000](http://localhost:3000)

### `npm test`
Launches the test runner in interactive watch mode

### `npm run build`
Builds the app for production to the `build` folder

### `npm run eject`
**Note: this is a one-way operation. Once you `eject`, you can't go back!**

## 🎨 Current Implementation Status

### ✅ Completed Components
- **Authentication System**: Login/Register forms with validation
- **Layout & Navigation**: Responsive sidebar with theme switching
- **Dashboard**: Interactive analytics with charts and metrics
- **Redux Store**: Complete state management setup
- **Type System**: Comprehensive TypeScript definitions
- **Routing**: Protected routes and navigation structure

### 🚧 Placeholder Components (Ready for Implementation)
- **Document Management**: File upload and processing interface
- **Analysis & Visualization**: NLP results and entity visualization
- **Dataset Management**: Creation and export tools
- **Settings**: User preferences and configuration

## 🔧 Quick Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start development server**:
   ```bash
   npm start
   ```

3. **Environment Variables** (create `.env` file):
   ```bash
   REACT_APP_API_URL=http://localhost:3001/api/v1
   REACT_APP_WS_URL=ws://localhost:3001
   ```

## 🎯 Next Development Steps

1. **Implement File Upload**: React Dropzone integration for document upload
2. **Add Real-time Updates**: WebSocket connection for live processing status
3. **Build Analysis Components**: Entity recognition and sentiment visualization
4. **Create Dataset Export**: Multiple format generation and download
5. **Add Error Handling**: Comprehensive error boundaries and user feedback

## 📚 Key Dependencies

- **React 18** + **TypeScript**: Modern React development
- **Material-UI (MUI)**: Professional UI components
- **Redux Toolkit**: Simplified Redux state management
- **React Router**: Client-side routing
- **Recharts**: Data visualization and charts
- **Axios**: HTTP client (ready for API integration)

## 🎨 Design System

- **Primary Color**: Professional Blue (#1976d2)
- **Secondary Color**: Accent Red (#dc004e)
- **Typography**: Roboto font family
- **Spacing**: 8px grid system
- **Components**: Rounded design (8px buttons, 12px cards)

---

**Status**: Frontend foundation complete, ready for feature development  
**Version**: 1.0.0  
**Built with**: React + TypeScript + Material-UI + Redux Toolkit
