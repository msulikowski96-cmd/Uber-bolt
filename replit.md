# Taxi Calculator - Ride Profitability Tracker

## Overview

Taxi Calculator is a Progressive Web Application (PWA) designed for taxi drivers to track and analyze ride profitability. The application features multi-user authentication with email/password login, allowing each driver to have their own private data. Drivers can calculate hourly rates for rides, set daily earning goals, track progress, compare platform performance (Uber, Bolt, etc.), and view detailed statistics through interactive charts. Built with Flask and designed for mobile-first usage, it provides offline capabilities and can be installed on devices as a native-like app.

## Recent Changes (October 2025)

- **Added user authentication system** - Email/password login with secure password hashing
- **Multi-user support** - Each user has separate data files (kursy.txt and cele.txt) stored in user_data/{user_id}/
- **Platform comparison feature** - Track and compare profitability across different taxi platforms (Uber, Bolt, FreeNow, etc.)
- **Database integration** - SQLite database for user management
- **Enhanced security** - Flask-Login for session management, bcrypt for password hashing

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Technology Stack:** Vanilla JavaScript with Bootstrap 5 for UI components and Plotly.js for data visualization.

**Design Pattern:** Multi-page application (MPA) with server-side rendering. The application uses Flask's template engine (Jinja2) to render three main pages: calculator (index.html), statistics (statystyki.html), and platform comparison (platformy.html).

**Rationale:** Chose MPA over SPA to keep the application simple and lightweight. Server-side rendering provides faster initial page loads, which is crucial for mobile users with potentially slower connections. Bootstrap provides a responsive, mobile-first framework out of the box.

**PWA Implementation:** Progressive Web App features implemented via service worker (service-worker.js) using Workbox for caching strategies:
- StaleWhileRevalidate for dynamic content
- CacheFirst for images with 30-day expiration
- Separate caches for fonts and static resources

**Pros:** Fast offline access, installable on mobile devices, reduced server load through aggressive caching.
**Cons:** Cache invalidation complexity, requires HTTPS in production.

### Backend Architecture

**Framework:** Flask (Python) - Lightweight WSGI web application framework.

**Architecture Pattern:** Hybrid approach - SQLite database for user authentication and file-based storage for ride data. Flask-Login manages user sessions securely.

**Key Components:**
1. **app.py** - Main Flask application with route handlers, authentication, and API endpoints
2. **database.py** - User model and database management (SQLite)
3. **forms.py** - WTForms for login and registration validation
4. **Database Storage (SQLite):**
   - `taxi_calculator.db` - Stores user accounts (email, hashed passwords)
5. **File Storage (per user):**
   - `user_data/{user_id}/kursy.txt` - Stores ride records with timestamp, distance, time, earnings, hourly rate, and platform
   - `user_data/{user_id}/cele.txt` - Stores user goals (daily target, minimum acceptable rate)

**Authentication:**
- **Flask-Login** - Session management and user authentication
- **Flask-WTF** - Form validation with CSRF protection
- **Bcrypt** - Secure password hashing (via werkzeug.security)
- **Email validation** - Ensures valid email addresses during registration

**Rationale:** Hybrid approach combines the best of both worlds - database for structured user data that requires querying (authentication) and file-based storage for sequential ride records that are simple to parse and backup. Each user has isolated data folders ensuring privacy and data separation.

**Pros:** 
- Zero setup overhead
- Portable (files can be backed up/transferred easily)
- No database maintenance required
- Lightweight deployment

**Cons:**
- Limited concurrent user support
- No relational queries
- Manual parsing required for analytics
- File corruption risk without proper locking

### Data Storage Solutions

**Primary Storage:** Text file-based persistence with structured format.

**Data Models:**

1. **Ride Records (kursy.txt):**
   ```
   [YYYY-MM-DD HH:MM:SS]
   key: value
   ----------------------------------------
   ```
   Includes: timestamp, pickup distance/time, ride distance/time, fare, fuel cost, profit, hourly rate, platform

