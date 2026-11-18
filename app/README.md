# Burger Shop: the Flutter app

The md2ui demo as a phone app. A native header (the logo, My orders) and footer (the prompt
bar, the total, View cart, Checkout) sit around one md2ui view, in a web view. The shop's
agent answers every request with an md2ui page in the shop's theme. It is the same backend as
the web app (`../backend`) and the same flow (`../web/src/main.ts`): the view's page opens
md2ui's WebSocket itself, as the web page does, with the same client
(`../web/src/wire_view.ts`), so pages, taps and the prompt bar travel there and never through
Dart. The app asks the shop for the socket's one-time ticket and hands the page its URL.

```
app (Flutter)                                 backend/main.py (FastAPI)
  header · footer · payment sheet  ──HTTP──>   /api/session, /api/state, /api/home, /api/home/fresh,
                                               /api/nav, /api/resume, /api/checkout…
  md2ui view (web view)            ══WS════>   /md2ui/ws?ticket=…  (md2ui's socket)
    assets/md2ui/embed.html  <── built from web/embed.html + web/src/embed.ts (@md2ui/dom)
    assets/md2ui/theme/      <── backend/md2ui_theme: THEME.md, its fonts, the icon font
```

The page is served by the app on `http://localhost:8787` (`lib/md2ui/server.dart`), and that is
the origin its socket carries; the backend names it in `ALLOWED_ORIGINS` (its default).

## Layout

| Path | What |
|---|---|
| `lib/main.dart` | The app and its theme |
| `lib/palette.dart` | The palette and faces, the same as `THEME.md`, for the native parts |
| `lib/api/shop_api.dart` | The backend's API, the same calls as the web app's `api.ts` |
| `lib/screens/shop_screen.dart` | The screen: header, md2ui view, working pill, footer; where each tap goes |
| `lib/screens/pay_sheet.dart` | The sandbox payment sheet: pays the checkout session directly, never through the agent |
| `lib/screens/settings_sheet.dart` | The backend URL, with a connection test (long-press the logo) |
| `lib/widgets/working_pill.dart` | The "Cooking up your answer…" pill, the web's bouncing dots |
| `lib/md2ui/` | The view and its bridge (the ticket, md2ui's state for the chrome, the page's Home and Checkout), the local page server, the theme's fonts list |
| `tool/sync_md2ui.sh` | Builds the md2ui page into `assets/md2ui`, copies the theme, lists the asset folders |
| `tool/make_icons.py` | Draws the icon's source images; `dart run flutter_launcher_icons` makes the sizes |
| `test/` | The API client against a scripted backend, and the working pill |

## How a tap travels

The embed page sends every tap over md2ui's socket as md2ui's event frame (the page shown, the
target's ordinal), and md2ui verifies it against the page it sent. Dart never sees a tap; it
follows md2ui's state frame (`md2uiState`: blocked, working and its step, the placeholder) for
the footer and the working pill, and reads the footer's badge after each page (`/api/state`).

- **➕ ➖ 🤍 ❤️** are answered by the shop's md2ui handlers: the page is redrawn in place. No
  agent turn. So are the taps that only choose a page (a category tab, Keep shopping).
- **Home** (the logo, Back to home) shows the session's saved home at once. On the first visit
  it shows the instant one, then the home writer's version in place.
- **The product form** (a size choice, a quantity count) stays on the page: md2ui records each
  choice, and the Add to cart press reaches the agent as md2ui's sentence, with the values.
- **Everything else**, and the prompt bar, go to the agent; its page comes back on the socket.
- **Checkout** opens the payment sheet on the app's own session, from the footer or the page.
  When the agent opens it (`open_checkout`, asked in words), `/api/state` says so after its
  page and `/api/resume` hands it the outcome when the sheet closes.

## Requirements

- **Flutter** 3.41 or newer (Dart `^3.11.0`, `pubspec.yaml`).
- **Xcode** 27 for iOS; the app targets **iOS 15.0** (`ios/Podfile`), the oldest Xcode 27
  builds for.
- **Android:** minSdk 24 (`android/app/build.gradle.kts`, for `flutter_inappwebview`).
- **Node** 24 with **pnpm** 10 for `tool/sync_md2ui.sh`, and **uv** for `tool/make_icons.py`:
  only to rebuild what they write into `assets/`, which is kept in the repository.

`flutter build apk --debug` and `flutter build ios --no-codesign` build. With Flutter 3.41.0,
`flutter build ios --simulator` stops in Flutter's own framework step: it reports that
`Flutter.framework` lacks "arm64 x86_64" while listing exactly those architectures. That is a
toolchain issue, not this project's; build for a device, or use a newer Flutter.

## Run

1. Start the backend (see `../README.md`). For a phone, bind it to your network:
   `.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000`.
2. Then:

```bash
cd app
flutter pub get
flutter run                    # iOS simulator: http://localhost:8000; Android emulator: http://10.0.2.2:8000
```

On a phone, long-press the logo and enter `http://<your Mac's LAN IP>:8000`, or bake it in
with `--dart-define=API_BASE_URL=http://…`. iOS asks for the Local Network permission the
first time. Plain http is allowed only to local hosts (iOS) and only in debug builds (Android).

## After a change

```bash
tool/sync_md2ui.sh                                  # the @md2ui pins, web/src/embed.ts or the theme changed
uv run tool/make_icons.py && dart run flutter_launcher_icons   # the icon changed
flutter analyze && flutter test
```

`tool/sync_md2ui.sh` builds with the `@md2ui/dom` and `@md2ui/wire` releases `web/package.json`
pins. Keep `lib/md2ui/theme.dart` and the fonts the script copies in step.
