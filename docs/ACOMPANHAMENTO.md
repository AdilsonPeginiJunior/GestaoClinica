# Acompanhamento técnico e continuidade

Data de abertura: 23/10/2026. Origem: avaliação técnica solicitada pelo usuário e autorização para iniciar o item crítico.

## Como retomar

1. Ler `AGENTS.md`, este documento e o diff atual (`git diff`, `git status --short`).
2. Continuar pela maior prioridade pendente. Preservar alterações existentes.
3. Após CADA execução de teste, acrescentar resultado ao histórico abaixo e atualizar o item correspondente.
4. Situações: **Pendente**, **Em andamento**, **Implementado, aguardando teste**, **Bloqueado**, **Concluído**. Concluir somente após validação dos critérios; registrar separadamente qualquer teste manual não executado.
5. Não considerar produção liberada por concluir um item isolado. As pendências de acesso, prontuário, operação e financeiro continuam independentes.
6. Conforme solicitação do usuário, concluir e validar cada etapa, atualizar AGENTS/README/acompanhamento e pedir confirmação antes de passar à próxima. Não exigir novas confirmações para tarefas internas da etapa já autorizada.

## Plano de trabalho

| ID | Prioridade | Item e critério de conclusão | Situação |
|---|---|---|---|
| FIN-01 | Crítica | Corrigir receita duplicada. Sessão R$ 220 / 60% deve resultar em receita R$ 220, repasse R$ 132 e saldo R$ 88; cobrir dados novos, legados e receitas manuais com testes isolados. | Concluído (testes automatizados; interface não validada manualmente) |
| UX-02 | Correção solicitada | Corrigir o título da última coluna da agenda para “Ações”, preservando as permissões e os botões existentes. Validar texto UTF-8 e compilação TypeScript. | Concluído (texto e TypeScript aprovados; sem inspeção visual no navegador) |
| UX-03 | Correção solicitada | Investigar “Motivo do tells”, declarar idioma pt-BR e impedir tradução automática dos rótulos. Validar HTML, label e build. | Concluído (código e build aprovados; navegador do usuário não inspecionado) |
| FIN-02 | Alta | Definir transições e estornos: impedir divergência ao cancelar/reabrir atendimento realizado; preservar histórico e vínculo com prontuário. Testar todas as transições permitidas/proibidas. | Concluído (29 testes combinados e build aprovados; sem inspeção visual/HTTP) |
| FIN-03 | Alta | Gravar atendimento/status e lançamentos em transação única; garantir unicidade no banco sob concorrência; testar rollback, repetição e concorrência. | Concluído no protótipo SQLite (54 testes; PostgreSQL e HTTP ainda não validados) |
| AGE-01 | Alta | Validar fim > início, sobreposição por profissional/paciente, existência e atividade dos vínculos, tanto na criação quanto na edição. Cobrir intervalos adjacentes e cancelados. | Concluído no protótipo local (93 testes combinados e build; sem inspeção visual/HTTP) |
| AGE-02 | Correção solicitada | Impedir novas reservas/reabertura em horário vencido e oferecer reagendamento futuro com vínculo ao original e preservação do histórico. | Concluído (123 testes combinados e build; sem inspeção visual/HTTP) |
| AGE-03 | Correção solicitada | Mostrar aviso junto ao campo quando data/hora estiver vencida/inválida; usar horário da API e fuso de Brasília; bloquear envio mesmo se o formulário envelhecer. | Concluído (126 testes backend, 16 frontend e build; conferência visual pendente) |
| AGE-04 | Funcionalidade solicitada | Agenda recorrente semanal/quinzenal com reserva até alteração ou fim do tratamento, exceções por sessão e preservação do histórico. | Concluído no protótipo (173 testes backend, 16 frontend e build; conferência visual pendente) |
| UX-04 | Correção solicitada | Mover gestão de recorrências e formulários da agenda para janelas modais, corrigir checkbox e validar navegação/compilação. | Concluído (14 verificações em Chrome headless, capturas revisadas e build aprovados) |
| CAD-01 | Alta | Completar cadastro administrativo com nascimento, endereço e busca por CEP; particular/convênio com dados mínimos da cobertura. Consulta de nome por CPF/nascimento depende de avaliação de integração específica. | Pendente (priorizado pelo usuário, após proteção de acesso) |
| CAD-02 | Média | Avaliar provedor autorizado de consulta CPF/nascimento, contrato, credenciais e retorno do nome; implementar somente após definição da integração. | Pendente (depende de serviço/credenciais; separado de CEP) |
| SEG-01 | Alta | Separar demo/produção; exigir segredo seguro fora de demo; impedir seed de contas demo em produção; testar inicialização e configuração. | Concluído no protótipo (193 testes backend, 28 verificações de interface e build) |
| SEG-02 | Alta | Negar acesso de psicólogo sem vínculo; testar isolamento da agenda, dashboard, pacientes, relatórios e prontuário, inclusive com cargos personalizados. Definir visibilidade administrativa de pacientes. | Concluído no protótipo (224 testes backend, 20 verificações de interface e build) |
| FIN-04 | Alta | Migrar dinheiro para Decimal/Numeric com arredondamento definido; preços por vigência e histórico de repasse; testar histórico após alteração de cadastro. | Pendente (base para taxas/recebimentos) |
| DAT-01 | Média | Padronizar armazenamento/fuso e fechamento em America/Sao_Paulo. Testar ida/volta da agenda e limites de dia/mês. | Pendente (normalização/identificação UTC da agenda entregue em AGE-01; fechamento de dia/mês e revisão completa continuam pendentes) |
| QUA-01 | Alta | Suíte repetível com banco isolado: permissões, prontuário, agenda e financeiro; corrigir teste de recepção (CPF fixo, gravações, ausência de falha se relatório for liberado). | Pendente |
| AMB-01 | Alta | Documentar ambiente Python funcional e reparar/recriar ambiente do backend se necessário; validar execução local pelo atalho. | Em andamento |
| QUA-02 | Média | Corrigir configuração do ESLint e obter lint e build completos; adicionar execução automatizada em CI. | Pendente (build aprovado em FIN-02; lint e CI continuam pendentes) |
| OPS-01 | Alta | PostgreSQL, driver, migrações Alembic (substituir alteração de schema no startup), implantação HTTPS/configuração por ambiente. Testar migração e recuperação. | Pendente |
| OPS-02 | Alta | Backup e restauração testada, logs/monitoramento e verificação de prontidão do banco, além do /health atual. | Pendente |
| CLI-01 | Alta | Auditoria de leitura/alterações do prontuário, autoria e retificações rastreáveis, proteção operacional e revisão dos requisitos de privacidade antes de dados reais. | Pendente |
| UX-01 | Média | Completar edição de pacientes/profissionais, reagendamento, faltas, paginação, filtros e mensagens de erro da API; validar fluxo manual. | Pendente (reagendamento entregue em AGE-02; demais telas/inspeção visual pendentes) |
| FIN-05 | Alta | Separar competência, contas a receber, recebimento e pagamento de repasses; incluir meio de pagamento, parcelas, taxas, previsão/efetivação do crédito e conciliação; definir incidência das taxas no repasse. | Pendente (priorizado pelo usuário; incidência das taxas ainda a esclarecer) |
| EXP-01 | Baixa | Após estabilização: convênios com vigência, exportações Excel/PDF, lembretes e WhatsApp. Definir critérios antes de implementar. | Pendente |

## FIN-01 — diagnóstico e decisão

- `backend/app/services.py` criava receita bruta + repasse + outra receita correspondente à parcela da clínica.
- `backend/app/routers/dashboard.py` somava as duas receitas. Exemplo anterior: 220 + 88 = 308.
- Solução implementada: gerar somente receita bruta e repasse. Saldo é receita menos repasse, como já faz a tela de relatórios.
- Compatibilidade: não apagar lançamentos legados. Excluir da soma do painel somente a parcela automática antiga identificada pelo conjunto tipo receita + automático + sem psicólogo + agendamento preenchido + descrição exata `Receita clinica sessao #<id>`.
- Receitas manuais, inclusive sem psicólogo, devem continuar contabilizadas. O relatório por psicólogo já exclui a parcela antiga por ter psicólogo nulo.
- A listagem bruta de lançamentos permanece com os registros históricos para inspeção; não somar essa lista indiscriminadamente. Uma futura migração de classificação explícita fica para FIN-04/OPS-01.
- Não estão incluídos em FIN-01: estornos, atomicidade/concorrência, Decimal ou mudança de competência.

## Histórico de validações

| Teste | Resultado | Efeito no acompanhamento |
|---|---|---|
| Avaliação anterior: `npm.cmd run build` | TypeScript passou; Vite falhou por acesso negado ao diretório durante carregamento da configuração. | QUA-02 pendente; build completo não confirmado. |
| Avaliação anterior: `npm.cmd run lint` | Falha ao carregar `reactHooks.configs.flat.recommended` (undefined). | QUA-02 pendente; código da aplicação não chegou a ser analisado pelo lint. |
| Avaliação anterior: Python dentro do sandbox | Executável base inacessível; teste financeiro não executado. | Sem evidência dinâmica na avaliação original. |
| 23/10: Python do backend, fora do sandbox, importação de SQLAlchemy/FastAPI | Falhou: extensão binária `pydantic_core._pydantic_core` ausente para Python 3.14; pasta contém binário cp313. | AMB-01 em andamento. Não reinstalar pacotes indiscriminadamente. |
| 23/10: Python da raiz, fora do sandbox, importação de SQLAlchemy/FastAPI | Passou: Python 3.14.7 e dependências importadas. | Usar ambiente da raiz com diretório de trabalho backend para testes isolados. Atalho ainda não validado. |
| 23/10: `..\.venv\Scripts\python.exe -m unittest -v test_financeiro` ANTES da correção | 10 testes: 6 falharam e 4 passaram. Confirmou receita particular de 308 em vez de 220, convênio de 224 em vez de 160 e três lançamentos em vez de dois. Houve aviso de escape no docstring do teste e avisos preexistentes de `utcnow`. | FIN-01 em andamento: defeito reproduzido. Corrigir escape do teste; tratar padronização de datas em DAT-01. |
| 23/10: mesmo comando APÓS a correção | 10/10 passaram, em SQLite em memória. Cobertura: particular, convênio, repasse 0/60/100%, repetição sequencial, legado preservado, receitas legítimas com campos semelhantes ao legado, comparação com relatório, período e ocultação dos valores sem permissão financeira. | FIN-01 concluído no escopo automatizado. Aviso de escape corrigido; avisos de `utcnow` continuam vinculados a DAT-01. |
| 23/10: `git diff --check` e revisão do diff/status | Passou, sem erros de espaços em branco. Alterações limitadas à correção financeira, regressões e documentação de continuidade; nenhum arquivo de banco alterado. | Entrega FIN-01 revisada. Arquivos novos ainda não commitados: AGENTS.md, teste financeiro e acompanhamento. |

