# OK Entrega Consulta

Consulta de OS e download de XML/PDF do OK Entrega, com React/Vite no Netlify e FastAPI no Render.

## Ambiente local

1. Copie `.env.example` para `backend/.env` e defina as variáveis.
2. No diretório `backend`, execute `python -m venv .venv`, ative o ambiente e `pip install -r requirements.txt`.
3. No diretório `frontend`, execute `npm install` e crie `frontend/.env` com `VITE_API_URL=http://localhost:8000`.
4. Inicie a API com `uvicorn app.main:app --reload` no diretório `backend` e o frontend com `npm run dev` no diretório `frontend`.

## Supabase

Execute a migration em `supabase/migrations/20260911_create_consultations.sql` no SQL Editor. As credenciais do OK Entrega ficam somente nas variáveis do Render: `OKENTREGA_EMAIL` e `OKENTREGA_PASSWORD`.

## Publicação

- Netlify: conecte o repositório; a configuração em `netlify.toml` usa `frontend`, `npm run build` e `dist`. Configure `VITE_API_URL` com a URL HTTPS do Render.
- Render: crie o Web Service pelo `render.yaml`. Defina `OKENTREGA_EMAIL`, `OKENTREGA_PASSWORD` e `ALLOWED_ORIGINS` com a URL exata do Netlify.
