# nova

Monorepo containing:

- **frontend/** → Angular application  
- **backend/** → FastAPI application  

## Running

### Frontend
```bash
cd frontend/webapp
ng serve
```

### Backend
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```
