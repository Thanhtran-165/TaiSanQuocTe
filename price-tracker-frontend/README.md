# Price Tracker Frontend

Modern Next.js frontend with **liquid glass UI** for gold and silver price tracking.

## Features

✨ **Liquid Glass UI** - Modern glassmorphism design with backdrop blur effects
🔄 **Real-time Updates** - Auto-refresh functionality for live prices
📊 **Multiple Tabs** - Today, History, and Comparison views
🎨 **Responsive Design** - Works perfectly on mobile and desktop
⚡ **Fast Performance** - Built with Next.js 14 and React 19

## Prerequisites

- Node.js 18+ and npm
- Backend API running on http://localhost:8000

## Quick Start

1. **Install dependencies:**
```bash
npm install
```

2. **Start backend first:**
```bash
cd ../price-tracker-backend
pip install -r requirements.txt
python main.py
# Backend runs on http://localhost:8000
```

3. **Start frontend:**
```bash
npm run dev
# Frontend runs on http://localhost:3000
```

4. **Open browser:**
```
http://localhost:3000
```

## Build for Production

```bash
npm run build
npm start
```

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS 4** - Utility-first CSS
- **Lucide React** - Beautiful icons
- **Custom Liquid Glass CSS** - Glassmorphism effects

## Project Structure

```
price-tracker-frontend/
├── app/
│   ├── globals.css       # Liquid glass styles
│   ├── layout.tsx        # Root layout
│   └── page.tsx          # Main dashboard (3 tabs)
├── components/
│   ├── PriceCard.tsx     # Reusable price card
│   └── Tabs.tsx          # Tab navigation
├── lib/
│   └── api.ts           # API client for backend
└── public/              # Static assets
```

## Liquid Glass Design

The UI features custom glassmorphism effects:

- **backdrop-blur** - Frosted glass effect (20px blur)
- **transparency** - Semi-transparent backgrounds (5-10% opacity)
- **gradient** - Beautiful purple-to-pink gradient background
- **hover effects** - Interactive card animations
- **border effects** - Subtle white borders for depth

### Glass Classes

- `.glass-card` - Main card with hover effect
- `.glass-panel` - Content panels
- `.glass-input` - Form inputs

## Troubleshooting

**Backend not connecting?**
```bash
# Check if backend is running
curl http://localhost:8000/api/health
```

**Styles not loading?**
```bash
rm -rf .next
npm run dev
```

## License

MIT
