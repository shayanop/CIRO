import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:shared_preferences/shared_preferences.dart';

class Config {
  static const _urlKey = 'server_url';
  static SharedPreferences? _prefs;

  static Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  static String get _defaultUrl =>
      kIsWeb ? 'http://localhost:8000' : 'http://10.0.2.2:8000';

  static String get baseUrl => _prefs?.getString(_urlKey) ?? _defaultUrl;

  static Future<void> setBaseUrl(String url) async {
    final clean = url.trimRight().replaceAll(RegExp(r'/$'), '');
    await _prefs?.setString(_urlKey, clean);
  }

  static Future<void> resetUrl() async {
    await _prefs?.remove(_urlKey);
  }
}
