// Where the shop's backend is, editable at runtime (the header's settings sheet) so a
// physical phone can point at the laptop's LAN IP or a tunnel without a rebuild.
//
// Precedence: the value saved in the sheet > --dart-define=API_BASE_URL > a default that
// works on simulators and emulators.

import 'dart:io' show Platform;

import 'package:shared_preferences/shared_preferences.dart';

abstract final class AppSettings {
  static const _key = 'api_base_url';
  static const _fromDefine = String.fromEnvironment('API_BASE_URL');

  static String get platformDefault {
    if (_fromDefine.isNotEmpty) return _fromDefine;
    // The Android emulator reaches the host machine at 10.0.2.2.
    return Platform.isAndroid ? 'http://10.0.2.2:8000' : 'http://localhost:8000';
  }

  static Future<String> loadBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_key) ?? platformDefault;
  }

  static Future<void> saveBaseUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_key, url.trim());
  }

  static Future<void> resetBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_key);
  }
}
