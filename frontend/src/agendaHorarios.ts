/** Datas da agenda são interpretadas em Brasília, independentemente do dispositivo. */
export const FUSO_CLINICA = "America/Sao_Paulo";

const formatador = new Intl.DateTimeFormat("en-US", {
  timeZone: FUSO_CLINICA, hourCycle: "h23",
  year: "numeric", month: "2-digit", day: "2-digit",
  hour: "2-digit", minute: "2-digit", second: "2-digit",
});

function partes(instante: number) {
  return Object.fromEntries(formatador.formatToParts(new Date(instante))
    .filter((p) => p.type !== "literal").map((p) => [p.type, Number(p.value)]));
}

export function dataHoraClinica(instante: number): string {
  const p = partes(instante);
  const dois = (n: number) => String(n).padStart(2, "0");
  return `${String(p.year).padStart(4, "0")}-${dois(p.month)}-${dois(p.day)}T${dois(p.hour)}:${dois(p.minute)}`;
}

export function instanteDaClinica(valor: string): number {
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/.exec(valor);
  if (!m) return NaN;
  const [ano, mes, dia, hora, minuto] = m.slice(1).map(Number);
  const alvo = Date.UTC(ano, mes - 1, dia, hora, minuto);
  const data = new Date(alvo);
  if (data.getUTCFullYear() !== ano || data.getUTCMonth() !== mes - 1 || data.getUTCDate() !== dia
    || data.getUTCHours() !== hora || data.getUTCMinutes() !== minuto) return NaN;
  let instante = alvo;
  for (let i = 0; i < 3; i++) {
    const p = partes(instante);
    const exibido = Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second);
    const diferenca = alvo - exibido;
    instante += diferenca;
    if (diferenca === 0) break;
  }
  return dataHoraClinica(instante) === valor ? instante : NaN;
}

export function erroHorario(valor: string, agora: number | null): string | null {
  const instante = instanteDaClinica(valor);
  if (!Number.isFinite(instante)) return "Informe uma data e hora válidas.";
  if (agora === null || !Number.isFinite(agora)) return "Aguarde a atualização do horário atual.";
  if (instante <= agora) return "Data ou hora inválida: o horário escolhido já passou. Selecione um horário futuro.";
  return null;
}

export function minimoFuturoClinica(agora: number | null): string | undefined {
  return agora === null ? undefined : dataHoraClinica((Math.floor(agora / 60000) + 1) * 60000);
}

export interface ReferenciaRelogio {
  instante: number;
  medidoEm: number;
}

export function criarReferenciaRelogio(agoraIso: string, inicio: number, fim: number): ReferenciaRelogio {
  const instante = Date.parse(agoraIso);
  if (!/(Z|[+-]\d{2}:\d{2})$/.test(agoraIso) || !Number.isFinite(instante)
    || !Number.isFinite(inicio) || !Number.isFinite(fim) || fim < inicio) {
    throw new Error("Horário de referência inválido.");
  }
  // Inclui toda a latência da consulta, evitando liberar um horário que pode
  // já ter vencido. A atualização segue o relógio monotônico, não Date.now().
  return { instante: instante + fim - inicio, medidoEm: fim };
}

export function agoraDaReferencia(ref: ReferenciaRelogio, medidoEm: number): number | null {
  const decorrido = medidoEm - ref.medidoEm;
  if (!Number.isFinite(decorrido) || decorrido < 0 || decorrido > 60000) return null;
  return ref.instante + decorrido;
}
