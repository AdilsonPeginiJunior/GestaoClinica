# Gestão Clínica — Protótipo Web

Sistema web de demonstração para clínica de psicologia: agenda, cadastros, faturamento e **repasse por psicólogo**. Destinado a apresentação ao cliente antes da versão de produção.

> **Aviso:** dados fictícios. Não utilizar com informações reais de pacientes sem adequação LGPD.

---

## Status atual

| Item | Situação |
|------|----------|
| **Versão** | 0.1.1-prototype |
| **Última atualização** | 2026-06-09 |
| Login e perfis (RBAC) | Funcional (demo) |
| Cadastro de pacientes / psicólogos | Funcional (demo) |
| Agenda e status de consulta | Funcional (demo) |
| Financeiro automático ao marcar *realizado* | Funcional (demo) |
| Relatório por psicólogo | Funcional (demo) |
| Prontuário eletrônico | Não iniciado |
| WhatsApp / exportação PDF | Planejado |
| Endpoint `/health` | Funcional (demo) |
| Teste automatizado recepção | `backend/test_recepcao.py` |
| Produção (PostgreSQL, VPS) | Planejado |

---

## Stack

### Protótipo (este repositório)

| Camada | Tecnologia |
|--------|------------|
| Backend | Python 3.11+, **FastAPI**, SQLAlchemy, Pydantic |
| Banco demo | **SQLite** (`backend/gestao_clinica.db`) |
| Auth | JWT + bcrypt |
| Frontend | **React 19**, TypeScript, **Vite**, React Router, Axios |
| Estilo | CSS customizado (tema clínica) |

### Produção (evolução planejada)

| Camada | Tecnologia |
|--------|------------|
| Banco | PostgreSQL 16 + Alembic |
| Servidor | Uvicorn/Gunicorn + Nginx + Let's Encrypt |
| DNS/CDN | Cloudflare |
| E-mail | Provedor transacional (recuperação de senha, lembretes) |
| Backup | Script + storage na VPS |
| CI/CD | GitHub Actions (opcional) |

**Linguagens:** Python, TypeScript, SQL, HTML/CSS, JSON, Markdown.

---

## Como rodar localmente

### Atalho (Windows)

Terminal 1 — backend:

```powershell
.\scripts\iniciar-backend.ps1
```

Terminal 2 — frontend:

```powershell
.\scripts\iniciar-frontend.ps1
```

**Se o login ficar em "Entrando…"** sem sair: a API provavelmente travou. Feche processos Python na porta 8000 e reinicie o backend:

```powershell
netstat -ano | findstr ":8000"
# encerre o PID listado, depois:
.\scripts\iniciar-backend.ps1
```

Teste rapido da API: http://localhost:8000/health

Se o frontend falhar com erro de `rolldown`/`binding`, reinstale:

```powershell
cd frontend
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

### 1. Backend (API)

```powershell
cd C:\Users\Junior\Desktop\PYTHON\GestaoClinica\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- API: http://localhost:8000  
- Documentação Swagger: http://localhost:8000/docs  
- Na primeira execução o banco é criado e populado com dados de demonstração.

### 2. Frontend

Em outro terminal:

```powershell
cd C:\Users\Junior\Desktop\PYTHON\GestaoClinica\frontend
npm install
npm run dev
```

- Interface: http://localhost:5173  

---

## Usuários de demonstração

Senha de todos: **`demo123`**

| Perfil | E-mail | O que demonstrar |
|--------|--------|------------------|
| Recepção | `recepcao@demo.com` | Pacientes, agenda, sem relatórios financeiros |
| Psicólogo | `psicologo@demo.com` | Só a própria agenda e relatório próprio |
| Sócia | `socia@demo.com` | Visão gerencial + relatórios |
| Admin | `admin@demo.com` | Mesmo que sócia (parametrização futura) |

Na tela de login há botões de **acesso rápido** para cada perfil.

---

## Roteiro de apresentação ao cliente (~10 min)

1. Entrar como **recepção** → cadastrar paciente → criar agendamento.
2. Marcar consulta como **realizado** na agenda.
3. Entrar como **sócia** → abrir **Relatórios** → escolher psicólogo e mostrar receita, repasse e saldo da clínica.
4. Entrar como **psicólogo** → mostrar que só vê os próprios dados.
5. Comentar roadmap: prontuário, convênios avançados, WhatsApp, hospedagem em `app.suaclinica.com.br`.

---

## Estrutura do projeto

```
GestaoClinica/
├── README.md                 ← este arquivo (atualizar a cada entrega)
├── backend/
│   ├── app/
│   │   ├── main.py           # entrada FastAPI
│   │   ├── models.py         # entidades ORM
│   │   ├── services.py       # regras (repasse, valores)
│   │   ├── seed.py           # dados demo
│   │   └── routers/          # endpoints REST
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api.ts            # chamadas à API
│       ├── context/          # autenticação
│       ├── pages/            # telas
│       └── components/       # layout
└── docs/                     # escopos originais (.docx)
```

---

## Melhorias já previstas (próximas versões)

- Tabelas de convênio/plano com vigência por data  
- Histórico de alteração de repasse por psicólogo  
- Prontuário com trilha de auditoria  
- Exportação Excel/PDF dos relatórios  
- Variáveis de ambiente (`.env`) para `SECRET_KEY` e URL do banco PostgreSQL  
- Testes automatizados (pytest + Vitest)  

---

## Changelog

### v0.1.1-prototype (2026-06-09)

- Correções no fluxo da recepção (login, agenda, cadastro de pacientes)
- Timeout e mensagens de erro quando a API não responde
- SQLite em modo WAL; CPF duplicado retorna 409 em vez de 500
- Endpoint `/health`, scripts `iniciar-backend.ps1` / `iniciar-frontend.ps1`
- Teste automatizado `backend/test_recepcao.py`

### v0.1.0-prototype (2026-05-16)

- Protótipo navegável com login por perfil  
- CRUD básico de pacientes e listagem de psicólogos  
- Agenda com transição de status e lançamentos financeiros automáticos  
- Dashboard e relatório por psicólogo  
- README com instruções de execução e roteiro de demo  

---

## Documentação de escopo

Os requisitos funcionais completos estão nos arquivos Word na raiz do projeto (`1 web app de gestão clínica.docx`, `2 primeiro escopo funcional completo.docx`).
