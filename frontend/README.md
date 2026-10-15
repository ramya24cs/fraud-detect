# Cost-Sensitive Fraud Detection System

A React-based frontend for the Cost-Sensitive Fraud Detection
with Operator Feedback Loop project.

## Technology Stack

- React
- Vite
- React Router
- Axios
- Recharts
- CSS

## Prerequisites

- Node.js
- npm
- Backend API (for real data and authentication)

## Installation

Open a terminal in the frontend directory and run:

    npm install

## Environment Configuration

Create a `.env` file inside the `frontend` directory.

For local demonstration, configure:

    VITE_DEMO_MODE=true
    VITE_API_BASE_URL=http://localhost:8000

Demo mode displays illustrative sample data. Feedback submissions
are not stored in the database, and displayed metrics are not actual
model evaluation results.

## Run the Application

Start the development server:

    npm run dev

Open the local URL shown in the terminal.

## Build for Production

Run:

    npm run build

The production-ready files are generated in the `dist` directory.

## Application Pages

- Dashboard
- Risk Analytics
- Review Queue
- Case Detail
- Feedback Analytics
- Model Monitoring
- Login

## Backend Integration

The frontend includes API service modules for authentication,
transaction predictions, feedback, dashboard metrics, and model
information.

Real authentication, fraud predictions, feedback persistence,
and model metrics require a correctly configured backend.

## Important Notes

- Demo values are illustrative, not actual research results.
- Feedback entered in demo mode is not saved to the database.
- Disable demo mode and verify authentication and API connectivity
  before production deployment.
- Never commit API secrets or private credentials to GitHub.