## Validações UX-02 — 23/10/2026

| Verificação | Resultado | Situação |
|---|---|---|
| Leitura UTF-8 via PowerShell: exigir `<th>Ações</th>` e ausência de `<th>Acoes</th>` em `frontend/src/pages/Agenda.tsx` | Passou; texto correto confirmado. | UX-02 validado no código. |
| Na pasta frontend: `.\node_modules\.bin\tsc.cmd -b` | Passou, código de saída 0. | UX-02 concluído nos critérios definidos. |
| `git diff --check` após implementação e primeira atualização dos documentos | Passou, código de saída 0. | Sem erros de espaços em branco. |

Arquivo funcional alterado: `frontend/src/pages/Agenda.tsx`. Documentos atualizados: `AGENTS.md`, `README.md` e este acompanhamento. Não foram alterados os botões, as permissões ou o banco. Build completo/lint continuam em QUA-02. Não houve inspeção visual no navegador; com Vite ativo, atualizar a página da agenda para conferir o resultado. Os arquivos SQLite `-wal`/`-shm` já estavam presentes ao iniciar esta etapa e não foram manipulados.

## Entrega FIN-01

- Arquivos de implementação: `backend/app/services.py` e `backend/app/routers/dashboard.py`.
- Regressões: `backend/test_financeiro.py` (unittest da biblioteca padrão; SQLAlchemy e dependências da aplicação já instalados no ambiente da raiz).
- Execução a partir de `backend`: `..\.venv\Scripts\python.exe -m unittest -v test_financeiro`.
- Os testes chamam as funções reais de serviço e dos endpoints com sessões isoladas; não iniciam servidor, não executam seed, não gravam no banco existente e não validam a interface nem o transporte HTTP/autenticação JWT.
- Resultado esperado: particular 220/132/88; convênio 160/96/64 (receita/repasse/saldo).
- Não há alteração de schema nem migração destrutiva. Registros legados permanecem armazenados; o filtro usa a assinatura exata do gerador anterior. Uma base editada externamente com descrições diferentes requer análise própria.
- A prevenção de duplicação por repetição foi validada apenas sequencialmente. Garantia sob concorrência permanece em FIN-03.
- Limites da entrega: execução manual pela interface, build/lint, reparo do ambiente do backend, estornos e demais itens da tabela não foram concluídos.

## Próxima ação

### Publicação do fechamento de SEG-02

- Usuário autorizou commit e envio ao GitHub. Branch local `main`, remoto `origin` no repositório GestaoClinica. O fechamento inclui as alterações acumuladas das etapas anteriores ainda não commitadas, necessárias à agenda/financeiro/segurança e aos testes/documentos de SEG-02.
- Arquivos auxiliares SQLite `gestao_clinica.db-wal`/`-shm` acrescentados ao .gitignore; banco e .env reais excluídos do staging. Capturas de testes contêm apenas fixtures fictícias. Revisão de staging aprovada: 62 arquivos de código/testes/documentação, `git diff --cached --check` sem erros e nenhuma ocorrência dos padrões pesquisados de chave privada/token nos fontes/documentos selecionados. A busca é uma verificação pontual, não certificação de ausência de segredos.
- `git fetch origin` aprovado e `HEAD...origin/main` sem divergência (0/0) antes do commit. Fechamento consolidado para `main`; o identificador e a confirmação de publicação são verificáveis pelo histórico Git e pela referência remota `origin/main`. Nenhum teste funcional repetido nesta etapa de publicação, pois as alterações adicionais foram somente documentação e exclusão de arquivos locais no .gitignore. CAD-01 não iniciada.

SEG-02 concluída; próxima etapa CAD-01 (cadastro completo, CEP e cobertura de convênio), aguardando confirmação conforme fluxo entre etapas. Depois: FIN-04 → FIN-05; CAD-02 depende da definição do provedor de consulta CPF/nascimento. Antes de dados reais, concluir também as demais exigências de operação/prontuário registradas no plano. AMB-01 permanece aberto.

## SEG-02 — isolamento de acesso

- Início autorizado. Diagnóstico: dashboard sem vínculo mostrava contagens globais; pacientes e catálogo de profissionais não limitavam o perfil psicólogo; permissões financeiras em cargo personalizado davam consulta e escrita globais. A verificação de ausência de vínculo variava conforme a rota.
- Política em implementação: perfil psicólogo sempre exige vínculo válido e tem escopo operacional próprio, independentemente do nome do cargo. Pacientes visíveis são os ligados à agenda ou recorrência do profissional, inclusive histórico; pacientes sem vínculo são cadastrados/direcionados pela recepção/gestão mediante primeiro agendamento. Permissões explícitas `relatorios:consultar_todos` e `prontuario:ler_todos` continuam permitindo leitura ampla, mas não dispensam vínculo do perfil psicólogo nem ampliam escrita clínica/agenda/financeiro. Gestão vê cadastro administrativo sem adquirir leitura clínica por isso.
- Validação nº 1: `..\.venv\Scripts\python.exe -m unittest -q test_isolamento`: **24 testes, 20 aprovados e 4 falhas**. Reproduzidos vazamento financeiro (5 lançamentos em vez de 2), escrita de lançamento para profissional/atendimento alheio e lançamento profissional sem atribuição de dono. Demais casos iniciais de vínculo/pacientes/dashboard/agenda/relatórios/prontuário passaram após as primeiras correções. SQLite isolado e ASGI/JWT real; nenhum dado real acessado. Situação: em andamento, corrigir financeiro e executar regressões.
- Validação nº 2: `..\.venv\Scripts\python.exe -m unittest -q test_isolamento test_recorrencias test_recorrencias_http`: **63 testes, 59 aprovados, 3 falhas e 1 erro**. Os 24 casos de isolamento passaram após correção financeira. Quatro fixtures anteriores de recorrência tentavam iniciar tratamento de paciente ainda sem vínculo; ajustar os dados fictícios para incluir o primeiro direcionamento pela recepção/gestão, mantendo a nova restrição. Não retirar a verificação de escopo para fazer regressão passar.
- Validação nº 3: suíte completa com `test_isolamento` e todas as suítes anteriores: **217/217 aprovados** após adequação das fixtures. Inclui 24 testes de escopo via JSON/ASGI/JWT e 193 regressões. Ampliando a matriz para revogação de permissões, inativação, recorrência alheia e rollback; build/interface ainda pendentes nesta etapa.
- Validação nº 4: frontend `npm.cmd run build`: **TypeScript/Vite aprovados**, 109 módulos. Cadastro de pacientes informa o escopo do profissional e não oferece criação global; filtro da agenda limita escolhas ao próprio profissional, inclusive com leitura ampla de relatórios.
- Validação nº 5: suíte backend ampliada: **224/224 aprovados** (31 testes de isolamento e 193 regressões). Cobertura adicional: revogação/cargo removido, usuário inativo, leitura ampla explícita sem ampliar agenda, bloqueio de série alheia, vínculo histórico por recorrência, referências financeiras inválidas e ausência de registros parciais em recusas. Avisos preexistentes utcnow.
- Validação nº 6: `npm.cmd run test:escopo-interface`: **6/6 verificações aprovadas** em Chrome headless com API simulada. Profissional não recebe botão de cadastro global nem outro profissional nos filtros/formulário; recepção autorizada mantém o botão. Não substitui os testes de autorização da API real via ASGI/JWT.
- Validação nº 7: `..\.venv\Scripts\python.exe -m unittest -q test_isolamento`: **31/31 aprovados** após revisão final do cadastro: GET seleciona paciente e escopo na mesma consulta; PATCH obtém a trava compartilhada do paciente e revalida escopo após a trava, dentro da transação. Evita confiar em cadastro em cache ou autorização anterior à transferência de reserva.
- Validação nº 8: `npm.cmd run test:agenda-modal`: **14/14 verificações aprovadas**, regressão com a fixture atualizada de perfis/catálogo. `git diff --check` aprovado, apenas avisos LF/CRLF. SEG-02 concluída no escopo automatizado do protótipo; sem alterações de schema, cadastro de contas reais ou gravações no banco da clínica. Sem commit.

### Política efetiva de SEG-02

- O perfil (`psicologo`, `recepcionista`, `socia`, `admin`) define a identidade/alcance operacional; o cargo define as funções concedidas. Renomear cargo ou atribuir um cargo personalizado não altera o perfil nem concede acesso implícito. A ausência de cargo/permissão, usuário inativo ou sessão ausente é recusada. Usuário com perfil psicólogo sem `psicologo_id` ou com referência a profissional inexistente recebe 403 em todas as rotas protegidas por permissão, antes de consultar/escrever dados do domínio. Login e `/auth/me` continuam disponíveis para identificar a conta e resolver o vínculo.
- Agenda e recorrências: profissional só lista, cria, altera status, reagenda, gera, altera ou encerra reservas próprias. Parâmetro de filtro de outro profissional não amplia a consulta. Criação de sessão/série para paciente alheio ou ainda não direcionado é recusada após adquirir as travas de recursos, antes da gravação.
- Pacientes: profissional com consulta vê apenas pacientes com pelo menos um agendamento ou regra de recorrência em seu nome, em qualquer status/vigência, preservando acompanhamento histórico. Busca e contagem do dashboard usam o mesmo escopo, sem duplicar paciente compartilhado. GET/PATCH por ID alheio ou inexistente retornam 404. Com `pacientes:gerenciar`, profissional pode atualizar dados administrativos dos próprios pacientes, mas não criar cadastro global.
- Recepção/sócia/admin com as permissões correspondentes veem o cadastro administrativo completo. Novos pacientes são cadastrados por esses usuários e direcionados ao profissional pelo primeiro agendamento (ou recorrência administrativa). Um cadastro ainda sem nenhuma reserva não aparece automaticamente para todos os profissionais. Não foi criada tabela ou tela de encaminhamento independente; essa ampliação pode ser avaliada em CAD-01. Cancelar/encerrar a reserva não revoga acesso ao histórico por si só.
- Dashboard de profissional conta somente seus atendimentos e pacientes ativos do mesmo escopo. Financeiro continua zerado sem `financeiro:consultar`; com a permissão, soma apenas seus lançamentos. Indicadores de gestão não concedem leitura de prontuário.
- Relatórios e prontuário: `relatorios:consultar_proprio` e `prontuario:ler_proprio` não permitem registros de outro profissional, mesmo para paciente compartilhado. Permissões separadas `*:consultar_todos` / `prontuario:ler_todos` são concessões amplas explícitas; não são conferidas pelo nome do cargo ou por ser sócia/admin. Quem tem leitura ampla de relatórios e consulta de profissionais recebe o catálogo para selecionar o relatório de outro profissional, sem ampliar sua agenda. Perfil psicólogo ainda precisa de vínculo válido mesmo com essas permissões amplas.
- Escrita de evolução exige `prontuario:criar`, vínculo e atendimento próprio realizado, com validação após a trava do atendimento. Ler todos nunca concede escrita clínica em nome de outro profissional. Leitura administrativa de pacientes não inclui evoluções.
- Financeiro: perfil psicólogo com permissões financeiras em cargo personalizado só consulta seus lançamentos/estornos e só registra manual em seu escopo. Sem profissional informado, o lançamento manual recebe seu próprio vínculo. Atendimento informado é travado e relido antes da autorização; vínculo conflitante é recusado. Gestão autorizada mantém lançamentos gerais e de todos, mas referências inexistentes/incoerentes são recusadas (404/422). Recusas fazem rollback, sem registros parciais.
- Cadastro de profissionais: perfil psicólogo vê o próprio registro (catálogo amplo apenas quando autorizado a consultar todos os relatórios) e não cria profissionais nem altera cadastro/percentual de repasse, mesmo com permissão gerencial indevidamente adicionada ao seu cargo. Gestão com permissão correspondente mantém esse controle.
- Privilégios são obtidos do banco em cada requisição autenticada; JWT não carrega uma cópia estática das permissões. Remover cargo/permissão ou inativar usuário afeta a requisição seguinte. Mudanças de cargo são exclusivas do perfil administrador; perfil sócia ou cargo personalizado com nome/funcionalidades de administrador não substituem esse requisito.

