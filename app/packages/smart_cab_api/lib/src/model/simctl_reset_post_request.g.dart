// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'simctl_reset_post_request.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$SimctlResetPostRequest extends SimctlResetPostRequest {
  @override
  final String? scenarioYaml;

  factory _$SimctlResetPostRequest(
          [void Function(SimctlResetPostRequestBuilder)? updates]) =>
      (SimctlResetPostRequestBuilder()..update(updates))._build();

  _$SimctlResetPostRequest._({this.scenarioYaml}) : super._();
  @override
  SimctlResetPostRequest rebuild(
          void Function(SimctlResetPostRequestBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  SimctlResetPostRequestBuilder toBuilder() =>
      SimctlResetPostRequestBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is SimctlResetPostRequest &&
        scenarioYaml == other.scenarioYaml;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, scenarioYaml.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'SimctlResetPostRequest')
          ..add('scenarioYaml', scenarioYaml))
        .toString();
  }
}

class SimctlResetPostRequestBuilder
    implements Builder<SimctlResetPostRequest, SimctlResetPostRequestBuilder> {
  _$SimctlResetPostRequest? _$v;

  String? _scenarioYaml;
  String? get scenarioYaml => _$this._scenarioYaml;
  set scenarioYaml(String? scenarioYaml) => _$this._scenarioYaml = scenarioYaml;

  SimctlResetPostRequestBuilder() {
    SimctlResetPostRequest._defaults(this);
  }

  SimctlResetPostRequestBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _scenarioYaml = $v.scenarioYaml;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(SimctlResetPostRequest other) {
    _$v = other as _$SimctlResetPostRequest;
  }

  @override
  void update(void Function(SimctlResetPostRequestBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  SimctlResetPostRequest build() => _build();

  _$SimctlResetPostRequest _build() {
    final _$result = _$v ??
        _$SimctlResetPostRequest._(
          scenarioYaml: scenarioYaml,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
