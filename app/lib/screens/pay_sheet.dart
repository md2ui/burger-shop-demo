// The sandbox payment window, native: a bottom sheet like a hosted payment link. It pays
// the backend's checkout session directly (/api/checkout/{id}/pay); the card number goes
// only there, never through the agent. Returns the session as the sheet left it: paid,
// failed (declined), or cancelled when the customer closed it.

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../api/shop_api.dart';
import '../palette.dart';

Future<Checkout> payWithCheckout(BuildContext context, ShopApi api, Checkout session) async {
  final result = await showModalBottomSheet<Checkout>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    backgroundColor: Palette.white,
    showDragHandle: true,
    shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(28))),
    builder: (context) => _PaySheet(api: api, session: session),
  );
  if (result != null) return result;
  // Closed without paying (dragged down, tapped outside): cancel it on the server.
  try {
    return await api.cancelCheckout(session.sessionId);
  } on ApiException {
    return session;
  }
}

class _PaySheet extends StatefulWidget {
  const _PaySheet({required this.api, required this.session});
  final ShopApi api;
  final Checkout session;

  @override
  State<_PaySheet> createState() => _PaySheetState();
}

class _PaySheetState extends State<_PaySheet> {
  final _card = TextEditingController();
  final _expiry = TextEditingController();
  final _cvc = TextEditingController();
  final _name = TextEditingController();
  String? _error;
  bool _paying = false;

  @override
  void dispose() {
    for (final c in [_card, _expiry, _cvc, _name]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _pay() async {
    setState(() {
      _paying = true;
      _error = null;
    });
    try {
      final result = await widget.api.pay(
        widget.session.sessionId,
        cardNumber: _card.text,
        expiry: _expiry.text,
        cvc: _cvc.text,
        name: _name.text,
      );
      if (!mounted) return;
      // Paid: the sheet closes at once; the shop's own page is the confirmation.
      if (result.status != 'paid') {
        // Declined: the session is closed, so the sheet is done; the agent hears it.
        setState(() => _error = 'Your card was declined. Nothing was charged.');
        await Future<void>.delayed(const Duration(milliseconds: 1600));
      }
      if (mounted) Navigator.of(context).pop(result);
    } on ApiException catch (e) {
      if (mounted) {
        setState(() {
          _paying = false;
          _error = _sentence(e.message);
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = widget.session;
    return Padding(
      padding: EdgeInsets.fromLTRB(24, 0, 24, 24 + MediaQuery.of(context).viewInsets.bottom),
      child: SingleChildScrollView(
        child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(children: [
                    const _TestMode(),
                    const Spacer(),
                    IconButton.filledTonal(
                      onPressed: _paying ? null : () => Navigator.of(context).pop(),
                      style: IconButton.styleFrom(backgroundColor: Palette.cream, foregroundColor: Palette.ink),
                      icon: const Icon(Icons.close),
                      tooltip: 'Close payment',
                    ),
                  ]),
                  const SizedBox(height: 12),
                  Row(children: [
                    ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: Image.asset('assets/icon/icon.png', width: 28, height: 28),
                    ),
                    const SizedBox(width: 8),
                    const Text('Pay Burger Shop', style: TextStyle(fontWeight: FontWeight.w600, color: Palette.body)),
                  ]),
                  const SizedBox(height: 6),
                  Text(s.total,
                      style: const TextStyle(
                          fontFamily: Fonts.heading, fontWeight: FontWeight.w800, fontSize: 36, color: Palette.ink)),
                  const Divider(height: 24, color: Palette.border),
                  for (final l in s.lines) _Line('${l.quantity} × ${l.name}', l.lineTotal),
                  _Line('Delivery', s.delivery, free: s.delivery == 'Free'),
                  const SizedBox(height: 20),
                  _Field(label: 'Card number', controller: _card, hint: '4242 4242 4242 4242', number: true,
                      autofill: AutofillHints.creditCardNumber, formatter: const _CardNumberFormatter()),
                  const SizedBox(height: 12),
                  Row(children: [
                    Expanded(
                        child: _Field(label: 'Expiry', controller: _expiry, hint: 'MM / YY', number: true,
                            autofill: AutofillHints.creditCardExpirationDate, formatter: const _ExpiryFormatter())),
                    const SizedBox(width: 12),
                    Expanded(
                        child: _Field(label: 'CVC', controller: _cvc, hint: '123', number: true,
                            autofill: AutofillHints.creditCardSecurityCode, maxLength: 4)),
                  ]),
                  const SizedBox(height: 12),
                  _Field(label: 'Name on card', controller: _name, hint: 'Jane Doe', autofill: AutofillHints.creditCardName),
                  const SizedBox(height: 8),
                  SizedBox(
                    height: 20,
                    child: _error == null
                        ? null
                        : Text(_error!, style: const TextStyle(color: Palette.error, fontWeight: FontWeight.w600, fontSize: 13)),
                  ),
                  const SizedBox(height: 8),
                  FilledButton(
                    onPressed: _paying ? null : _pay,
                    child: Text(_paying ? 'Processing…' : 'Pay ${s.total}'),
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'Sandbox: 4242 4242 4242 4242 pays, 4000 0000 0000 0002 is declined. '
                    'Any future expiry and CVC. No real money moves.',
                    style: TextStyle(fontSize: 12, color: Palette.muted),
                  ),
                ],
              ),
      ),
    );
  }
}

String _sentence(String s) => s.isEmpty ? s : '${s[0].toUpperCase()}${s.substring(1)}${s.endsWith('.') ? '' : '.'}';

class _TestMode extends StatelessWidget {
  const _TestMode();
  @override
  Widget build(BuildContext context) => DecoratedBox(
        decoration: BoxDecoration(color: Palette.mustardTint, borderRadius: BorderRadius.circular(10)),
        child: const Padding(
          padding: EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          child: Text('TEST MODE',
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 0.4, color: Palette.mustardInk)),
        ),
      );
}

class _Line extends StatelessWidget {
  const _Line(this.label, this.value, {this.free = false});
  final String label;
  final String value;
  final bool free;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 3),
        child: Row(children: [
          Expanded(child: Text(label, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: Palette.body))),
          Text(value,
              style: TextStyle(
                  fontSize: 13,
                  fontWeight: free ? FontWeight.w700 : FontWeight.w500,
                  color: free ? const Color(0xFF1F5A35) : Palette.body)),
        ]),
      );
}

