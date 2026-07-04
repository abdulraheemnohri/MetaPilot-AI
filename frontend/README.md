# MetaPilot AI - Frontend

A React-based frontend for the MetaPilot AI application - a multi-AI orchestrator that combines results from multiple AI providers into a single, intelligent response.

## 🚀 Quick Start

### Prerequisites

- Node.js 18.16 or later
- pnpm, npm, or yarn

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── ui/             # Base UI components
│   │   └── ...
│   ├── pages/              # Page components
│   ├── store/              # Zustand state management
│   ├── services/           # API service layers
│   ├── hooks/              # Custom React hooks
│   ├── context/            # React context providers
│   ├── utils/              # Utility functions
│   ├── types/              # TypeScript type definitions
│   ├── App.tsx             # Main application component
│   └── main.tsx            # Application entry point
├── tailwind.config.js      # Tailwind CSS configuration
├── postcss.config.js       # PostCSS configuration
├── vite.config.ts          # Vite configuration
└── package.json            # Project dependencies
```

## 🛠 Technologies

- React 18 + TypeScript
- Vite
- Tailwind CSS
- Zustand
- TanStack Query
- React Router DOM

## 📄 License

MIT License