// The shop backend's HTTP API (backend/main.py), as the app uses it beside md2ui's socket,
// which the embed page opens itself: the same calls as the web app (web/src/api.ts). The
// backend keeps the conversation; the app only holds its id. Every page arrives over the
// socket, never in an answer here.
//
//   session / socketUri  a one-time ticket for md2ui's socket, and the URL that spends it
//   state                the footer's badge, and the agent's payment window if its turn waits
//   home / freshHome     the home page at once, then the home writer's version
//   nav                  a page of the app's own buttons (View cart, My orders, the
//                        confirmation after the footer's payment), with no agent turn
//   resume               the end of the agent's payment window
//   openCheckout / pay / cancelCheckout   the sandbox payment window

import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

class ApiException implements Exception {
  ApiException(this.message, {this.statusCode});
  final String message;
  final int? statusCode;
  @override
  String toString() => message;
}

class CartBadge {
  const CartBadge({required this.itemCount, required this.totalLabel});
  CartBadge.fromJson(Map json)
      : itemCount = json['item_count'] as int,
        totalLabel = json['total_label'] as String;
  static const empty = CartBadge(itemCount: 0, totalLabel: r'$0.00');

  final int itemCount;
  final String totalLabel;
  String get countLabel => itemCount == 1 ? '1 item' : '$itemCount items';
}

class CheckoutLine {
  CheckoutLine.fromJson(Map json)
      : name = json['name'] as String,
        quantity = json['quantity'] as int,
        lineTotal = json['line_total'] as String;
  final String name;
  final int quantity;
  final String lineTotal;
}

class Checkout {
  Checkout.fromJson(Map json)
      : sessionId = json['session_id'] as String,
        status = json['status'] as String,
        lines = [for (final l in json['lines'] as List) CheckoutLine.fromJson(l as Map)],
        delivery = json['delivery'] as String,
        total = json['total'] as String,
        orderId = json['order_id'] as String?,
        error = json['error'] as String?,
        cart = json['cart'] == null ? null : CartBadge.fromJson(json['cart'] as Map);

  final String sessionId;
  final String status; // open | paid | cancelled | failed
  final List<CheckoutLine> lines;
  final String delivery;
  final String total;
  final String? orderId;
  final String? error;
  final CartBadge? cart;
}

class PendingCheckout {
  PendingCheckout.fromJson(Map json)
      : toolUseId = json['tool_use_id'] as String,
        toolName = json['tool_name'] as String,
        checkout = Checkout.fromJson(json['checkout'] as Map);
  final String toolUseId;
  final String toolName;
  final Checkout checkout;
}

/// What the footer shows, read after every page: the badge, and the agent's payment window
/// when its turn waits on one (its open_checkout tool).
class ShopState {
  ShopState.fromJson(Map json)
      : cart = CartBadge.fromJson(json['cart'] as Map),
        pending = json['pending_action'] == null ? null : PendingCheckout.fromJson(json['pending_action'] as Map);
  final CartBadge cart;
  final PendingCheckout? pending;
}

/// A one-time ticket for md2ui's socket, and the conversation it joins.
class Session {
  Session.fromJson(Map json)
      : conversationId = json['conversation_id'] as String,
        ticket = json['ticket'] as String;
  final String conversationId;
  final String ticket;
}

class HomeResponse {
  HomeResponse.fromJson(Map json)
      : conversationId = json['conversation_id'] as String,
        token = json['token'] as int,
        cart = CartBadge.fromJson(json['cart'] as Map),
        fresh = json['fresh'] as bool? ?? false;
  final String conversationId;
  final int token;
  final CartBadge cart;

  /// From home: true when the session has no saved home that fits, so ask for a fresh one.
  final bool fresh;
}

class ShopApi {
  ShopApi(this.baseUrl, {http.Client? client}) : _http = client ?? http.Client();

  String baseUrl;
  final http.Client _http;

  // An agent turn can take a while; everything else is quick.
  static const _agentTimeout = Duration(minutes: 3);
  static const _appTimeout = Duration(seconds: 20);

  Uri _uri(String path) => Uri.parse('${baseUrl.replaceAll(RegExp(r'/+$'), '')}$path');

  Future<Map<String, dynamic>> health() => _send('GET', '/api/health');

  Future<ShopState> state(String? conversationId) async => ShopState.fromJson(await _send(
      'GET', conversationId == null ? '/api/state' : '/api/state?conversation_id=${Uri.encodeQueryComponent(conversationId)}'));

  /// A ticket for this conversation, or for a new one when the server does not know it.
  Future<Session> session(String? conversationId) async =>
      Session.fromJson(await _send('POST', '/api/session', body: {'conversation_id': conversationId}));

  /// md2ui's socket on the shop's server, opened with [ticket] (spent once, within 30 s).
  Uri socketUri(String ticket) {
    final base = _uri('/md2ui/ws');
    return base.replace(scheme: base.scheme == 'https' ? 'wss' : 'ws', queryParameters: {'ticket': ticket});
  }

  Future<HomeResponse> home(String? conversationId) async =>
      HomeResponse.fromJson(await _send('POST', '/api/home', body: {'conversation_id': conversationId}));

  Future<HomeResponse> freshHome(String conversationId, int token) async => HomeResponse.fromJson(await _send(
      'POST', '/api/home/fresh',
      body: {'conversation_id': conversationId, 'token': token}, timeout: _agentTimeout));

  /// A page of the app's own buttons: `cart`, `orders`, or `success` after the app's payment.
  Future<void> nav(String conversationId, String to) =>
      _send('POST', '/api/nav', body: {'conversation_id': conversationId, 'to': to});

  /// The payment window closed. Carries no outcome: the backend reads the checkout session.
  Future<void> resume(String conversationId, String toolUseId) => _send(
      'POST', '/api/resume',
      body: {'conversation_id': conversationId, 'tool_use_id': toolUseId}, timeout: _agentTimeout);

  Future<Checkout> openCheckout() async => Checkout.fromJson(await _send('POST', '/api/checkout'));

  /// The sandbox card form. The card number goes only here, never through the agent.
  Future<Checkout> pay(String sessionId, {required String cardNumber, required String expiry, required String cvc, String name = ''}) async =>
      Checkout.fromJson(await _send('POST', '/api/checkout/${Uri.encodeComponent(sessionId)}/pay',
          body: {'card_number': cardNumber, 'expiry': expiry, 'cvc': cvc, 'name': name}));

  Future<Checkout> cancelCheckout(String sessionId) async =>
      Checkout.fromJson(await _send('POST', '/api/checkout/${Uri.encodeComponent(sessionId)}/cancel'));

  Future<Map<String, dynamic>> _send(String method, String path, {Object? body, Duration timeout = _appTimeout}) async {
    final http.Response response;
    try {
      final request = http.Request(method, _uri(path));
      if (body != null) {
        request.headers['content-type'] = 'application/json';
        request.body = jsonEncode(body);
      }
      response = await http.Response.fromStream(await _http.send(request).timeout(timeout));
    } on TimeoutException {
      throw ApiException('The shop took too long to answer.');
    } on Exception catch (e) {
      throw ApiException('Could not reach the shop at $baseUrl ($e).');
    }
    final data = response.body.isEmpty ? <String, dynamic>{} : jsonDecode(utf8.decode(response.bodyBytes));
    if (response.statusCode >= 400) {
      final detail = data is Map ? data['detail'] : null;
      throw ApiException(detail is String ? detail : 'HTTP ${response.statusCode}', statusCode: response.statusCode);
    }
    return Map<String, dynamic>.from(data as Map);
  }
}
