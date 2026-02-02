# AquaSentinel Pro

Enterprise-grade early warning platform for waterborne disease outbreak prediction.

## 🚀 Quick Start

From inside `aquasentinel-pro/`:

```bash
# Start all services with Docker Compose
docker-compose up --build
```

Then open your browser to:
- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 📋 What's Included

### ✅ **Complete Frontend (Next.js 14 + Tailwind CSS)**
- 🗺️ **Interactive Risk Map** - Leaflet-powered world map showing real-time risk levels
- 📊 **Risk Trends Chart** - 30-day historical risk visualization with Recharts
- 🚨 **Active Alerts Panel** - Live disease outbreak notifications
- 📈 **Analytics Dashboard** - Regional statistics and summary metrics
- 🎨 **Professional UI** - shadcn/ui components with Tailwind styling

### ✅ **Complete Backend (Python FastAPI Microservices)**
- **Core Service** - PostgreSQL database with full CRUD APIs for regions, predictions, alerts
- **ML Service** - Smart risk prediction with parameter-based calculations
- **Ingestion Service** - Mock data providers for WHO, NASA GIBS, NOAA
- **API Gateway** - Unified API with CORS and service routing

### ✅ **Database & Infrastructure**
- TimescaleDB (PostgreSQL) with SQLAlchemy ORM
- Redis cache (configured, ready to use)
- NATS message bus (configured, ready to use)
- Full database seeding with 20+ regions, 100+ predictions, 10+ alerts

---

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │  Next.js 14 + Tailwind + Leaflet + Recharts
│  (Port 3000)│
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  API Gateway    │  FastAPI + CORS + Service Routing
│   (Port 8000)   │
└────────┬────────┘
         │
    ┌────┴────────────────┐
    │                     │
    ▼                     ▼
┌──────────┐      ┌──────────┐      ┌──────────┐
│  Core    │      │    ML    │      │Ingestion │
│ Service  │      │ Service  │      │ Service  │
│(Port 8001)│     │(Port 8002)│     │(Port 8003)│
└────┬─────┘      └──────────┘      └──────────┘
     │
     ▼
┌──────────────────┐
│  TimescaleDB     │  PostgreSQL + TimescaleDB
│  (Port 5432)     │
└──────────────────┘
```

---

## 🧪 Testing the Application

### **1. Start Services**
```bash
docker-compose up --build
```

Wait for all services to start (you'll see "Core service ready!" in logs).

### **2. Verify Backend APIs**

Test the API Gateway:
```bash
# Health check
curl http://localhost:8000/health

# Get all regions
curl http://localhost:8000/regions | jq

# Get active alerts
curl http://localhost:8000/alerts | jq

# Get analytics summary
curl http://localhost:8000/analytics/summary | jq

# Predict risk
curl -X POST http://localhost:8000/ml/predict \
  -H "Content-Type: application/json" \
  -d '{"region_id": 1, "recent_rainfall": 0.8, "sanitation_index": 0.4}' | jq
```

### **3. Verify Database**

Connect to PostgreSQL:
```bash
docker exec -it aquasentinel-pro-postgres-1 psql -U postgres -d aquasentinel
```

Check data:
```sql
-- View regions
SELECT id, name, country, current_risk_level, current_risk_score FROM regions LIMIT 5;

-- Count predictions
SELECT COUNT(*) FROM risk_predictions;

-- View active alerts
SELECT id, region_id, severity, disease_type FROM alerts WHERE status = 'active' LIMIT 5;

