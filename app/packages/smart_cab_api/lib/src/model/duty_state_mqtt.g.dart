// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'duty_state_mqtt.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$DutyStateMqtt extends DutyStateMqtt {
  @override
  final String? host;
  @override
  final int? port;
  @override
  final String? username;
  @override
  final String? password;
  @override
  final String? topicPrefix;

  factory _$DutyStateMqtt([void Function(DutyStateMqttBuilder)? updates]) =>
      (DutyStateMqttBuilder()..update(updates))._build();

  _$DutyStateMqtt._(
      {this.host, this.port, this.username, this.password, this.topicPrefix})
      : super._();
  @override
  DutyStateMqtt rebuild(void Function(DutyStateMqttBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  DutyStateMqttBuilder toBuilder() => DutyStateMqttBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is DutyStateMqtt &&
        host == other.host &&
        port == other.port &&
        username == other.username &&
        password == other.password &&
        topicPrefix == other.topicPrefix;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, host.hashCode);
    _$hash = $jc(_$hash, port.hashCode);
    _$hash = $jc(_$hash, username.hashCode);
    _$hash = $jc(_$hash, password.hashCode);
    _$hash = $jc(_$hash, topicPrefix.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'DutyStateMqtt')
          ..add('host', host)
          ..add('port', port)
          ..add('username', username)
          ..add('password', password)
          ..add('topicPrefix', topicPrefix))
        .toString();
  }
}

class DutyStateMqttBuilder
    implements Builder<DutyStateMqtt, DutyStateMqttBuilder> {
  _$DutyStateMqtt? _$v;

  String? _host;
  String? get host => _$this._host;
  set host(String? host) => _$this._host = host;

  int? _port;
  int? get port => _$this._port;
  set port(int? port) => _$this._port = port;

  String? _username;
  String? get username => _$this._username;
  set username(String? username) => _$this._username = username;

  String? _password;
  String? get password => _$this._password;
  set password(String? password) => _$this._password = password;

  String? _topicPrefix;
  String? get topicPrefix => _$this._topicPrefix;
  set topicPrefix(String? topicPrefix) => _$this._topicPrefix = topicPrefix;

  DutyStateMqttBuilder() {
    DutyStateMqtt._defaults(this);
  }

  DutyStateMqttBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _host = $v.host;
      _port = $v.port;
      _username = $v.username;
      _password = $v.password;
      _topicPrefix = $v.topicPrefix;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(DutyStateMqtt other) {
    _$v = other as _$DutyStateMqtt;
  }

  @override
  void update(void Function(DutyStateMqttBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  DutyStateMqtt build() => _build();

  _$DutyStateMqtt _build() {
    final _$result = _$v ??
        _$DutyStateMqtt._(
          host: host,
          port: port,
          username: username,
          password: password,
          topicPrefix: topicPrefix,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
