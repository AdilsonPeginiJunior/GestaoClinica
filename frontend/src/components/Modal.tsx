import { useEffect, useId, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";

/** Dialog nativo: mantém o foco na janela, restaura o botão e suporta Escape. */
export default function Modal({ titulo, children, onFechar, ocupado = false, amplo = false }: {
  titulo: string; children: ReactNode; onFechar: () => void; ocupado?: boolean; amplo?: boolean;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const tituloId = useId();

  useEffect(() => {
    const elemento = dialog.current!;
    const focoAnterior = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const overflowAnterior = document.body.style.overflow;
    elemento.showModal();
    document.body.style.overflow = "hidden";
    return () => {
      elemento.close();
      document.body.style.overflow = overflowAnterior;
      if (focoAnterior?.isConnected) focoAnterior.focus({ preventScroll: true });
    };
  }, []);

  return createPortal(<dialog ref={dialog} className={`modal${amplo ? " modal-amplo" : ""}`}
    aria-labelledby={tituloId} aria-modal="true" aria-busy={ocupado}
    onCancel={e => { e.preventDefault(); if (!ocupado) onFechar(); }}>
    <header className="modal-cabecalho">
      <h3 id={tituloId}>{titulo}</h3>
      <button type="button" className="modal-fechar" onClick={onFechar} disabled={ocupado} aria-label="Fechar janela">×</button>
    </header>
    <div className="modal-corpo">{children}</div>
  </dialog>, document.body);
}
