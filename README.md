# 🏥 Vital-Vault

> **Your Personal Health Records, Secured and Intelligent.**

Vital-Vault is a full-stack medical records management platform that lets individuals securely store, search, and understand their health history. It leverages AI-powered document processing to extract structured data from uploaded files (PDFs, images, lab reports) and presents everything through a beautiful, responsive dashboard.

---

## ✨ Features

- **Secure Document Upload** — Upload PDFs, scans, and images of medical records with automatic AI extraction
- **AI-Powered Extraction** — Uses Cerebras AI + OCR (Tesseract / PyMuPDF) to parse lab results, diagnoses, medications, and more from raw documents
- **Interactive Health Timeline** — Visualize your entire medical history on a chronological timeline
- **Medication Tracker** — Track current and past medications with dosage and schedule details
- **Appointment Manager** — Log upcoming and past appointments with doctors and specialists
- **User Authentication** — JWT-based auth with rate limiting and secure password hashing
- **Data Export** — Export your health records as structured data
- **Responsive Dashboard** — Clean, modern Next.js frontend with full mobile support

---

## 🛠️ Tech Stack

### Frontend
| Technology | Purpose |
|---|---|
| [Next.js 14](https://nextjs.org/) | React framework with App Router |
| TypeScript | Type-safe frontend development |
| Tailwind CSS | Utility-first styling |

### Backend
| Technology | Purpose |
|---|---|
| [FastAPI](https://fastapi.tiangolo.com/) | High-performance Python API framework |
| SQLAlchemy (async) | ORM with async PostgreSQL support |
| Alembic | Database migrations |
| Celery + Redis | Background task processing for AI extraction |
| Cerebras AI | LLM for medical document understanding |
| PyMuPDF + Tesseract | PDF parsing and OCR |
| aioboto3 | S3-compatible object storage for file uploads |

### Infrastructure
| Technology | Purpose |
|---|---|
| PostgreSQL | Primary relational database |
| Redis | Message broker + cache |
| Docker + Docker Compose | Containerised local development |

---

## 🚀 Getting Started

### Prerequisites

- [Docker](https://www.docker.com/get-started) & Docker Compose
- [Node.js 18+](https://nodejs.org/)
- A Cerebras API key (for AI extraction)

### 1. Clone the Repository

```bash
git clone https://github.com/AbhinandanSharma007/Vital-Vault.git
cd Vital-Vault
```

### 2. Configure the Backend

```bash
cd backend
cp .env.example .env
```

Edit `.env` and fill in the required values:

```env
# Database
DATABASE_URL=postgresql+asyncpg://vitalvault:password@localhost:5432/vitalvault

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-super-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Cerebras AI
CEREBRAS_API_KEY=your-cerebras-api-key

# S3 / Object Storage
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
S3_BUCKET_NAME=vital-vault
S3_ENDPOINT_URL=http://localhost:9000
```

### 3. Start the Backend (Docker)

```bash
cd backend
docker-compose up --build
```

This starts:
- **FastAPI** on `http://localhost:8000`
- **PostgreSQL** on `localhost:5432`
- **Redis** on `localhost:6379`
- **Celery Worker** for background AI processing
- **Flower** (Celery monitor) on `http://localhost:5555`

### 4. Run Database Migrations

```bash
docker-compose exec api alembic upgrade head
```

### 5. Configure & Start the Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local  # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Frontend runs at `http://localhost:3000`

---

## 📁 Project Structure

```
Vital-Vault/
├── backend/
│   ├── app/
│   │   ├── core/           # Storage, security utilities
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── routers/        # FastAPI route handlers
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # Business logic & AI extraction
│   │   ├── repositories/   # Database access layer
│   │   ├── tasks/          # Celery async tasks
│   │   └── main.py         # Application entry point
│   ├── alembic/            # Database migration scripts
│   ├── docker/             # Docker configs for services
│   ├── requirements.txt    # Python dependencies
│   └── docker-compose.yml
│
└── frontend/
    └── src/
        ├── app/            # Next.js App Router pages
        ├── components/     # Reusable UI components
        └── lib/            # API client & utilities
```

---

## 🔌 API Overview

The REST API is documented via Swagger UI at `http://localhost:8000/docs` once the backend is running.

| Endpoint | Description |
|---|---|
| `POST /api/v1/auth/register` | Create a new user account |
| `POST /api/v1/auth/login` | Obtain JWT access token |
| `GET /api/v1/records` | List all medical records |
| `POST /api/v1/records/upload` | Upload a medical document |
| `GET /api/v1/timeline` | Fetch health timeline events |
| `GET /api/v1/medications` | List medications |
| `GET /api/v1/appointments` | List appointments |

---

## 🔒 Security

- Passwords hashed with **bcrypt** via Passlib
- JWT tokens with configurable expiry
- Rate limiting on all auth endpoints via **SlowAPI**
- Sensitive files (`.env`, secrets) excluded from version control

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "feat: add my feature"`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

<p align="center">Built with ❤️ for better health record management</p>
