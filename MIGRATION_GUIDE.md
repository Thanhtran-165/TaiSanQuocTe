# Price Tracker - Streamlit to Next.js Migration

Complete migration from Streamlit to modern **FastAPI + Next.js** with Liquid Glass UI.

## What's New

✅ **Modern Liquid Glass UI** - Beautiful glassmorphism design
✅ **Better Performance** - React 19 + Next.js 14
✅ **Type Safety** - Full TypeScript support
✅ **Real-time Updates** - Auto-refresh functionality
✅ **Responsive Design** - Mobile-friendly interface
✅ **API Architecture** - Separated backend/frontend for scalability

## Project Structure

```
Word Asset/
├── ui/                          # Original Streamlit app (legacy)
│   ├── app.py                  # Streamlit application
│   ├── data_fetcher.py         # Data fetching logic
│   └── price_history.db        # SQLite database
│
├── price-tracker-backend/       # NEW: FastAPI backend
│   ├── main.py                 # API endpoints
│   ├── requirements.txt        # Python dependencies
│   └── README.md               # Backend docs
│
└── price-tracker-frontend/      # NEW: Next.js frontend
    ├── app/                    # Next.js App Router
    │   ├── page.tsx           # Dashboard with 3 tabs
    │   ├── layout.tsx         # Root layout
    │   └── globals.css        # Liquid glass styles
    ├── components/             # React components
    │   ├── PriceCard.tsx      # Price display cards
    │   └── Tabs.tsx           # Tab navigation
    ├── lib/                    # Utilities
    │   └── api.ts             # API client
    └── README.md              # Frontend docs
```

## Quick Start

### 1. Start Backend

```bash
cd price-tracker-backend
pip install -r requirements.txt
python main.py
```

Backend runs on: **http://localhost:8000**

API Docs: **http://localhost:8000/docs**

### 2. Start Frontend

```bash
cd price-tracker-frontend
npm install
npm run dev
```

Frontend runs on: **http://localhost:3000**

### 3. Open in Browser

Navigate to: **http://localhost:3000**

## Features Comparison

| Feature | Streamlit (Old) | Next.js (New) |
|---------|----------------|---------------|
| UI Framework | Streamlit | React + Next.js |
| Styling | Limited CSS | Full CSS + Tailwind |
| Performance | Page reloads | Fast refresh |
| Type Safety | Python | TypeScript |
| Mobile Support | Basic | Responsive |
| Customization | Limited | Unlimited |
| Architecture | Monolithic | Client-Server |

## Liquid Glass UI Features

The new UI includes:

- **Glassmorphism Effects** - backdrop-blur with transparency
- **Gradient Background** - Purple to pink gradient
- **Hover Animations** - Interactive card effects
- **Custom Scrollbars** - Styled scrollbars
- **Responsive Layout** - Mobile, tablet, desktop

## API Endpoints

Backend provides REST API:

```
GET /api/prices/today              # Today's prices
GET /api/prices/history?days=7     # Historical data
GET /api/prices/sjc-items          # SJC products
GET /api/prices/phuquy-items       # Phu Quy products
GET /api/health                    # Health check
```

## Migration Benefits

### Performance
- ⚡ Faster page loads with React
- 🔄 Real-time updates without full reload
- 📱 Optimized for mobile devices

### Development
- 🔧 Easier to customize and extend
- 🎨 Full control over UI/UX
- 🐛 Better debugging with TypeScript

### Scalability
- 📈 Backend can serve multiple clients
- 🔄 Easy to add mobile apps later
- 🌐 Can deploy frontend independently

## What's Migrated

✅ All 3 tabs (Today, History, Comparison)
✅ Real-time price data
✅ Price spread calculations
✅ Historical data viewing
✅ Auto-refresh functionality
✅ All data sources (SJC, Phu Quy, International)
✅ USD/VND exchange rate

## What's Enhanced

🎨 **UI Design**
- Modern glassmorphism effects
- Smooth animations and transitions
- Better color contrast and readability
- Custom styled components

⚡ **User Experience**
- Faster loading times
- Better mobile experience
- Interactive hover effects
- Improved error handling

🔧 **Developer Experience**
- TypeScript for type safety
- Component-based architecture
- Easy to customize styles
- Better code organization

## Troubleshooting

### Backend Issues

**Port 8000 already in use?**
```bash
# Change port in main.py:
uvicorn.run(app, host="0.0.0.0", port=8001)
```

**Import errors?**
```bash
# Make sure you're in the correct directory
cd "Word Asset/price-tracker-backend"
```

### Frontend Issues

**Can't connect to backend?**
```bash
# Check backend is running:
curl http://localhost:8000/api/health

# Check console for CORS errors
```

**Styles not loading?**
```bash
# Clear Next.js cache:
cd price-tracker-frontend
rm -rf .next
npm run dev
```

## Next Steps

### Optional Enhancements

1. **Add Charts**
   - Integrate Plotly.js for interactive charts
   - Add price trend graphs

2. **Add Alerts**
   - Price threshold notifications
   - Email/SMS alerts

3. **Add Authentication**
   - User accounts
   - Saved preferences

4. **Deploy to Production**
   - Backend: Railway, Render, or AWS
   - Frontend: Vercel or Netlify

### Keep Streamlit?

The original Streamlit app in `ui/` still works. You can:
- Keep both running
- Use Streamlit for admin features
- Migrate gradually

## Support

For issues or questions:
- Backend: Check `price-tracker-backend/README.md`
- Frontend: Check `price-tracker-frontend/README.md`
- Original: Check `ui/README.md`

## License

MIT

---

**Enjoy your new Liquid Glass UI! 🎉**