### Arquivos, reprodução e limites de SEG-02

- Backend: novo `app/escopo.py`; alterações em `auth.py`, routers de pacientes/profissionais/dashboard/prontuário/financeiro/agendamentos e criação de recorrência em `recorrencias.py`; novo `test_isolamento.py`; fixtures de `test_recorrencias.py` e `test_recorrencias_http.py` adaptadas ao direcionamento inicial de pacientes. O helper ASGI de teste agora trata query string separadamente do path, para exercitar filtros reais.
- Frontend: `pages/Pacientes.tsx` e `pages/Agenda.tsx`; fixtures/verificador isolados e script `test:escopo-interface`. Nenhum segredo, perfil, cargo ou dado real alterado. Catálogo de permissões existente preservado; nenhuma migração/schema novo nesta etapa.
- Backend: na pasta backend, ambiente de teste demo: `..\.venv\Scripts\python.exe -m unittest -q test_isolamento test_configuracao test_recorrencias test_recorrencias_concorrencia test_recorrencias_http test_relogio_agenda test_reagendamento test_agenda test_agenda_concorrencia test_financeiro test_status_agendamento test_transacoes test_concorrencia test_schema_financeiro`. Última execução completa: 224 aprovados; após revisão final de GET/PATCH de pacientes, seus 31 testes de isolamento foram repetidos e aprovados.
- Frontend: `npm.cmd run test:escopo-interface`, `npm.cmd run test:agenda-modal`, `npm.cmd run build`; executar testes de Chrome sequencialmente (porta 5197). Login por ambiente e helpers temporais não foram alterados e suas suítes específicas não foram repetidas nesta etapa.
- Testes de autorização usam aplicação real via ASGI/JSON/JWT e bancos SQLite isolados, sem servidor de rede; testes de tela usam Chrome headless, perfil temporário e API simulada. Não houve navegação na sessão do usuário. PostgreSQL real, testes de carga/segurança externos, auditoria de leitura/retificação e implantação continuam pendentes. O bloqueio/rollback usa os mecanismos existentes de transação; esta etapa não equivale a certificação de segurança ou liberação de produção.
- Conferência manual pendente na sessão habitual: reiniciar API e Ctrl+F5; comparar Pacientes/Agenda/Dashboard como recepção e como profissional; direcionar paciente novo pela recepção e conferir sua aparição para o profissional; verificar ausência de prontuários para recepção/sócia padrão. Usar somente base/dados fictícios até concluir as etapas operacionais restantes.

## SEG-01 — separação de demonstração e produção

- Diagnóstico: configuração permitia chave pública padrão, startup executava seed demo em qualquer ambiente e login sempre exibia acessos rápidos demo. Não havia bootstrap explícito de administrador de produção.
- Implementação em validação: APP_ENV=demo/production, validação de chave/banco no modo production, DEMO_SEED proibido em produção, proteção dentro da função seed, bloqueio de base com contas demo (sem apagar usuários), configuração pública mínima e atalhos de login condicionados à API. Bootstrap administrativo explícito, com senha lida por getpass.
- Prioridades de cadastro/convênio e recebimentos atualizadas a pedido do usuário; nenhum desses módulos foi marcado como implementado. Regra de distribuição das taxas de cartão continua sem resposta e não será presumida.
- Validação nº 1: backend `..\.venv\Scripts\python.exe -m unittest -q test_configuracao`: **17/17 aprovados** em SQLite isolado e processo temporário. Configuração, ausência de seed em produção, preservação da base demo, catálogo, bootstrap e erros sem exposição de chave aprovados. Avisos preexistentes de utcnow.
- Validação nº 2: frontend `npm.cmd run build`: **TypeScript e Vite aprovados**, 109 módulos. Situação: implementação inicial validada; complementar regressões e apresentação do login nos dois modos.
- Validação nº 3: frontend `npm.cmd run test:login-ambiente`: **10/10 verificações aprovadas** em Chrome headless/API simulada. Demo exibe quatro atalhos; produção, demo sem seed, configuração indisponível ou pendente não exibem atalhos; login manual continua disponível. Nenhum dado real acessado. Suíte backend ampliada em execução neste registro.
- Validação nº 4: suíte completa backend incluindo `test_configuracao` e as doze suítes anteriores: **193/193 aprovados** (20 de SEG-01 e 173 regressões). Inclui chave inválida bloqueando importação antes de abrir banco, startup sem dados demo, bootstrap com hash, login/JWT via ASGI e recusa de contas demo em produção mesmo sem lifespan. Avisos preexistentes utcnow. Backend aprovado; complementando testes do login para payload público inválido/inconsistente e baseURL configurável.
- Validação nº 5: `npm.cmd run test:login-ambiente`: **14/14 verificações aprovadas**, incluindo configuração pública malformada e produção com flag demo inconsistente, ambas sem atalhos. `npm.cmd run build`: **TypeScript/Vite aprovados**, 109 módulos, após baseURL configurável e validação da resposta pública. Complementada proteção de DATABASE_URL contra caminhos equivalentes ao SQLite padrão; aguardando regressão final.
- Validação nº 6: `npm.cmd run test:agenda-modal`: **14/14 verificações aprovadas**, regressão das janelas de agenda em Chrome headless/API simulada. Sem alteração dos dados reais. Suíte backend final em execução neste registro.
- Validação nº 7: mesmo comando completo de backend, após normalização do caminho SQLite: **193/193 aprovados**. `git diff --check` aprovado, apenas avisos LF/CRLF. SEG-01 concluída no escopo do protótipo. Não foram repetidos os 16 testes de funções temporais (helpers não alterados); os novos testes de login e a regressão da agenda cobrem a interface alterada.

### Regras e operação de SEG-01

- `APP_ENV` aceita somente `demo` (padrão compatível com o uso local) ou `production`; erro de digitação interrompe a inicialização. `DEMO_SEED` ausente habilita dados fictícios apenas em demo; `false` desabilita, e `true` em production é recusado. Proteção existe no startup e dentro da função de seed.
- Production exige `SECRET_KEY` própria com pelo menos 32 caracteres, variedade mínima e sem valores padrão/de exemplo, e `DATABASE_URL` explícita. URLs equivalentes ao arquivo SQLite padrão são recusadas; CORS com `*` também é recusado. A validação ocorre ao importar a configuração, antes de criar engine/abrir banco. Gerar a chave com `secrets.token_urlsafe(48)`; a verificação de formato não substitui geração aleatória. Configuração é imutável e repr/erros de validação não exibem chave/URL.
- Startup de production instala schema e catálogo de permissões/cargos, mas não cria usuários, profissionais, pacientes, agenda ou lançamentos fictícios. Base com e-mails das quatro contas demo (inclusive variação de maiúsculas) é recusada sem apagar contas. Login e JWT dessas contas são recusados em production também no nível de autenticação, mesmo que o lifespan não seja executado. Uma base demo não deve ser promovida renomeando contas: manter bases separadas.
- Primeiro administrador: configurar o ambiente production e a base nova, iniciar a API para preparar schema/catálogo, interromper esse processo e executar na mesma configuração `..\.venv\Scripts\python.exe -m app.criar_admin --email administrador@clinica.com` na pasta backend. Nome por prompt; senha/confirmacão por getpass (mínimo 12 caracteres, até 72 bytes UTF-8). O comando valida endereço, recusa contas demo, grava hash e trava o cargo ao verificar ausência de administrador. Se já existe administrador, não cria outro nem redefine senha. Não criar administrador de produção no banco demo.
- `GET /api/config/publico` divulga somente `ambiente` e `demo_habilitada`. Login só mostra atalhos quando ambos confirmam demo; falha, carregamento, payload inválido ou modo production mantém atalhos ocultos. Login manual permanece disponível. Layout identifica demonstração conforme API. Esses ajustes visuais não substituem controles do backend.
- Frontend usa `/api` na própria origem em ambos os builds, com proxy Vite no desenvolvimento. Para API em outra origem, definir `VITE_API_BASE_URL` no build; esta variável é pública e não deve conter segredos. Reverse proxy/HTTPS continuam OPS-01.
- Arquivos: backend `app/config.py`, `app/main.py`, `app/seed.py`, `app/auth.py`, novo `app/criar_admin.py`, `.env.example` e `test_configuracao.py`; frontend `src/api.ts`, `pages/Login.tsx`, `components/Layout.tsx`, novo `context/useAmbiente.ts`, `.env.example`, `package.json`, fixtures/verificador de interface; AGENTS, README e acompanhamento.
- Não houve alteração de `.env` real, criação de contas reais, mudança do modo do usuário, implantação externa ou manipulação do SQLite em uso. Testes usam bancos em memória/temporários e ASGI com dependências substituídas; Chrome usa API simulada e perfil temporário. PostgreSQL real, migrações formais, provisionamento completo, HTTPS, backup e auditoria clínica continuam pendentes. Não representa liberação para produção.
- Reprodução backend (na pasta backend, ambiente de teste demo): `..\.venv\Scripts\python.exe -m unittest -q test_configuracao test_recorrencias test_recorrencias_concorrencia test_recorrencias_http test_relogio_agenda test_reagendamento test_agenda test_agenda_concorrencia test_financeiro test_status_agendamento test_transacoes test_concorrencia test_schema_financeiro`.
- Reprodução frontend: `npm.cmd run test:login-ambiente`, `npm.cmd run test:agenda-modal`, `npm.cmd run build`. Os dois testes de Chrome usam a porta 5197 e devem ser executados um após o outro. Não houve commit. Próxima etapa SEG-02 não iniciada.

