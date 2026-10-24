# Gestão Clínica — Protótipo Web

Sistema web de demonstração para clínica de psicologia: agenda, cadastros, faturamento e **repasse por psicólogo**. Destinado a apresentação ao cliente antes da versão de produção.

> **Aviso:** dados fictícios. Não utilizar com informações reais de pacientes sem adequação LGPD.

## Acompanhamento e continuidade

O plano priorizado, a situação de cada item, as decisões técnicas e o histórico de testes estão em [docs/ACOMPANHAMENTO.md](docs/ACOMPANHAMENTO.md). Leia também [AGENTS.md](AGENTS.md) antes de continuar o desenvolvimento. Atualize o acompanhamento após cada teste e entrega.

Por solicitação do usuário, cada etapa deve ser concluída e validada antes de pedir confirmação para avançar à próxima. A conclusão de uma etapa não representa liberação do sistema para produção.

---

## Status atual

| Item | Situação |
|------|----------|
| **Versão** | 0.2.0-prototype |
| **Última atualização** | 2026-10-23 |
| Login e perfis (RBAC) | Funcional (demo) |
| Separação demo/produção | SEG-01 validada: produção exige chave/banco próprios, sem seed ou autenticação das contas demo; bootstrap administrativo explícito |
| Isolamento de acessos | SEG-02 validada: profissional sem vínculo bloqueado; agenda/pacientes/dashboard/financeiro próprios; leitura clínica ampla somente por permissão explícita |
| Cargos e permissões configuráveis | Funcional (protótipo) |
| Cadastro de pacientes / psicólogos | Funcional (demo) |
| Cadastro completo / cobertura de convênio | Planejado em CAD-01: nascimento, endereço/CEP e operadora/plano/carteirinha; hoje há apenas classificação particular/convênio |
| Meios de pagamento, taxas e recebimentos | Planejado em FIN-05; realização da sessão ainda não controla crédito efetivo em caixa/banco |
| Agenda e status de consulta | Funcional (demo) |
| Validação de horários e conflitos | Fim posterior ao início, vínculos ativos e bloqueio de sobreposição por profissional/paciente, inclusive em reservas simultâneas |
| Horários vencidos e reagendamento | Nova reserva só no futuro; reagendamento cria registro vinculado e preserva o anterior |
| Agenda recorrente | Semanal ou a cada 14 dias, reserva até alteração/encerramento e exceção por sessão; conferência visual pendente |
| Janelas da agenda | Novo agendamento, reagendamento, estorno e recorrências em modais; 14 verificações de interação e capturas isoladas aprovadas |
| Financeiro automático ao marcar *realizado* | Funcional (demo) |
| Cancelamento de realizado com estorno | Funcional (protótipo): exige permissão financeira, motivo e ausência de evolução clínica |
| Transações e concorrência financeira | Validado em SQLite: realização atômica, chaves únicas e bloqueio compartilhado com agenda/prontuário |
| Relatório por psicólogo | Funcional (demo) |
| Prontuário eletrônico | MVP iniciado: evoluções imutáveis por atendimento realizado |
| WhatsApp / exportação PDF | Planejado |
| Endpoint `/health` | Funcional (demo) |
| Testes automatizados isolados | 224 testes backend; 6 verificações de escopo e 14 das janelas aprovadas nesta etapa. Histórico de outras suítes no acompanhamento; teste de recepção antigo ainda requer revisão |
| Produção (PostgreSQL, VPS) | Planejado |

---

## Stack

Prioridades seguintes: **CAD-01 → FIN-04 → FIN-05**. Incluem cadastro com nascimento/endereço/CEP e convênio (operadora, plano, carteirinha), valores por vigência e meios de pagamento com taxas/parcelas/datas de crédito. Consulta de nome por CPF/nascimento é **CAD-02**, dependente de integração ainda não definida. A distribuição das taxas entre clínica e profissional ainda precisa ser decidida. Situações completas no acompanhamento.

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
- Em modo demo (padrão), a primeira execução cria o banco e dados fictícios. `DEMO_SEED=false` desabilita essa carga.

### Separação de ambientes — SEG-01

O uso local continua em **demo**. Copie `backend/.env.example` para `backend/.env` somente se precisar ajustar a configuração. Nenhum `.env` real foi alterado nesta entrega.

Em **production**, defina `APP_ENV=production`, `DEMO_SEED=false`, `SECRET_KEY` aleatória própria e `DATABASE_URL` de uma base separada. Chave padrão/curta/de exemplo, seed ligado ou banco SQLite padrão interrompem a inicialização. CORS não aceita `*` nesse modo. Gere a chave localmente com `secrets.token_urlsafe(48)` e mantenha-a fora do repositório; ela não é enviada ao frontend.

