// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'simctl_release_post_request.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$SimctlReleasePostRequest extends SimctlReleasePostRequest {
  @override
  final String runId;

  factory _$SimctlReleasePostRequest(
          [void Function(SimctlReleasePostRequestBuilder)? updates]) =>
      (SimctlReleasePostRequestBuilder()..update(updates))._build();

  _$SimctlReleasePostRequest._({required this.runId}) : super._();
  @override
  SimctlReleasePostRequest rebuild(
          void Function(SimctlReleasePostRequestBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  SimctlReleasePostRequestBuilder toBuilder() =>
      SimctlReleasePostRequestBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is SimctlReleasePostRequest && runId == other.runId;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, runId.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'SimctlReleasePostRequest')
          ..add('runId', runId))
        .toString();
  }
}

class SimctlReleasePostRequestBuilder
    implements
        Builder<SimctlReleasePostRequest, SimctlReleasePostRequestBuilder> {
  _$SimctlReleasePostRequest? _$v;

  String? _runId;
  String? get runId => _$this._runId;
  set runId(String? runId) => _$this._runId = runId;

  SimctlReleasePostRequestBuilder() {
    SimctlReleasePostRequest._defaults(this);
  }

  SimctlReleasePostRequestBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _runId = $v.runId;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(SimctlReleasePostRequest other) {
    _$v = other as _$SimctlReleasePostRequest;
  }

  @override
  void update(void Function(SimctlReleasePostRequestBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  SimctlReleasePostRequest build() => _build();

  _$SimctlReleasePostRequest _build() {
    final _$result = _$v ??
        _$SimctlReleasePostRequest._(
          runId: BuiltValueNullFieldError.checkNotNull(
              runId, r'SimctlReleasePostRequest', 'runId'),
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