## CAD-01 / FIN-05 — ampliação solicitada de cadastro e recebimentos

- Consulta do código atual: cadastro tem nome, CPF, telefone e tipo particular/convênio; API/modelo também possuem e-mail/observações. Não há nascimento, endereço, busca por CEP, integração com Receita Federal, identificação da operadora/plano/carteirinha, meio de pagamento, taxas de cartão ou datas de liquidação. O lançamento automático ao realizar a sessão não comprova recebimento em caixa/banco.
- CAD-01 proposto: nascimento e endereço (CEP, logradouro, número, complemento, bairro, cidade e UF), com busca por CEP e opção de ajuste manual. Consulta do nome por CPF/nascimento é integração separada, ainda sem serviço/credenciais definidos; não prometer disponibilidade como parte da busca de CEP.
- Particular/convênio já existe como classificação. Ampliação proposta: se convênio, operadora, plano e número da carteirinha; validade, titular e autorização quando aplicáveis. Distinguir cadastro da operadora (dados de cobrança/contato, contrato, valores e prazos por vigência) da cobertura do paciente. Dados mínimos finais dependem das operadoras atendidas.
- FIN-05 proposto: cadastrar meios de pagamento (dinheiro, Pix, débito, crédito, transferência e recebimento da operadora), regras configuráveis por adquirente/modalidade/parcelamento, taxa percentual/fixa, eventual antecipação, parcelas e datas previstas. Cada recebível deve registrar bruto, taxas, líquido e data prevista; confirmação de recebimento registra data/valor efetivos e permite conciliar diferenças. Não presumir taxas ou prazos universais de cartão, nem marcar pago apenas por realizar a sessão.
- Registrar a cobrança e a modalidade efetivamente usadas por sessão/recebível, mesmo havendo preferência no cadastro. Preservar condições históricas: mudanças posteriores de plano, preço, prazo ou taxa não recalculam cobranças antigas. Reutilizar estornos rastreáveis, sem apagar lançamentos.
- Regra a esclarecer antes de alterar repasses: taxas serão absorvidas pela clínica ou descontadas da base de repasse? Não alterar a base bruta atual sem decisão explícita; separar a configuração e o histórico da regra financeira (FIN-04/FIN-05).
- Sequência proposta para revisão: CAD-01 (cadastro/cobertura/CEP), FIN-04 (valores monetários e condições por vigência), FIN-05 (cobrança/recebimento/taxas/conciliação). SEG-01 segue pendente; não reordenar automaticamente sem confirmação do usuário.
- Situação: requisitos documentados em AGENTS/README/acompanhamento; nenhuma implementação funcional ou teste executado nesta análise. Não cadastrar condições de operadoras nem enviar CPF/nascimento a serviços externos durante a investigação.

## UX-04 — janelas da agenda

- Solicitação: substituir os blocos grandes de recorrência/reagendamento por popup/janela e corrigir a apresentação vista na captura do usuário.
- Implementação: `Modal.tsx` com dialog nativo, fundo bloqueado, foco contido/restaurado, Escape e botão de fechar; fechamento indisponível durante gravação. Janelas para novo atendimento, reagendamento, cancelamento com estorno e gestão de recorrências. Checkbox de encerradas em linha; alteração/encerramento da série substitui a listagem dentro da mesma janela.
- Validação nº 1: `npm.cmd run build`: TypeScript e Vite aprovados, 108 módulos. Situação: compilável; conferência de interação ainda pendente. Sem alterações de backend/banco nesta correção.
- Validação nº 2: `npm.cmd run test:agenda-modal -- --screenshots`: falhou no próprio verificador CDP ao tentar serializar um elemento DOM ("Object reference chain is too long"), antes das asserções de interação. Corrigido o polling para retornar somente booleanos. Teste usa Chrome headless separado, perfil temporário e API simulada; não acessa dados reais. Situação: validação de interação em andamento.
- Validação nº 3: mesmo comando, seis verificações aprovadas (abertura, fundo, checkbox, foco contido, filtro e edição), seguido de timeout ao simular Escape. Ajustada a automação para enviar códigos nativos de tecla e cliques reais de ponteiro, com foco da página habilitado; não considerar Escape validado antes da nova execução.
- Validação nº 4: Escape fechou a janela, mas a asserção de restauração de foco/rolagem falhou. Acrescentada restauração explícita do elemento que abriu o dialog no cleanup do componente React; o dialog pode já ter sido removido do DOM quando o efeito é limpo. Situação: correção aplicada, aguardando reexecução.
- Validação nº 5: `npm.cmd run test:agenda-modal -- --screenshots`: **14/14 verificações aprovadas** em Chrome headless (React StrictMode, Vite separado na porta 5197, perfil temporário e API inteiramente simulada). Cobertura: agenda sem painel aberto, dialog modal, rolagem bloqueada, checkbox em linha, Tab, filtro de encerradas, edição sem tabela abaixo, Escape/foco, novo atendimento, estorno sem envio, horário inválido, largura de 360px, fechamento bloqueado ao salvar e uma única requisição simulada no sucesso. Capturas fictícias em `frontend/tests/artifacts/ux04-*.png`; revisão visual e build final pendentes neste registro.
- Validação nº 6: `npm.cmd run build` após correção de foco: **TypeScript e Vite aprovados**, 108 módulos. Capturas desktop (1280×850) e mobile (360×740) abertas e revisadas: janelas centralizadas, conteúdo legível e checkbox alinhado. Revisão final `git diff --check` aprovada, somente avisos LF/CRLF. **UX-04 concluído** no escopo da interface isolada; não houve navegação na sessão real nem gravações na API da clínica.
- Arquivos: novo `frontend/src/components/Modal.tsx`; alterados `pages/Agenda.tsx`, `components/RecorrenciasAgenda.tsx`, `index.css`, `package.json`; fixtures/verificador em `frontend/tests/agenda-modal*` e duas capturas fictícias em `tests/artifacts`; AGENTS, README e acompanhamento. Nenhuma alteração de backend/schema nesta etapa; as suítes backend de AGE-04 (173 testes) não foram repetidas.
- Reprodução: na pasta frontend, `npm.cmd run test:agenda-modal` (Node 24.21.0 e Chrome/Edge instalados; variável CHROME_PATH para outro caminho). `-- --screenshots` grava capturas. Usa porta 5197, perfil temporário, API simulada e o componente real da agenda. O verificador encerra o navegador/servidor e remove somente seu perfil temporário; não usa login/perfil real.
- Verificação na sessão do usuário: Ctrl+F5; clicar em **Horários recorrentes**, **Novo agendamento**, **Reagendar** ou **Cancelar e estornar**. Conferir botão ×, Escape e retorno à agenda; fechamento fica bloqueado enquanto salva. Alterar/encerrar recorrência ocorre dentro da mesma janela, com **Voltar** para a lista. Sem commit; SEG-01 não iniciado.

## AGE-04 — agenda recorrente entregue

- Início autorizado. Verificação de ambiente: `.\.venv\Scripts\python.exe -c "from zoneinfo import ZoneInfo; print(ZoneInfo('America/Sao_Paulo'))"` falhou por ausência de `tzdata`. Dependência adicionada ao requirements; necessária no Windows para recorrência por calendário em Brasília. Sem testes funcionais executados neste momento.
- Ambiente: instalação de `tzdata>=2025.2` no ambiente virtual da raiz aprovada (tzdata 2026.5), sem alteração de outras dependências.
- Teste AGE-04 nº 1: backend `..\.venv\Scripts\python.exe -m unittest -q test_recorrencias`: **24/24 aprovados**, SQLite em memória. Cobertura inicial: semanal/14 dias, conflitos além de 90 dias, quinzenas alternadas, paciente, meia-noite, exceção, versão/encerramento, rollback, geração idempotente e isolamento. Avisos preexistentes utcnow. Situação: backend inicial implementado; concorrência, integração/frontend e regressões ainda pendentes.
- Teste AGE-04 nº 2: frontend `npm.cmd run build`: **TypeScript e Vite aprovados**, 107 módulos. Opções de repetição, painel de recorrências, alteração/encerramento e geração de 90 dias integrados. Situação: implementado, aguardando regressões/concorrência; sem inspeção visual.
- Teste AGE-04 nº 3: suíte combinada com `test_recorrencias test_recorrencias_concorrencia` e as nove suítes anteriores: **163 testes, 162 aprovados e 1 falha**. A comparação de schema comparou instâncias SQLAlchemy de tipos por identidade, embora o schema impresso fosse igual; corrigir a asserção para comparar assinatura das colunas. Concorrência (incluindo dois processos spawn) e demais regressões passaram. AGE-04 permanece em andamento.
- Teste AGE-04 nº 4: `..\.venv\Scripts\python.exe -m unittest -q test_recorrencias test_recorrencias_http`: **37/37 aprovados** após correção da asserção. Rotas exercitadas por ASGI/JSON com JWT real e dependência de banco substituída por SQLite isolado, sem iniciar lifespan/seed no banco real. Inclui criação/listagem/cancelamento/encerramento, geração, 401/403/409/422, profissionais sem vínculo e encerramento de cadeias de reagendamento pontual. Não equivale a navegador ou transporte de rede.
- Teste AGE-04 nº 5: frontend `npm.cmd run test:horarios`: **16/16 aprovados**, regressão das funções temporais usadas nos formulários. Suíte backend ampliada em execução neste registro.
- Teste AGE-04 nº 6: backend `..\.venv\Scripts\python.exe -m unittest -q test_recorrencias test_recorrencias_concorrencia test_recorrencias_http test_relogio_agenda test_reagendamento test_agenda test_agenda_concorrencia test_financeiro test_status_agendamento test_transacoes test_concorrencia test_schema_financeiro`: **173/173 aprovados** (35 testes de recorrência, 8 de concorrência de recorrência, 4 ASGI/JSON/JWT e 126 regressões). Inclui geração que efetivamente amplia a agenda com quatro threads e dois processos spawn, duas alterações simultâneas, disputa de alteração com reserva avulsa e encerramento concorrente com geração. Apenas avisos preexistentes de utcnow.
- Revisão final: `git diff --check` aprovado, somente avisos de normalização LF/CRLF. Inventário de UI novamente vazio (`apps: [], browsers: []`): não houve inspeção visual. Os testes não gravaram na base da clínica; sem commit.

