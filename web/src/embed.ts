// The page the Flutter app's web view loads (app/assets/md2ui, built by
// app/tool/sync_md2ui.sh). One <md2ui-view> fills it, on md2ui's WebSocket as the web app's
// is (wire_view.ts): the page opens the socket itself, so pages, taps and the agent's state
// never pass through the app. The app keeps its native chrome, and talks to the page through
// `window.md2uiHost` and flutter_inappwebview's bridge (`callHandler`):
//
//   app -> page   md2uiHost.theme({ src, fonts })   the theme and its faces
//                 md2uiHost.connect()               open the socket, once a page load
//                 md2uiHost.hold(held)              the app's payment sheet is open
//                 md2uiHost.prompt(text) -> sent    what the customer typed, as md2ui's prompt
//                 md2uiHost.typing()                a key pressed in the app's prompt field
//   page -> app   md2uiHostReady {}
//                 md2uiSession {} -> { url }        the socket's URL with a one-time ticket the
//                                                   app asked the shop for (/api/session)
//                 md2uiOpen {}                      the socket opened, the first time or again
//                 md2uiPage {}                      a page arrived whole
//                 md2uiState { blocked, working, note, placeholder }   for the chrome
//                 md2uiAppAction { slug }           the page's Home or Checkout: the app's own
//                 md2uiLink { href }                an http(s) or mailto: link
//                 md2uiError { message }
//
// The page's origin is the app's page server's, http://localhost:8787 (app/lib/md2ui/
// server.dart), on every platform; the shop's backend names it in ALLOWED_ORIGINS. The
// ticket comes from the app, over its own HTTP, because the page cannot read the shop's
// /api/session: it is another origin, and the shop answers no cross-origin request.

import { defineMd2uiView, type FontSource, type Md2uiViewElement } from "@md2ui/dom";
import { WireView } from "./wire_view.ts";

interface Bridge {
  callHandler(name: string, ...args: unknown[]): Promise<unknown>;
}

const bridge = (): Bridge | undefined =>
  (window as { flutter_inappwebview?: Bridge }).flutter_inappwebview;

function post(name: string, payload: unknown): void {
  const flutter = bridge();
  if (flutter === undefined) console.info(name, payload); // a plain browser, for checks
  else void flutter.callHandler(name, payload);
}

const failure = (e: unknown) => ({ message: e instanceof Error ? e.message : String(e) });

defineMd2uiView();
const view = document.querySelector<Md2uiViewElement>("#view");
if (view === null) throw new Error("no <md2ui-view>");

let reported = "";
const wire = new WireView(view, {
  async socketUrl() {
    const session = (await bridge()?.callHandler("md2uiSession", {})) as { url?: unknown } | null | undefined;
    if (typeof session?.url !== "string") throw new Error("The app has no ticket for the shop");
    return session.url;
  },
  opened: () => post("md2uiOpen", {}),
  paged: () => post("md2uiPage", {}),
  changed() {
    const state = { blocked: wire.blocked, working: wire.working, note: wire.note ?? null, placeholder: wire.placeholder ?? null };
    const next = JSON.stringify(state);
    if (next === reported) return;
    reported = next;
    post("md2uiState", state);
  },
  failed: (e) => post("md2uiError", failure(e)),
});

view.addEventListener("md2ui-action", (event) => {
  const action = event.detail;
  if (action.kind === "link") {
    event.preventDefault(); // the app opens links; the web view never navigates away
    post("md2uiLink", { href: action.href });
    return;
  }
  if (action.kind === "agent" && (action.slug === "home" || action.slug === "checkout")) {
    event.preventDefault(); // the app's own: its home page, and its payment sheet
    post("md2uiAppAction", { slug: action.slug });
    return;
  }
  if (!wire.forward(action)) event.preventDefault();
});
view.addEventListener("md2ui-error", (event) => post("md2uiError", event.detail));

let themeSrc: string | null = null;
let connected = false;

(window as { md2uiHost?: unknown }).md2uiHost = {
  theme(next: { src: string; fonts: FontSource[] }): void {
    if (themeSrc === next.src) return;
    themeSrc = next.src;
    view.themeSrc = next.src;
    view.fonts = [...next.fonts];
  },
  connect(): void {
    if (connected) return;
    connected = true;
    wire.open().catch((e: unknown) => post("md2uiError", failure(e)));
  },
  hold(held: boolean): void {
    wire.hold(held);
  },
  prompt(text: string): boolean {
    return wire.prompt(text);
  },
  typing(): void {
    wire.typing();
  },
};

post("md2uiHostReady", {});
