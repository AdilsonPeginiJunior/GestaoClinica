/**
 * Lista profissionais e percentual de repasse (base do fechamento financeiro).
 */
import { useEffect, useState } from "react";
import { fetchPsicologos } from "../api";
import type { Psicologo } from "../types";

export default function Psicologos() {
  const [lista, setLista] = useState<Psicologo[]>([]);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    fetchPsicologos()
      .then(setLista)
      .catch(() => setErro("Erro ao carregar psicologos."));
  }, []);

  return (
    <>
      <header className="page-header">
        <h2>Psicologos</h2>
        <p>Equipe da clinica com regra de repasse por profissional.</p>
      </header>
      {erro && <p className="erro">{erro}</p>}
      <div className="tabela-wrapper">
      <table className="tabela">
        <thead>
          <tr>
            <th>Nome</th>
            <th>CRP</th>
            <th>E-mail</th>
            <th>Repasse %</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {lista.map((p) => (
            <tr key={p.id}>
              <td>{p.nome}</td>
              <td>{p.crp}</td>
              <td>{p.email}</td>
              <td>{p.percentual_repasse}%</td>
              <td>{p.ativo ? "Ativo" : "Inativo"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </>
  );
}
