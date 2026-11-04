// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'operations_report_requests.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$OperationsReportRequests extends OperationsReportRequests {
  @override
  final int? total;
  @override
  final int? completed;
  @override
  final int? noShows;
  @override
  final int? cancelled;
  @override
  final int? expired;
  @override
  final int? stillOpen;

  factory _$OperationsReportRequests(
          [void Function(OperationsReportRequestsBuilder)? updates]) =>
      (OperationsReportRequestsBuilder()..update(updates))._build();

  _$OperationsReportRequests._(
      {this.total,
      this.completed,
      this.noShows,
      this.cancelled,
      this.expired,
      this.stillOpen})
      : super._();
  @override
  OperationsReportRequests rebuild(
          void Function(OperationsReportRequestsBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  OperationsReportRequestsBuilder toBuilder() =>
      OperationsReportRequestsBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is OperationsReportRequests &&
        total == other.total &&
        completed == other.completed &&
        noShows == other.noShows &&
        cancelled == other.cancelled &&
        expired == other.expired &&
        stillOpen == other.stillOpen;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, total.hashCode);
    _$hash = $jc(_$hash, completed.hashCode);
    _$hash = $jc(_$hash, noShows.hashCode);
    _$hash = $jc(_$hash, cancelled.hashCode);
    _$hash = $jc(_$hash, expired.hashCode);
    _$hash = $jc(_$hash, stillOpen.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'OperationsReportRequests')
          ..add('total', total)
          ..add('completed', completed)
          ..add('noShows', noShows)
          ..add('cancelled', cancelled)
          ..add('expired', expired)
          ..add('stillOpen', stillOpen))
        .toString();
  }
}

class OperationsReportRequestsBuilder
    implements
        Builder<OperationsReportRequests, OperationsReportRequestsBuilder> {
  _$OperationsReportRequests? _$v;

  int? _total;
  int? get total => _$this._total;
  set total(int? total) => _$this._total = total;

  int? _completed;
  int? get completed => _$this._completed;
  set completed(int? completed) => _$this._completed = completed;

  int? _noShows;
  int? get noShows => _$this._noShows;
  set noShows(int? noShows) => _$this._noShows = noShows;

  int? _cancelled;
  int? get cancelled => _$this._cancelled;
  set cancelled(int? cancelled) => _$this._cancelled = cancelled;

  int? _expired;
  int? get expired => _$this._expired;
  set expired(int? expired) => _$this._expired = expired;

  int? _stillOpen;
  int? get stillOpen => _$this._stillOpen;
  set stillOpen(int? stillOpen) => _$this._stillOpen = stillOpen;

  OperationsReportRequestsBuilder() {
    OperationsReportRequests._defaults(this);
  }

  OperationsReportRequestsBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _total = $v.total;
      _completed = $v.completed;
      _noShows = $v.noShows;
      _cancelled = $v.cancelled;
      _expired = $v.expired;
      _stillOpen = $v.stillOpen;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(OperationsReportRequests other) {
    _$v = other as _$OperationsReportRequests;
  }

  @override
  void update(void Function(OperationsReportRequestsBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  OperationsReportRequests build() => _build();

  _$OperationsReportRequests _build() {
    final _$result = _$v ??
        _$OperationsReportRequests._(
          total: total,
          completed: completed,
          noShows: noShows,
          cancelled: cancelled,
          expired: expired,
          stillOpen: stillOpen,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
