# Resume Analysis Frontend

AI-powered resume analysis platform frontend built with React 18, Vite, TypeScript, and Material-UI.

## Tech Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite 5
- **UI Library**: Material-UI (MUI) v6 with Emotion
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Testing**: Vitest + React Testing Library
- **Code Quality**: ESLint, Prettier

## Prerequisites

- Node.js >= 18.0.0
- npm >= 9.0.0

## Installation

```bash
cd frontend
npm install
```

## Development

Start the development server:

```bash
npm run dev
```

The application will be available at [http://localhost:5173](http://localhost:5173)

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run test` - Run tests
- `npm run test:ui` - Run tests with UI
- `npm run test:coverage` - Run tests with coverage report
- `npm run lint` - Run ESLint
- `npm run format` - Format code with Prettier

## Project Structure

```
frontend/
├── src/
│   ├── api/           # API client and endpoints
│   ├── components/    # React components
│   ├── hooks/         # Custom React hooks
│   ├── types/         # TypeScript type definitions
│   ├── utils/         # Utility functions
│   ├── tests/         # Test setup and utilities
│   ├── App.tsx        # Root application component
│   ├── main.tsx       # Application entry point
│   └── index.css      # Global styles
├── public/            # Static assets
├── index.html         # HTML template
├── package.json       # Dependencies and scripts
├── vite.config.ts     # Vite configuration
├── tsconfig.json      # TypeScript configuration
└── .eslintrc.cjs      # ESLint configuration
```

## Configuration

### Environment Variables

Create a `.env` file in the frontend directory (see `.env.example`):

```bash
# Backend API URL
VITE_API_URL=http://localhost:8000

# Application Title
VITE_APP_TITLE=Resume Analysis Platform
```

### API Proxy

The development server is configured to proxy API requests to the backend:

- `/api/*` → `http://localhost:8000/api/*`
- `/health` → `http://localhost:8000/health`

## Features

- 📄 Resume upload with drag-and-drop support
- 🔍 Real-time analysis results display
- 🎨 Material-UI components with custom theming
- 📊 Job matching visualization with color-coded skills
- 🌐 Responsive design for mobile and desktop
- ♿ Accessibility support (WCAG 2.1 AA)

## Testing

Run tests in watch mode:

```bash
npm run test
```

Run tests with coverage:

```bash
npm run test:coverage
```

## Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Code Style

This project uses:
- **ESLint** for linting
- **Prettier** for code formatting
- **TypeScript strict mode** for type safety

## License

MIT