- Origem: usuário solicita pacientes semanais/quinzenais automaticamente na agenda do profissional, com horário indisponível até mudança ou anotação de fim do tratamento.
- Diagnóstico inicial: existiam somente agendamentos avulsos e vínculos de reagendamento. Foram adicionadas regras persistentes e seus vínculos com as sessões. O perfil psicólogo com permissão `agenda:gerenciar` cria/consulta/gera/altera/encerra apenas a própria recorrência; profissional sem vínculo recebe 403. A agenda avulsa também passou a negar consulta de profissional sem vínculo. Isso não conclui a revisão geral SEG-02.
- Interface entregue: **Não repetir / Semanal / Quinzenal (a cada 14 dias)** no novo agendamento. A primeira sessão determina o dia da semana e o horário em America/Sao_Paulo, sem término obrigatório. Duração de 50 minutos no formulário; API aceita de 1 a 1440 minutos inteiros. Interpretação usa `zoneinfo`/tzdata no backend e os helpers de AGE-03 no frontend.
- A reserva é verificada contra atendimentos e contra padrões recorrentes, independentemente da existência de sessões geradas. Quinzenas alternadas podem coexistir; intervalos adjacentes são permitidos. Validação de padrões usa o ciclo comum de 14 dias e considera exceções existentes. A regressão cobre conflito dez anos à frente, ainda fora do horizonte materializado.
- Materialização: criação gera 90 dias a partir da primeira sessão; ao abrir/atualizar a agenda, usuário com `agenda:gerenciar` aciona POST de geração para os próximos 90 dias a partir de agora. GETs não gravam. Não há serviço agendador externo nesta entrega. A reserva virtual continua bloqueando além dos 90 dias; geração só adiciona sessões futuras, sem inventar sessões passadas durante eventual período sem acesso. Usuário com apenas consulta vê o que já foi gerado.
- Cada ocorrência tem vínculo único regra/início e agendamento único. Geração repetida preserva cancelamentos/faltas e não cria receita. Cadastro inativo não expande as sessões, mas mantém a reserva até encerramento; é possível encerrar mesmo com paciente/profissional inativo.
- **Cancelar só esta sessão** ou **Reagendar** afeta apenas a ocorrência, mantendo as seguintes. Cancelado/falta libera a exceção daquele dia. Reagendamentos pontuais continuam vinculados ao tratamento por sua cadeia auditável e são abrangidos por alteração/encerramento quando estiverem no período afetado.
- **Alterar próximas sessões** exige data efetiva futura, primeira sessão no novo horário igual/posterior a ela, frequência e motivo. Encerra a versão antiga, cancela sessões abertas abrangidas e cria uma versão ligada à anterior, tudo na mesma transação. Conflito desfaz inclusive cancelamentos já preparados. Só pode haver um sucessor para cada versão.
- **Encerrar recorrência** exige motivo; data vazia encerra agora, preenchida programa o encerramento futuro. Corte é inclusivo pelo início da sessão. Não apaga histórico nem registra alta clínica. Sessões passadas permanecem; havendo realizado, prontuário ou financeiro no período afetado, recusa com 409 e orienta escolher data posterior. Sessões canceladas pelo encerramento não podem reabrir/reagendar nesse período; se necessário, criar nova reserva avulsa.
- Concorrência: criação/geração/alteração/encerramento usam transação e travas de recursos; regras existentes são relidas sob trava e sessões alteradas são travadas. Reabertura/realização/reagendamento continuam usando os bloqueios de atendimento existentes. Conflitos transitórios podem retornar 409 para atualizar e tentar novamente, sem repetição automática.

### Arquivos, instalação e limites de AGE-04

- Novos: `backend/app/recorrencias.py`, `backend/app/routers/recorrencias.py`, três testes `backend/test_recorrencias*.py`, `frontend/src/components/RecorrenciasAgenda.tsx`.
- Alterados: backend `models.py`, `schemas.py`, `main.py`, `services.py`, `transacoes.py`, `validacao_agenda.py`, router de agendamentos e `requirements.txt`; frontend `api.ts`, `types.ts`, `pages/Agenda.tsx`; AGENTS, README e acompanhamento. Preservadas as alterações anteriores da sessão.
- Instalar requirements no ambiente usado para executar a API (tzdata já instalado no ambiente funcional da raiz). Reiniciar a API: na pasta backend, `..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000`. Inicialização cria `recorrencias_agenda` e `ocorrencias_recorrencia`; não adiciona colunas a `agendamentos` nem altera registros antigos. Criação idempotente em schema existente simulada e testada. Migrações formais permanecem OPS-01; não houve migração manual na base em uso.
- Rotas novas: `GET/POST /api/recorrencias`, `POST /api/recorrencias/gerar`, `POST /api/recorrencias/{id}/alterar` e `/encerrar`; permissões de agenda existentes. JSON/JWT testados via ASGI, sem servidor de rede/lifespan. Nenhum teste executou seed no banco real.
- Limites: PostgreSQL real, transporte HTTP pela rede, navegação visual, lint/CI e implantação externa não validados. Sem feriados, férias ou pausa em lote nesta etapa; usar exceção de sessão ou encerrar/alterar a sequência. Regras de fuso seguem os dados IANA instalados; atualizar tzdata se a legislação temporal mudar. O nome interno `psicologo` foi preservado, sem criar novos perfis ou categorias profissionais.

### Conferência manual de AGE-04 (pendente)

1. Reiniciar a API e atualizar o frontend com Ctrl+F5. Entrar com cargo que gerencie agenda; profissional logado deve ter vínculo cadastrado e só pode escolher a si mesmo.
2. Em Novo agendamento, escolher uma terça-feira futura e **Semanal**. Conferir a regra no painel e as sessões seguintes; tentar ocupar o mesmo horário para outro paciente, inclusive em data além dos 90 dias: deve recusar.
3. Cancelar/reagendar somente uma sessão e conferir que as seguintes permanecem. Em uma sequência quinzenal, conferir intervalos de 14 dias e a possibilidade de outra reserva na semana alternada.
4. Usar **Alterar próximas sessões**, informando corte, novo horário e motivo. Conferir a versão anterior no histórico e a nova sequência; testar conflito para confirmar que a sequência anterior permanece íntegra.
5. **Encerrar recorrência**, com motivo e data vazia para agora (ou futura para programar). Conferir a liberação futura, preservação de sessões passadas e impossibilidade de reabrir as canceladas pelo encerramento. Encerramento não gera alta clínica.

## AGE-03 — aviso e referência temporal

- Usuário relatou conseguir selecionar 23/10/2026 19:50 quando esse horário já estava passado. O formulário anterior não mostrava erro junto ao campo: apenas desabilitava o envio para valores que o relógio local considerava vencidos.
- O código de backend já exige futuro e os testes de AGE-02 confirmam a rejeição; a ocorrência exata da sessão do usuário não foi reproduzida. Não atribuir causa definitiva a fuso, relógio ou versão sem evidência.
- Inspeção do ambiente: sistema em Brasília (E. South America Standard Time) e relógio 23/10/2026 19:56 durante a investigação. Esse horário serve apenas como evidência desta verificação, não como constante da aplicação.
- Inventário de navegador/UI retornou vazio nesta sessão; não afirmar inspeção visual. Node disponível: 24.21.0, permite testes de funções TypeScript pelo runner nativo, sem instalar pacotes.
- Implementado: aviso visível/associado ao campo em criação e reagendamento, datas interpretadas em America/Sao_Paulo, relógio obtido da API e revalidado antes de enviar. Na ausência da referência temporal, a reserva fica bloqueada, com aviso e opção de atualizar o horário.
- A referência avança a cada segundo com relógio monotônico, ressincroniza a cada 30 segundos e ao voltar à página; expira após 60 segundos sem atualização. Inclui a latência da consulta conservadoramente. Relógio/fuso do dispositivo não determinam a validade da reserva. A API mantém a validação final na gravação.
- O seletor recebe limite mínimo no próximo minuto. Mesmo que o navegador permita digitar/selecionar um valor anterior, o aviso aparece e o envio fica bloqueado; o formulário aberto também detecta quando a seleção vence.

| Comando/verificação | Resultado | Situação |
|---|---|---|
| Frontend: `npm.cmd run test:horarios` (Node 24.21.0) | 16/16 aprovados: 19:50 vencido às 19:56, minuto atual, futuro, virada do dia, datas inválidas, formulário envelhecido, diferentes fusos/relógio do dispositivo e referência ausente/expirada. | Funções temporais aprovadas; não é teste de interação React/navegador. |
| Frontend: `npm.cmd run build` | TypeScript e Vite aprovados; 106 módulos. | Build completo aprovado. |
| Backend: `..\.venv\Scripts\python.exe -m unittest -q test_relogio_agenda test_reagendamento test_agenda test_agenda_concorrencia test_financeiro test_status_agendamento test_transacoes test_concorrencia test_schema_financeiro` | 126/126 aprovados, incluindo relógio UTC com fuso explícito e rejeição de 19:50 em Brasília quando o servidor está às 19:56. Avisos preexistentes de utcnow permanecem em DAT-01. | AGE-03 aprovado no escopo automatizado; bancos isolados. |

- Arquivos: `frontend/src/agendaHorarios.ts`, `context/useRelogioAgenda.ts`, `pages/Agenda.tsx`, `api.ts`, `tests/agenda-horarios.test.mjs`, `package.json`; backend `app/routers/agendamentos.py`, `app/schemas.py`, `test_relogio_agenda.py`; AGENTS, README e acompanhamento.
- Sem alteração de schema nesta etapa. Reiniciar a API para expor `GET /api/agendamentos/relogio` (permissão `agenda:consultar`) e atualizar o frontend. Não foram gravados agendamentos no banco da clínica durante os testes.
- Limites: sem inspeção visual (nenhum navegador conectado), sem fluxo HTTP/JWT completo, sem reprodução do envio exato relatado. PostgreSQL e implantação externa permanecem pendentes. SEG-01 não iniciado.
- Revisão final: `git diff --check` aprovado (saída 0); apenas avisos de normalização LF/CRLF. Documentos atualizados, sem commit.

## AGE-02 — regra temporal e reagendamento

- Nova orientação do usuário substitui a decisão anterior de AGE-01 que aceitava novas reservas passadas. Novo agendamento deve começar estritamente depois do instante atual.
- Uma consulta cujo início passou não pode voltar a agendado/confirmado, nem ter o horário antigo sobrescrito por PATCH para contornar essa regra. Reagendamento cria outro atendimento futuro, mantendo o original.
- Exemplo de aceite: criado em 15/10, marcado para 22/10/2026 às 19h e cancelado em 21/10; no dia 23/10 não pode reabrir, mas pode originar outro agendamento futuro.
- Manter permitidos realização/falta/cancelamento e evolução clínica de atendimentos passados, conforme as regras clínicas/financeiras já existentes. Não bloquear o lançamento posterior de um atendimento que realmente ocorreu.
- Reagendamento exige permissão de agenda, profissional próprio quando aplicável, cadastros ativos, horário futuro e disponibilidade. Não permitir por esse fluxo em realizado, com prontuário, histórico financeiro automático ou reagendamento anterior.
- O vínculo persistirá original, novo atendimento, autor e data. Um original poderá gerar somente um sucessor; reagendamentos posteriores deverão partir do sucessor.

