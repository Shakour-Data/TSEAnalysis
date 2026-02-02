# Installation Guide

This guide provides detailed instructions for installing and setting up the TSE Analysis System.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (for cloning the repository)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/tse-analysis.git
cd tse-analysis
```

### 2. Create Virtual Environment (Recommended)

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 5. Initialize Database

```bash
python -c "from app.database import init_db; init_db()"
```

### 6. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the port in `app.py` or stop the conflicting service.
2. **Database errors**: Ensure SQLite is properly installed and the database file has write permissions.
3. **Missing dependencies**: Run `pip install -r requirements.txt` again.

### Getting Help

If you encounter issues not covered here, please:
- Check the [Troubleshooting Guide](guides/troubleshooting.md)
- Open an issue on GitHub
- Contact the development team