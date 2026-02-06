# Aguka - Electronics Retail Operations Management System

**Target Price:** 500,000 RWF (Lifetime License)  
**Market:** Smartphone Retail & Spare Parts Repair Shops (Rwanda)  
**Type:** Offline-first Desktop Application

## Overview

Aguka is a localized retail operations management system built specifically for electronics micro-retailers in Rwanda. The system replaces handwritten ledgers with a structured, offline-first digital workflow that manages inventory, agent credit (consignment), staff accountability, financial reporting, and loss prevention.

## Technology Stack

- **Backend:** Django (Python) + Django REST Framework
- **Frontend:** React (TypeScript) + Material UI
- **Database:** SQLite (WAL mode, append-only ledger)
- **Desktop:** Electron wrapper
- **Package Manager:** UV (Python), npm/yarn (Node.js)
- **Packaging:** PyInstaller + electron-builder

## Architecture

```
┌─────────────────────────────────────┐
│      Electron Desktop App           │
│  ┌──────────────────────────────┐   │
│  │   React Frontend (TS)        │   │
│  │   - Owner Dashboard          │   │
│  │   - Cashier Dashboard        │   │
│  │   - POS Interface            │   │
│  └──────────────────────────────┘   │
│              ↓ HTTP                  │
│  ┌──────────────────────────────┐   │
│  │   Django Backend (subprocess)│   │
│  │   - REST API                 │   │
│  │   - SQLite Database          │   │
│  │   - Append-only Ledger       │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

## Project Structure

```
EROM_system/
├── backend/                 # Django backend
│   ├── apps/               # Django apps
│   │   ├── core/          # Base models, utilities
│   │   ├── inventory/     # Product & stock management
│   │   ├── agents/        # Agent ledger & consignment
│   │   ├── sales/         # POS & transactions
│   │   ├── reports/       # Report generation
│   │   ├── licensing/     # License management
│   │   └── audit/         # Audit logging
│   ├── config/            # Django settings
│   ├── manage.py
│   └── requirements.txt
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # Reusable components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API client
│   │   ├── store/         # State management
│   │   └── types/         # TypeScript types
│   ├── public/
│   └── package.json
├── electron/              # Electron wrapper
│   ├── main.js           # Main process
│   ├── preload.js        # Preload script
│   └── package.json
├── scripts/              # Build & deployment scripts
└── docs/                 # Documentation
```

## Core Features (Phase 1)

### 1. Licensing & Activation
- Shop registration with unique license key
- Device fingerprinting
- Offline license validation
- License recovery workflow

### 2. Role-Based Access Control
- **Owner:** Full access, reports, backups, settings, approvals
- **Cashier/Manager:** Daily operations, inventory, sales, agents

### 3. Inventory Management
- Product CRUD with categories
- Stock tracking (purchase/sale)
- Fast search & filters
- Low-stock alerts
- Preloaded smartphone parts catalog

### 4. Agent Ledger (Consignment Tracking)
- Agent profiles with credit limits
- Stock transfer to field technicians
- Debt aging (7/30/60/90 days)
- Repayment logging
- Outstanding balance tracking

### 5. Point of Sale
- Fast cashier workflow
- Touch-friendly interface
- Automatic inventory deduction
- Receipt generation

### 6. Blind Count Reconciliation
- Physical vs system stock comparison
- Discrepancy flagging
- Correction workflow with owner approval
- No destructive edits

### 7. Reporting & Export
- Daily sales summary
- Inventory valuation
- Agent debt reports
- Discrepancy logs
- CSV export
- PDF receipts

### 8. Backup & Recovery
- Encrypted local backups (AES-256)
- USB export
- Restore wizard
- Automatic daily backups

### 9. Audit Trail
- Immutable audit log
- All actions tracked (user, timestamp, before/after)
- Correction/reversal tracking

## Development Setup

### Prerequisites
- Python 3.9+
- UV (Python package manager)
- Node.js 16+
- npm or yarn
- Git

### Install UV
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or on Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Backend Setup
```bash
cd backend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

### Electron Setup
```bash
cd electron
npm install
npm run dev
```

## Build & Package

### Development Build
```bash
npm run build:dev
```

### Production Build
```bash
npm run build:prod
```

### Create Installer
```bash
npm run package:win  # Windows installer
```

## Database Schema

### Core Tables (Append-Only Ledger)
- `transactions` - All financial transactions
- `inventory_movements` - Stock changes
- `agent_ledger` - Consignment tracking
- `audit_log` - Complete audit trail

### Master Data
- `products` - Product catalog
- `agents` - Field technician profiles
- `users` - Owner and cashier accounts
- `shop_config` - License and shop settings

## Security Features

- AES-256-GCM encrypted backups
- Argon2 password hashing
- Role-based permissions
- Audit trail for all mutations
- Device fingerprinting
- Offline license validation

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

## Deployment Timeline

- **Weeks 1-2:** Project setup & database schema
- **Weeks 3-4:** Inventory module
- **Weeks 5-6:** Agent ledger
- **Week 7:** Reconciliation
- **Week 8:** Reporting
- **Week 9:** Role management
- **Week 10:** Licensing
- **Week 11:** Backup/recovery
- **Week 12:** Electron packaging
- **Week 13:** QA & testing

## Support

For technical support or issues, contact: [Support details to be added]

## License

Proprietary - © 2026 Aguka EROM System. All rights reserved.
