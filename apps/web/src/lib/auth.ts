// Session organisateur : un JWT stocké en localStorage (client uniquement).
// Pas de cookie/session serveur — cohérent avec le choix d'architecture
// « JWT via FastAPI » acté avant M6 (voir docs/RAPPORT.md, entrée M5).

const TOKEN_KEY = "billetterie_organizer_token";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function storeToken(token: string): void {
  try {
    window.localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // Stockage indisponible (navigation privée, quota) : la session ne
    // survivra pas au rechargement, mais la page reste utilisable.
  }
}

export function clearToken(): void {
  try {
    window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Rien à faire si le stockage est indisponible.
  }
}
