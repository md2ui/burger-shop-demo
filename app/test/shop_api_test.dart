// The API client against a scripted backend: what it sends, and what it makes of answers.

import 'dart:convert';

import 'package:burger_shop/api/shop_api.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _cart = {'item_count': 2, 'total': 21.99, 'total_label': r'$21.99'};

void main() {
  late List<http.Request> sent;

  ShopApi api(Map<String, Object?> Function(http.Request) answer, {int status = 200}) {
    sent = [];
    return ShopApi('http://shop.test/', client: MockClient((request) async {
      sent.add(request);
      return http.Response(jsonEncode(answer(request)), status, headers: {'content-type': 'application/json'});
    }));
  }

  test('a ticket for md2ui\'s socket, and the URL that spends it', () async {
    final shop = api((_) => {'conversation_id': 'conv_1', 'ticket': 'tk-1/+'});
    final session = await shop.session(null);
    expect(sent.single.url.toString(), 'http://shop.test/api/session');
    expect(jsonDecode(sent.single.body), {'conversation_id': null});
    expect(session.conversationId, 'conv_1');
    expect(shop.socketUri(session.ticket).toString(), 'ws://shop.test/md2ui/ws?ticket=tk-1%2F%2B');
    expect(ShopApi('https://shop.example:8443').socketUri('t').toString(), 'wss://shop.example:8443/md2ui/ws?ticket=t');
  });

  test('the app\'s own buttons are pages, shown with no answer of their own', () async {
    final shop = api((_) => {});
    await shop.nav('conv_1', 'cart');
    expect(sent.single.url.path, '/api/nav');
    expect(jsonDecode(sent.single.body), {'conversation_id': 'conv_1', 'to': 'cart'});
  });

  test('after a page, the state says when the agent\'s turn waits on the payment window', () async {
    final shop = api((_) => {
          'cart': _cart,
          'pending_action': {
            'tool_use_id': 'tu_pay',
            'tool_name': 'open_checkout',
            'checkout': {
              'session_id': 'cs_1',
              'status': 'open',
              'lines': [
                {'name': 'Classic Smash', 'quantity': 2, 'line_total': r'$19.00'},
              ],
              'item_count': 2,
              'subtotal': r'$19.00',
              'delivery': r'$2.99',
              'total': r'$21.99',
              'order_id': null,
              'error': null,
            },
          },
        });
    final r = await shop.state('conv_1');
    expect(sent.single.url.toString(), 'http://shop.test/api/state?conversation_id=conv_1');
    expect(r.cart.countLabel, '2 items');
    expect(r.pending!.toolName, 'open_checkout');
    expect(r.pending!.checkout.total, r'$21.99');
    expect(r.pending!.checkout.lines.single.quantity, 2);
  });

  test('home says whether to ask for a fresh one', () async {
    final shop = api((_) => {'conversation_id': 'conv_1', 'token': 3, 'cart': _cart, 'fresh': true});
    final r = await shop.home(null);
    expect(jsonDecode(sent.single.body), {'conversation_id': null});
    expect((r.fresh, r.token), (true, 3));
  });

  test('the card number goes only to the pay endpoint', () async {
    final shop = api((_) => {
          'session_id': 'cs_1', 'status': 'paid', 'lines': [], 'item_count': 2, 'subtotal': r'$19.00',
          'delivery': 'Free', 'total': r'$19.00', 'order_id': 'BS-1043', 'error': null, 'cart': _cart,
        });
    final r = await shop.pay('cs_1', cardNumber: '4242 4242 4242 4242', expiry: '12/30', cvc: '123');
    expect(sent.single.url.path, '/api/checkout/cs_1/pay');
    expect(jsonDecode(sent.single.body)['card_number'], '4242 4242 4242 4242');
    expect((r.status, r.orderId), ('paid', 'BS-1043'));
  });

  test('a refusal comes back as its detail, with its status', () async {
    final shop = api((_) => {'detail': 'the cart is empty'}, status: 409);
    await expectLater(
      shop.openCheckout(),
      throwsA(isA<ApiException>()
          .having((e) => e.message, 'message', 'the cart is empty')
          .having((e) => e.statusCode, 'status', 409)),
    );
  });
}
