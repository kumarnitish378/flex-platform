/// Build-time configuration, supplied with `--dart-define` (A01).
///
/// Nothing here has a production default. A URL baked into the binary is a URL
/// somebody ships by accident, and hard rule 7 is explicit that map service URLs always
/// come from config - `TILES_URL` in particular (ADR-0010 section A2). The debug
/// defaults point at a developer's own machine and are useless anywhere else, which is
/// the intention.
library;

/// How the app reaches the backend and the map tiles.
class Env {
  const Env._();

  /// The API root, including the version prefix: `http://10.0.2.2:8000/api/v1`.
  ///
  /// `10.0.2.2` is the host machine as seen from the Android emulator, which is why the
  /// debug default is not `localhost` - that would be the emulator itself.
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000/api/v1',
  );

  /// Raster tile template - the usual `{z}/{x}/{y}.png` shape, supplied per build.
  ///
  /// No example URL here, not even in a comment: the repo guard that enforces hard rule
  /// 7 reads source files and cannot tell a comment from code, and it is right not to
  /// try. The value for each environment lives in the build command and `.env.example`.
  ///
  /// Empty by default on purpose: a map with no configured tile source must fail
  /// visibly in review rather than quietly fall back to somebody's demo server.
  static const String tilesUrl = String.fromEnvironment('TILES_URL');

  /// Sent with every tile request, and never the MapLibre default (ADR-0010 A2).
  static const String osmContactEmail = String.fromEnvironment('OSM_CONTACT_EMAIL');

  /// MQTT broker for the driver's GPS publishing (B11/B12). Host only; the driver's
  /// credentials come from the duty response, never from the build.
  static const String mqttHost = String.fromEnvironment('MQTT_HOST');

  static const int mqttPort = int.fromEnvironment('MQTT_PORT', defaultValue: 1883);

  /// True when this build is wired to something real. Checked by a test, so a release
  /// build with the debug default cannot pass CI.
  static bool get isConfigured => apiBaseUrl.isNotEmpty && !apiBaseUrl.contains('10.0.2.2');
}
