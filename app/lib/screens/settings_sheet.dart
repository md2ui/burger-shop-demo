// Where the shop's backend is, with a connection test: points a physical phone at the
// laptop's LAN IP (http://192.168.1.50:8000) or an https tunnel without a rebuild.

import 'package:flutter/material.dart';

import '../api/shop_api.dart';
import '../palette.dart';
import '../settings.dart';

class SettingsSheet extends StatefulWidget {
  const SettingsSheet({super.key, required this.api});
  final ShopApi api;

  @override
  State<SettingsSheet> createState() => _SettingsSheetState();
}

class _SettingsSheetState extends State<SettingsSheet> {
  late final _url = TextEditingController(text: widget.api.baseUrl);
  String? _status;
  bool _testing = false;

  @override
  void dispose() {
    _url.dispose();
    super.dispose();
  }

  Future<void> _test() async {
    setState(() {
      _testing = true;
      _status = null;
    });
    try {
      final health = await ShopApi(_url.text.trim()).health();
      _status = 'Connected: ${health['model']} (${health['runtime']})';
    } on ApiException catch (e) {
      _status = e.message;
    }
    if (mounted) setState(() => _testing = false);
  }

  Future<void> _save() async {
    await AppSettings.saveBaseUrl(_url.text);
    widget.api.baseUrl = _url.text.trim();
    if (mounted) Navigator.of(context).pop(true);
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(24, 0, 24, 24 + MediaQuery.of(context).viewInsets.bottom),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text('Shop server', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 12),
          TextField(
            controller: _url,
            keyboardType: TextInputType.url,
            autocorrect: false,
            decoration: const InputDecoration(hintText: 'http://192.168.1.50:8000'),
          ),
          const SizedBox(height: 8),
          const Text(
            'iOS simulator: http://localhost:8000 · Android emulator: http://10.0.2.2:8000 · '
            'A phone: your Mac\'s IP on the same Wi-Fi (start the backend with --host 0.0.0.0), or an https tunnel.',
            style: TextStyle(fontSize: 12, color: Palette.muted),
          ),
          if (_status != null) ...[const SizedBox(height: 12), Text(_status!)],
          const SizedBox(height: 16),
          Row(children: [
            Expanded(
              child: OutlinedButton(onPressed: _testing ? null : _test, child: Text(_testing ? 'Testing…' : 'Test')),
            ),
            const SizedBox(width: 12),
            Expanded(child: FilledButton(onPressed: _save, child: const Text('Save'))),
          ]),
          TextButton(
            onPressed: () async {
              await AppSettings.resetBaseUrl();
              _url.text = AppSettings.platformDefault;
            },
            child: const Text('Back to the default'),
          ),
        ],
      ),
    );
  }
}
