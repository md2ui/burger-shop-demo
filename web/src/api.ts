// The backend's HTTP API (backend/main.py), as the web app uses it beside md2ui's socket:
// the ticket that opens the socket, the home page, the native chrome's pages, the footer's
// badge and the payment window. The dev server proxies /api, /theme and /md2ui to the
// backend, so every path here is same-origin.

export interface CartBadge {
  readonly item_count: number;
  readonly total: number;
  readonly total_label: string;
}

export interface Checkout {
  readonly session_id: string;
  readonly status: "open" | "paid" | "cancelled" | "failed";
  readonly lines: readonly { name: string; quantity: number; line_total: string }[];
  readonly item_count: number;
  readonly subtotal: string;
  readonly delivery: string;
  readonly total: string;
  readonly order_id: string | null;
  readonly error: string | null;
  readonly cart?: CartBadge;
}

/** The agent's turn waits on the app's payment window (its open_checkout tool). */
export interface PendingAction {
  readonly tool_use_id: string;
  readonly tool_name: string;
  readonly checkout: Checkout;
}

export interface ShopState {
  readonly cart: CartBadge;
  readonly pending_action: PendingAction | null;
}

/** The page itself arrives over md2ui's socket; this says whether to ask for a fresh one. */
export interface HomeResponse {
  readonly conversation_id: string;
  readonly token: number;
  readonly cart: CartBadge;
  /** From /api/home: true when the session has no saved home that fits, so ask for a fresh one. */
  readonly fresh: boolean;
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

async function call<T>(method: "GET" | "POST", path: string, body?: unknown): Promise<T> {
  const response = await fetch(path, {
    method,
    headers: body === undefined ? {} : { "content-type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data: unknown = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = (data as { detail?: unknown }).detail;
    throw new ApiError(response.status, typeof detail === "string" ? detail : `HTTP ${response.status}`);
  }
  return data as T;
}

export const api = {
  /** A one-time ticket for md2ui's socket, and the conversation it joins (this one, or a new one). */
  session: (conversation_id: string | null) =>
    call<{ conversation_id: string; ticket: string }>("POST", "/api/session", { conversation_id }),
  state: (conversation_id: string | null) =>
    call<ShopState>("GET", `/api/state${conversation_id ? `?conversation_id=${encodeURIComponent(conversation_id)}` : ""}`),
  home: (conversation_id: string) => call<HomeResponse>("POST", "/api/home", { conversation_id }),
  freshHome: (conversation_id: string, token: number) =>
    call<HomeResponse>("POST", "/api/home/fresh", { conversation_id, token }),
  /** A page of the app's own buttons (View cart, My orders, the confirmation after paying). */
  nav: (conversation_id: string, to: "cart" | "orders" | "success") =>
    call<unknown>("POST", "/api/nav", { conversation_id, to }),
  resume: (conversation_id: string, tool_use_id: string) =>
    call<unknown>("POST", "/api/resume", { conversation_id, tool_use_id }),
  openCheckout: () => call<Checkout>("POST", "/api/checkout"),
  pay: (sessionId: string, card: { card_number: string; expiry: string; cvc: string; name: string }) =>
    call<Checkout>("POST", `/api/checkout/${encodeURIComponent(sessionId)}/pay`, card),
  cancelCheckout: (sessionId: string) => call<Checkout>("POST", `/api/checkout/${encodeURIComponent(sessionId)}/cancel`),
};
