span

---

**Source Code**: <a href="https://github.com/yashhere/fastapi-htmx-starter" target="_blank">https://github.com/yashhere/fastapi-htmx-starter</a>

---

# 🚀 FastAPI + HTMX Starter Template

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)
![HTMX](https://img.shields.io/badge/HTMX-Enabled-orange.svg)
![License](https://img.shields.io/badge/License-MIT-blue.svg)

*A modern, production-ready starter template for building dynamic web applications with FastAPI, HTMX, and TailwindCSS.*

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## 🌟 Why Choose This Template?

This starter template combines the **speed of FastAPI** with the **simplicity of HTMX** to create modern web applications without the complexity of heavyweight JavaScript frameworks. Unlike traditional SPA approaches, this template offers:

- **🎯 Zero JavaScript fatigue** - Build dynamic UIs with simple HTML attributes
- **⚡ Blazing fast performance** - Server-side rendering with minimal client-side overhead
- **🔧 Full-stack TypeScript alternative** - Python everywhere with excellent type safety
- **📱 Progressive enhancement** - Works without JavaScript, enhanced with it
- **🎨 Modern UI/UX** - TailwindCSS for rapid, responsive design
- **🔐 Enterprise-ready auth** - Complete authentication system out of the box

## ✨ Features

### 🎯 **Core Technologies**

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern, fast web framework with automatic API documentation
- **[HTMX](https://htmx.org/)** - High power tools for HTML - create dynamic UIs with simple attributes
- **[TailwindCSS](https://tailwindcss.com/)** - Utility-first CSS framework for rapid UI development
- **[SQLAlchemy 2.0](https://docs.sqlalchemy.org/)** - Modern async ORM with full type support
- **[Alembic](https://alembic.sqlalchemy.org/)** - Lightweight database migration tool

### 🔐 **Authentication & Security**

- Complete user management system with **[fastapi-users](https://fastapi-users.github.io/fastapi-users/)**
- Cookie-based authentication with JWT tokens
- User registration, login, logout, and profile management
- Protected routes and role-based access control
- Secure password hashing with industry standards

### 🎨 **Frontend Experience**

- **Dynamic interactions** without writing JavaScript
- **Real-time updates** with HTMX partial page swaps
- **Responsive design** with TailwindCSS utilities
- **Loading states** and error handling built-in
- **SEO-friendly** server-side rendering

### 🛠️ **Developer Experience**

- **Modern Python** (3.12+) with full type annotations
- **Code quality tools** - Black, Ruff, MyPy pre-configured
- **Testing suite** with Pytest and async support
- **Database migrations** with Alembic
- **CLI commands** for common development tasks
- **Hot reload** development server

### 📦 **Production Ready**

- **Environment configuration** with Pydantic Settings
- **Database abstraction** - easily switch between SQLite, PostgreSQL, etc.
- **Error handling** with custom exception handlers
- **Gzip compression** middleware
- **Docker ready** deployment setup

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** (recommended) or pip for package management

### 1. 📁 Create Your Project

```bash
# Clone the template
git clone <your-template-repo-url> my-awesome-app
cd my-awesome-app

# Remove git history to start fresh
rm -rf .git
git init
```

### 2. 🔧 Environment Setup

```bash
# Create and activate virtual environment with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install all dependencies
uv pip install -e .
```

### 3. ⚙️ Configuration

```bash
# Create environment file
cp .env.example .env

# Generate a secure secret key and add to .env
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" >> .env

# Edit .env file with your settings
# DATABASE_URL, EMAIL_CONFIG, etc.
```

### 4. 🗄️ Database Setup

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations to create tables
alembic upgrade head
```

### 5. 🎉 Launch Your App

```bash
# Start development server
uv run serve
# or
python -m app.cli serve

# Your app is now running at http://localhost:8000
```

**🎊 That's it! Your modern web application is ready!**

## 📁 Project Structure

```
fastapi-htmx-starter/
├── 📁 app/
│   ├── 📁 api/              # API route handlers
│   │   ├── auth.py          # Authentication routes
│   │   ├── items.py         # CRUD example routes
│   │   ├── user.py          # User management routes
│   │   └── dependencies.py  # Shared dependencies
│   ├── 📁 core/             # Core application logic
│   │   ├── config.py        # Settings and configuration
│   │   ├── database.py      # Database connection and setup
│   │   ├── templates.py     # Jinja2 template configuration
│   │   └── users.py         # User authentication logic
│   ├── 📁 models/           # SQLAlchemy models
│   │   ├── user.py          # User model
│   │   └── item.py          # Example item model
│   ├── 📁 schemas/          # Pydantic schemas
│   │   ├── user.py          # User validation schemas
│   │   └── item.py          # Item validation schemas
│   ├── 📁 services/         # Business logic layer
│   ├── 📁 static/           # Static assets (CSS, JS, images)
│   ├── 📁 templates/        # Jinja2 HTML templates
│   │   ├── base.jinja2      # Base template
│   │   ├── index.jinja2     # Homepage
│   │   ├── 📁 auth/         # Authentication templates
│   │   ├── 📁 items/        # CRUD example templates
│   │   └── 📁 partials/     # HTMX partial templates
│   ├── 📁 tests/            # Test suite
│   ├── cli.py               # CLI commands
│   └── main.py              # FastAPI application
├── 📁 alembic/              # Database migrations
├── 📄 pyproject.toml        # Project configuration
├── 📄 alembic.ini           # Alembic configuration
├── 📄 .env.example          # Environment template
└── 📄 README.md             # This file
```

## 🎯 What's Included

### 🔐 Complete Authentication System

```python
# User registration with validation
POST /auth/register

# Login/logout with cookie sessions
POST /auth/cookie/login
POST /auth/cookie/logout

# User profile management
GET /users/me
PATCH /users/me
```

### 📝 CRUD Example (Items)

- ✅ Create, read, update, delete operations
- 🔍 Search and pagination
- ✏️ Inline editing with HTMX
- 🔄 Real-time updates without page refresh

### 🎨 Modern Frontend Stack

- **HTMX Interactions**: Dynamic forms, live search, partial updates
- **TailwindCSS Styling**: Responsive, mobile-first design
- **Jinja2 Templates**: Server-side rendering with template inheritance
- **Progressive Enhancement**: Works without JS, better with it

## 🛠️ Development Commands

```bash
# 🚀 Development server with hot reload
uv run serve

# 🧪 Run test suite
uv run test

# 📝 Code formatting
uv run format

# 🔍 Code linting
uv run lint

# 🔬 Type checking
uv run check-types
```

## 🗄️ Database Management

```bash
# Create new migration after model changes
alembic revision --autogenerate -m "Add new feature"

# Apply pending migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history
```

## 🧪 Testing

Comprehensive testing setup with async support:

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest app/tests/test_main.py -v

# Run tests with detailed coverage report
pytest --cov=app --cov-report=html
```

## 🎨 Customization Guide

### 🔧 Adding New Features

1. **Create a new model**:

   ```python
   # app/models/post.py
   class Post(Base):
       __tablename__ = "posts"
       id: Mapped[int] = mapped_column(primary_key=True)
       title: Mapped[str] = mapped_column(String(100))
   ```
2. **Add API routes**:

   ```python
   # app/api/posts.py
   @router.get("/posts")
   async def get_posts():
       # Your logic here
   ```
3. **Create templates**:

   ```html
   <!-- app/templates/posts/list.jinja2 -->
   <div hx-get="/posts" hx-trigger="load">
     <!-- Dynamic content -->
   </div>
   ```

### 🎨 Styling with TailwindCSS

```html
<!-- Beautiful, responsive components -->
<button class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
  Click me
</button>
```

### ⚡ HTMX Magic

```html
<!-- Live search without JavaScript -->
<input hx-get="/search" hx-trigger="keyup changed delay:300ms"
       hx-target="#results" placeholder="Search...">
<div id="results"></div>
```

## 🚀 Deployment

### 🔧 Environment Variables

**Required for production:**

```bash
SECRET_KEY=your-super-secure-secret-key-here
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
DEBUG=false
```

### 🐳 Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

# Install uv and dependencies
RUN pip install uv && uv pip install --system -e .

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

### ☁️ Platform Deployment

This template works great with:

- **Railway** - Zero-config deployments
- **Render** - Automatic deployments from git
- **Heroku** - Classic platform-as-a-service
- **DigitalOcean App Platform** - Managed container deployments
- **AWS/GCP/Azure** - Full cloud deployments

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **🐛 Report bugs** - Open an issue with details
2. **💡 Suggest features** - Share your ideas
3. **📝 Improve docs** - Help others learn
4. **🔧 Submit PRs** - Fix bugs or add features

### Development Setup

```bash
git clone <repo-url>
cd fastapi-htmx-starter
uv venv && source .venv/bin/activate
uv pip install -e .
pytest  # Make sure tests pass
```

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support & Community

- **🐛 Issues**: [GitHub Issues](https://github.com/yashhere/fastapi-htmx-starter/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/yashhere/fastapi-htmx-starter/discussions)
- **📧 Email**: hello@yashagarwal.in

---

<div align="center">

**⭐ If this template helped you, please consider giving it a star! ⭐**

Made with ❤️ by [Yash Agarwal](https://yashagarwal.in)

</div>
