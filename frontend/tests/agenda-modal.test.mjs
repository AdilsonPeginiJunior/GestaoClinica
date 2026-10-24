/** Chrome headless + Vite/CDP; nenhuma dependência de automação adicional. */
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdtemp, readFile, rm, mkdir, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { once } from "node:events";
import { createServer } from "vite";

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const chrome = process.env.CHROME_PATH || [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
].find(existsSync);
assert.ok(chrome, "Informe CHROME_PATH para executar o navegador headless.");
const perfil = await mkdtemp(path.join(tmpdir(), "clinica-modal-teste-"));
const server = await createServer({ root: raiz, server: { host: "127.0.0.1", port: 5197, strictPort: true, open: false } });
let navegador, socket;
const aguardar = ms => new Promise(resolve => setTimeout(resolve, ms));
let total = 0;
function verificar(condicao, mensagem) { assert.ok(condicao, mensagem); total++; console.log(`OK ${mensagem}`); }
try {
  await server.listen();
  navegador = spawn(chrome, ["--headless=new", "--no-first-run", "--no-default-browser-check", "--disable-background-networking",
    "--remote-debugging-port=0", `--user-data-dir=${perfil}`, "about:blank"], { windowsHide: true, stdio: "ignore" });
  let porta;
  for (let i = 0; i < 100; i++) {
    try { porta = Number((await readFile(path.join(perfil, "DevToolsActivePort"), "utf8")).split("\n")[0]); break; }
    catch { await aguardar(100); }
  }
  assert.ok(porta, "Chrome não iniciou o protocolo de teste.");
  const abas = await (await fetch(`http://127.0.0.1:${porta}/json/list`)).json();
  socket = new WebSocket(abas.find(a => a.type === "page").webSocketDebuggerUrl);
  await once(socket, "open");
  let id = 0;
  const pendentes = new Map();
  socket.addEventListener("message", e => {
    const r = JSON.parse(e.data);
    const p = pendentes.get(r.id);
    if (p) { pendentes.delete(r.id); r.error ? p.reject(new Error(JSON.stringify(r.error))) : p.resolve(r.result); }
  });
  const call = (method, params = {}) => new Promise((resolve, reject) => {
    const numero = ++id;
    pendentes.set(numero, { resolve, reject });
    socket.send(JSON.stringify({ id: numero, method, params }));
  });
  const avaliar = async expression => {
    const r = await call("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));
    return r.result.value;
  };
  const esperar = async expression => {
    for (let i = 0; i < 100; i++) { if (await avaliar(`Boolean(${expression})`)) return; await aguardar(50); }
    throw new Error(`Condição não atendida: ${expression}`);
  };
  const clicar = async texto => {
    const ponto = await avaliar(`(() => { const b = [...document.querySelectorAll('button')].find(b => b.textContent.trim() === ${JSON.stringify(texto)}); if (!b) throw Error('Botão ausente'); b.scrollIntoView({ block: 'center' }); const r = b.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 }; })()`);
    await call("Input.dispatchMouseEvent", { type: "mousePressed", ...ponto, button: "left", clickCount: 1 });
    await call("Input.dispatchMouseEvent", { type: "mouseReleased", ...ponto, button: "left", clickCount: 1 });
  };
  const tecla = async key => {
    const codigo = key === "Escape" ? 27 : 9;
    await call("Input.dispatchKeyEvent", { type: "rawKeyDown", key, code: key, windowsVirtualKeyCode: codigo, nativeVirtualKeyCode: codigo });
    await call("Input.dispatchKeyEvent", { type: "keyUp", key, code: key, windowsVirtualKeyCode: codigo, nativeVirtualKeyCode: codigo });
  };
  await call("Emulation.setDeviceMetricsOverride", { width: 1280, height: 850, deviceScaleFactor: 1, mobile: false });
  if (process.argv.includes("--escopo")) {
    await call("Page.navigate", { url: "http://127.0.0.1:5197/tests/agenda-modal.html?tela=pacientes&perfil=psicologo" });
    await esperar("document.querySelector('tbody tr')");
    verificar(await avaliar("document.body.textContent.includes('Pacientes vinculados à sua agenda')"), "Profissional recebe indicação do escopo de pacientes");
    verificar(await avaliar("![...document.querySelectorAll('button')].some(b => b.textContent.trim() === 'Novo paciente')"), "Cargo com gerenciar pacientes não oferece cadastro global ao profissional");
    await call("Page.navigate", { url: "http://127.0.0.1:5197/tests/agenda-modal.html?tela=pacientes&perfil=recepcionista" });
    await esperar("document.querySelector('tbody tr')");
    verificar(await avaliar("[...document.querySelectorAll('button')].some(b => b.textContent.trim() === 'Novo paciente')"), "Recepção autorizada mantém cadastro de novos pacientes");
    await call("Page.navigate", { url: "http://127.0.0.1:5197/tests/agenda-modal.html?perfil=psicologo" });
    await esperar("document.querySelector('.filtros select') && document.querySelectorAll('tbody tr').length === 2");
    verificar(await avaliar("document.querySelectorAll('.filtros select option').length === 2"), "Agenda não oferece outro profissional no filtro mesmo com catálogo amplo");
    await clicar("Novo agendamento");
    await esperar("document.querySelector('dialog #novo-horario')");
    verificar(await avaliar("document.querySelectorAll('dialog select')[1].options.length === 1"), "Novo agendamento permite somente o próprio profissional");
    verificar(await avaliar("document.querySelectorAll('dialog select')[1].value === '1'"), "Profissional vinculado é selecionado no formulário");
  } else if (process.argv.includes("--login")) {
    for (const [consulta, esperado, rotulo] of [
      ["ambiente=demo", 4, "Demonstração"],
      ["ambiente=production", 0, "Produção"],
      ["ambiente=demo&seed=false", 0, "Demo sem seed"],
      ["ambiente=erro", 0, "Configuração indisponível"],
      ["ambiente=malformado", 0, "Configuração inválida"],
      ["ambiente=inconsistente", 0, "Produção com flag demo inconsistente"],
    ]) {
      await call("Page.navigate", { url: `http://127.0.0.1:5197/tests/agenda-modal.html?tela=login&${consulta}` });
      await esperar("window.__configConsultada && document.querySelector('.login-card')");
      await avaliar("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))");
      verificar(await avaliar(`document.querySelectorAll('.demo-users button').length === ${esperado}`), `${rotulo}: atalhos demo conforme configuração da API`);
      verificar(await avaliar("!!document.querySelector('input[type=email]') && !!document.querySelector('input[type=password]')"), `${rotulo}: login manual permanece disponível`);
    }
    await call("Page.navigate", { url: "http://127.0.0.1:5197/tests/agenda-modal.html?tela=login&ambiente=aguardando" });
    await esperar("window.__resolverConfig && document.querySelector('.login-card')");
    verificar(await avaliar("!document.querySelector('.demo-users')"), "Configuração pendente não exibe credenciais demo");
    await avaliar("window.__resolverConfig()");
    await esperar("document.querySelectorAll('.demo-users button').length === 4");
    verificar(true, "Atalhos aparecem somente depois da confirmação de demo pela API");
  } else {
  await call("Page.navigate", { url: "http://127.0.0.1:5197/tests/agenda-modal.html" });
  await call("Page.bringToFront");
  await call("Emulation.setFocusEmulationEnabled", { enabled: true });
  await esperar("document.querySelectorAll('tbody tr').length === 2 && document.querySelector('button')");
  verificar(await avaliar("!document.querySelector('dialog')"), "Agenda começa sem painéis ou janela aberta");
  await clicar("Horários recorrentes");
  await esperar("document.querySelector('dialog:modal')");
  verificar(await avaliar("document.body.style.overflow === 'hidden'"), "Janela bloqueia rolagem do fundo");
  verificar(await avaliar("getComputedStyle(document.querySelector('.campo-checkbox')).flexDirection === 'row'"), "Checkbox e texto ficam na mesma linha");
  await tecla("Tab");
  verificar(await avaliar("document.querySelector('dialog').contains(document.activeElement)"), "Foco permanece na janela ao usar Tab");
  const artefatos = path.join(raiz, "tests/artifacts");
  if (process.argv.includes("--screenshots")) {
    await mkdir(artefatos, { recursive: true });
    const foto = await call("Page.captureScreenshot");
    await writeFile(path.join(artefatos, "ux04-recorrencias-desktop.png"), Buffer.from(foto.data, "base64"));
  }
  await avaliar("document.querySelector('.campo-checkbox input').click()");
  await esperar("document.querySelectorAll('dialog tbody tr').length === 2");
  verificar(true, "Mostrar encerradas inclui a sequência encerrada");
  await clicar("Alterar próximas sessões");
  await esperar("document.querySelector('#recorrencia-corte')");
  verificar(await avaliar("!document.querySelector('dialog table')"), "Edição da série ocupa a janela sem tabela abaixo");
  await clicar("Voltar");
  await esperar("document.querySelector('dialog table')");
  await tecla("Escape");
  await esperar("!document.querySelector('dialog')");
  verificar(await avaliar("document.activeElement.textContent.trim() === 'Horários recorrentes' && document.body.style.overflow !== 'hidden'"), "Escape fecha e devolve foco/rolagem à agenda");
  await clicar("Novo agendamento");
  await esperar("document.querySelector('dialog #novo-horario')");
  verificar(await avaliar("document.querySelector('dialog h3').textContent === 'Novo agendamento'"), "Novo atendimento abre em janela");
  await avaliar("document.querySelector('.modal-fechar').click()");
  await esperar("!document.querySelector('dialog')");
  await clicar("Cancelar e estornar");
  await esperar("document.querySelector('dialog #motivo-cancelamento')");
  verificar(true, "Cancelamento com estorno abre em janela sem enviar dados");
  await tecla("Escape");
  await esperar("!document.querySelector('dialog')");
  await clicar("Reagendar");
  await esperar("document.querySelector('dialog #nova-data-reagendamento')");
  const preencher = nome => avaliar(`(() => { const input = document.querySelector('#nova-data-reagendamento'); Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(input, window.${nome}); input.dispatchEvent(new Event('input', { bubbles: true })); })()`);
  await preencher("__passado");
  await esperar("document.querySelector('#reagendamento-horario-erro')");
  verificar(await avaliar("document.querySelector('dialog button[type=submit]').disabled"), "Horário vencido mantém aviso e bloqueio dentro da janela");
  await preencher("__futuro");
  await esperar("!document.querySelector('dialog button[type=submit]').disabled");
  await call("Emulation.setDeviceMetricsOverride", { width: 360, height: 740, deviceScaleFactor: 1, mobile: true });
  verificar(await avaliar("document.querySelector('dialog').getBoundingClientRect().width <= 352"), "Janela cabe em tela de 360 pixels");
  if (process.argv.includes("--screenshots")) {
    const foto = await call("Page.captureScreenshot");
    await writeFile(path.join(artefatos, "ux04-reagendamento-mobile.png"), Buffer.from(foto.data, "base64"));
  }
  await clicar("Confirmar reagendamento");
  await esperar("window.__salvando === true");
  verificar(await avaliar("document.querySelector('.modal-fechar').disabled"), "Fechar fica indisponível durante gravação");
  await tecla("Escape");
  verificar(await avaliar("!!document.querySelector('dialog:modal')"), "Escape não interrompe gravação em andamento");
  await avaliar("window.__resolver()");
  await esperar("!document.querySelector('dialog')");
  verificar(await avaliar("window.__gravacoes.length === 1 && document.body.textContent.includes('Novo agendamento criado')"), "Sucesso fecha a janela com uma única requisição simulada");
  }
  console.log(`${total} verificações de interação aprovadas. API simulada; nenhum banco acessado.`);
  await call("Browser.close");
} finally {
  socket?.close();
  if (navegador && navegador.exitCode === null) {
    await Promise.race([once(navegador, "exit"), aguardar(2000)]);
    if (navegador.exitCode === null) navegador.kill();
  }
  await server.close();
  // Somente o perfil temporário criado acima, nunca o perfil real do navegador.
  const alvo = path.resolve(perfil);
  assert.equal(path.dirname(alvo).toLowerCase(), path.resolve(tmpdir()).toLowerCase());
  assert.ok(path.basename(alvo).startsWith("clinica-modal-teste-"));
  await rm(alvo, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
}
