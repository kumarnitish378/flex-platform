// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'simctl_release_post200_response.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$SimctlReleasePost200Response extends SimctlReleasePost200Response {
  @override
  final bool? released;

  factory _$SimctlReleasePost200Response(
          [void Function(SimctlReleasePost200ResponseBuilder)? updates]) =>
      (SimctlReleasePost200ResponseBuilder()..update(updates))._build();

  _$SimctlReleasePost200Response._({this.released}) : super._();
  @override
  SimctlReleasePost200Response rebuild(
          void Function(SimctlReleasePost200ResponseBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  SimctlReleasePost200ResponseBuilder toBuilder() =>
      SimctlReleasePost200ResponseBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is SimctlReleasePost200Response && released == other.released;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, released.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'SimctlReleasePost200Response')
          ..add('released', released))
        .toString();
  }
}

class SimctlReleasePost200ResponseBuilder
    implements
        Builder<SimctlReleasePost200Response,
            SimctlReleasePost200ResponseBuilder> {
  _$SimctlReleasePost200Response? _$v;

  bool? _released;
  bool? get released => _$this._released;
  set released(bool? released) => _$this._released = released;

  SimctlReleasePost200ResponseBuilder() {
    SimctlReleasePost200Response._defaults(this);
  }

  SimctlReleasePost200ResponseBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _released = $v.released;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(SimctlReleasePost200Response other) {
    _$v = other as _$SimctlReleasePost200Response;
  }

  @override
  void update(void Function(SimctlReleasePost200ResponseBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  SimctlReleasePost200Response build() => _build();

  _$SimctlReleasePost200Response _build() {
    final _$result = _$v ??
        _$SimctlReleasePost200Response._(
          released: released,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
