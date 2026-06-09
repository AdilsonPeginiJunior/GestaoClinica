/**
 * Contexto de autenticação — mantém usuário logado e token JWT no localStorage.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  fetchMe,
  getStoredToken,
  login as apiLogin,
  setAuthToken,
} from "../api";
import type { Usuario } from "../types";

interface AuthContextValue {
  usuario: Usuario | null;
  carregando: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [carregando, setCarregando] = useState(true);

  // Restaura sessão se já existir token salvo (ex.: F5 na página)
  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setCarregando(false);
      return;
    }
    fetchMe()
      .then(setUsuario)
      .catch(() => setAuthToken(null))
      .finally(() => setCarregando(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await apiLogin(email, password);
    setAuthToken(access_token);
    const me = await fetchMe();
    setUsuario(me);
  }, []);

  const logout = useCallback(() => {
    setAuthToken(null);
    setUsuario(null);
  }, []);

  const value = useMemo(
    () => ({ usuario, carregando, login, logout }),
    [usuario, carregando, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth deve ser usado dentro de AuthProvider");
  return ctx;
}
