// Burger Shop, the md2ui demo app: the shop's agent answers every request with an md2ui
// page, drawn in the app's theme between a native header and footer. The backend is the
// same one the web app uses (../backend).

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'api/shop_api.dart';
import 'palette.dart';
import 'screens/shop_screen.dart';
import 'settings.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(SystemUiOverlayStyle.dark.copyWith(statusBarColor: Palette.white));
  runApp(BurgerShopApp(api: ShopApi(await AppSettings.loadBaseUrl())));
}

class BurgerShopApp extends StatelessWidget {
  const BurgerShopApp({super.key, required this.api});
  final ShopApi api;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Burger Shop',
      debugShowCheckedModeBanner: false,
      theme: burgerTheme(),
      home: ShopScreen(api: api),
    );
  }
}
