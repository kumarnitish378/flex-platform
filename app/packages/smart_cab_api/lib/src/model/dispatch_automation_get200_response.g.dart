// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'dispatch_automation_get200_response.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$DispatchAutomationGet200Response
    extends DispatchAutomationGet200Response {
  @override
  final bool? automationPaused;

  factory _$DispatchAutomationGet200Response(
          [void Function(DispatchAutomationGet200ResponseBuilder)? updates]) =>
      (DispatchAutomationGet200ResponseBuilder()..update(updates))._build();

  _$DispatchAutomationGet200Response._({this.automationPaused}) : super._();
  @override
  DispatchAutomationGet200Response rebuild(
          void Function(DispatchAutomationGet200ResponseBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  DispatchAutomationGet200ResponseBuilder toBuilder() =>
      DispatchAutomationGet200ResponseBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is DispatchAutomationGet200Response &&
        automationPaused == other.automationPaused;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, automationPaused.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'DispatchAutomationGet200Response')
          ..add('automationPaused', automationPaused))
        .toString();
  }
}

class DispatchAutomationGet200ResponseBuilder
    implements
        Builder<DispatchAutomationGet200Response,
            DispatchAutomationGet200ResponseBuilder> {
  _$DispatchAutomationGet200Response? _$v;

  bool? _automationPaused;
  bool? get automationPaused => _$this._automationPaused;
  set automationPaused(bool? automationPaused) =>
      _$this._automationPaused = automationPaused;

  DispatchAutomationGet200ResponseBuilder() {
    DispatchAutomationGet200Response._defaults(this);
  }

  DispatchAutomationGet200ResponseBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _automationPaused = $v.automationPaused;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(DispatchAutomationGet200Response other) {
    _$v = other as _$DispatchAutomationGet200Response;
  }

  @override
  void update(void Function(DispatchAutomationGet200ResponseBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  DispatchAutomationGet200Response build() => _build();

  _$DispatchAutomationGet200Response _build() {
    final _$result = _$v ??
        _$DispatchAutomationGet200Response._(
          automationPaused: automationPaused,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
