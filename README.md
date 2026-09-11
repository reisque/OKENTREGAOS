# OK Entrega Consulta

Consulta anual de OS e download individual de XML do OK Entrega, com React/Vite no Netlify e FastAPI no Render.

## Ambiente local

1. Copie `.env.example` para `backend/.env` e defina as variáveis.
2. No diretório `backend`, execute `python -m venv .venv`, ative o ambiente e `pip install -r requirements.txt`.
3. No diretório `frontend`, execute `npm install` e crie `frontend/.env` com `VITE_API_URL=http://localhost:8000`.
4. Inicie a API com `uvicorn app.main:app --reload` no diretório `backend` e o frontend com `npm run dev` no diretório `frontend`.

## Supabase

Execute a migration em `supabase/migrations/20260911_create_consultations.sql` no SQL Editor. A primeira abertura busca as OS do ano corrente e salva os dados no Supabase. Nas aberturas seguintes, o site carrega a última consulta salva no banco, sem consultar o portal novamente. Uma nova consulta anual só acontece pelo botão de atualização ou quando completar uma hora desde a última consulta; nesse caso, as OS novas ou alteradas são gravadas por upsert. A pesquisa é feita sobre os resultados sincronizados no navegador, sem custo adicional de serviço.

O site sincroniza automaticamente uma hora depois da última consulta concluída (manual ou automática). A data e a hora da última consulta ficam visíveis no topo. Os XMLs são baixados somente de forma individual para evitar travamentos no navegador.

## Publicação

- Netlify: conecte o repositório; a configuração em `netlify.toml` usa `frontend`, `npm run build` e `dist`. Configure `VITE_API_URL` com a URL HTTPS do Render.
- Render: crie o Web Service pelo `render.yaml`. Defina `OKENTREGA_EMAIL`, `OKENTREGA_PASSWORD` e `ALLOWED_ORIGINS` com a URL exata do Netlify.
