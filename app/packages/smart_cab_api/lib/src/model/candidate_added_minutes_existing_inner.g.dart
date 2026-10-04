// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'candidate_added_minutes_existing_inner.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$CandidateAddedMinutesExistingInner
    extends CandidateAddedMinutesExistingInner {
  @override
  final String? requestId;
  @override
  final num? minutes;

  factory _$CandidateAddedMinutesExistingInner(
          [void Function(CandidateAddedMinutesExistingInnerBuilder)?
              updates]) =>
      (CandidateAddedMinutesExistingInnerBuilder()..update(updates))._build();

  _$CandidateAddedMinutesExistingInner._({this.requestId, this.minutes})
      : super._();
  @override
  CandidateAddedMinutesExistingInner rebuild(
          void Function(CandidateAddedMinutesExistingInnerBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  CandidateAddedMinutesExistingInnerBuilder toBuilder() =>
      CandidateAddedMinutesExistingInnerBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is CandidateAddedMinutesExistingInner &&
        requestId == other.requestId &&
        minutes == other.minutes;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, requestId.hashCode);
    _$hash = $jc(_$hash, minutes.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'CandidateAddedMinutesExistingInner')
          ..add('requestId', requestId)
          ..add('minutes', minutes))
        .toString();
  }
}

class CandidateAddedMinutesExistingInnerBuilder
    implements
        Builder<CandidateAddedMinutesExistingInner,
            CandidateAddedMinutesExistingInnerBuilder> {
  _$CandidateAddedMinutesExistingInner? _$v;

  String? _requestId;
  String? get requestId => _$this._requestId;
  set requestId(String? requestId) => _$this._requestId = requestId;

  num? _minutes;
  num? get minutes => _$this._minutes;
  set minutes(num? minutes) => _$this._minutes = minutes;

  CandidateAddedMinutesExistingInnerBuilder() {
    CandidateAddedMinutesExistingInner._defaults(this);
  }

  CandidateAddedMinutesExistingInnerBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _requestId = $v.requestId;
      _minutes = $v.minutes;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(CandidateAddedMinutesExistingInner other) {
    _$v = other as _$CandidateAddedMinutesExistingInner;
  }

  @override
  void update(
      void Function(CandidateAddedMinutesExistingInnerBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  CandidateAddedMinutesExistingInner build() => _build();

  _$CandidateAddedMinutesExistingInner _build() {
    final _$result = _$v ??
        _$CandidateAddedMinutesExistingInner._(
          requestId: requestId,
          minutes: minutes,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