2. **User Goals (cele.txt):**
   ```
   cel_dzienny:450
   min_stawka:30
   ```

**Data Processing:** 
- Sequential file reading for analytics
- In-memory aggregation for statistics
- Daily summaries appended to kursy.txt with automatic recalculation

**Rationale:** Append-only log format for ride records ensures data integrity and provides audit trail. Simple key-value format for goals allows easy updates.

### State Management

**Session Storage:** Flask server-side sessions with secret key for security. Used for temporary user preferences like theme selection (dark/light mode).

**Client-Side State:** Minimal - form values and theme preference stored in browser localStorage for PWA offline functionality.

### API Structure

**RESTful Endpoints (JSON APIs):**

1. `POST /oblicz` - Calculate ride profitability, returns JSON with results and saves to file
2. `GET /cele` - Retrieve user goals and daily progress
3. `POST /cele` - Update user goals
4. `GET /statystyki` - Render statistics page (server-side)
5. `GET /platformy` - Render platform comparison page (server-side)
6. `GET /api/statystyki` - Fetch statistics data as JSON for charts
7. `GET /api/platformy` - Fetch platform comparison data as JSON

**Data Flow:**
1. User submits ride details via form
2. Flask calculates profitability metrics (hourly rate, profit margin)
3. Data saved to kursy.txt with timestamp
4. Daily progress recalculated against goals
5. Response sent to client for immediate display

### Analytics & Visualization

**Charting Library:** Plotly.js for interactive, responsive charts.

**Chart Types:**
- Line charts for hourly rate trends over time
- Bar charts for platform comparison
- Progress indicators for daily goals

**Data Aggregation:** Server-side parsing of kursy.txt to generate:
- Daily averages
- Platform-wise statistics (average rate, total earnings, ride count)
- Time-based analysis (best hours for earnings)

## External Dependencies

### Third-Party Libraries

1. **Flask (>=3.1.2)** - Web framework for Python
   - Purpose: HTTP routing, template rendering, session management
   - Used for: All backend logic and API endpoints

2. **Plotly (>=6.3.1)** - Interactive graphing library
   - Purpose: Data visualization
   - Used for: Statistics charts and platform comparison graphs

3. **Bootstrap 5.3.0** - CSS framework (CDN)
   - Purpose: Responsive UI components
   - Used for: Layout, forms, modals, cards, buttons

4. **Bootstrap Icons 1.11.0** - Icon library (CDN)
   - Purpose: UI icons
   - Used for: Navigation icons, status indicators

5. **Workbox 5.1.2** - Service worker library (CDN)
   - Purpose: PWA caching strategies
   - Used for: Offline functionality, cache management

### External Services

**CDN Resources:**
- Bootstrap CSS/JS from cdn.jsdelivr.net
- Bootstrap Icons from cdn.jsdelivr.net  
- Plotly.js from cdn.plot.ly
- Workbox from storage.googleapis.com

**Rationale:** CDN usage reduces bundle size and leverages browser caching across sites. However, creates dependency on external availability.

**Offline Strategy:** Service worker caches CDN resources on first load, enabling offline functionality after initial visit.

### PWA Configuration

**Manifest (manifest.json):**
- App name: "Taxi Calculator - Kalkulator Opłacalności"
- Display mode: Standalone (full-screen app experience)
- Theme color: #667eea (purple gradient)
- Icons: 512x512 maskable icon for various devices
- Categories: Productivity, Finance, Business

**Service Worker Strategy:**
- StaleWhileRevalidate for HTML/API responses (show cached, update in background)
- CacheFirst for static assets (images, fonts)
- Versioned cache names for updates (taxi-calculator-offline-v1)

### Deployment Considerations

**No External Database:** Application is self-contained with file-based storage. Can run on any Python environment with Flask installed.

**No Authentication Service:** No user authentication system. Single-user application model. Could be extended with Flask-Login or OAuth for multi-user scenarios.

**No Cloud Storage:** All data stored locally on server filesystem. Consider adding cloud backup integration (Dropbox, Google Drive) for data persistence.