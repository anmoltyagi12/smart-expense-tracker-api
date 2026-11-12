
# Smart Expense Tracker API

A backend REST API built with FastAPI and SQLAlchemy to manage personal income, expenses, categories, budgets, and monthly financial analytics. It also integrates Google Gemini AI to generate monthly spending insights.

## Features

- User registration and JWT authentication
- Secure password hashing
- Create, read, update, and delete transactions
- Income and expense categorization
- Custom and default categories
- Monthly budget management
- Monthly financial summaries
- Budget utilization and threshold monitoring
- Search, filter, sort, and paginate transactions
- Top 5 expense analysis
- AI-powered monthly spending insights
- Cached AI insights stored in the database
- Input validation using Pydantic

## Tech Stack

- Python 3.11
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic v2
- JWT Authentication
- Google Gemini API
- Google GenAI SDK
- Uvicorn

## Project Structure

```text
Expense-tracker/
│
├── app/
│   ├── models/
│   ├── routes/
│   ├── schemas/
│   ├── services/
│   ├── config.py
│   ├── database.py
│   └── main.py
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── seed_categories.py
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd Expense-tracker
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root using `.env.example` as a template.

```env
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.8-flash
```

Never commit your actual `.env` file or API key.

### 5. Run the application

```bash
uvicorn app.main:app --reload
```

The API will be available at:

http://127.0.0.1:8000

Interactive Swagger documentation:

http://127.0.0.1:8000/docs

## Database

The project uses SQLite with SQLAlchemy ORM.

The database file is created automatically when the application starts.

Transaction amounts are stored as integer paise.

Example:

- ₹100 = 10000 paise
- ₹500 = 50000 paise
- ₹1000 = 100000 paise


## API Endpoints

All protected endpoints require a JWT Bearer token.

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login and obtain access token |
| GET | `/users/me` | Get current user profile |

### Transactions
| Method | Endpoint | Description |
|---|---|---|
| POST | `/transactions/` | Create transaction |
| GET | `/transactions/` | List transactions |
| GET | `/transactions/search` | Search and filter transactions |
| GET | `/transactions/{transaction_id}` | Get transaction details |
| PUT | `/transactions/{transaction_id}` | Update transaction |
| DELETE | `/transactions/{transaction_id}` | Delete transaction |

### Categories
| Method | Endpoint | Description |
|---|---|---|
| POST | `/categories/` | Create category |
| GET | `/categories/` | List categories |
| PUT | `/categories/{category_id}` | Update category |
| DELETE | `/categories/{category_id}` | Delete category |

### Budgets
| Method | Endpoint | Description |
|---|---|---|
| POST | `/budgets/` | Create budget |
| GET | `/budgets/` | List budgets |
| GET | `/budgets/{budget_id}` | Get budget details |
| PUT | `/budgets/{budget_id}` | Update budget |
| DELETE | `/budgets/{budget_id}` | Delete budget |

### Analytics
| Method | Endpoint | Description |
|---|---|---|
| GET | `/analytics/monthly-summary` | Monthly income, expenses, savings and budget utilization |
| GET | `/analytics/top-expenses` | Get top 5 expenses within a date range |

### AI Insights
| Method | Endpoint | Description |
|---|---|---|
| GET | `/ai-insights/monthly` | Generate or retrieve cached monthly AI spending insights |

### System
| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/` | API welcome/root endpoint |

## AI Integration

The project uses Google's Gemini API to generate monthly spending insights.

### How it works

1. The API retrieves the authenticated user's monthly financial records.
2. It calculates total income, total expenses, net savings, and category-wise spending.
3. Only aggregated financial figures and category names are sent to Gemini.
4. Gemini generates a structured JSON response.
5. Pydantic validates the generated response.
6. Validated insights are stored in the database.
7. Subsequent requests return cached insights unless `force_refresh=true`.

AI suggestions do not modify existing transactions.

### Prompt Design

The AI system prompt is maintained separately in:

`app/services/ai_prompt.py`

The prompt instructs the model to:

- Analyze only supplied financial figures.
- Identify meaningful spending patterns.
- Provide practical saving suggestions.
- Avoid inventing financial information.
- Avoid judgmental language.
- Avoid recommending risky financial products.
- Return output matching the defined response schema.

### AI Input Example

```json
{
  "month": 11,
  "year": 2026,
  "currency": "INR",
  "total_income": 30000.00,
  "total_expenses": 18000.00,
  "net_savings": 12000.00,
  "category_spending": [
    {
      "category": "Food",
      "amount": 8000.00
    },
    {
      "category": "Travel",
      "amount": 6000.00
    },
    {
      "category": "Shopping",
      "amount": 4000.00
    }
  ]
}
```

### AI Output Example 1

```json
{
  "monthly_summary": "Your monthly expenses were INR 18000 against an income of INR 30000, leaving savings of INR 12000.",
  "spending_observations": [
    "Food represents the largest spending category.",
    "Travel is another significant expense."
  ],
  "saving_suggestions": [
    "Review food purchases and plan meals in advance.",
    "Set a monthly travel spending limit."
  ],
  "risk_level": "moderate"
}
```

### AI Output Example 2

```json
{
  "monthly_summary": "Your expenses are relatively low compared with your monthly income, resulting in positive savings.",
  "spending_observations": [
    "Your spending is distributed across the tracked categories.",
    "You have retained a portion of your income as savings."
  ],
  "saving_suggestions": [
    "Continue monitoring category-wise expenses.",
    "Maintain a monthly savings target."
  ],
  "risk_level": "low"
}
```

### AI Output Example 3

```json
{
  "monthly_summary": "Your expenses are higher than your monthly income, indicating a need to review spending.",
  "spending_observations": [
    "Monthly expenses exceed available income.",
    "Spending should be reviewed before the next month."
  ],
  "saving_suggestions": [
    "Prioritize essential expenses.",
    "Reduce discretionary purchases.",
    "Set category-wise spending limits."
  ],
  "risk_level": "high"
}
```

*Note: These are illustrative examples of the expected output format, not actual Gemini responses.*

## Error Handling and Validation

- Invalid amounts are rejected.
- Invalid transaction types are rejected.
- Future transaction dates are rejected.
- Invalid category ownership or type is rejected.
- Date range errors return HTTP 400.
- Missing or invalid authentication returns appropriate HTTP errors.
- Gemini service failures return HTTP 503.
- AI output is validated before being stored.
- AI failures do not modify existing transactions.

## Security

- Passwords are hashed before storage.
- JWT authentication protects private endpoints.
- User-specific records are filtered by authenticated user ID.
- Environment variables are used for secrets and API keys.
- Sensitive user information is not sent to the AI service.

## Future Improvements

- Automated test coverage
- CSV transaction export
- Recurring transactions
- Database migrations
- Docker deployment
- Improved AI retry and fallback handling

## License

This project is developed for educational and portfolio purposes.
