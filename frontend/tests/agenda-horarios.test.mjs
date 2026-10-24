import test from "node:test";
import assert from "node:assert/strict";
import {
  agoraDaReferencia, criarReferenciaRelogio, dataHoraClinica,
  erroHorario, instanteDaClinica, minimoFuturoClinica,
} from "../src/agendaHorarios.ts";

const agora = Date.parse("2026-10-23T22:56:00Z"); // 19:56 em Brasília.

test("19:50 é interpretado como 22:50 UTC em Brasília", () => {
  assert.equal(instanteDaClinica("2026-10-23T19:50"), Date.parse("2026-10-23T22:50:00Z"));
});

test("caso relatado: 19:50 recebe aviso quando a ação ocorre às 19:56", () => {
  assert.match(erroHorario("2026-10-23T19:50", agora), /horário escolhido já passou/);
});

test("o próprio minuto atual não é um horário futuro", () => {
  assert.match(erroHorario("2026-10-23T19:56", agora), /já passou/);
});

test("próximo minuto pode ser reservado", () => {
  assert.equal(erroHorario("2026-10-23T19:57", agora), null);
});

test("dia anterior é recusado mesmo com hora do dia maior", () => {
  assert.match(erroHorario("2026-10-22T23:59", agora), /já passou/);
});

test("meia-noite do dia seguinte é válida e convertida corretamente", () => {
  assert.equal(erroHorario("2026-10-24T00:00", agora), null);
  assert.equal(instanteDaClinica("2026-10-24T00:00"), Date.parse("2026-10-24T03:00:00Z"));
});

test("datas e horas impossíveis não são normalizadas silenciosamente", () => {
  for (const valor of ["", "inválido", "2026-02-30T10:00", "2026-13-01T10:00", "2026-10-23T25:00", "2026-10-23T19:65"]) {
    assert.equal(Number.isNaN(instanteDaClinica(valor)), true, valor);
    assert.match(erroHorario(valor, agora), /data e hora válidas/);
  }
});

test("sem relógio confirmado não libera data futura", () => {
  assert.match(erroHorario("2026-10-24T10:00", null), /Aguarde/);
  assert.equal(minimoFuturoClinica(null), undefined);
});

test("mínimo do seletor usa o próximo minuto de Brasília", () => {
  assert.equal(minimoFuturoClinica(agora), "2026-10-23T19:57");
  assert.equal(minimoFuturoClinica(Date.parse("2026-10-24T02:59:59Z")), "2026-10-24T00:00");
});

test("formulário aberto passa a avisar quando a seleção vence", () => {
  const valor = "2026-10-23T19:57";
  assert.equal(erroHorario(valor, agora), null);
  assert.match(erroHorario(valor, agora + 60000), /já passou/);
});

test("interpretação não depende do fuso do dispositivo", () => {
  const anterior = process.env.TZ;
  try {
    for (const fuso of ["UTC", "Asia/Tokyo", "America/New_York"]) {
      process.env.TZ = fuso;
      assert.equal(instanteDaClinica("2026-10-23T19:50"), Date.parse("2026-10-23T22:50:00Z"));
      assert.match(erroHorario("2026-10-23T19:50", agora), /já passou/);
    }
  } finally {
    if (anterior === undefined) delete process.env.TZ;
    else process.env.TZ = anterior;
  }
});

test("referência inclui latência de forma conservadora", () => {
  const ref = criarReferenciaRelogio("2026-10-23T22:56:00Z", 100, 200);
  assert.equal(agoraDaReferencia(ref, 1200), agora + 1100);
});

test("relógio do dispositivo incorreto não muda a referência da API", () => {
  const original = Date.now;
  try {
    Date.now = () => 0;
    const ref = criarReferenciaRelogio("2026-10-23T22:56:00Z", 100, 100);
    assert.match(erroHorario("2026-10-23T19:50", agoraDaReferencia(ref, 100)), /já passou/);
  } finally { Date.now = original; }
});

test("referência vencida ou contador reiniciado não usa fallback local", () => {
  const ref = criarReferenciaRelogio("2026-10-23T22:56:00Z", 100, 100);
  assert.equal(agoraDaReferencia(ref, 60101), null);
  assert.equal(agoraDaReferencia(ref, 99), null);
});

test("referência sem fuso ou inválida é recusada", () => {
  for (const valor of ["2026-10-23T22:56:00", "data inválida"]) {
    assert.throws(() => criarReferenciaRelogio(valor, 100, 200), /inválido/);
  }
});

test("formatação do seletor usa Brasília", () => {
  assert.equal(dataHoraClinica(agora), "2026-10-23T19:56");
});
