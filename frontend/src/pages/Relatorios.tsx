/**
 * Relatorio financeiro por psicologo — principal diferencial para o cliente.
 */
import { useEffect, useState } from "react";
import { fetchPsicologos, fetchRelatorioPsicologo } from "../api";
import type { Psicologo, RelatorioPsicologo } from "../types";

export default function Relatorios() {
  const [psicologos, setPsicologos] = useState<Psicologo[]>([]);
  const [psicologoId, setPsicologoId] = useState<number>(0);
  const [relatorio, setRelatorio] = useState<RelatorioPsicologo | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    fetchPsicologos()
      .then((lista) => {
        setPsicologos(lista);
        if (lista[0]) setPsicologoId(lista[0].id);
      })
      .catch(() => setErro("Erro ao carregar psicologos."));
  }, []);

  useEffect(() => {
    if (!psicologoId) return;
    setErro(null);
    fetchRelatorioPsicologo(psicologoId)
      .then(setRelatorio)
      .catch(() => setErro("Sem permissao ou API indisponivel."));
  }, [psicologoId]);

  const formatMoeda = (v: number) =>
    v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

  const saldoClinica =
    relatorio ? relatorio.receita_bruta - relatorio.repasse_total : 0;

  return (
    <>
      <header className="page-header">
        <h2>Relatorios</h2>
        <p>Apuracao de consultas, faturamento bruto e repasse por profissional.</p>
      </header>
      {erro && <p className="erro">{erro}</p>}
      <div className="filtros">
        <label>
          Psicologo
          <select value={psicologoId} onChange={(e) => setPsicologoId(Number(e.target.value))}>
            {psicologos.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nome}
              </option>
            ))}
          </select>
        </label>
      </div>
      {relatorio && (
        <>
          <div className="grid-stats">
            <div className="card">
              <div className="valor">{relatorio.sessoes_realizadas}</div>
              <div className="rotulo">Sessoes realizadas</div>
            </div>
            <div className="card">
              <div className="valor">{formatMoeda(relatorio.receita_bruta)}</div>
              <div className="rotulo">Receita bruta</div>
            </div>
            <div className="card">
              <div className="valor">{formatMoeda(relatorio.repasse_total)}</div>
              <div className="rotulo">Repasse devido</div>
            </div>
            <div className="card">
              <div className="valor">{formatMoeda(saldoClinica)}</div>
              <div className="rotulo">Saldo clinica (estimado)</div>
            </div>
          </div>
          <h3>Lancamentos do periodo</h3>
          <table className="tabela">
            <thead>
              <tr>
                <th>Descricao</th>
                <th>Tipo</th>
                <th>Valor</th>
              </tr>
            </thead>
            <tbody>
              {relatorio.lancamentos.map((l) => (
                <tr key={l.id}>
                  <td>{l.descricao}</td>
                  <td>{l.tipo}</td>
                  <td>{formatMoeda(l.valor)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </>
  );
}
