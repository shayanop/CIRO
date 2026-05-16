import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:ciro_app/main.dart';
import 'package:ciro_app/services/app_state.dart';

void main() {
  testWidgets('App launches with bottom nav', (WidgetTester tester) async {
    await tester.pumpWidget(
      ChangeNotifierProvider(
        create: (_) => AppState(),
        child: const CiroApp(),
      ),
    );
    expect(find.byType(BottomNavigationBar), findsOneWidget);
  });
}
