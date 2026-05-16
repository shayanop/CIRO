import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/models.dart';
import '../services/app_state.dart';

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
            backgroundColor: const Color(0xFF1C2340),
            content: Text(
              'Pipeline complete · ${result.event.crisisType.toUpperCase()} · ${result.event.location}',
              style: const TextStyle(color: Color(0xFF00D4FF)),
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
      decoration: const BoxDecoration(
        color: Color(0xFF141929),
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(
              width: 40, height: 4,
              decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2)),
            ),
          ),
          const SizedBox(height: 16),
          const Text('SUBMIT SIGNAL', style: TextStyle(color: Color(0xFF00D4FF), fontWeight: FontWeight.bold, letterSpacing: 1.5)),
          const SizedBox(height: 16),

          // Quick presets
          const Text('PRESETS', style: TextStyle(color: Colors.white38, fontSize: 10, letterSpacing: 1)),
          const SizedBox(height: 6),
          Wrap(
            spacing: 6,
            runSpacing: 4,
            children: _defaultSignals.entries.map((e) => ActionChip(
              label: Text(e.key.replaceAll('_', ' ').toUpperCase(), style: const TextStyle(fontSize: 9)),
              backgroundColor: const Color(0xFF1C2340),
              labelStyle: const TextStyle(color: Color(0xFF00D4FF)),
              onPressed: () => _textController.text = e.value,
            )).toList(),
          ),
          const SizedBox(height: 14),

          // Text field
          TextField(
            controller: _textController,
            style: const TextStyle(color: Colors.white),
            maxLines: 4,
            decoration: InputDecoration(
              hintText: 'Type signal text in Urdu or English…',
              hintStyle: const TextStyle(color: Colors.white30),
              filled: true,
              fillColor: const Color(0xFF1C2340),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10),
                borderSide: const BorderSide(color: Colors.white12),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10),
                borderSide: const BorderSide(color: Color(0xFF00D4FF)),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10),
                borderSide: const BorderSide(color: Colors.white12),
              ),
            ),
          ),
          const SizedBox(height: 14),

          // Source + language row
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('SOURCE', style: TextStyle(color: Colors.white38, fontSize: 10, letterSpacing: 1)),
                    const SizedBox(height: 4),
                    DropdownButtonFormField<String>(
                      value: _source,
                      dropdownColor: const Color(0xFF1C2340),
                      style: const TextStyle(color: Colors.white),
                      decoration: _inputDeco(),
                      items: const [
                        DropdownMenuItem(value: 'social', child: Text('Social')),
                        DropdownMenuItem(value: 'weather', child: Text('Weather')),
                        DropdownMenuItem(value: 'traffic', child: Text('Traffic')),
                      ],
                      onChanged: (v) => setState(() => _source = v!),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('LANGUAGE', style: TextStyle(color: Colors.white38, fontSize: 10, letterSpacing: 1)),
                    const SizedBox(height: 4),
                    ToggleButtons(
                      isSelected: [_lang == 'ur', _lang == 'en'],
                      onPressed: (i) => setState(() => _lang = i == 0 ? 'ur' : 'en'),
                      selectedColor: const Color(0xFF00D4FF),
                      color: Colors.white38,
                      fillColor: const Color(0xFF00D4FF).withOpacity(0.1),
                      borderColor: Colors.white12,
                      selectedBorderColor: const Color(0xFF00D4FF),
                      borderRadius: BorderRadius.circular(8),
                      constraints: const BoxConstraints(minWidth: 52, minHeight: 40),
                      children: const [Text('🇵🇰 UR'), Text('🇬🇧 EN')],
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),

          // Submit
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: _submitting ? null : _submit,
              icon: _submitting
                  ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black))
                  : const Icon(Icons.send),
              label: Text(_submitting ? 'PROCESSING...' : 'SUBMIT & RUN PIPELINE'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 14),
              ),
            ),
          ),
        ],
      ),
    );
  }

  InputDecoration _inputDeco() => InputDecoration(
        filled: true,
        fillColor: const Color(0xFF1C2340),
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: Colors.white12)),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: Colors.white12)),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: Color(0xFF00D4FF))),
      );
}
