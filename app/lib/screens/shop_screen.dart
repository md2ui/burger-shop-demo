// The Burger Shop: a native header and footer around one md2ui view, which shows the
// conversation's current page: the same flow as the web app (web/src/main.ts). The view's
// page opens md2ui's socket itself, with a ticket the app asks the shop for, so pages and
// taps travel there and never through the app.
//
// Where a tap goes:
//   - Every tap in the view, and the prompt bar, go over the socket as md2ui's frames. md2ui
//     verifies each against the page it sent and answers ➕ ➖ 🤍 ❤️ and the taps that only
//     choose a page (a category tab, Keep shopping) with the shop's handlers, no agent turn;
//     a choice or a count is recorded for its commit press; everything else reaches the
//     agent, whose page comes back over the socket. The chrome follows md2ui's state frame.
//   - Home (the logo, Back to home) shows the session's saved home at once, or the instant
//     one and then the home writer's version, in place.
//   - The header's My orders and the footer's View cart are the app's: the backend shows the
//     page with no agent turn (/api/nav).
//   - Checkout opens the sandbox payment sheet on the app's own session, from the footer or
//     the page (`agent:checkout`), confirmed by the backend. When the agent opens it (its
//     open_checkout tool), /api/state says so after its page, and /api/resume hands the
//     agent the outcome once the sheet closes.

import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:url_launcher/url_launcher.dart';

import '../api/shop_api.dart';
import '../md2ui/md2ui_view.dart';
import '../palette.dart';
import '../widgets/working_pill.dart';
import 'pay_sheet.dart';
import 'settings_sheet.dart';

const _ownHint = 'Ask for anything: “something spicy under \$12”';

class ShopScreen extends StatefulWidget {
  const ShopScreen({super.key, required this.api});
  final ShopApi api;

  @override
  State<ShopScreen> createState() => _ShopScreenState();
}

class _ShopScreenState extends State<ShopScreen> {
  final _view = Md2uiController();
  final _prompt = TextEditingController();

  /// The backend keeps the conversation; this app run is one session (and one saved home).
  String? _conversationId;
  CartBadge _cart = CartBadge.empty;
  Md2uiState _wire = Md2uiState.connecting; // what the agent is doing, as md2ui says
  bool _paying = false; // the payment sheet is open: nothing else answers until it closes
  bool _freshening = false; // the fresh home is being written: the page stays usable
  /// Home is due once the socket opens: the first time, and when the server started a new
  /// conversation (it restarted).
  bool _homeDue = true;

  ShopApi get _api => widget.api;
  bool get _blocked => _wire.blocked || _paying;

  @override
  void initState() {
    super.initState();
    _start();
  }

  @override
  void dispose() {
    _prompt.dispose();
    super.dispose();
  }

  /// The footer from the server, then the socket, which shows the home page.
  Future<void> _start() async {
    try {
      _setCart((await _api.state(null)).cart);
    } on ApiException {
      _say('The shop\'s server is not reachable at ${_api.baseUrl}. Long-press the logo to change it.');
      return;
    }
    await _view.connect();
  }

  // --- what the screen shows ----------------------------------------------------------
  void _setCart(CartBadge cart) => setState(() => _cart = cart);

