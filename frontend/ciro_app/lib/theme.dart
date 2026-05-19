import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

// ── Colour palette ──────────────────────────────────────────────────────────
const kPrimary   = Color(0xFF00D4FF); // cyan
const kSecondary = Color(0xFF7B2FBE); // purple
const kAccent    = Color(0xFF00FF9D); // neon green
const kDanger    = Color(0xFFFF3B5C); // alarm red
const kWarning   = Color(0xFFFFAA00); // amber
const kBg        = Color(0xFF060A14); // near-black
const kSurface   = Color(0xFF0F1628); // dark navy
const kCard      = Color(0xFF161D33); // card bg
const kCardBorder= Color(0xFF1E2A45); // subtle border

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

// ── Crisis icon colours ───────────────────────────────────────────────────────
const crisisColors = <String, Color>{
  'flood'          : Color(0xFF38BDF8),
  'heatwave'       : Color(0xFFF97316),
  'blockage'       : Color(0xFFFBBF24),
  'accident'       : Color(0xFFEF4444),
  'infrastructure' : Color(0xFF94A3B8),
  'fire'           : Color(0xFFEF4444),
  'earthquake'     : Color(0xFFA78BFA),
  'storm'          : Color(0xFF60A5FA),
};

// ── Glassmorphism helper ──────────────────────────────────────────────────────
BoxDecoration glassDecoration({Color? borderColor, double opacity = 0.08}) =>
    BoxDecoration(
      color: Colors.white.withOpacity(opacity),
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: borderColor ?? kCardBorder, width: 1),
    );

ThemeData ciroTheme() => ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: kBg,
      colorScheme: const ColorScheme.dark(
        primary:    kPrimary,
        secondary:  kSecondary,
        surface:    kSurface,
        background: kBg,
        error:      kDanger,
      ),
      cardColor: kCard,
      textTheme: GoogleFonts.interTextTheme(ThemeData.dark().textTheme).copyWith(
        displayLarge : GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.w800),
        headlineMedium: GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.w700),
        titleMedium  : GoogleFonts.inter(color: Colors.white70),
        bodyMedium   : GoogleFonts.inter(color: Colors.white60, fontSize: 13),
        labelSmall   : GoogleFonts.inter(color: Colors.white38, fontSize: 10, letterSpacing: 1.2),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: kBg,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: GoogleFonts.inter(
          color: kPrimary,
          fontSize: 20,
          fontWeight: FontWeight.w800,
          letterSpacing: 0.8,
        ),
        iconTheme: const IconThemeData(color: Colors.white70),
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
          textStyle: GoogleFonts.inter(fontWeight: FontWeight.w700, fontSize: 13),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: kCard,
        labelStyle: GoogleFonts.inter(color: Colors.white70, fontSize: 11),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      ),
      dividerColor: Colors.white.withOpacity(0.06),
      cardTheme: CardTheme(
        color: kCard,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
          side: BorderSide(color: kCardBorder, width: 1),
        ),
        margin: EdgeInsets.zero,
      ),
    );