O startup de produção prepara schema e catálogo de cargos, sem criar usuários/pacientes/agendamentos demo. Uma base com contas demo é recusada sem remover usuários; essas contas também são recusadas pelo login/JWT de produção. Não reutilize a base demo para dados reais.

Para criar **somente o primeiro administrador**, após inicializar schema/catálogo, interrompa a API e, na mesma configuração de produção e pasta backend, execute:

```powershell
..\.venv\Scripts\python.exe -m app.criar_admin --email administrador@clinica.com
```

Nome e senha são solicitados no terminal; senha não aparece nem vai em argumentos. O comando não cria outro administrador nem redefine senha se já existir um. Depois, reinicie a API. Procedimento validado em banco isolado; não houve criação de conta real.

O login consulta `/api/config/publico`: atalhos demo aparecem somente quando a API confirma demonstração habilitada. Em produção ou falha da consulta, permanece o login manual. O frontend usa `/api` na mesma origem; para outra origem, configure `VITE_API_BASE_URL` no build (veja `frontend/.env.example`). Variáveis VITE são públicas, nunca guardar segredos nelas.

Validação: **193 testes backend, 28 verificações de interface e build aprovados**. Na pasta frontend, execute `npm.cmd run test:login-ambiente` e depois `npm.cmd run test:agenda-modal`; ambos usam Chrome/Edge isolado na porta 5197. Comando backend completo no acompanhamento. PostgreSQL, HTTPS, migrações, backup e demais controles de produção continuam pendentes; esta etapa não publica nem libera o sistema para produção.

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

Em modo demo com seed habilitado, a tela de login oferece **acesso rápido** para cada perfil. Esses atalhos ficam ocultos no modo production.

## Cargos, permissões e prontuário

O catálogo de permissões é criado no banco na inicialização. O usuário `admin@demo.com` acessa **Cargos e acessos** para criar, editar e excluir cargos, atribuir permissões e associar os usuários existentes aos cargos. A API também valida as permissões em cada rota; ocultar links na interface não é usado como controle de segurança. Somente o perfil de administrador pode administrar cargos ou atribuições.

Os cargos iniciais preservam as permissões operacionais dos perfis da demonstração. O cargo Psicólogo pode consultar e registrar evoluções dos próprios atendimentos; leitura clínica ampla é uma permissão separada e não é concedida por padrão a sócias ou administradores. Os itens de permissão representam funções implementadas no sistema; módulos novos precisam ser adicionados ao catálogo e ligados às rotas pela equipe de desenvolvimento.

### Isolamento de acessos — SEG-02

- Profissional sem vínculo cadastrado (ou vínculo inexistente) recebe acesso negado aos módulos protegidos, mesmo com cargo personalizado amplo.
- O perfil psicólogo vê agenda/recorrências próprias e apenas pacientes já ligados a elas, inclusive históricos. O dashboard usa o mesmo alcance. **Novos pacientes são cadastrados e direcionados pela recepção/gestão mediante primeiro agendamento ou recorrência**; não ficam automaticamente visíveis a todos os profissionais.
- Recepção/gestão autorizadas veem o cadastro administrativo completo. Isso não permite consultar evoluções clínicas. Leitura ampla de relatórios/prontuário depende das permissões explícitas correspondentes; não amplia escrita clínica ou agenda alheia.
- Permissões financeiras em cargo personalizado permitem ao profissional consultar/gravar apenas no próprio âmbito. IDs de outro profissional/atendimento são recusados na escrita; vínculos inconsistentes não são gravados. O profissional não pode alterar percentual de repasse, mesmo que seu cargo receba permissão de gerenciamento de profissionais.
- Retirar permissão/cargo ou inativar usuário tem efeito na requisição seguinte. Segurança é aplicada na API; esconder botões não substitui a autorização.
- Validação: **224 testes backend, 6 verificações de escopo, 14 de modais e build aprovados**; bancos/API de tela isolados. Na pasta frontend, `npm.cmd run test:escopo-interface` e depois `npm.cmd run test:agenda-modal`. Comando backend completo e roteiro de conferência no acompanhamento. PostgreSQL, auditoria, operação e validação na sessão habitual continuam pendentes.

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

### Janelas da agenda — UX-04 (2026-10-23)

- **Horários recorrentes** abre em janela pelo botão da agenda. Novo agendamento, reagendamento e cancelamento com estorno também abrem em janelas, com botão × e Escape para fechar.
- Fundo bloqueado, foco restaurado ao botão de origem, conteúdo adaptado ao celular e checkbox de encerradas alinhado. Durante salvamento, a janela aguarda a resposta antes de permitir fechar.
- Validação: build aprovado e 14 verificações em Chrome headless com API simulada; capturas desktop/mobile revisadas. Na pasta frontend: `npm.cmd run test:agenda-modal` (Chrome/Edge instalado; CHROME_PATH opcional). Não acessa dados reais. Backend não alterado nesta correção.
- Atualize com Ctrl+F5 para conferir na sua sessão. Histórico de testes e limitações no acompanhamento.

