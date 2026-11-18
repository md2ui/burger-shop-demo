// One <md2ui-view> on md2ui's WebSocket, through md2ui-ts's wire client (@md2ui/wire). The
// web app (main.ts) and the Flutter app's embed page (embed.ts) both run their view through
// it, so both show the pages, send the taps and follow the agent's state the same way.
//
// The host brings the socket's address, a URL carrying a one-time ticket from the shop (the
// web page asks /api/session itself, the embed page asks the app), and its own chrome, which
// it redraws from `blocked`, `working`, `note` and `placeholder` whenever `changed` is called.
// A dropped socket is opened again a second later, with a fresh ticket.

import type { Md2uiAction, Md2uiViewElement } from "@md2ui/dom";
import { type AnsweredEvent, connectWebSocket, type WireClient, type WireClientEvent } from "@md2ui/wire";

export interface WireViewHost {
  /** The socket's URL, with a fresh one-time ticket from the shop. */
  socketUrl(): Promise<string>;
  /** The socket opened, the first time or again. */
  opened(): void;
  /** A page arrived whole: what the footer shows may have changed. */
  paged(): void;
  /** What the chrome follows changed. */
  changed(): void;
  /** The socket could not be opened again. */
  failed(error: unknown): void;
}

/** A tap md2ui's event frame can carry: anything but a plain link. */
export type ViewTap = Exclude<Md2uiAction, { kind: "link" }>;

export class WireView {
  /** The agent is working, as md2ui's last state said. */
  working = false;
  /** The step the agent named while it works (md2ui ADR-613). */
  note: string | undefined;
  /** The question the agent waits on, for the prompt field (md2ui ADR-613). */
  placeholder: string | undefined;

  readonly #view: Md2uiViewElement;
  readonly #host: WireViewHost;
  #client: WireClient | null = null;
  /** The host holds the view: its payment window is open. */
  #held = false;

  constructor(view: Md2uiViewElement, host: WireViewHost) {
    this.#view = view;
    this.#host = host;
  }

  /** Input waits: before the socket listens, while the agent works, or while the host holds it. */
  get blocked(): boolean {
    return this.#client === null || this.#client.blocked || this.#held;
  }

  hold(held: boolean): void {
    this.#held = held;
    this.#refresh();
  }

  /** Opens the socket; resolves once it is open. */
  async open(): Promise<void> {
    const socket = new WebSocket(await this.#host.socketUrl());
    const opened = new Promise<void>((resolve, reject) => {
      socket.addEventListener("open", () => resolve(), { once: true });
      socket.addEventListener("error", () => reject(new Error("Could not reach the shop")), { once: true });
    });
    this.#client = connectWebSocket(socket, (event) => this.#onWire(event));
    socket.addEventListener("close", () => {
      this.#client = null;
      this.working = false;
      this.#refresh();
      setTimeout(() => void this.open().catch((e: unknown) => this.#host.failed(e)), 1000);
    });
    await opened;
    this.#host.opened();
  }

  /** Sends a tap as md2ui's event frame; false when the protocol refuses it now. */
  forward(action: ViewTap): boolean {
    if (this.#client === null || action.messageId === null) return false;
    const sent = this.#client.sendEvent({
      message: action.messageId,
      target: action.ordinal,
      kind: action.kind,
      ...(action.kind === "agent" && { slug: action.slug }),
      ...("checked" in action && action.checked !== undefined && { checked: action.checked }),
      ...("value" in action && action.value !== undefined && { value: action.value }),
      ...(action.kind === "agent" && action.settled !== undefined && { settled: action.settled }),
    }).sent;
    this.#refresh();
    return sent;
  }

  /** Sends what the customer typed as md2ui's prompt frame; false when it may not go now. */
  prompt(text: string): boolean {
    const sent = this.#client?.sendPrompt(text).sent ?? false;
    this.#refresh();
    return sent;
  }

  /** A key pressed in the host's prompt field. */
  typing(): void {
    this.#client?.sendTyping();
  }

  #onWire(event: WireClientEvent): void {
    const view = this.#view;
    switch (event.type) {
      case "message": {
        // A message without `r` is a new page: it fades in whole and starts at the top; a
        // replacement (a redraw after ➕, the fresh home) moves node by node and keeps the scroll.
        const newPage = event.replaces === undefined && view.messageId !== event.id;
        view.motion = newPage ? "page" : "edit";
        view.streaming = !event.complete;
        view.markdown = event.markdown;
        view.messageId = event.id;
        if (newPage) view.scrollTop = 0;
        if (event.complete) this.#host.paged();
        break;
      }
      case "state":
        this.working = event.state === "w";
        this.note = event.note;
        this.placeholder = event.state === "l" ? event.placeholder : undefined;
        if (event.answered !== undefined) this.#release(event.answered);
        break;
      case "refused":
        console.warn("md2ui refused", event.frame);
        break;
      case "dropped":
      case "ignored":
        console.warn("md2ui", event);
    }
    this.#refresh();
  }

  /** Lets go of the buttons the server answered, on the page they now stand on. */
  #release(answered: readonly AnsweredEvent[]): void {
    const shown = answered.filter((a) => a.message === this.#view.messageId).map((a) => a.target);
    if (shown.length > 0) this.#view.release(shown);
  }

  #refresh(): void {
    this.#view.disabled = this.blocked;
    this.#host.changed();
  }
}
