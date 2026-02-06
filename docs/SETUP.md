# Development Setup Guide - EROM System

## Quick Start with UV

### 1. Install UV (if not already installed)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
uv venv

# Activate environment
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Install dependencies
uv pip install -r requirements.txt

# Create database and run migrations
python manage.py makemigrations
python manage.py migrate

# Create initial shop and owner account
python manage.py setup_shop

# Run development server
python manage.py runserver
```

### 3. Frontend Setup (Coming Next)
```bash
cd frontend
npm install
npm start
```

### 4. Electron Wrapper (Coming Next)
```bash
cd electron
npm install
npm run dev
```

## UV Commands Reference

### Package Management
```bash
# Install package
uv pip install <package>

# Install from requirements.txt
uv pip install -r requirements.txt

# Add package and update requirements.txt
uv pip install <package> && uv pip freeze > requirements.txt

# Uninstall package
uv pip uninstall <package>

# List installed packages
uv pip list

# Show package info
uv pip show <package>
```

### Virtual Environment
```bash
# Create new venv
uv venv

# Create with specific Python version
uv venv --python 3.11

# Remove venv
rm -rf .venv
```

### Running Commands
```bash
# Run Python in the venv
uv run python manage.py runserver

# Run without activating venv
uv run --with django python manage.py migrate
```

## Why UV?

- **Fast**: 10-100x faster than pip
- **Reliable**: Better dependency resolution
- **Compatible**: Drop-in replacement for pip
- **Modern**: Written in Rust, actively maintained

## Development Workflow

### Daily Development
```bash
# Activate environment
source .venv/bin/activate

# Start Django server
python manage.py runserver

# In another terminal: Make migrations when models change
python manage.py makemigrations
python manage.py migrate
```

### Adding New Dependencies
```bash
# Install package
uv pip install package-name

# Update requirements.txt
uv pip freeze > requirements.txt

# Commit changes
git add requirements.txt
git commit -m "Add package-name dependency"
```

### Database Management
```bash
# Create migrations for app
python manage.py makemigrations app_name

# Apply migrations
python manage.py migrate

# Create superuser (Owner account)
python manage.py createsuperuser

# Reset database (CAUTION)
rm db.sqlite3
python manage.py migrate
```

## Next Steps

1. Complete remaining Django models (agents, sales, audit)
2. Run migrations to create database
3. Set up React frontend
4. Build Electron wrapper
5. Test offline functionality

## Troubleshooting

### UV not found
```bash
# Ensure UV is in PATH
export PATH="$HOME/.cargo/bin:$PATH"
```

### Virtual environment issues
```bash
# Remove and recreate
rm -rf .venv
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Django import errors
```bash
# Ensure you're in activated venv
which python  # Should show .venv/bin/python
uv pip install -r requirements.txt
```
