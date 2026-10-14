# Gestão Clínica — Protótipo Web

Sistema web de demonstração para clínica de psicologia: agenda, cadastros, faturamento e **repasse por psicólogo**. Destinado a apresentação ao cliente antes da versão de produção.

> **Aviso:** dados fictícios. Não utilizar com informações reais de pacientes sem adequação LGPD.

---

## Status atual

| Item | Situação |
|------|----------|
| **Versão** | 0.2.0-prototype |
| **Última atualização** | 2026-10-08 |
| Login e perfis (RBAC) | Funcional (demo) |
| Cargos e permissões configuráveis | Funcional (protótipo) |
| Cadastro de pacientes / psicólogos | Funcional (demo) |
| Agenda e status de consulta | Funcional (demo) |
| Financeiro automático ao marcar *realizado* | Funcional (demo) |
| Relatório por psicólogo | Funcional (demo) |
| Prontuário eletrônico | MVP iniciado: evoluções imutáveis por atendimento realizado |
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

Abra um terminal na raiz do projeto e execute:

```bash
python app.py
```

O atalho abre terminais separados para a API e a interface e, em seguida, abre o navegador em http://localhost:5173. Mantenha os dois terminais abertos enquanto usar o sistema. Na primeira execucao, o terminal do backend pode criar o ambiente virtual e instalar as dependencias.

Para iniciar os servicos separadamente, use `.\scripts\iniciar-backend.ps1` e `.\scripts\iniciar-frontend.ps1` em terminais distintos.

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

## Cargos, permissões e prontuário

O catálogo de permissões é criado no banco na inicialização. O usuário `admin@demo.com` acessa **Cargos e acessos** para criar, editar e excluir cargos, atribuir permissões e associar os usuários existentes aos cargos. A API também valida as permissões em cada rota; ocultar links na interface não é usado como controle de segurança. Somente o perfil de administrador pode administrar cargos ou atribuições.

Os cargos iniciais preservam as permissões operacionais dos perfis da demonstração. O cargo Psicólogo pode consultar e registrar evoluções dos próprios atendimentos; leitura clínica ampla é uma permissão separada e não é concedida por padrão a sócias ou administradores. Os itens de permissão representam funções implementadas no sistema; módulos novos precisam ser adicionados ao catálogo e ligados às rotas pela equipe de desenvolvimento.

O MVP clínico permite registrar uma evolução textual em um atendimento marcado como realizado, uma vez por atendimento. O registro guarda paciente, atendimento, profissional e data; não há edição ou exclusão de evoluções nesta etapa. Este protótipo não possui criptografia específica dos registros, trilha de auditoria de leitura nem adequação operacional completa à LGPD. **Não registrar dados reais de saúde.**

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
└── docs/                     # escopos e documentos de planejamento
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

### v0.2.0-prototype (2026-10-08)

- Catálogo de permissões e cargos persistidos no banco; atribuição a usuários restrita ao administrador.
- Autorização no backend por cargo nas rotas de pacientes, profissionais, agenda, relatórios e financeiro.
- MVP do prontuário com evoluções vinculadas a atendimentos realizados, leitura por permissão e registros sem edição/exclusão.

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

Os escopos e documentos de planejamento estão em [`docs/`](./docs/), incluindo os dois arquivos Word de requisitos, suas extrações de texto e o documento de hospedagem.
