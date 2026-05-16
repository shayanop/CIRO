import 'package:flutter/material.dart';

const _kPrimary = Color(0xFF00D4FF);
const _kSecondary = Color(0xFF7B2FBE);
const _kBg = Color(0xFF0A0E1A);
const _kSurface = Color(0xFF141929);
const _kCard = Color(0xFF1C2340);

const severityColors = {
  'low': Color(0xFF4CAF50),
  'medium': Color(0xFFFF9800),
  'high': Color(0xFFFF5722),
  'critical': Color(0xFFF44336),
};

const agentColors = {
  'signal': Color(0xFF2196F3),
  'detect': Color(0xFF9C27B0),
  'reason': Color(0xFFE91E63),
  'plan': Color(0xFFFF9800),
  'simulate': Color(0xFF4CAF50),
};

ThemeData ciroTheme() => ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: _kBg,
      colorScheme: const ColorScheme.dark(
        primary: _kPrimary,
        secondary: _kSecondary,
        surface: _kSurface,
        background: _kBg,
      ),
      cardColor: _kCard,
      appBarTheme: const AppBarTheme(
        backgroundColor: _kBg,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          color: _kPrimary,
          fontSize: 20,
          fontWeight: FontWeight.bold,
          letterSpacing: 1.2,
        ),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: _kSurface,
        selectedItemColor: _kPrimary,
        unselectedItemColor: Colors.white38,
        type: BottomNavigationBarType.fixed,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: _kPrimary,
          foregroundColor: _kBg,
          textStyle: const TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
      chipTheme: const ChipThemeData(
        backgroundColor: _kCard,
        labelStyle: TextStyle(color: Colors.white70, fontSize: 11),
        padding: EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      ),
      dividerColor: Colors.white12,
    );