class _Field extends StatelessWidget {
  const _Field({
    required this.label,
    required this.controller,
    required this.hint,
    this.number = false,
    this.autofill,
    this.maxLength,
    this.formatter,
  });
  final String label;
  final TextEditingController controller;
  final String hint;
  final bool number;
  final String? autofill;
  final int? maxLength;
  final TextInputFormatter? formatter;

  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Palette.body)),
          const SizedBox(height: 6),
          TextField(
            controller: controller,
            keyboardType: number ? TextInputType.number : TextInputType.name,
            inputFormatters: [
              ?formatter,
              if (maxLength != null) LengthLimitingTextInputFormatter(maxLength),
            ],
            autofillHints: autofill == null ? null : [autofill!],
            style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w500, color: Palette.ink, letterSpacing: 0.3),
            decoration: InputDecoration(
              hintText: hint,
              fillColor: Palette.white,
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: Palette.border)),
              enabledBorder:
                  OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: Palette.border)),
              focusedBorder:
                  OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: Palette.forest, width: 2)),
            ),
          ),
        ],
      );
}

/// Card digits in groups of four as you type, so a short number shows (16 for the test card).
class _CardNumberFormatter extends TextInputFormatter {
  const _CardNumberFormatter();

  @override
  TextEditingValue formatEditUpdate(TextEditingValue oldValue, TextEditingValue newValue) {
    final digits = newValue.text.replaceAll(RegExp(r'\D'), '');
    final capped = digits.length > 19 ? digits.substring(0, 19) : digits;
    final grouped = [for (var i = 0; i < capped.length; i += 4) capped.substring(i, i + 4 > capped.length ? capped.length : i + 4)]
        .join(' ');
    return TextEditingValue(text: grouped, selection: TextSelection.collapsed(offset: grouped.length));
  }
}

/// MM/YY with the slash put in for you: a phone's number pad has no `/` key.
class _ExpiryFormatter extends TextInputFormatter {
  const _ExpiryFormatter();

  @override
  TextEditingValue formatEditUpdate(TextEditingValue oldValue, TextEditingValue newValue) {
    final digits = newValue.text.replaceAll(RegExp(r'\D'), '');
    final capped = digits.length > 4 ? digits.substring(0, 4) : digits;
    // Deleting the slash deletes the digit before it, so backspace never sticks on it.
    final deleting = newValue.text.length < oldValue.text.length;
    final text = capped.length > 2 || (capped.length == 2 && !deleting) ? '${capped.substring(0, 2)}/${capped.substring(2)}' : capped;
    return TextEditingValue(text: text, selection: TextSelection.collapsed(offset: text.length));
  }
}
