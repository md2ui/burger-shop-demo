// The md2ui view: the app's embed page (web/embed.html, built into assets/md2ui) in a web
// view, served on localhost. The page opens md2ui's socket itself, as the web app does, so
// pages and taps never pass through the app: it asks the app only for the socket's ticket,
// and tells it what the chrome follows (the agent's state, a page arrived, the page's own
// Home and Checkout, links).

import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';

import '../palette.dart';
import 'server.dart';
import 'theme.dart';

/// What the chrome follows, as md2ui's state frame says it (md2ui ADR-613): whether input
/// waits ([blocked]: before the socket listens, while the agent works, while the app holds
/// the view), whether the agent is [working] and on what step ([note]), and the question it
/// waits on, for the prompt field ([placeholder]).
class Md2uiState {
  const Md2uiState({required this.blocked, this.working = false, this.note, this.placeholder});
  Md2uiState.fromJson(Map json)
      : blocked = json['blocked'] as bool? ?? true,
        working = json['working'] as bool? ?? false,
        note = json['note'] as String?,
        placeholder = json['placeholder'] as String?;
  static const connecting = Md2uiState(blocked: true);

  final bool blocked;
  final bool working;
  final String? note;
  final String? placeholder;
}

/// Drives a [Md2uiView]: when it opens the socket, when the app holds it, what the prompt
/// field sends.
class Md2uiController {
  InAppWebViewController? _web;
  bool _ready = false;
  bool _connect = false;
  bool _held = false;

  /// Opens md2ui's socket once the page is ready; after a reload, again.
  Future<void> connect() async {
    _connect = true;
    if (_ready) await _call('connect');
  }

  /// Holds the view while the app's payment sheet is open, or lets it go.
  Future<void> hold(bool held) async {
    _held = held;
    if (_ready) await _call('hold', held);
  }

  /// Sends what the customer typed as md2ui's prompt; false when it may not go now.
  Future<bool> prompt(String text) async => _ready && await _call('prompt', text) == true;

  /// A key pressed in the prompt field.
  Future<void> typing() async {
    if (_ready) await _call('typing');
  }

  /// Loads the page afresh: a new socket, for another server.
  Future<void> reload() async {
    _ready = false;
    await _web?.reload();
  }

  Future<void> _onHostReady() async {
    _ready = true;
    await _call('theme', md2uiTheme);
    if (_held) await _call('hold', true);
    if (_connect) await _call('connect');
  }

  Future<Object?> _call(String method, [Object? argument]) =>
      _web?.evaluateJavascript(source: 'window.md2uiHost.$method(${argument == null ? '' : jsonEncode(argument)})') ??
      Future.value();
}

class Md2uiView extends StatefulWidget {
  const Md2uiView({
    super.key,
    required this.controller,
    required this.socketUri,
    required this.onOpen,
    required this.onPage,
    required this.onState,
    required this.onAppAction,
    required this.onLink,
  });

  final Md2uiController controller;

  /// md2ui's socket with a fresh one-time ticket from the shop; null when there is none.
  final Future<Uri?> Function() socketUri;
  final VoidCallback onOpen;
  final VoidCallback onPage;
  final void Function(Md2uiState state) onState;

  /// The page's `agent:home` or `agent:checkout`: the app's own home page and payment sheet.
  final void Function(String slug) onAppAction;
  final void Function(Uri link) onLink;

  @override
  State<Md2uiView> createState() => _Md2uiViewState();
}

class _Md2uiViewState extends State<Md2uiView> {
  late final Future<void> _serverReady = Md2uiServer.ensureStarted();

  void _registerHandlers(InAppWebViewController web) {
    web.addJavaScriptHandler(handlerName: 'md2uiHostReady', callback: (_) => widget.controller._onHostReady());
    web.addJavaScriptHandler(
      handlerName: 'md2uiSession',
      callback: (_) async {
        final uri = await widget.socketUri();
        return uri == null ? null : {'url': '$uri'};
      },
    );
    web.addJavaScriptHandler(handlerName: 'md2uiOpen', callback: (_) => widget.onOpen());
    web.addJavaScriptHandler(handlerName: 'md2uiPage', callback: (_) => widget.onPage());
    web.addJavaScriptHandler(
      handlerName: 'md2uiState',
      callback: (args) => widget.onState(Md2uiState.fromJson(args.first as Map)),
    );
    web.addJavaScriptHandler(
      handlerName: 'md2uiAppAction',
      callback: (args) => widget.onAppAction('${(args.first as Map)['slug']}'),
    );
    web.addJavaScriptHandler(
      handlerName: 'md2uiLink',
      callback: (args) {
        final uri = Uri.tryParse('${(args.first as Map)['href']}');
        if (uri != null) widget.onLink(uri);
      },
    );
    web.addJavaScriptHandler(handlerName: 'md2uiError', callback: (args) => debugPrint('md2ui: ${args.first}'));
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<void>(
      future: _serverReady,
      builder: (context, snapshot) {
        if (snapshot.hasError) {
          return Center(child: Text('The local page server did not start: ${snapshot.error}'));
        }
        if (snapshot.connectionState != ConnectionState.done) return const ColoredBox(color: Palette.root);
        return InAppWebView(
          initialUrlRequest: URLRequest(url: WebUri.uri(Md2uiServer.pageUri)),
          initialSettings: InAppWebViewSettings(
            isInspectable: kDebugMode, // Safari > Develop, chrome://inspect
            transparentBackground: true,
            supportZoom: false,
            disableHorizontalScroll: true,
            allowsBackForwardNavigationGestures: false,
            allowsLinkPreview: false,
          ),
          onWebViewCreated: (web) {
            widget.controller._web = web;
            _registerHandlers(web);
          },
          // Only the local page loads here; links go to the app.
          shouldOverrideUrlLoading: (web, action) async {
            final url = action.request.url;
            if (url == null || url.host == 'localhost') return NavigationActionPolicy.ALLOW;
            widget.onLink(url);
            return NavigationActionPolicy.CANCEL;
          },
          onConsoleMessage: (web, message) {
            if (kDebugMode) debugPrint('[md2ui] ${message.messageLevel} ${message.message}');
          },
        );
      },
    );
  }
}
