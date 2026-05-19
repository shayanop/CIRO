import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/models.dart';
import '../services/app_state.dart';
import '../theme.dart';

const _defaultSignals = {
  'en_flood': 'G-10 mein pani bhar gaya hai, gaariyan phans gayi hain. Shadeed baarish jari hai.',
  'en_heat': 'Extreme heatwave in Karachi — 48°C recorded near Saddar. People collapsing on streets.',
  'en_block': 'Shahrah-e-Faisal completely jammed after truck accident near old airport.',
  'en_flood2': 'Flash flood in George Town Karachi — roads submerged, people on rooftops.',
  'en_storm': 'Severe storm warning for Lahore. Roads flooded near Liberty Roundabout.',
};

class BilingualInputSheet extends StatefulWidget {
  const BilingualInputSheet({super.key});

  @override
  State<BilingualInputSheet> createState() => _BilingualInputSheetState();
}

class _BilingualInputSheetState extends State<BilingualInputSheet> {
  final _textController = TextEditingController();
  String _source = 'social';
  String _lang = 'ur';
  bool _submitting = false;

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final text = _textController.text.trim();
    if (text.isEmpty) return;
    setState(() => _submitting = true);

    final input = RawSignalInput(
      source: _source,
      text: text,
      metadata: {'language_hint': _lang},
    );

    final result = await context.read<AppState>().runPipeline(input);

    if (mounted) {
      Navigator.pop(context);
      if (result != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            backgroundColor: kCard,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
              side: BorderSide(color: kCardBorder),
            ),
            content: Row(
              children: [
                const Icon(Icons.check_circle_rounded, color: kAccent, size: 20),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Pipeline complete · ${result.event.crisisType.toUpperCase()} · ${result.event.location}',
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      decoration: BoxDecoration(
        color: kBg,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
        border: Border(top: BorderSide(color: kCardBorder, width: 1.5)),
      ),
      padding: const EdgeInsets.fromLTRB(24, 16, 24, 32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(
              width: 48, height: 5,
              decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(3)),
            ),
          ),
          const SizedBox(height: 24),
          const Text('SUBMIT SIGNAL', style: TextStyle(color: kPrimary, fontWeight: FontWeight.w800, letterSpacing: 1.5)),
          const SizedBox(height: 20),

          // Quick presets
          const Text('PRESETS', style: TextStyle(color: Colors.white38, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1.2)),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: _defaultSignals.entries.map((e) => ActionChip(
              label: Text(e.key.replaceAll('_', ' ').toUpperCase(), style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold)),
              backgroundColor: kCard,
              side: BorderSide(color: kCardBorder),
              labelStyle: const TextStyle(color: kPrimary),
              padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 0),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              onPressed: () => _textController.text = e.value,
            )).toList(),
          ),
          const SizedBox(height: 20),

          // Text field
          TextField(
            controller: _textController,
            style: const TextStyle(color: Colors.white, fontSize: 14),
            maxLines: 4,
            decoration: InputDecoration(
              hintText: 'Type signal text in Urdu or English…',
              hintStyle: const TextStyle(color: Colors.white24),
              filled: true,
              fillColor: kCard,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(color: kCardBorder),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: kPrimary, width: 2),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(color: kCardBorder),
              ),
            ),
          ),
          const SizedBox(height: 20),

          // Source + language row
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('SOURCE', style: TextStyle(color: Colors.white38, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1.2)),
                    const SizedBox(height: 8),
                    DropdownButtonFormField<String>(
                      value: _source,
                      dropdownColor: kCard,
                      icon: const Icon(Icons.expand_more_rounded, color: Colors.white38),
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 14),
                      decoration: _inputDeco(),
                      items: const [
                        DropdownMenuItem(value: 'social', child: Text('Social Media')),
                        DropdownMenuItem(value: 'weather', child: Text('Weather API')),
                        DropdownMenuItem(value: 'traffic', child: Text('Traffic Data')),
                      ],
                      onChanged: (v) => setState(() => _source = v!),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('LANGUAGE', style: TextStyle(color: Colors.white38, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1.2)),
                    const SizedBox(height: 8),
                    ToggleButtons(
                      isSelected: [_lang == 'ur', _lang == 'en'],
                      onPressed: (i) => setState(() => _lang = i == 0 ? 'ur' : 'en'),
                      selectedColor: kBg,
                      color: Colors.white54,
                      fillColor: kPrimary,
                      borderColor: kCardBorder,
                      selectedBorderColor: kPrimary,
                      borderRadius: BorderRadius.circular(12),
                      textStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                      constraints: const BoxConstraints(minWidth: 64, minHeight: 48),
                      children: const [Text('🇵🇰 UR'), Text('🇬🇧 EN')],
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 32),

          // Submit
          SizedBox(
            width: double.infinity,
            height: 52,
            child: ElevatedButton.icon(
              onPressed: _submitting ? null : _submit,
              icon: _submitting
                  ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white38))
                  : const Icon(Icons.bolt_rounded, size: 22),
              label: Text(
                _submitting ? 'PROCESSING...' : 'SUBMIT & RUN PIPELINE',
                style: const TextStyle(fontWeight: FontWeight.w800, letterSpacing: 1),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: kPrimary,
                foregroundColor: kBg,
                disabledBackgroundColor: kCard,
                disabledForegroundColor: Colors.white24,
                elevation: _submitting ? 0 : 8,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
              ),
            ),
          ),
        ],
      ),
    );
  }

  InputDecoration _inputDeco() => InputDecoration(
        filled: true,
        fillColor: kCard,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: kCardBorder)),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: kCardBorder)),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: kPrimary, width: 2)),
      );
}
