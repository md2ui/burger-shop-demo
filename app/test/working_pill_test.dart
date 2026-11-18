import 'package:burger_shop/widgets/working_pill.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('the pill says what is happening, and its dots move', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: Scaffold(body: Center(child: WorkingPill(label: 'Cooking up your answer…')))));
    expect(find.text('Cooking up your answer…'), findsOneWidget);
    final dot = find.byType(Transform).first;
    final before = tester.widget<Transform>(dot).transform.getTranslation().y;
    await tester.pump(const Duration(milliseconds: 250));
    expect(tester.widget<Transform>(dot).transform.getTranslation().y, isNot(before));
  });
}
