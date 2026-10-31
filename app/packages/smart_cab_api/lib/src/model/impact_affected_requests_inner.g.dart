// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'impact_affected_requests_inner.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$ImpactAffectedRequestsInner extends ImpactAffectedRequestsInner {
  @override
  final String? requestId;
  @override
  final String? employeeName;
  @override
  final num? addedMinutes;
  @override
  final num? etaChangeMinutes;
  @override
  final bool? requeued;

  factory _$ImpactAffectedRequestsInner(
          [void Function(ImpactAffectedRequestsInnerBuilder)? updates]) =>
      (ImpactAffectedRequestsInnerBuilder()..update(updates))._build();

  _$ImpactAffectedRequestsInner._(
      {this.requestId,
      this.employeeName,
      this.addedMinutes,
      this.etaChangeMinutes,
      this.requeued})
      : super._();
  @override
  ImpactAffectedRequestsInner rebuild(
          void Function(ImpactAffectedRequestsInnerBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  ImpactAffectedRequestsInnerBuilder toBuilder() =>
      ImpactAffectedRequestsInnerBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is ImpactAffectedRequestsInner &&
        requestId == other.requestId &&
        employeeName == other.employeeName &&
        addedMinutes == other.addedMinutes &&
        etaChangeMinutes == other.etaChangeMinutes &&
        requeued == other.requeued;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, requestId.hashCode);
    _$hash = $jc(_$hash, employeeName.hashCode);
    _$hash = $jc(_$hash, addedMinutes.hashCode);
    _$hash = $jc(_$hash, etaChangeMinutes.hashCode);
    _$hash = $jc(_$hash, requeued.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'ImpactAffectedRequestsInner')
          ..add('requestId', requestId)
          ..add('employeeName', employeeName)
          ..add('addedMinutes', addedMinutes)
          ..add('etaChangeMinutes', etaChangeMinutes)
          ..add('requeued', requeued))
        .toString();
  }
}

class ImpactAffectedRequestsInnerBuilder
    implements
        Builder<ImpactAffectedRequestsInner,
            ImpactAffectedRequestsInnerBuilder> {
  _$ImpactAffectedRequestsInner? _$v;

  String? _requestId;
  String? get requestId => _$this._requestId;
  set requestId(String? requestId) => _$this._requestId = requestId;

  String? _employeeName;
  String? get employeeName => _$this._employeeName;
  set employeeName(String? employeeName) => _$this._employeeName = employeeName;

  num? _addedMinutes;
  num? get addedMinutes => _$this._addedMinutes;
  set addedMinutes(num? addedMinutes) => _$this._addedMinutes = addedMinutes;

  num? _etaChangeMinutes;
  num? get etaChangeMinutes => _$this._etaChangeMinutes;
  set etaChangeMinutes(num? etaChangeMinutes) =>
      _$this._etaChangeMinutes = etaChangeMinutes;

  bool? _requeued;
  bool? get requeued => _$this._requeued;
  set requeued(bool? requeued) => _$this._requeued = requeued;

  ImpactAffectedRequestsInnerBuilder() {
    ImpactAffectedRequestsInner._defaults(this);
  }

  ImpactAffectedRequestsInnerBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _requestId = $v.requestId;
      _employeeName = $v.employeeName;
      _addedMinutes = $v.addedMinutes;
      _etaChangeMinutes = $v.etaChangeMinutes;
      _requeued = $v.requeued;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(ImpactAffectedRequestsInner other) {
    _$v = other as _$ImpactAffectedRequestsInner;
  }

  @override
  void update(void Function(ImpactAffectedRequestsInnerBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  ImpactAffectedRequestsInner build() => _build();

  _$ImpactAffectedRequestsInner _build() {
    final _$result = _$v ??
        _$ImpactAffectedRequestsInner._(
          requestId: requestId,
          employeeName: employeeName,
          addedMinutes: addedMinutes,
          etaChangeMinutes: etaChangeMinutes,
          requeued: requeued,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
