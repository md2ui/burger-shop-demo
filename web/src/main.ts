// The Burger Shop web app: a native header and footer around one <md2ui-view>, which
// shows the conversation's current page. The page and every tap on it travel over md2ui's
// WebSocket, through md2ui-ts's wire client (wire_view.ts, which the Flutter app's embed
// page runs too); the shop's server verifies each tap against the page it sent and decides
// who answers it.
//
// Where a tap goes:
//   - Every agent: target, choice, count and the prompt bar go over the socket as md2ui's
//     frames. The server answers ➕ ➖ 🤍 ❤️ and the taps that only choose a page (a category
//     tab, View cart, Keep shopping) itself, with no agent turn; a choice or a count a commit
//     press will carry is recorded there; everything else reaches the agent, whose page comes
//     back over the socket.
//   - Home (the logo, Back to home) and the native chrome's View cart and My orders are the
//     app's: the server shows the page, over the socket, with no agent turn.
//   - Checkout is the app's too: the page's `agent:checkout` and the footer's button open the
//     sandbox payment window on the app's own session. When the agent opens it (its
//     open_checkout tool), /api/state says so after its page, and /api/resume hands the
//     agent the outcome once the window closes.

import { defineMd2uiView, type FontSource, type Md2uiViewElement } from "@md2ui/dom";
import { api, type CartBadge, type Checkout, type PendingAction } from "./api.ts";
import { payWithCheckout } from "./checkout.ts";
import { WireView } from "./wire_view.ts";

const FONT_DIR = "/theme/assets/fonts";
// Every face THEME.md draws in: the view measures text in a Worker, which sees only these.
const FONTS: FontSource[] = [
  { family: "Plus Jakarta Sans", url: `${FONT_DIR}/PlusJakartaSans-Medium.ttf`, weight: 500 },
  { family: "Plus Jakarta Sans", url: `${FONT_DIR}/PlusJakartaSans-SemiBold.ttf`, weight: 600 },
  { family: "Plus Jakarta Sans", url: `${FONT_DIR}/PlusJakartaSans-Bold.ttf`, weight: 700 },
  { family: "Plus Jakarta Sans", url: `${FONT_DIR}/PlusJakartaSans-ExtraBold.ttf`, weight: 800 },
  { family: "Inter 18pt", url: `${FONT_DIR}/Inter_18pt-Regular.ttf`, weight: 400 },
  { family: "Inter 18pt", url: `${FONT_DIR}/Inter_18pt-Medium.ttf`, weight: 500 },
  { family: "Inter 18pt", url: `${FONT_DIR}/Inter_18pt-SemiBold.ttf`, weight: 600 },
  { family: "Inter 18pt", url: `${FONT_DIR}/Inter_18pt-Bold.ttf`, weight: 700 },
  // The theme's emoji font, matched by the URL its `Font:` resolves to.
  { family: "md2ui icons", url: "/theme/assets/icons/material-design-icons-md2ui.ttf" },
];

const COOKING = "Cooking up your answer…";
const FRESHENING = "Freshening up your page…";

const $ = <T extends Element>(selector: string): T => {
  const el = document.querySelector<T>(selector);
  if (el === null) throw new Error(`missing ${selector}`);
  return el;
};

defineMd2uiView();
const view = $<Md2uiViewElement>("#view");
const working = $<HTMLElement>("[data-working]");
const status = $<HTMLElement>("[data-status]");
const total = $<HTMLElement>("[data-total]");
const count = $<HTMLElement>("[data-count]");
const viewCart = $<HTMLButtonElement>("[data-view-cart]");
const checkout = $<HTMLButtonElement>("[data-checkout]");
const myOrders = $<HTMLButtonElement>("[data-orders]");
const ask = $<HTMLFormElement>("[data-ask]");
const prompt = $<HTMLInputElement>("[data-ask] input");
const send = $<HTMLButtonElement>("[data-ask] button");
const payDialog = $<HTMLDialogElement>("[data-pay]");
const ownPlaceholder = prompt.placeholder;

// The server keeps the conversation; the tab keeps its id, so a reload is the same session
// (and its saved home). A server restart forgets it, and the next ticket starts a new one.
const SESSION_KEY = "burger-shop.conversation";
let conversationId: string | null = (() => {
  try {
    return sessionStorage.getItem(SESSION_KEY);
  } catch {
    return null;
  }
})();

function keepSession(id: string): void {
  conversationId = id;
  try {
    sessionStorage.setItem(SESSION_KEY, id);
  } catch {}
}

/** The fresh home is being written; the page stays usable meanwhile. */
let freshening = false;
/** Home is due once the socket opens: the first time, and when the server started a new conversation. */
let homeDue = true;
/** The payment window is open: nothing else answers until it closes. */
let paying = false;
let cart: CartBadge = { item_count: 0, total: 0, total_label: "$0.00" };

view.themeSrc = "/theme/THEME.md";
view.fonts = FONTS;
view.addEventListener("md2ui-error", (event) => console.warn("md2ui", event.detail));

// --- what the window and the footer show ---------------------------------------------
function showCart(next: CartBadge): void {
  cart = next;
  total.textContent = next.total_label;
  count.textContent = next.item_count === 1 ? "1 item" : `${next.item_count} items`;
  refresh();
}

