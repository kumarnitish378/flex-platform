// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'sim_clock.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$SimClock extends SimClock {
  @override
  final DateTime? now;
  @override
  final int? advanceSeconds;

  factory _$SimClock([void Function(SimClockBuilder)? updates]) =>
      (SimClockBuilder()..update(updates))._build();

  _$SimClock._({this.now, this.advanceSeconds}) : super._();
  @override
  SimClock rebuild(void Function(SimClockBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  SimClockBuilder toBuilder() => SimClockBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is SimClock &&
        now == other.now &&
        advanceSeconds == other.advanceSeconds;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, now.hashCode);
    _$hash = $jc(_$hash, advanceSeconds.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'SimClock')
          ..add('now', now)
          ..add('advanceSeconds', advanceSeconds))
        .toString();
  }
}

class SimClockBuilder implements Builder<SimClock, SimClockBuilder> {
  _$SimClock? _$v;

  DateTime? _now;
  DateTime? get now => _$this._now;
  set now(DateTime? now) => _$this._now = now;

  int? _advanceSeconds;
  int? get advanceSeconds => _$this._advanceSeconds;
  set advanceSeconds(int? advanceSeconds) =>
      _$this._advanceSeconds = advanceSeconds;

  SimClockBuilder() {
    SimClock._defaults(this);
  }

  SimClockBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _now = $v.now;
      _advanceSeconds = $v.advanceSeconds;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(SimClock other) {
    _$v = other as _$SimClock;
  }

  @override
  void update(void Function(SimClockBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  SimClock build() => _build();

  _$SimClock _build() {
    final _$result = _$v ??
        _$SimClock._(
          now: now,
          advanceSeconds: advanceSeconds,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
