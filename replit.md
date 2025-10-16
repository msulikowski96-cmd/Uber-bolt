# Taxi Calculator - Ride Profitability Calculator

## Overview

Taxi Calculator is a Progressive Web Application (PWA) designed for taxi/rideshare drivers to calculate ride profitability, track earnings, and analyze performance across multiple platforms (Uber, Bolt, etc.). The application helps drivers make informed decisions about which rides to accept by calculating net profit, hourly rates, and providing AI-powered insights.

**Core Features:**
- Real-time ride profitability calculator with fuel cost analysis
- Multi-platform comparison (Uber, Bolt, etc.)
- Historical ride tracking and statistics
- Daily goal setting and progress monitoring
- AI assistant for ride analysis and recommendations
- Financial reports and visualizations
- Offline-capable PWA with service worker support

**Target Users:** Taxi and rideshare drivers in Poland (Polish language interface)

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Technology Stack:**
- **Framework:** Flask with Jinja2 templating
- **UI Library:** Bootstrap 5.3.0
- **Icons:** Bootstrap Icons 1.11.0
- **Charts/Visualizations:** Plotly 2.27.0
- **PWA Implementation:** Service Worker with offline caching

**Design Pattern:**
- Server-side rendered templates with progressive enhancement
- Mobile-first responsive design with hamburger navigation
- Gradient-based purple/blue theme with modern card layouts
- Offline-first approach using service worker caching

**Key UI Components:**
- Collapsible sidebar navigation with mobile overlay
- Calculator form with real-time validation
- Interactive charts using Plotly for statistics
- PWA manifest for installable app experience

**Rationale:** Server-side rendering provides better SEO and initial load performance, while PWA features enable offline functionality crucial for drivers who may have intermittent connectivity.

### Backend Architecture

**Framework:** Flask 3.1.2 (Python web framework)

**Authentication & Session Management:**
- **Library:** Flask-Login for user session management
- **Password Security:** Werkzeug's password hashing (PBKDF2-based)
- **Form Validation:** Flask-WTF with WTForms validators
- **Session Storage:** Server-side sessions with secure secret key (32+ characters required)

**Security Measures:**
- CSRF protection via Flask-WTF
- Safe URL redirect validation to prevent open redirects
- Environment-based secret key management
- ProxyFix middleware for proper header handling behind reverse proxies

**Rationale:** Flask-Login provides robust session management out of the box, while WTForms handles validation and CSRF protection, reducing custom security code.

### Data Storage

**Database:** PostgreSQL (via SQLAlchemy ORM)

**ORM Configuration:**
- **Library:** Flask-SQLAlchemy with declarative base
- **Connection Pooling:** Pool size of 10, max overflow 20
- **Connection Management:** Pre-ping enabled, 300s pool recycle, 10s timeout
- **Timezone:** UTC configured at connection level

**Data Models:**
- **User Model:** Email-based authentication with hashed passwords, timestamps
- **File-based Storage:** Per-user text files for ride history (`kursy.txt`) and goals (`cele.txt`)

**Storage Pattern:**
- User data stored in `user_data/{user_id}/` directories
- Ride records in structured text format with timestamps
- Daily summaries calculated and appended to history

**Rationale:** Hybrid approach using PostgreSQL for user authentication (ACID compliance for critical data) and file-based storage for ride history (simpler parsing, easier backup). This may need migration to full database storage for better querying and reporting capabilities.

**Limitation:** Current file-based ride storage limits advanced querying and concurrent access. Migration to database tables recommended for production scale.

### Application Structure

**Entry Points:**
- `main.py` - Application launcher
- `app.py` - Main Flask application with route definitions
- `database.py` - Database models and initialization
- `forms.py` - WTForms form definitions

**User Flow:**
1. Registration/Login (email + password)
2. User-specific data directory creation on registration
3. Calculator input → profitability calculation → storage
4. Statistics/reports generated from historical data
5. Platform comparison and AI insights

**Calculation Logic:**
- Fuel cost based on distance and consumption
- Net profit = (Ride amount × Driver percentage) - Fuel cost
- Hourly rate = Net profit / Total time (approach + ride)
- Profitability ratings based on hourly thresholds

## External Dependencies

### Third-Party Services

**Analytics & Tracking:**
- **Google Analytics (GA4):** Tag ID `G-YREKGGTGVE` for user behavior tracking
- **Iubenda:** Cookie consent management (Site ID: 4275582, Policy ID: 77417804)

**Content Delivery:**
- **Bootstrap CDN:** UI framework and icons delivery
- **Plotly CDN:** Chart library for data visualization

### Cloud Infrastructure

**Database:**
- PostgreSQL database (connection via `DATABASE_URL` environment variable)
- Driver: `psycopg2-binary` for PostgreSQL connectivity

**Deployment Hints:**
- Koyeb platform mentioned in manifest (start_url reference)
- ProxyFix configured for reverse proxy deployment
- Gunicorn listed as WSGI server for production

### Python Dependencies

**Core Framework:**
- `flask>=3.1.2` - Web framework
- `flask-sqlalchemy` - ORM integration
- `flask-login` - User session management
- `flask-wtf` - Form handling and CSRF protection

**Security & Validation:**
- `werkzeug` - Password hashing utilities
- `email-validator` - Email format validation
- `wtforms` - Form field validators

**Utilities:**
- `plotly>=6.3.1` - Data visualization
- `requests` - HTTP client (likely for external API calls)
- `pillow` - Image processing (likely for icon generation)

**Production Server:**
- `gunicorn` - WSGI HTTP server

### Environment Variables Required

- `SESSION_SECRET` - Flask session encryption key (minimum 32 characters)
- `DATABASE_URL` - PostgreSQL connection string

### PWA Configuration

**Manifest:** `/static/manifest.json`
- App installable as standalone application
- Theme color: `#667eea` (purple)
- 512x512 icon with maskable support
- Polish language (pl) primary
- Categories: productivity, finance, business

**Service Worker:** Offline caching strategy with runtime and precache
- Cache name versioning: `taxi-calculator-offline-v3`
- Precached assets: static files, icons, manifest
- Network-first strategy with fallback to cache