-- Exit
\q
```

### **4. Test Frontend**

1. Open http://localhost:3000
2. Click "Open Dashboard →"
3. Verify:
   - ✅ Stats cards show data (regions monitored, alerts, etc.)
   - ✅ Map displays with colored risk markers
   - ✅ Clicking markers shows region popups
   - ✅ Alerts list shows active disease outbreaks
   - ✅ Risk trends chart displays 30-day data
   - ✅ No console errors in browser DevTools

---

## 📁 Project Structure

```
aquasentinel-pro/
├── src/
│   ├── frontend/              # Next.js application
│   │   ├── app/              # Pages (App Router)
│   │   │   ├── page.tsx      # Home page
│   │   │   └── dashboard/    # Dashboard page
│   │   ├── components/       # React components
│   │   │   ├── RiskMap.tsx   # Leaflet map
│   │   │   ├── RiskChart.tsx # Recharts visualization
│   │   │   ├── AlertsList.tsx
│   │   │   └── ui/           # shadcn/ui components
│   │   ├── lib/              # Utilities
│   │   │   └── api.ts        # API client
│   │   ├── hooks/            # Custom React hooks
│   │   └── public/
│   │       └── mock-data/    # Frontend mock JSON files
│   │
│   ├── core-service/         # Main backend service
│   │   └── app/
│   │       ├── models.py     # SQLAlchemy models
│   │       ├── schemas.py    # Pydantic schemas
│   │       ├── db.py         # Database connection
│   │       ├── seed.py       # Database seeding
│   │       └── routes/       # API endpoints
│   │           ├── regions.py
│   │           ├── predictions.py
│   │           ├── alerts.py
│   │           └── analytics.py
│   │
│   ├── ml-service/           # ML prediction service
│   │   └── app/
│   │       ├── inference.py  # Risk calculation
│   │       └── risk_factors.py
│   │
│   ├── ingestion-service/    # Data ingestion
│   │   └── app/
│   │       └── providers/
│   │           ├── who.py    # WHO mock data
│   │           ├── nasa_gibs.py
│   │           └── noaa.py
│   │
│   └── api-gateway/          # API Gateway
│       └── app/
│           └── main.py       # Service routing
│
├── docker-compose.yml        # Multi-service orchestration
└── README.md                # This file
```

---

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
# Backend
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/aquasentinel
NATS_URL=nats://nats:4222
REDIS_URL=redis://redis:6379

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

For frontend development:
```bash
cd src/frontend
cp .env.local.example .env.local
```

---

## 🛠️ Development

### Install Frontend Dependencies Locally

```bash
cd src/frontend
npm install
npm run dev
```

### Access API Documentation

FastAPI automatically generates interactive API docs:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f core-service
docker-compose logs -f frontend
```

### Stop Services

```bash
docker-compose down

# Remove volumes (reset database)
docker-compose down -v
```

---

## 📊 Key Features

### Risk Prediction Algorithm
The ML service calculates risk scores using weighted factors:
- **Rainfall Anomaly** (30%)
- **Sanitation Index** (25%)
- **Population Density** (20%)
- **Flood Extent** (15%)
- **Water Quality** (10%)

### Mock Data Providers
- **WHO**: Disease outbreak reports, active alerts
- **NASA GIBS**: Satellite flood extent, rainfall data
- **NOAA**: Weather observations, precipitation forecasts

### Database Schema
- **Regions**: Geographic locations with current risk levels
- **Risk Predictions**: Historical ML predictions with confidence scores
- **Alerts**: Active disease outbreak notifications
- **Data Sources**: Ingested data tracking from all providers

---

## 🎯 Success Criteria

✅ All 7 Docker services start successfully
✅ Database contains 20+ regions with seed data
✅ Backend APIs return valid JSON responses
✅ Frontend displays with full Tailwind styling
✅ Map shows risk-colored markers for all regions
✅ Chart displays 30-day historical trends
✅ Alerts panel shows active disease outbreaks
✅ No errors in browser console or server logs

---

## 🚧 Future Enhancements

- [ ] Real-time updates with WebSockets
- [ ] User authentication and role-based access
- [ ] Advanced ML models (Prophet, LSTM)
- [ ] Real API integrations (WHO, NASA, NOAA)
- [ ] Email/SMS alerting system
- [ ] Historical data export (CSV, JSON)
- [ ] Mobile-responsive optimizations
- [ ] Kubernetes deployment configs

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🙋 Support

For issues or questions:
- Create an issue in the GitHub repository
- Check API docs at http://localhost:8000/docs
- Review logs: `docker-compose logs -f`

---

**Built with Next.js, FastAPI, PostgreSQL, Leaflet, and Recharts** 🚀
