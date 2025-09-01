# Wingman Project Makefile
# Usage: make <command>

.PHONY: help start stop redis-start redis-stop redis-status clean test migrate makemigrations shell

# Default target
help:
	@echo "Wingman Project - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  start          - Start Django development server with Redis"
	@echo "  stop           - Stop Django development server"
	@echo "  dev            - Start development environment (Redis + Django)"
	@echo ""
	@echo "Redis Management:"
	@echo "  redis-start    - Start Redis service"
	@echo "  redis-stop     - Stop Redis service"
	@echo "  redis-status   - Check Redis service status"
	@echo "  redis-test     - Test Redis connection"
	@echo "  redis-clear-limits - Clear rate limiting data"
	@echo ""
	@echo "Django Management:"
	@echo "  migrate        - Run database migrations"
	@echo "  makemigrations - Create new migrations"
	@echo "  shell          - Open Django shell"
	@echo "  test           - Run tests"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean          - Clean Python cache files"
	@echo "  install        - Install dependencies"
	@echo "  setup          - Initial project setup"

# Start development environment
dev: redis-start
	@echo "Starting development environment..."
	@echo "Redis: Starting..."
	@sleep 2
	@echo "Django: Starting development server..."
	@echo "Server will be available at: http://127.0.0.1:8000/"
	@echo "Press Ctrl+C to stop"
	@source venv/bin/activate && python manage.py runserver

# Start Django server (assumes Redis is running)
start:
	@echo "Starting Django development server..."
	@echo "Server will be available at: http://127.0.0.1:8000/"
	@echo "Press Ctrl+C to stop"
	@source venv/bin/activate && python manage.py runserver

# Stop Django server (Ctrl+C in terminal)
stop:
	@echo "Django server stopped. Use Ctrl+C in the terminal where it's running."

# Redis management
redis-start:
	@echo "Starting Redis service..."
	@brew services start redis
	@sleep 2
	@echo "Redis started successfully!"

redis-clear-limits:
	@echo "Clearing Redis rate limiting data..."
	@redis-cli -n 1 flushdb 2>/dev/null || echo "Redis not running or not accessible"
	@echo "Rate limits cleared!"

redis-stop:
	@echo "Stopping Redis service..."
	@brew services stop redis
	@echo "Redis stopped successfully!"

redis-status:
	@echo "Redis service status:"
	@brew services list | grep redis || echo "Redis not found"

redis-test:
	@echo "Testing Redis connection..."
	@redis-cli ping || echo "Redis is not running or not accessible"

# Django management
migrate:
	@echo "Running database migrations..."
	@source venv/bin/activate && python manage.py migrate

makemigrations:
	@echo "Creating new migrations..."
	@source venv/bin/activate && python manage.py makemigrations

shell:
	@echo "Opening Django shell..."
	@source venv/bin/activate && python manage.py shell

test:
	@echo "Running tests..."
	@source venv/bin/activate && python manage.py test

# Maintenance
clean:
	@echo "Cleaning Python cache files..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@echo "Clearing Redis rate limiting data..."
	@redis-cli -n 1 flushdb 2>/dev/null || echo "Redis not running or not accessible"
	@echo "Cleanup complete!"

install:
	@echo "Installing dependencies..."
	@source venv/bin/activate && pip install -r requirements.txt

setup: install redis-start migrate
	@echo "Project setup complete!"
	@echo "You can now run 'make dev' to start development"

# Quick development workflow
work: redis-start
	@echo "Development environment ready!"
	@echo "Redis: Running"
	@echo "Run 'make start' to start Django server"
	@echo "Run 'make redis-stop' when done working"

done: redis-stop
	@echo "Development session ended!"
	@echo "Redis stopped - no background services running"
