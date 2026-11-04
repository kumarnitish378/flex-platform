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
  @override
  final int? optimizerRuns;
  @override
  final int? optimizerApplied;
  @override
  final int? optimizerSuggested;
  @override
  final int? optimizerHinted;
  @override
  final int? optimizerFailed;

  factory _$SimClock([void Function(SimClockBuilder)? updates]) =>
      (SimClockBuilder()..update(updates))._build();

  _$SimClock._(
      {this.now,
      this.advanceSeconds,
      this.optimizerRuns,
      this.optimizerApplied,
      this.optimizerSuggested,
      this.optimizerHinted,
      this.optimizerFailed})
      : super._();
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
        advanceSeconds == other.advanceSeconds &&
        optimizerRuns == other.optimizerRuns &&
        optimizerApplied == other.optimizerApplied &&
        optimizerSuggested == other.optimizerSuggested &&
        optimizerHinted == other.optimizerHinted &&
        optimizerFailed == other.optimizerFailed;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, now.hashCode);
    _$hash = $jc(_$hash, advanceSeconds.hashCode);
    _$hash = $jc(_$hash, optimizerRuns.hashCode);
    _$hash = $jc(_$hash, optimizerApplied.hashCode);
    _$hash = $jc(_$hash, optimizerSuggested.hashCode);
    _$hash = $jc(_$hash, optimizerHinted.hashCode);
    _$hash = $jc(_$hash, optimizerFailed.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'SimClock')
          ..add('now', now)
          ..add('advanceSeconds', advanceSeconds)
          ..add('optimizerRuns', optimizerRuns)
          ..add('optimizerApplied', optimizerApplied)
          ..add('optimizerSuggested', optimizerSuggested)
          ..add('optimizerHinted', optimizerHinted)
          ..add('optimizerFailed', optimizerFailed))
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

  int? _optimizerRuns;
  int? get optimizerRuns => _$this._optimizerRuns;
  set optimizerRuns(int? optimizerRuns) =>
      _$this._optimizerRuns = optimizerRuns;

  int? _optimizerApplied;
  int? get optimizerApplied => _$this._optimizerApplied;
  set optimizerApplied(int? optimizerApplied) =>
      _$this._optimizerApplied = optimizerApplied;

  int? _optimizerSuggested;
  int? get optimizerSuggested => _$this._optimizerSuggested;
  set optimizerSuggested(int? optimizerSuggested) =>
      _$this._optimizerSuggested = optimizerSuggested;

  int? _optimizerHinted;
  int? get optimizerHinted => _$this._optimizerHinted;
  set optimizerHinted(int? optimizerHinted) =>
      _$this._optimizerHinted = optimizerHinted;

  int? _optimizerFailed;
  int? get optimizerFailed => _$this._optimizerFailed;
  set optimizerFailed(int? optimizerFailed) =>
      _$this._optimizerFailed = optimizerFailed;

  SimClockBuilder() {
    SimClock._defaults(this);
  }

  SimClockBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _now = $v.now;
      _advanceSeconds = $v.advanceSeconds;
      _optimizerRuns = $v.optimizerRuns;
      _optimizerApplied = $v.optimizerApplied;
      _optimizerSuggested = $v.optimizerSuggested;
      _optimizerHinted = $v.optimizerHinted;
      _optimizerFailed = $v.optimizerFailed;
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
          optimizerRuns: optimizerRuns,
          optimizerApplied: optimizerApplied,
          optimizerSuggested: optimizerSuggested,
          optimizerHinted: optimizerHinted,
          optimizerFailed: optimizerFailed,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