| Teste/verificação | Resultado | Situação |
|---|---|---|
| Backend: `..\.venv\Scripts\python.exe -m unittest -q test_reagendamento`, antes da correção | 14 testes: 6 falhas de asserção (com subtestes) e 7 erros pelas ações/metadados de reagendamento ainda ausentes. Reproduzida reabertura vencida e reserva no passado. | AGE-02 em andamento; comportamento anterior comprovado. |
| Backend: mesmo comando após implementação inicial | 14/14 passaram: exemplo informado, recusa de novas reservas passadas/agora, reabertura futura, reagendamento vinculado, unicidade do sucessor, preservação do histórico e bloqueios clínicos/financeiros. | Backend inicial validado; complementar interface, falhas e concorrência. |
| Backend: `..\.venv\Scripts\python.exe -m unittest -q test_reagendamento test_agenda test_agenda_concorrencia test_financeiro test_status_agendamento test_transacoes test_concorrencia test_schema_financeiro` | 107/107 passaram. Fixtures anteriores passaram a controlar o relógio ou usar datas futuras para não depender do dia/hora de execução; asserções de negócio foram preservadas. | Regressões aprovadas; complementar rollback e concorrência do novo fluxo. |
| Frontend: `npm.cmd run build` após formulário e expiração dos botões | TypeScript e Vite aprovados; 104 módulos. | Interface compilável; sem inspeção visual no navegador. |
| Backend: `..\.venv\Scripts\python.exe -m unittest -q test_reagendamento test_agenda_concorrencia` após complementos | 39/39 passaram: 27 de vencimento/reagendamento e 12 de reservas concorrentes. Inclui rollback após flush do vínculo, expiração exata, falha durante espera, cadeia de sucessores, schema não destrutivo e dois processos reagendando o mesmo original. | Novos cenários aprovados; revisão conjunta final em andamento. |
| Backend: comando completo com `test_reagendamento test_agenda test_agenda_concorrencia test_financeiro test_status_agendamento test_transacoes test_concorrencia test_schema_financeiro` | 123/123 passaram. Nenhum dado real utilizado; avisos preexistentes de utcnow continuam em DAT-01. | AGE-02 concluído no escopo automatizado. |
| `git diff --check` e revisão das ações, modelo e serviços | Passou sem erros de espaços em branco; aviso de normalização LF/CRLF no HTML de UX-03. | Código revisado; documentação final atualizada em seguida. |

### Comportamento entregue

- O backend rejeita início passado ou igual ao instante atual em TODO novo POST de agendamento, independentemente do status enviado (422). Valida novamente depois de adquirir as travas, pois o horário pode vencer enquanto aguarda.
- O backend recusa voltar um horário vencido para agendado/confirmado e recusa substituir a reserva vencida por PATCH, mesmo se o cliente enviar outra data futura (409). Deve-se usar o endpoint de reagendamento, mantendo o original.
- A API de agenda informa `pode_reabrir`, `pode_reagendar`, `reagendado_de_id` e `reagendado_para_id`. O formulário usa essas ações. A comparação inicial com o relógio do navegador foi substituída em AGE-03 por referência da API, atualizada a cada segundo e revalidada no envio.
- Reabrir permanece permitido ANTES do início, sem prontuário/financeiro/reagendamento anterior. Exatamente no início ou depois, o botão desaparece e a API recusa a ação. Confirmar também deixa de aparecer para reservas vencidas.
- O botão **Reagendar** abre nova data/hora futura para o mesmo paciente/profissional. A interface mantém a duração anterior positiva; usa 50 minutos caso um legado tenha duração inválida. O backend verifica intervalo, cadastros ativos, permissão e conflitos normalmente.
- `POST /api/agendamentos/{id}/reagendar` recebe início/fim e cria outro agendamento com status agendado. Cancelado e falta mantêm seu status original; agendado/confirmado são cancelados na mesma transação. Datas e criação do original não são alteradas.
- A tabela nova `reagendamentos` guarda original, sucessor, autor e data. Original e sucessor são únicos no vínculo; dois pedidos simultâneos só criam um sucessor. Se houver novo reagendamento, partir do sucessor, formando cadeia.
- Com prontuário, realizado ou histórico financeiro automático, o reagendamento vinculado é bloqueado neste fluxo. Para outro atendimento nesses casos, criar um novo agendamento independente, preservando os bloqueios clínicos/financeiros existentes.
- Os vínculos de reagendamento impedem reativar ou mudar a reserva de um original já substituído; a manutenção textual continua possível. Nenhum lançamento financeiro é gerado apenas por reagendar.
- Realização tardia, falta, cancelamento e evolução clínica continuam disponíveis para registrar atendimentos passados, segundo as regras anteriores. O seed de demonstração continua criando histórico fictício internamente; essa exceção não é um endpoint público de reserva passada.

### Arquivos, execução e limites

- Backend: `app/models.py`, `app/schemas.py`, `app/horarios.py`, `app/validacao_agenda.py`, `app/transacoes.py`, `app/services.py` e `app/routers/agendamentos.py`. A listagem carrega as relações adicionais em lote.
- Frontend: `src/pages/Agenda.tsx`, `src/types.ts`, `src/api.ts`. Campos datetime-local exigem próximo minuto futuro; o envio também valida o instante atual, e os conflitos são exibidos com a mensagem da API.
- Novo teste: `backend/test_reagendamento.py` (27). `test_agenda_concorrencia.py` passou a 12 testes. Fixtures de agenda/transações/status controlam o relógio e fixtures de processos usam datas relativas futuras; não foram retiradas as asserções anteriores.
- Comando na pasta backend: `..\.venv\Scripts\python.exe -m unittest -q test_reagendamento test_agenda test_agenda_concorrencia test_financeiro test_status_agendamento test_transacoes test_concorrencia test_schema_financeiro`.
- Reiniciar a API para a inicialização do protótipo criar a tabela adicional `reagendamentos`. A criação não altera os campos antigos e foi testada preservando o original. Não foi aplicada migração manual ao banco existente; com reload ativo, a inicialização poderá executá-la automaticamente.
- Atualizar a página. Conferência manual sugerida: consulta cancelada de 22/10/2026 19h, com relógio já posterior ao início, deve mostrar **Reagendar**, sem **Reabrir como agendado**. Escolher um horário futuro deve criar uma nova linha e manter a anterior como cancelada/reagendada.
- A API foi exercitada por chamadas às funções reais com sessões isoladas; os testes de disputa incluem dois processos independentes. Não houve validação visual nem HTTP/JWT ponta a ponta. Integração com outro banco e migrações formais seguem em OPS-01/QUA-01.
- O registro histórico de cancelamento simples ainda não possui data/autor próprios além dos dados que o sistema já guardava; esta etapa acrescenta autoria/data do REAGENDAMENTO e preserva o original, sem inventar eventos antigos.
- AGENTS/README/acompanhamento atualizados. Sem commit. SEG-01 não foi iniciado.

## AGE-01 — entrega e validações

- Fim deve ser posterior ao início, na criação e considerando o estado final de um PATCH parcial.
- Intervalos são [início, fim): adjacentes são permitidos. Agendado, confirmado e realizado ocupam horário; cancelado e falta liberam.
- Bloquear sobreposição tanto do profissional quanto do paciente, inclusive com profissional/paciente diferentes no outro lado do vínculo. Excluir o próprio atendimento na edição.
- Exigir vínculos existentes/ativos em novos agendamentos, trocas de vínculos/horários e transições que voltem ou avancem para horário ocupado. Não impedir cancelamento/falta nem manutenção textual do histórico só porque um cadastro foi inativado.
- Adquirir bloqueios de profissional e paciente, em ordem consistente, antes de verificar conflitos e gravar. Isso deve impedir dois POSTs simultâneos de reservarem o mesmo recurso/horário.
- Normalização mínima necessária: comparar e armazenar novos instantes em UTC, mantendo o armazenamento sem fuso atual. Datas antigas sem fuso são tratadas como UTC, sem migração destrutiva. A revisão completa de dias/meses/timezone permanece em DAT-01.

| Teste/verificação | Resultado | Situação |
|---|---|---|
| Backend: `..\.venv\Scripts\python.exe -m unittest -v test_agenda`, antes da correção | 21 testes executados: 26 falhas de asserção (incluindo subtestes). Reproduzidos fim inválido, conflitos, vínculos ausentes/inativos, PATCH parcial inválido e datas sem identificação/conversão de fuso. | AGE-01 em andamento, defeitos reproduzidos. |
| Backend: `..\.venv\Scripts\python.exe -m unittest -v test_agenda test_financeiro test_status_agendamento test_transacoes test_concorrencia test_schema_financeiro`, após implementação inicial | 75/75 passaram: 21 novos e 54 regressões. Fixtures de status passaram a usar horários distintos para testar transições sem criar conflitos artificiais. | AGE-01 implementado; faltam disputas simultâneas de criação/reagendamento e validação da interface. |
| Backend: `..\.venv\Scripts\python.exe -m unittest -v test_agenda test_agenda_concorrencia` | 39/39 passaram: 30 regras de agenda + 9 disputas de reservas, incluindo dois processos, edição/criação/reabertura concorrentes e inativação antes de reservar. | Regras e concorrência de AGE-01 aprovadas; executar verificação conjunta final. |
| Frontend: `npm.cmd run build`, após ajustes do formulário | TypeScript e Vite aprovados; 104 módulos. | Build completo aprovado; sem inspeção visual no navegador. |
| Backend: `..\.venv\Scripts\python.exe -m unittest -q test_agenda test_agenda_concorrencia test_financeiro test_status_agendamento test_transacoes test_concorrencia test_schema_financeiro` | 93/93 passaram: 39 de agenda + 54 regressões financeiras, clínicas, transacionais e de schema. Inclui processos independentes, intervalos adjacentes, offsets, meia-noite, PATCH parcial, rollback e preservação de histórico. | AGE-01 concluído no escopo automatizado. Avisos de utcnow permanecem em DAT-01. |
| `git diff --check` e revisão dos módulos, schemas e formulário | Passou sem erros de espaços em branco; aviso de normalização LF/CRLF no HTML de UX-03. | Entrega revisada; documentação final atualizada em seguida. |

### Regras atuais e respostas da API