### Agenda recorrente — AGE-04 (2026-10-23)

- Novo agendamento oferece **Não repetir / Semanal / Quinzenal (a cada 14 dias)**. A primeira data define o dia da semana e horário de Brasília, reservado até alteração ou encerramento.
- **Cancelar só esta sessão** ou **Reagendar** mantém as seguintes. No painel **Horários recorrentes**, use **Alterar próximas sessões** ou **Encerrar recorrência**, informando motivo e data efetiva. Data vazia no encerramento significa agora. Não registra alta clínica.
- A sequência antiga permanece no histórico. Sessões realizadas, prontuários e financeiro são preservados; o sistema recusa um corte que afete sessões com histórico, solicitando data posterior. Receita/repasse só são gerados ao marcar cada sessão realizada.
- As próximas sessões são geradas para 90 dias ao abrir/atualizar a agenda com permissão de gerenciamento. A reserva continua bloqueando após esse período. Não há tarefa externa de geração; sessões passadas não são inventadas após período sem acesso.
- Atualize `backend/requirements.txt` no ambiente da API (nova dependência tzdata, já instalada no ambiente da raiz), reinicie o backend e use Ctrl+F5. O startup cria duas tabelas novas, sem alterar os agendamentos antigos.
- Validação: **173 testes backend, 16 frontend e build aprovados**, incluindo concorrência entre processos e novas rotas com JWT via ASGI. Roteiro manual e comando completo no acompanhamento. Conferência visual, rede HTTP e PostgreSQL continuam pendentes; SEG-01 aguarda confirmação.

### Aviso de horário inválido — AGE-03 (2026-10-23)

- Criar ou reagendar com data/hora vencida mostra aviso junto ao campo e bloqueia a confirmação, inclusive quando o formulário fica aberto até o horário vencer.
- A agenda usa horário de Brasília e referência da API, atualizada periodicamente e novamente antes de salvar. Se não conseguir confirmar o horário atual, informa o problema e impede a reserva até atualizar.
- Reiniciar o backend para disponibilizar `/api/agendamentos/relogio` e atualizar a página com Ctrl+F5. Nenhuma mudança de banco nesta etapa.
- Validação: 126 testes backend, 16 testes de horários frontend e build aprovados. Na pasta frontend: `npm.cmd run test:horarios` (testado com Node 24.21.0) e `npm.cmd run build`. Comando backend completo no acompanhamento.
- Conferência visual e fluxo HTTP/JWT completo pendentes; nenhum navegador conectado nesta sessão. SEG-01 aguarda confirmação.

### Horários vencidos e reagendamento — AGE-02 (2026-10-23)

- **Reabrir como agendado** só aparece antes do início da consulta; a API também bloqueia reabertura/confirmar horário vencido. Novos agendamentos exigem horário estritamente futuro.
- **Reagendar** cria outro agendamento futuro para o mesmo paciente/profissional e mantém o original no histórico, com vínculo, autor e data. Conflitos, cadastros inativos e histórico clínico/financeiro continuam protegidos.
- Dois pedidos simultâneos de reagendamento não duplicam o sucessor. Uma falha desfaz a criação, o vínculo e eventual cancelamento do original.
- Registro posterior de realização, falta, cancelamento e evolução de um atendimento passado continua permitido pelas demais regras.
- Reiniciar a API para criar a tabela adicional `reagendamentos` e atualizar a página. A interface ajusta os botões conforme o horário e limita a seleção a datas futuras.
- Validação: **123 testes e build completo aprovados**; sem inspeção visual/HTTP ponta a ponta. Na pasta backend: `..\.venv\Scripts\python.exe -m unittest -q test_reagendamento test_agenda test_agenda_concorrencia test_financeiro test_status_agendamento test_transacoes test_concorrencia test_schema_financeiro`.
- SEG-01 continua aguardando confirmação do usuário.

### Horários, vínculos e conflitos de agenda — AGE-01 (2026-10-23)

- Criação e edição validam fim posterior ao início e cadastros existentes/ativos. A API impede sobreposição por profissional e por paciente, inclusive em reservas simultâneas.
- Consultas adjacentes são permitidas. Agendado/confirmado/realizado ocupam horário; cancelado/falta liberam. Reabertura e reagendamento verificam novamente a disponibilidade.
- Novos horários com offset são convertidos para UTC, e as respostas identificam o fuso para exibição local correta. Datas antigas não são reescritas; a revisão completa de fechamento por dia/mês continua em DAT-01.
- O formulário de agendamento oferece apenas cadastros ativos e desabilita o envio enquanto salva. A tela completa de edição permanece em UX-01.
- Validação: **93 testes aprovados no banco local e build completo da interface aprovado**. Sem inspeção visual/HTTP ponta a ponta. Nenhuma nova migração de schema nesta etapa.
- Testes na pasta `backend`: `..\.venv\Scripts\python.exe -m unittest -q test_agenda test_agenda_concorrencia test_financeiro test_status_agendamento test_transacoes test_concorrencia test_schema_financeiro`.
- Próxima etapa: SEG-01 (separação demonstração/produção e configuração segura), após confirmação do usuário.

