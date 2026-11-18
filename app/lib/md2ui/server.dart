// Serves the bundled md2ui page (assets/md2ui, built by tool/sync_md2ui.sh) on
// http://localhost, so the web view gets a secure context: ES modules, on-demand chunks,
// the fetch of THEME.md and FontFace loads all need one, and file:// is not.

import 'package:flutter_inappwebview/flutter_inappwebview.dart';

abstract final class Md2uiServer {
  static const port = 8787;
  static final _server = InAppLocalhostServer(port: port, documentRoot: 'assets/md2ui');

  static final pageUri = Uri(scheme: 'http', host: 'localhost', port: port, path: '/embed.html');

  /// Starts the server once; later calls return at once.
  static Future<void> ensureStarted() async {
    if (!_server.isRunning()) await _server.start();
  }
}
