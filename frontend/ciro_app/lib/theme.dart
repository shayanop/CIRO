import 'package:flutter/material.dart';

// ── Colour palette ──────────────────────────────────────────────────────────
const kPrimary    = Color(0xFF00D4FF);
const kSecondary  = Color(0xFF7B2FBE);
const kAccent     = Color(0xFF00FF9D);
const kDanger     = Color(0xFFFF3B5C);
const kWarning    = Color(0xFFFFAA00);
const kBg         = Color(0xFF060A14);
const kSurface    = Color(0xFF0F1628);
const kCard       = Color(0xFF161D33);
const kCardBorder = Color(0xFF1E2A45);

// ── Severity colours ─────────────────────────────────────────────────────────
const severityColors = <String, Color>{
  'low'     : Color(0xFF4ADE80),
  'medium'  : Color(0xFFFBBF24),
  'high'    : Color(0xFFF97316),
  'critical': Color(0xFFEF4444),
};

// ── Agent colours ─────────────────────────────────────────────────────────────
const agentColors = <String, Color>{
  'signal'  : Color(0xFF3B82F6),
  'detect'  : Color(0xFFA855F7),
  'reason'  : Color(0xFFEC4899),
  'plan'    : Color(0xFFF59E0B),
  'simulate': Color(0xFF10B981),
};

// ── Crisis type colours ───────────────────────────────────────────────────────
const crisisColors = <String, Color>{
  'flood'         : Color(0xFF38BDF8),
  'heatwave'      : Color(0xFFF97316),
  'blockage'      : Color(0xFFFBBF24),
  'accident'      : Color(0xFFEF4444),
  'infrastructure': Color(0xFF94A3B8),
  'fire'          : Color(0xFFEF4444),
  'earthquake'    : Color(0xFFA78BFA),
  'storm'         : Color(0xFF60A5FA),
};

// ── Glassmorphism helper ──────────────────────────────────────────────────────
BoxDecoration glassDecoration({Color? borderColor, double opacity = 0.08}) =>
    BoxDecoration(
      color: Colors.white.withOpacity(opacity),
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: borderColor ?? kCardBorder, width: 1),
    );

// ── Theme ─────────────────────────────────────────────────────────────────────
ThemeData ciroTheme() => ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: kBg,
      fontFamily: 'Roboto',
      colorScheme: const ColorScheme.dark(
        primary:    kPrimary,
        secondary:  kSecondary,
        surface:    kSurface,
        background: kBg,
        error:      kDanger,
      ),
      cardColor: kCard,
      textTheme: const TextTheme(
        displayLarge  : TextStyle(color: Colors.white,   fontWeight: FontWeight.w800),
        headlineMedium: TextStyle(color: Colors.white,   fontWeight: FontWeight.w700),
        titleMedium   : TextStyle(color: Colors.white70),
        bodyMedium    : TextStyle(color: Colors.white60, fontSize: 13),
        labelSmall    : TextStyle(color: Colors.white38, fontSize: 10, letterSpacing: 1.2),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: kBg,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          color: kPrimary,
          fontSize: 20,
          fontWeight: FontWeight.w800,
          letterSpacing: 0.8,
          fontFamily: 'Roboto',
        ),
        iconTheme: IconThemeData(color: Colors.white70),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: kSurface,
        selectedItemColor: kPrimary,
        unselectedItemColor: Colors.white38,
        type: BottomNavigationBarType.fixed,
        elevation: 0,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: kPrimary,
          foregroundColor: kBg,
          textStyle: const TextStyle(
              fontWeight: FontWeight.w700, fontSize: 13, fontFamily: 'Roboto'),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
      chipTheme: const ChipThemeData(
        backgroundColor: kCard,
        labelStyle: TextStyle(color: Colors.white70, fontSize: 11),
        padding: EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      ),
      dividerColor: Color(0x0FFFFFFF),
      cardTheme: CardTheme(
        color: kCard,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
          side: const BorderSide(color: kCardBorder, width: 1),
        ),
        margin: EdgeInsets.zero,
      ),
    );