| Operação | Validação |
|---|---|
| Criar, inclusive já realizado/cancelado/falta | IDs positivos, vínculos existentes/ativos e fim posterior ao início. Sobreposição é verificada se o status ocupa horário. |
| Editar paciente/profissional/início/fim | Avaliar os campos enviados junto aos que já estão armazenados; preservar as restrições históricas de FIN-02. |
| Confirmar, realizar ou reabrir como agendado | Conferir vínculos ativos e conflitos de horário sob trava. Reabrir com histórico financeiro continua proibido por FIN-02. |
| Cancelar ou marcar falta sem mudar a reserva | Não exigir reativação cadastral nem impedir a saída de um legado inválido/conflitante. As restrições de prontuário e estorno continuam valendo. |
| Repetir realizado ou alterar apenas observação | Preservar o histórico; não exigir reativação de cadastro antigo nem refazer validação de reserva sem mudança. O financeiro continua sendo verificado por FIN-03. |

- Retornos: 422 para intervalo inválido/vínculo inexistente/ID não positivo/nulo; 409 para conflito de horário ou cadastro inativo. Não expor nomes de outros pacientes nas mensagens de conflito.
- `inicio_outro < fim_novo` e `fim_outro > inicio_novo` definem a sobreposição, excluindo o próprio agendamento. Os dois lados da comparação usam a convenção UTC do banco.
- Ao reservar, a API trava primeiro o profissional e depois o paciente por UPDATE que mantém o valor de `ativo`, sem mudar os cadastros. A trava permanece até commit/rollback. A atividade é relida do banco, sem depender do cache da sessão.
- POSTs distintos e PATCHes disputando o mesmo recurso/intervalo agora têm apenas um vencedor; o outro recebe 409. Reservas de recursos diferentes e intervalos adjacentes permanecem permitidos.
- A decisão inicial de AGE-01 de aceitar novas reservas passadas foi substituída pela regra do usuário em AGE-02: novos agendamentos/reagendamentos exigem futuro. Não foi criada duração mínima/máxima; o formulário de novo agendamento mantém 50 minutos.

### Horários e interface

- `backend/app/horarios.py` converte entradas com offset para UTC sem fuso no armazenamento. Exemplo: 10h com -03:00 corresponde a 13h UTC. Não há alteração de datas já armazenadas.
- `AgendamentoRead` identifica início/fim como UTC nas respostas, inclusive em relatórios e prontuário que reutilizam esse schema. O navegador pode então mostrar corretamente o horário local. Os filtros temporais da listagem de agenda também normalizam offsets.
- Entradas sem offset e registros antigos sem fuso continuam sendo interpretados como UTC. Não presumir retrospectivamente que representavam horário de São Paulo. Padronização do fechamento do dashboard/relatórios e demais timestamps permanece em DAT-01.
- Novo agendamento na interface mostra somente pacientes e profissionais ativos. O filtro de visualização da equipe mantém os profissionais inativos para consultar histórico. Envio é desabilitado enquanto salva; mensagens de conflito da API são exibidas.
- A edição de horário/vínculos foi validada pela API; o formulário de reagendamento foi entregue depois, em AGE-02. Demais telas completas de edição e conferência visual continuam em UX-01.

### Arquivos, reprodução e limites

- Novos módulos: `backend/app/horarios.py`, `backend/app/validacao_agenda.py`. Integração em `app/services.py`, `app/routers/agendamentos.py` e `app/schemas.py`.
- Frontend: `frontend/src/pages/Agenda.tsx`. Documentos: AGENTS, README e acompanhamento.
- Novos testes: `backend/test_agenda.py` (30) e `backend/test_agenda_concorrencia.py` (9). Ajuste de fixture em `test_status_agendamento.py` para separar os horários de atendimentos independentes, preservando a matriz de 25 transições e suas asserções.
- Comando completo na pasta backend: `..\.venv\Scripts\python.exe -m unittest -q test_agenda test_agenda_concorrencia test_financeiro test_status_agendamento test_transacoes test_concorrencia test_schema_financeiro`.
- Testes usaram bancos em memória e arquivos temporários/WAL, incluindo sessões/processos independentes. Não houve uso do banco da clínica pelos testes nem alteração manual do banco existente. Não houve novo schema nesta etapa.
- Reiniciar a API e atualizar a página para conferir manualmente: tentar sobrepor outro paciente no mesmo profissional, tentar o mesmo paciente com outro profissional, depois tentar um horário exatamente adjacente. Os dois primeiros devem ser recusados e o terceiro aceito.
- Não executados: inspeção visual no navegador, transporte HTTP/JWT e integração com outro banco. A validação foi feita no SQLite atual; os testes do banco de futura hospedagem ficam em OPS-01/QUA-01.
- Scripts externos/SQL direto ou caminhos internos que ignorem o protocolo de trava não têm proteção de sobreposição por constraint de banco. Os endpoints de criação e atualização usam o protocolo; não introduzir novos caminhos de escrita que o contornem.
- Histórico legado conflitante não foi alterado automaticamente. Cancelamento/falta e manutenção textual continuam disponíveis dentro das demais regras; novas reservas/reações de status precisam respeitar a disponibilidade.
- Sem commit. Próxima etapa SEG-01 depende da confirmação do usuário.

## FIN-03 — entrega e validações

- Estratégia: uma transação para criar/realizar e faturar; preparação de lançamentos sem commit interno; trava de escrita no atendimento compartilhada entre agenda, cancelamento e evolução; releitura após adquirir a trava.
- SQLite usa bloqueio de escrita do banco; PostgreSQL usa bloqueio da linha, obtido por UPDATE sem alterar seus valores. Em conflito transitório/timeout, rollback e resposta 409 para repetir a operação, sem repetição automática de efeitos.
- Chave automática nullable com índice único por atendimento/chave. Atualização de schema preserva lançamentos antigos e preenche apenas originais reconhecidos e estornos vinculados; duplicação preexistente identificada deve bloquear inicialização para revisão, nunca ser apagada automaticamente.

| Teste/verificação | Resultado | Situação |
|---|---|---|
| Backend: `..\.venv\Scripts\python.exe -m unittest -v test_transacoes`, antes da correção | 4/4 falharam: status realizado persistia após falha financeira, criação deixava atendimento sem financeiro, realização usava dois commits e seed persistia parcialmente. | FIN-03 em andamento, defeitos reproduzidos. |
| Backend: `..\.venv\Scripts\python.exe -m unittest -v test_financeiro test_status_agendamento test_transacoes`, após atomicidade/bloqueio | 33/33 passaram: regressões FIN-01/02 e quatro cenários de atomicidade, incluindo falha após flush. | FIN-03 em andamento; faltam testes de corrida, atualização de schema e unicidade direta. |
| Backend: `..\.venv\Scripts\python.exe -m unittest -v test_concorrencia test_schema_financeiro` | 15/15 passaram: seis realizações simultâneas, dois processos independentes, duplo cancelamento/evolução, corridas com prontuário/troca de profissional/PATCH sem status, timeout 409 com nova tentativa, schema legado/idempotência e índice único. | SQLite temporário/WAL e bancos em memória validados. Complementar inicialização real do lifespan e ordenação determinística das corridas clínicas. |
| Backend: `..\.venv\Scripts\python.exe -m unittest -v test_financeiro test_status_agendamento test_transacoes test_concorrencia test_schema_financeiro` | 54/54 passaram: 10 financeiros + 19 status/estorno + 6 transações + 12 concorrência + 7 schema. Inclui as duas ordens determinísticas cancelamento/evolução, rollback da evolução e lifespan real sobre schema antigo com dois reinícios sem duplicação. | FIN-03 concluído no SQLite. Avisos preexistentes de utcnow permanecem em DAT-01. |
| `git diff --check` e revisão dos serviços, rotas, seed e novos módulos | Passou sem erros de espaços em branco. Apenas aviso de normalização LF/CRLF no HTML alterado em UX-03. | Entrega revisada; documentação final atualizada em seguida. |

### Comportamento atual

- POST de atendimento já realizado, PATCH para realizado e carga inicial gravam atendimento e par receita/repasse na mesma transação. Se a preparação ou gravação financeira falhar, não sobra realizado sem lançamentos nem criação parcial.
- `transacao()` em `backend/app/transacoes.py` é responsável pelo commit/rollback. `criar_lancamentos_agendamento_realizado()` SOMENTE prepara lançamentos: quem chamar deve possuir a trava do atendimento ou tê-lo inserido na transação atual; não chamar isoladamente esperando commit.
- `bloquear_agendamento()` executa UPDATE sem alterar valores e relê a linha/relacionamentos. Todos os PATCHes e registros de evolução passam pela mesma trava no banco, que funciona entre sessões/processos. Autoriza-se o profissional depois da releitura do vínculo atual.
- PATCH sem status usa o status relido sob trava, evitando desfazer uma realização concorrente. Estornos e evolução clínica não podem ser gravados com validações feitas sobre estados antigos.
- Chaves `receita` e `repasse` identificam o par original; `estorno:<id-original>` identifica cada compensação. O índice único `uq_lancamento_chave_automatica` sobre atendimento/chave impede repetições com essas chaves mesmo em gravação SQL direta. Receitas manuais continuam sem chave e podem coexistir.
- Históricos automáticos incompletos/inconsistentes retornam 409 ao tentar realizar novamente, em vez de completar/recalcular silenciosamente um histórico incerto. Um legado realizado sem nenhum lançamento pode ser faturado ao repetir realizado; um par parcial exige revisão.
- Conflitos de integridade, timeout de escrita SQLite e erros transitórios PostgreSQL identificados retornam 409 após rollback. O cliente deve atualizar a tela e tentar novamente; não há repetição automática da operação. A sessão é reutilizável após rollback.

### Atualização do banco existente

1. Reiniciar a API com o ambiente funcional da raiz. A inicialização chama `atualizar_schema_financeiro()` depois de criar as tabelas ausentes e antes de seed/abertura da aplicação.
2. A atualização adiciona somente `lancamentos_financeiros.chave_automatica VARCHAR(64)` nullable e o índice único. Preenche as chaves de originais reconhecidos pela assinatura do gerador antigo e de compensações vinculadas em `estornos_financeiros`.
3. Valores, descrições, datas, autores e vínculos financeiros são preservados. Receita manual, parcela duplicada legada e automático de descrição desconhecida não recebem classificação inferida. Origens externas/desconhecidas requerem revisão própria.
4. A atualização é idempotente e usa transação de escrita no SQLite; no PostgreSQL há advisory lock específico para serializar esta atualização entre workers. Migração formal/Alembic e provisionamento concorrente de schema vazio permanecem em OPS-01.
5. Se houver mais de um original reconhecido do mesmo tipo/atendimento, a inicialização é interrompida com os IDs dos atendimentos. Não apagar registros para liberar a inicialização; investigar e definir correção rastreável. Os testes confirmaram bloqueio antes de alterar a tabela financeira ou executar seed nesse caso.
6. Não execute scripts antigos geradores (`backend/_gen_backend.py`) para reparar arquivos: eles contêm versões anteriores às correções e podem sobrescrevê-las.

