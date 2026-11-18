// The sandbox payment window: a modal like a hosted payment link, over the shop. It
// pays the backend's checkout session directly; the card number goes only to
// /api/checkout/{id}/pay and never through the agent. Resolves with the session as the
// window left it: paid, or cancelled when the customer closed it.

import { ApiError, type Checkout, api } from "./api.ts";

const $ = <T extends Element>(root: ParentNode, selector: string): T => {
  const el = root.querySelector<T>(selector);
  if (el === null) throw new Error(`missing ${selector}`);
  return el;
};

const DECLINED_PAUSE_MS = 1650;

export function payWithCheckout(dialog: HTMLDialogElement, session: Checkout): Promise<Checkout> {
  const form = $<HTMLFormElement>(dialog, "[data-pay-form]");
  const error = $<HTMLElement>(dialog, "[data-pay-error]");
  const submit = $<HTMLButtonElement>(dialog, "[data-pay-submit]");
  const close = $<HTMLButtonElement>(dialog, "[data-pay-close]");

  $<HTMLElement>(dialog, "[data-pay-amount]").textContent = session.total;
  const lines = $<HTMLUListElement>(dialog, "[data-pay-lines]");
  lines.replaceChildren(
    ...session.lines.map((line) => item(`${line.quantity} × ${line.name}`, line.line_total)),
    item("Delivery", session.delivery, session.delivery === "Free" ? "free" : ""),
  );
  submit.textContent = `Pay ${session.total}`;
  form.reset();
  // A phone's number pad has no `/` and no space: group the card in fours and put the
  // expiry's slash in as the customer types.
  $<HTMLInputElement>(dialog, "input[name=card_number]").oninput = (event) => {
    const input = event.currentTarget as HTMLInputElement;
    input.value = input.value.replace(/\D/g, "").slice(0, 19).replace(/(\d{4})(?=\d)/g, "$1 ");
  };
  $<HTMLInputElement>(dialog, "input[name=expiry]").oninput = (event) => {
    const input = event.currentTarget as HTMLInputElement;
    const digits = input.value.replace(/\D/g, "").slice(0, 4);
    const deleting = (event as InputEvent).inputType?.startsWith("delete");
    input.value = digits.length > 2 || (digits.length === 2 && !deleting) ? `${digits.slice(0, 2)}/${digits.slice(2)}` : digits;
  };
  error.textContent = "";
  close.disabled = false;

  return new Promise((resolve) => {
    let result: Checkout = session;

    const finish = () => {
      form.removeEventListener("submit", onSubmit);
      close.removeEventListener("click", onClose);
      dialog.removeEventListener("cancel", onCancel);
      dialog.removeEventListener("close", onClosed);
      resolve(result);
    };
    const onClosed = () => finish();
    const cancel = async () => {
      if (result.status === "open") {
        result = await api.cancelCheckout(session.session_id).catch(() => ({ ...result, status: "cancelled" as const }));
      }
      dialog.close();
    };
    const onClose = () => void cancel();
    const onCancel = (event: Event) => {
      event.preventDefault(); // Esc: cancel through the backend first
      void cancel();
    };
    const onSubmit = async (event: SubmitEvent) => {
      event.preventDefault();
      const data = new FormData(form);
      const card = {
        card_number: String(data.get("card_number") ?? ""),
        expiry: String(data.get("expiry") ?? ""),
        cvc: String(data.get("cvc") ?? ""),
        name: String(data.get("name") ?? ""),
      };
      submit.disabled = true;
      submit.textContent = "Processing…";
      error.textContent = "";
      try {
        result = await api.pay(session.session_id, card);
        if (result.status === "paid") {
          dialog.close(); // the shop's own page says it is paid
          return;
        }
        // Declined: the session is closed, so the window is done; the agent hears it.
        error.textContent = "Your card was declined. Nothing was charged.";
        setTimeout(() => dialog.close(), DECLINED_PAUSE_MS);
      } catch (e) {
        error.textContent = e instanceof ApiError ? capitalize(e.message) : "Could not reach the payment service.";
        submit.disabled = false;
        submit.textContent = `Pay ${session.total}`;
      }
    };

    form.addEventListener("submit", onSubmit);
    close.addEventListener("click", onClose);
    dialog.addEventListener("cancel", onCancel);
    dialog.addEventListener("close", onClosed);
    submit.disabled = false;
    dialog.showModal();
    $<HTMLInputElement>(dialog, "input[name=card_number]").focus();
  });
}

function item(label: string, value: string, className = ""): HTMLLIElement {
  const li = document.createElement("li");
  if (className) li.className = className;
  const a = document.createElement("span");
  a.textContent = label;
  const b = document.createElement("span");
  b.textContent = value;
  li.append(a, b);
  return li;
}

const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1) + (s.endsWith(".") ? "" : ".");