  void _say(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  // --- md2ui's socket -------------------------------------------------------------------
  /// A one-time ticket for this run's conversation, or a new one if the server forgot it.
  Future<Uri?> _socketUri() async {
    try {
      final session = await _api.session(_conversationId);
      if (session.conversationId != _conversationId) _homeDue = true;
      _conversationId = session.conversationId;
      return _api.socketUri(session.ticket);
    } on ApiException catch (e) {
      _say(e.message);
      return null;
    }
  }

  void _opened() {
    if (!_homeDue) return;
    _homeDue = false;
    _goHome();
  }

  /// After each page: the footer's badge, and the agent's payment sheet if its turn waits on one.
  Future<void> _afterPage() async {
    try {
      final state = await _api.state(_conversationId);
      _setCart(state.cart);
      final pending = state.pending;
      if (pending != null && !_paying) await _payForAgent(pending);
    } on ApiException catch (e) {
      _say(e.message);
    }
  }

  // --- the home page: the saved one, or instant then fresh ---------------------------
  /// Home at once, then, once a session, the home writer's version in place of it. Both
  /// arrive over the socket; the server swaps the fresh one in only if nothing but
  /// ➕ ➖ 🤍 ❤️ happened since.
  Future<void> _goHome() async {
    final id = _conversationId;
    if (id == null) return;
    try {
      final home = await _api.home(id);
      _setCart(home.cart);
      if (!home.fresh) return; // the session's saved home, its live parts up to date
      setState(() => _freshening = true);
      await _api.freshHome(id, home.token);
    } on ApiException catch (e) {
      _say(e.message);
    } finally {
      if (mounted) setState(() => _freshening = false);
    }
  }

  // --- the page's own Home and Checkout, and links ------------------------------------
  void _onAppAction(String slug) {
    if (slug == 'home') _goHome();
    if (slug == 'checkout') _checkout();
  }

  Future<void> _onLink(Uri link) async {
    if (!await launchUrl(link, mode: LaunchMode.externalApplication)) _say('Could not open $link');
  }

  void _show(String to) {
    final id = _conversationId;
    if (id != null) _api.nav(id, to).catchError((Object e) => _say('$e'));
  }

  // --- the payment sheet ----------------------------------------------------------------
  Future<Checkout> _inSheet(Checkout session) async {
    setState(() => _paying = true);
    final sheet = payWithCheckout(context, _api, session);
    try {
      await _view.hold(true);
      return await sheet;
    } finally {
      if (mounted) setState(() => _paying = false);
      await _view.hold(false);
    }
  }

  /// The footer's Checkout or the page's: the app's own session; paid, the shop confirms it.
  Future<void> _checkout() async {
    if (_paying || _cart.itemCount == 0 || _conversationId == null) return;
    try {
      final result = await _inSheet(await _api.openCheckout());
      if (result.cart != null) _setCart(result.cart!);
      // Paid: the backend shows the confirmation; declined, the sheet said so and the agent hears it.
      if (result.status == 'paid') _show('success');
    } on ApiException catch (e) {
      _say(e.message);
    }
  }

  /// The agent's open_checkout: its turn waits; the outcome is the server's, not the sheet's.
  Future<void> _payForAgent(PendingCheckout pending) async {
    final id = _conversationId;
    if (id == null || !mounted) return;
    await _inSheet(pending.checkout);
    await _api.resume(id, pending.toolUseId);
  }

  // --- the prompt bar -------------------------------------------------------------------
  Future<void> _send() async {
    final text = _prompt.text.trim();
    if (text.isEmpty || _blocked) return;
    if (!await _view.prompt(text)) return;
    _prompt.clear();
    if (mounted) FocusScope.of(context).unfocus();
  }

  Future<void> _settings() async {
    final saved = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      backgroundColor: Palette.white,
      builder: (context) => SettingsSheet(api: _api),
    );
    if (saved == true) {
      // Another server: a new conversation, on a socket of its own.
      _conversationId = null;
      _homeDue = true;
      setState(() => _wire = Md2uiState.connecting);
      await _view.reload();
      await _start();
    }
  }

