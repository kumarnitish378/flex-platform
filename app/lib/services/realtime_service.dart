library;

import 'dart:async';
import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../core/env.dart';
import '../core/session.dart';

/// Event payload received over WebSocket.
class RealtimeEvent {
  const RealtimeEvent({
    required this.event,
    required this.channel,
    required this.data,
  });

  factory RealtimeEvent.fromJson(Map<String, dynamic> json) {
    return RealtimeEvent(
      event: json['event'] as String? ?? '',
      channel: json['channel'] as String? ?? '',
      data: (json['data'] as Map<String, dynamic>?) ?? <String, dynamic>{},
    );
  }

  final String event;
  final String channel;
  final Map<String, dynamic> data;
}

/// WebSocket realtime service with automatic reconnect, backoff, auth, and subscriptions (A07).
class RealtimeService {
  RealtimeService(this._ref);

  final Ref _ref;
  WebSocketChannel? _channel;
  StreamSubscription<dynamic>? _subscription;
  Timer? _pingTimer;
  Timer? _reconnectTimer;

  bool _isConnected = false;
  int _reconnectAttempts = 0;
  final Set<String> _subscribedChannels = <String>{};

  final StreamController<RealtimeEvent> _eventController =
      StreamController<RealtimeEvent>.broadcast();

  Stream<RealtimeEvent> get events => _eventController.stream;
  bool get isConnected => _isConnected;

  String _getWsUrl() {
    final String apiBase = Env.apiBaseUrl;
    final String wsBase = apiBase
        .replaceFirst('http://', 'ws://')
        .replaceFirst('https://', 'wss://');
    return '$wsBase/ws';
  }

  /// Connect to the realtime WebSocket endpoint.
  Future<void> connect() async {
    final Session session = _ref.read(sessionProvider);
    if (!session.isSignedIn) {
      return;
    }

    _reconnectTimer?.cancel();
    _subscription?.cancel();
    _channel?.sink.close();

    try {
      final String url = _getWsUrl();
      _channel = WebSocketChannel.connect(Uri.parse(url));

      // Send auth frame immediately upon connection
      final Map<String, String> authFrame = <String, String>{
        'type': 'auth',
        'token': session.accessToken ?? '',
        'active_role': session.activeRole?.wireName ?? 'employee',
      };
      _channel!.sink.add(jsonEncode(authFrame));

      _isConnected = true;
      _reconnectAttempts = 0;

      // Resubscribe active channels
      if (_subscribedChannels.isNotEmpty) {
        _sendSubscribe(_subscribedChannels.toList());
      }

      _startPingTimer();

      _subscription = _channel!.stream.listen(
        _onMessage,
        onError: _onError,
        onDone: _onDone,
      );
    } catch (e) {
      _handleDisconnect();
    }
  }

  void _onMessage(dynamic message) {
    if (message is! String) {
      return;
    }
    try {
      final Map<String, dynamic> json = jsonDecode(message) as Map<String, dynamic>;
      final String type = json['type'] as String? ?? '';

      if (type == 'event') {
        _eventController.add(RealtimeEvent.fromJson(json));
      } else if (type == 'pong') {
        // Heartbeat ACK
      }
    } catch (_) {
      // Ignore unparseable frames
    }
  }

  void _onError(dynamic error) {
    _handleDisconnect();
  }

  void _onDone() {
    _handleDisconnect();
  }

  void _handleDisconnect() {
    _isConnected = false;
    _pingTimer?.cancel();

    // Exponential backoff reconnect: 1s, 2s, 4s, 8s, up to 30s
    final int delaySeconds = (1 << _reconnectAttempts).clamp(1, 30);
    _reconnectAttempts++;

    _reconnectTimer = Timer(Duration(seconds: delaySeconds), () {
      if (_ref.read(sessionProvider).isSignedIn) {
        connect();
      }
    });
  }

  void _startPingTimer() {
    _pingTimer?.cancel();
    _pingTimer = Timer.periodic(const Duration(seconds: 30), (Timer timer) {
      if (_isConnected && _channel != null) {
        _channel!.sink.add(jsonEncode(<String, String>{'type': 'ping'}));
      }
    });
  }

  /// Subscribe to a list of channels.
  void subscribe(List<String> channels) {
    _subscribedChannels.addAll(channels);
    if (_isConnected) {
      _sendSubscribe(channels);
    }
  }

  /// Unsubscribe from channels.
  void unsubscribe(List<String> channels) {
    _subscribedChannels.removeAll(channels);
    if (_isConnected) {
      _channel?.sink.add(
        jsonEncode(<String, dynamic>{
          'type': 'unsubscribe',
          'channels': channels,
        }),
      );
    }
  }

  void _sendSubscribe(List<String> channels) {
    _channel?.sink.add(
      jsonEncode(<String, dynamic>{
        'type': 'subscribe',
        'channels': channels,
      }),
    );
  }

  /// Disconnect and clean up resources.
  void dispose() {
    _pingTimer?.cancel();
    _reconnectTimer?.cancel();
    _subscription?.cancel();
    _channel?.sink.close();
    _eventController.close();
  }
}

final Provider<RealtimeService> realtimeServiceProvider = Provider<RealtimeService>((Ref ref) {
  final RealtimeService service = RealtimeService(ref);
  ref.onDispose(service.dispose);
  return service;
});