/** The controls follow the wire: blocked while the agent works, before the socket listens,
 * or while the payment window is open. */
function refresh(): void {
  const blocked = wire.blocked;
  viewCart.disabled = blocked;
  myOrders.disabled = blocked;
  checkout.disabled = blocked || cart.item_count === 0;
  send.disabled = blocked;
  prompt.disabled = blocked;
  prompt.placeholder = wire.placeholder || ownPlaceholder;
  working.hidden = !(wire.working || freshening);
  working.lastElementChild!.textContent = wire.working ? (wire.note ?? COOKING) : FRESHENING;
}

function say(message: string, error = false): void {
  status.textContent = message;
  status.classList.toggle("error", error);
  if (message) setTimeout(() => status.textContent === message && say(""), 6000);
}

function failed(e: unknown, fallback: string): void {
  say(e instanceof Error ? e.message : fallback, true);
}

// --- md2ui's socket ----------------------------------------------------------------------
const wire = new WireView(view, {
  /** A one-time ticket from the shop for this tab's conversation, or a new one if the server forgot it. */
  async socketUrl() {
    const { conversation_id, ticket } = await api.session(conversationId);
    if (conversation_id !== conversationId) homeDue = true;
    keepSession(conversation_id);
    const scheme = location.protocol === "https:" ? "wss" : "ws";
    return `${scheme}://${location.host}/md2ui/ws?ticket=${encodeURIComponent(ticket)}`;
  },
  opened() {
    if (!homeDue) return;
    homeDue = false;
    void goHome();
  },
  paged: () => void afterPage(),
  changed: refresh,
  failed: (e) => failed(e, "Could not reach the shop"),
});

/** After each page: the footer's badge, and the agent's payment window if its turn waits on one. */
async function afterPage(): Promise<void> {
  try {
    const state = await api.state(conversationId);
    showCart(state.cart);
    if (state.pending_action !== null && !paying) await payForAgent(state.pending_action);
  } catch (e) {
    failed(e, "Could not reach the shop");
  }
}

// --- taps in the window ---------------------------------------------------------------
view.addEventListener("md2ui-action", (event) => {
  const action = event.detail;
  if (action.kind === "link") return; // the view opens it
  if (action.kind === "agent" && action.slug === "home") {
    event.preventDefault();
    void goHome();
    return;
  }
  if (action.kind === "agent" && action.slug === "checkout") {
    event.preventDefault(); // the app's own payment window, not an agent turn
    void payFromApp();
    return;
  }
  if (!wire.forward(action)) event.preventDefault();
});

// --- the home page: instant, then fresh ------------------------------------------------
/** Home at once (the session's saved home, or the instant one in the shop's words), then,
 * once a session, the home writer's version in place of it. Both arrive over the socket. */
async function goHome(): Promise<void> {
  if (conversationId === null) return;
  const id = conversationId;
  try {
    const home = await api.home(id);
    showCart(home.cart);
    if (!home.fresh) return;
    freshening = true;
    refresh();
    // Swapped in by the server only if nothing but ➕ ➖ 🤍 ❤️ happened since.
    await api.freshHome(id, home.token);
  } catch (e) {
    failed(e, "Could not load the home page");
  } finally {
    freshening = false;
    refresh();
  }
}

// --- the payment window ----------------------------------------------------------------
async function inWindow(session: Checkout): Promise<Checkout> {
  paying = true;
  wire.hold(true);
  try {
    return await payWithCheckout(payDialog, session);
  } finally {
    paying = false;
    wire.hold(false);
  }
}

/** The page's Checkout or the footer's: the app's own session; paid, the shop confirms it. */
async function payFromApp(): Promise<void> {
  if (conversationId === null || paying || cart.item_count === 0) return;
  try {
    const result = await inWindow(await api.openCheckout());
    if (result.cart) showCart(result.cart);
    if (result.status === "paid") await api.nav(conversationId, "success");
  } catch (e) {
    failed(e, "Could not open checkout");
  }
}

/** The agent's open_checkout: its turn waits; the outcome is the server's, not the window's. */
async function payForAgent(pending: PendingAction): Promise<void> {
  if (conversationId === null) return;
  await inWindow(pending.checkout);
  await api.resume(conversationId, pending.tool_use_id);
}

// --- the footer and the prompt bar -----------------------------------------------------
const show = (to: "cart" | "orders") => () => {
  if (conversationId !== null) void api.nav(conversationId, to).catch((e) => failed(e, "Could not open it"));
};
viewCart.addEventListener("click", show("cart"));
myOrders.addEventListener("click", show("orders"));
checkout.addEventListener("click", () => void payFromApp());

ask.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = prompt.value.trim();
  if (text && wire.prompt(text)) prompt.value = "";
});
prompt.addEventListener("input", () => wire.typing());

$<HTMLAnchorElement>("[data-home]").addEventListener("click", (event) => {
  event.preventDefault();
  void goHome();
});

// --- start: the footer from the server, then the socket, which shows the home page -------
void (async () => {
  try {
    showCart((await api.state(null)).cart);
    await wire.open();
  } catch {
    say("The shop's server is not running (backend on :8000).", true);
  }
})();