  @override
  Widget build(BuildContext context) {
    final working = _wire.working || _freshening;
    return Scaffold(
      backgroundColor: Palette.root,
      body: Column(
        children: [
          _Header(onHome: _goHome, onSettings: _settings, onOrders: () => _show('orders'), busy: _blocked),
          Expanded(
            child: Stack(
              children: [
                Positioned.fill(
                  child: Md2uiView(
                    controller: _view,
                    socketUri: _socketUri,
                    onOpen: _opened,
                    onPage: _afterPage,
                    onState: (state) => setState(() => _wire = state),
                    onAppAction: _onAppAction,
                    onLink: _onLink,
                  ),
                ),
                Positioned(
                  left: 0,
                  right: 0,
                  bottom: 16,
                  child: IgnorePointer(
                    child: AnimatedSwitcher(
                      duration: const Duration(milliseconds: 180),
                      child: working
                          ? Center(
                              key: ValueKey(_wire.working),
                              child: WorkingPill(label: _wire.working ? _wire.note ?? 'Cooking up your answer…' : 'Freshening up your page…'),
                            )
                          : const SizedBox.shrink(),
                    ),
                  ),
                ),
              ],
            ),
          ),
          _Footer(
            prompt: _prompt,
            hint: _wire.placeholder ?? _ownHint,
            cart: _cart,
            busy: _blocked,
            onSend: _send,
            onTyping: _view.typing,
            onViewCart: () => _show('cart'),
            onCheckout: _checkout,
          ),
        ],
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.onHome, required this.onSettings, required this.onOrders, required this.busy});
  final VoidCallback onHome;
  final VoidCallback onSettings;
  final VoidCallback onOrders;
  final bool busy;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: const BoxDecoration(color: Palette.white, border: Border(bottom: BorderSide(color: Palette.border))),
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 10, 12, 10),
          child: Row(
            children: [
              Semantics(
                button: true,
                label: 'Burger Shop, home. Long-press for the server settings.',
                child: GestureDetector(
                  onTap: onHome,
                  onLongPress: onSettings,
                  child: SvgPicture.asset('assets/brand/logo.svg', height: 32, excludeFromSemantics: true),
                ),
              ),
              const Spacer(),
              TextButton.icon(
                onPressed: busy ? null : onOrders,
                style: TextButton.styleFrom(
                  backgroundColor: Palette.cream,
                  foregroundColor: Palette.forest,
                  minimumSize: const Size(0, 40),
                  padding: const EdgeInsets.symmetric(horizontal: 14),
                  shape: const StadiumBorder(),
                  textStyle: const TextStyle(fontFamily: Fonts.heading, fontWeight: FontWeight.w700, fontSize: 14),
                ),
                icon: const Icon(Icons.receipt_long_outlined, size: 18),
                label: const Text('My orders'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Footer extends StatelessWidget {
  const _Footer({
    required this.prompt,
    required this.hint,
    required this.cart,
    required this.busy,
    required this.onSend,
    required this.onTyping,
    required this.onViewCart,
    required this.onCheckout,
  });
  final TextEditingController prompt;
  final String hint;
  final CartBadge cart;
  final bool busy;
  final VoidCallback onSend;
  final VoidCallback onTyping;
  final VoidCallback onViewCart;
  final VoidCallback onCheckout;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: Palette.white,
        border: const Border(top: BorderSide(color: Palette.border)),
        boxShadow: [BoxShadow(color: Palette.forest.withValues(alpha: 0.06), blurRadius: 24, offset: const Offset(0, -6))],
      ),
      child: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(children: [
                Expanded(
                  child: TextField(
                    controller: prompt,
                    enabled: !busy,
                    textInputAction: TextInputAction.send,
                    onChanged: (_) => onTyping(),
                    onSubmitted: (_) => onSend(),
                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500, color: Palette.ink),
                    decoration: InputDecoration(hintText: hint),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  onPressed: busy ? null : onSend,
                  style: IconButton.styleFrom(
                    backgroundColor: Palette.forest,
                    foregroundColor: Palette.white,
                    minimumSize: const Size.square(44),
                  ),
                  icon: const Icon(Icons.send_rounded, size: 20),
                  tooltip: 'Send',
                ),
              ]),
              const SizedBox(height: 12),
              Row(children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      FittedBox(
                        fit: BoxFit.scaleDown,
                        alignment: Alignment.centerLeft,
                        child: Text(cart.totalLabel,
                            style: const TextStyle(
                                fontFamily: Fonts.heading,
                                fontWeight: FontWeight.w800,
                                fontSize: 26,
                                height: 1.1,
                                color: Palette.ink)),
                      ),
                      Text(cart.countLabel, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: Palette.muted)),
                    ],
                  ),
                ),
                OutlinedButton(onPressed: busy ? null : onViewCart, child: const Text('View cart')),
                const SizedBox(width: 8),
                FilledButton(onPressed: busy || cart.itemCount == 0 ? null : onCheckout, child: const Text('Checkout')),
              ]),
            ],
          ),
        ),
      ),
    );
  }
}
