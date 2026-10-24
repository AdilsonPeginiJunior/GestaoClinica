/** Referência temporal da API, sem liberar reservas com relógio desconhecido. */
import { useCallback, useEffect, useRef, useState } from "react";
import { fetchRelogioAgenda } from "../api";
import { agoraDaReferencia, criarReferenciaRelogio, FUSO_CLINICA, type ReferenciaRelogio } from "../agendaHorarios";

export function useRelogioAgenda() {
  const referencia = useRef<ReferenciaRelogio | null>(null);
  const [agora, setAgora] = useState<number | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const consulta = useRef(0);

  const sincronizar = useCallback(async () => {
    const numero = ++consulta.current;
    const inicio = performance.now();
    try {
      const dados = await fetchRelogioAgenda();
      if (dados.fuso_horario !== FUSO_CLINICA) throw new Error("Fuso de referência inesperado.");
      const medido = performance.now();
      const ref = criarReferenciaRelogio(dados.agora, inicio, medido);
      const atual = agoraDaReferencia(ref, medido)!;
      if (numero === consulta.current) {
        referencia.current = ref;
        setAgora(atual);
        setErro(null);
      }
      return atual;
    } catch (falha) {
      if (numero === consulta.current) {
        referencia.current = null;
        setAgora(null);
        setErro("Não foi possível atualizar o horário atual. Tente novamente antes de agendar.");
      }
      throw new Error("Não foi possível confirmar o horário atual. Atualize a página e tente novamente.", { cause: falha });
    }
  }, []);

  useEffect(() => {
    const atualizar = () => {
      referencia.current = null;
      setAgora(null);
      void sincronizar().catch(() => {});
    };
    const aoVoltar = () => { if (document.visibilityState === "visible") atualizar(); };
    atualizar();
    const segundos = window.setInterval(() => {
      const atual = referencia.current ? agoraDaReferencia(referencia.current, performance.now()) : null;
      setAgora(atual);
    }, 1000);
    const consultaPeriodica = window.setInterval(() => { void sincronizar().catch(() => {}); }, 30000);
    window.addEventListener("focus", atualizar);
    document.addEventListener("visibilitychange", aoVoltar);
    return () => {
      ++consulta.current;
      window.clearInterval(segundos);
      window.clearInterval(consultaPeriodica);
      window.removeEventListener("focus", atualizar);
      document.removeEventListener("visibilitychange", aoVoltar);
    };
  }, [sincronizar]);

  return { agora, erro, sincronizar };
}