### Transações e concorrência — FIN-03 (2026-10-23)

- Criação/realização e receita/repasse passam a ser gravados em uma única transação. Falhas desfazem status e lançamentos; seed também evita persistência parcial.
- Agenda, cancelamento e evolução clínica usam o mesmo bloqueio no banco e releem o atendimento antes de validar, inclusive entre processos independentes.
- Chaves automáticas e índice único impedem repetir o faturamento do mesmo atendimento. Em conflito transitório, a API desfaz a operação e retorna 409 para atualizar/tentar novamente.
- Ao reiniciar o backend, uma atualização não destrutiva adiciona a coluna de chave e o índice e classifica lançamentos antigos reconhecidos. Se encontrar duplicação legada, a inicialização para para revisão, sem apagar histórico. Detalhes no acompanhamento.
- Validação: **54 testes aprovados em SQLite**, incluindo WAL, seis operações simultâneas, dois processos, falhas após escrita parcial e inicialização com schema antigo. PostgreSQL real, HTTP/JWT e interface manual ainda não validados.
- Para executar na pasta `backend`: `..\.venv\Scripts\python.exe -m unittest -v test_financeiro test_status_agendamento test_transacoes test_concorrencia test_schema_financeiro`.
- Próxima etapa: AGE-01 (validação de horários, vínculos e conflitos de agenda), após confirmação do usuário.

### Idioma da interface — UX-03 (2026-10-23)

- HTML declarado como português do Brasil e marcado para não ser traduzido automaticamente. O rótulo correto é **Motivo do cancelamento**; a exibição “Motivo do tells” não corresponde ao código.
- Campo de motivo com label explicitamente associado ao textarea. Após atualizar, usar `Ctrl+F5`; se o navegador ainda alterar o texto, desativar a tradução automática para localhost.
- Validação: HTML/rótulo conferidos e build completo aprovado. A sessão do navegador do usuário não foi inspecionada.

### Cancelamentos e estornos — FIN-02 (2026-10-23)

- Transições de status validadas pela API. Atendimento cancelado/falta deve voltar a agendado antes de ser realizado; com histórico financeiro automático, não pode ser reaberto.
- Na agenda, usuários com permissão financeira podem **Cancelar e estornar** um realizado sem evolução clínica, informando motivo. Os originais são preservados e compensações negativas estornam a receita e o repasse, com autor/data/motivo persistidos.
- Atendimentos com prontuário não podem mudar de status. Paciente, profissional e horários ficam protegidos após realização ou existência de histórico clínico/financeiro.
- Consulta de auditoria: `GET /api/financeiro/estornos`, com filtro opcional `agendamento_id` e permissão `financeiro:consultar`.
- Reiniciar a API para criar a tabela nova `estornos_financeiros` pela inicialização do protótipo. Migrações formais e garantias gerais de concorrência continuam no plano.
- Validação: 29 testes isolados e build completo do frontend aprovados; sem inspeção visual/HTTP ponta a ponta. Na pasta `backend`: `..\.venv\Scripts\python.exe -m unittest -v test_financeiro test_status_agendamento`.
- Próxima etapa: FIN-03 (atomicidade da realização e concorrência), após confirmação do usuário.

### Correção de texto da agenda (2026-10-23)

- Corrigido o título da última coluna da agenda de `Acoes` para `Ações`, em UTF-8.
- Validação: texto UTF-8 confirmado e compilação TypeScript (`tsc -b`) aprovada; sem inspeção visual no navegador nesta entrega.
- Próxima etapa planejada: FIN-02 (transições de atendimento e estornos), após confirmação do usuário.

### Correção financeira (2026-10-23)

- Sessões realizadas passam a gerar somente receita bruta e repasse; a parcela da clínica é calculada pela diferença.
- O painel deixa de somar novamente a parcela da clínica gerada pelas versões antigas, preservando os registros históricos e as receitas manuais.
- Dez testes financeiros isolados aprovados. Na pasta `backend`, execute `..\.venv\Scripts\python.exe -m unittest -v test_financeiro` usando o ambiente funcional da raiz.
- Plano de continuidade e pendências registrados em `docs/ACOMPANHAMENTO.md`.

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
