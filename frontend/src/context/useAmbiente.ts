import { useEffect, useState } from "react";
import { fetchConfiguracaoPublica, type ConfiguracaoPublica } from "../api";

/** Falha de consulta mantém acessos demo ocultos; quem decide é a API. */
export function useAmbiente() {
  const [config, setConfig] = useState<ConfiguracaoPublica | null>(null);
  useEffect(() => {
    let ativo = true;
    fetchConfiguracaoPublica().then(dados => {
      if (ativo && (dados.ambiente === "demo" || dados.ambiente === "production")
          && typeof dados.demo_habilitada === "boolean") setConfig(dados);
    }).catch(() => {});
    return () => { ativo = false; };
  }, []);
  return config;
}