### Arquivos e limites da validação

- Implementação: `backend/app/services.py`, `routers/agendamentos.py`, `routers/prontuario.py`, `models.py`, `seed.py`, `main.py`; novos `transacoes.py` e `schema_financeiro.py`.
- Novos testes: `backend/test_transacoes.py`, `backend/test_concorrencia.py`, `backend/test_schema_financeiro.py`. Os outros testes permanecem como regressão.
- Concorrência exercitada em arquivo SQLite temporário com WAL, conexões independentes e foreign_keys habilitado nos testes; inclui seis threads e dois processos spawn. Bases são removidas após os testes. Nenhum teste usa o banco da clínica.
- Lifespan/startup testado com engine e SessionLocal substituídos por bancos isolados. Não se iniciou servidor nem se aplicou manualmente a atualização ao banco existente durante a validação. Se houver dev server com reload ativo, ele poderá executá-la ao recarregar o código.
- Não validados nesta entrega: PostgreSQL real, transporte HTTP/JWT, interface manual, implantação externa e geração de schema vazio por vários workers ao mesmo tempo. PostgreSQL exige teste de integração antes de produção (OPS-01/QUA-01).
- O frontend não mudou nesta etapa; não foi repetido o build já aprovado em UX-03. Lint/CI continuam em QUA-02.
- Não há chave de idempotência para repetir um POST de criação: dois POSTs independentes ainda podem criar agendamentos diferentes. FIN-03 protege o faturamento do MESMO atendimento; conflitos de horários/duplicação de agenda são AGE-01.
- A garantia do índice aplica-se às chaves preenchidas pelo sistema. Alterações externas por SQL que omitam essas chaves não são uma API suportada; histórico não reconhecido é preservado para revisão, sem classificação arbitrária.
- AGENTS, README e acompanhamento atualizados; sem commit. Antes de AGE-01, solicitar confirmação do usuário.

## UX-03 — rótulo alterado na exibição

- A captura enviada pelo usuário mostra “Motivo do tells”. A inspeção do código confirmou `Motivo do cancelamento`, sem ocorrência de `tells` nos fontes da interface.
- Encontrado `lang="en"` no HTML apesar de a interface estar em português. Tradução automática do navegador/extensão é uma hipótese consistente, mas não foi confirmada por inspeção da sessão do navegador do usuário.
- Correção: `lang="pt-BR" translate="no"` na raiz do documento. O label de motivo também possui `translate="no"` e associação explícita ao textarea por `htmlFor`/`id`.
- Arquivos: `frontend/index.html`, `frontend/src/pages/Agenda.tsx`, AGENTS, README e acompanhamento. FIN-03 não foi iniciado.

| Verificação | Resultado | Situação |
|---|---|---|
| Leitura UTF-8 via PowerShell do HTML e do campo de motivo; `git diff --check` | Idioma pt-BR, translate=no, rótulo correto e associação label/textarea confirmados; sem erros no diff. Aviso de normalização LF/CRLF do Git, sem falha. | Código validado; build em execução no momento desta verificação. |
| Na pasta frontend: `npm.cmd run build`, fora do sandbox | Passou: TypeScript e Vite; 104 módulos. | UX-03 concluído no escopo de código/build. Recarregar com Ctrl+F5; extensão/tradução já aplicada no navegador pode exigir desativação pelo usuário. Sem inspeção visual na sessão do usuário. |

## FIN-02 — entrega e regras implementadas

### Validações desta etapa

| Comando/verificação | Resultado | Situação |
|---|---|---|
| Na pasta backend: `..\.venv\Scripts\python.exe -m unittest -v test_status_agendamento` antes da implementação | 12 testes executados: 25 falhas de asserção (incluindo subtestes) e 1 erro pela ausência do modelo de estorno. Reproduzidas transições indevidas, falta de permissão/motivo e alteração de vínculos históricos. O teste de falha de gravação passou, mas será reforçado para simular flush antes da falha. | FIN-02 em andamento, defeitos reproduzidos. |
| Na pasta backend: `..\.venv\Scripts\python.exe -m unittest -v test_financeiro test_status_agendamento` após implementação | 22/22 testes passaram, incluindo 25 combinações de status, estorno exato após mudança de percentual, motivo/autor persistidos, prontuário preservado e rollback após flush seguido de falha. | FIN-02 implementado; complementar revisão de casos inconsistentes e integração. |
| Na pasta frontend: `.\node_modules\.bin\tsc.cmd -b` após formulário de cancelamento | Passou, código de saída 0. | Interface compilável. Inspeção no navegador ainda pendente. |
| Na pasta backend: mesmo comando das duas suítes, após complementos | 29/29 testes passaram (10 financeiros e 19 de status/estorno). Novos cenários: histórico incompleto/ausente, bloqueio de vínculos após estorno, consulta filtrada, estorno em mês posterior, reabertura sem financeiro e inclusão não destrutiva da tabela em schema antigo simulado. | Critérios automatizados de FIN-02 aprovados; revisão final em andamento. |
| Na pasta frontend: `.\node_modules\.bin\tsc.cmd -b` após indicador de histórico financeiro | Passou, código de saída 0. | Botão de reabertura ocultado para histórico financeiro; tipagem aprovada. |
| Na pasta frontend: `npm.cmd run build`, fora do sandbox que bloqueava o Vite | Passou: TypeScript e Vite, 104 módulos, bundle gerado. | Build completo aprovado. QUA-02 continua aberto para lint/CI. |
| `git diff --check` e revisão do diff/status após implementação | Passou, sem erros de espaços em branco; revisados campos, permissões, formulário e schema. | FIN-02 concluído; documentos de entrega atualizados em seguida. |

- Agendado/confirmado podem alternar entre si ou encerrar como realizado, cancelado ou falta. Repetir o mesmo status é idempotente.
- Cancelado/falta sem histórico financeiro automático podem voltar apenas a agendado. Após cancelamento financeiro, o agendamento não reabre: criar outro para uma nova sessão.
- Realizado só pode permanecer realizado ou ir a cancelado. Cancelar exige `financeiro:gerenciar`, motivo não vazio e ausência de prontuário.
- Estornos são lançamentos negativos do mesmo tipo e valor dos originais, com vínculo persistido ao lançamento original, autor, data e motivo. Não apagar nem recalcular o original com percentuais atuais.
- Lançamentos manuais vinculados não serão estornados automaticamente. A parcela duplicada legada não é receita contabilizável; preservar e ignorar no estorno, assim como na soma do painel.
- Bloquear alterações de paciente/profissional/horários após realização ou quando já houver prontuário ou lançamentos automáticos. Validar tudo antes de persistir um PATCH misto.
- Estorno e cancelamento são atômicos. As garantias adicionais de concorrência/realização foram entregues em FIN-03 (ver seção atual acima).

### Transições

| Origem | Destinos permitidos |
|---|---|
| Agendado | Agendado, confirmado, realizado, cancelado, falta |
| Confirmado | Confirmado, agendado, realizado, cancelado, falta |
| Realizado | Realizado; cancelado somente com permissão financeira, motivo, histórico íntegro e sem prontuário |
| Cancelado | Cancelado; agendado somente sem histórico financeiro automático/prontuário |
| Falta | Falta; agendado somente sem histórico financeiro automático/prontuário |

Repetir o status não cria novos estornos. Um atendimento com prontuário não muda de status. Históricos financeiros automáticos incompletos, ausentes em um realizado ou inconsistentes retornam 409 no cancelamento e exigem revisão, sem correção silenciosa de dados legados.

### Como conferir

1. Reiniciar o backend pelo ambiente funcional da raiz. Na pasta `backend`: `..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000`.
2. A inicialização existente do protótipo (`Base.metadata.create_all`) cria a tabela nova `estornos_financeiros`, sem alterar colunas/tabelas antigas. O procedimento foi testado em schema antigo simulado em memória; não houve migração manual do banco existente. Migração formal com Alembic continua em OPS-01.
3. Atualizar o frontend. Entrar como sócia/admin (ou cargo com `agenda:gerenciar` e `financeiro:gerenciar`), selecionar um realizado SEM evolução e usar **Cancelar e estornar**. Informar motivo e confirmar no formulário.
4. Nos relatórios, os originais positivos permanecem e as compensações negativas aparecem. Na mesma competência, 220 e -220 / 132 e -132 totalizam zero. Se o estorno ocorrer em mês posterior, ele reduz o mês do cancelamento, preservando a data dos originais; os totais desse mês podem ser negativos. Revisão de competência/recebimentos continua em FIN-05.
5. Em `/docs`, consultar `GET /api/financeiro/estornos?agendamento_id=<id>` com usuário autorizado (`financeiro:consultar`) para verificar motivo, autor, data e IDs original/compensação. A consulta de auditoria não possui tela específica nesta etapa.
6. A tentativa de cancelar um atendimento com evolução deve retornar 409 e manter atendimento, prontuário e financeiro. Para realizado sem permissão financeira, retornar 403.

### Arquivos e limites

- Backend: `app/models.py`, `app/schemas.py`, `app/services.py`, `app/routers/agendamentos.py`, `app/routers/dashboard.py` e `app/routers/financeiro.py`. Filtro de parcela legada centralizado para uso no painel e nos estornos.
- Frontend: `src/pages/Agenda.tsx`, `src/api.ts`, `src/types.ts`. Motivo obrigatório, botões adequados ao status, indicação de histórico financeiro e mensagens textuais da API.
- Testes: `backend/test_status_agendamento.py` (19 testes, incluindo 25 combinações de status), além dos 10 testes de FIN-01. Banco SQLite em memória; sem seed/servidor e sem gravação no banco da clínica pelos testes.
- Documentos: AGENTS, README e este acompanhamento atualizados. Não foi criado commit.
- Não executados: fluxo visual no navegador, transporte HTTP/JWT de ponta a ponta, lint, implantação externa ou testes de concorrência. QUA-01/QUA-02/FIN-03 continuam abertos; não se trata de liberação para produção.
- Estado na entrega FIN-02: cancelamento/compensações usavam uma transação, mas realização tinha commits separados. Essa limitação foi corrigida em FIN-03, incluindo as corridas entre evolução, realização, cancelamento e alterações da agenda no SQLite. Integração PostgreSQL continua pendente.
- Histórico de status comum (sem operação financeira) ainda não tem auditoria persistente própria. Aqui a autoria/motivo auditáveis são dos estornos. Lançamentos manuais e a parcela duplicada legada ficam intactos.
- Reversão de estorno, correção de prontuário e cancelamento com evolução não são suportados por esse fluxo. Não apagar registros para contornar os bloqueios; evolução futura deve preservar rastreabilidade.
