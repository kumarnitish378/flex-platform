// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'operations_report.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$OperationsReport extends OperationsReport {
  @override
  final OperationsReportPeriod period;
  @override
  final OperationsReportRequests requests;
  @override
  final OperationsReportWait wait;
  @override
  final OperationsReportPooling pooling;
  @override
  final OperationsReportDistance distance;
  @override
  final OperationsReportOverrides overrides;
  @override
  final OperationsReportSuggestions suggestions;
  @override
  final BuiltMap<String, int> assignmentsByActor;
  @override
  final OperationsReportOptimizer optimizer;

  factory _$OperationsReport(
          [void Function(OperationsReportBuilder)? updates]) =>
      (OperationsReportBuilder()..update(updates))._build();

  _$OperationsReport._(
      {required this.period,
      required this.requests,
      required this.wait,
      required this.pooling,
      required this.distance,
      required this.overrides,
      required this.suggestions,
      required this.assignmentsByActor,
      required this.optimizer})
      : super._();
  @override
  OperationsReport rebuild(void Function(OperationsReportBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  OperationsReportBuilder toBuilder() =>
      OperationsReportBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is OperationsReport &&
        period == other.period &&
        requests == other.requests &&
        wait == other.wait &&
        pooling == other.pooling &&
        distance == other.distance &&
        overrides == other.overrides &&
        suggestions == other.suggestions &&
        assignmentsByActor == other.assignmentsByActor &&
        optimizer == other.optimizer;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, period.hashCode);
    _$hash = $jc(_$hash, requests.hashCode);
    _$hash = $jc(_$hash, wait.hashCode);
    _$hash = $jc(_$hash, pooling.hashCode);
    _$hash = $jc(_$hash, distance.hashCode);
    _$hash = $jc(_$hash, overrides.hashCode);
    _$hash = $jc(_$hash, suggestions.hashCode);
    _$hash = $jc(_$hash, assignmentsByActor.hashCode);
    _$hash = $jc(_$hash, optimizer.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'OperationsReport')
          ..add('period', period)
          ..add('requests', requests)
          ..add('wait', wait)
          ..add('pooling', pooling)
          ..add('distance', distance)
          ..add('overrides', overrides)
          ..add('suggestions', suggestions)
          ..add('assignmentsByActor', assignmentsByActor)
          ..add('optimizer', optimizer))
        .toString();
  }
}

class OperationsReportBuilder
    implements Builder<OperationsReport, OperationsReportBuilder> {
  _$OperationsReport? _$v;

  OperationsReportPeriodBuilder? _period;
  OperationsReportPeriodBuilder get period =>
      _$this._period ??= OperationsReportPeriodBuilder();
  set period(OperationsReportPeriodBuilder? period) => _$this._period = period;

  OperationsReportRequestsBuilder? _requests;
  OperationsReportRequestsBuilder get requests =>
      _$this._requests ??= OperationsReportRequestsBuilder();
  set requests(OperationsReportRequestsBuilder? requests) =>
      _$this._requests = requests;

  OperationsReportWaitBuilder? _wait;
  OperationsReportWaitBuilder get wait =>
      _$this._wait ??= OperationsReportWaitBuilder();
  set wait(OperationsReportWaitBuilder? wait) => _$this._wait = wait;

  OperationsReportPoolingBuilder? _pooling;
  OperationsReportPoolingBuilder get pooling =>
      _$this._pooling ??= OperationsReportPoolingBuilder();
  set pooling(OperationsReportPoolingBuilder? pooling) =>
      _$this._pooling = pooling;

  OperationsReportDistanceBuilder? _distance;
  OperationsReportDistanceBuilder get distance =>
      _$this._distance ??= OperationsReportDistanceBuilder();
  set distance(OperationsReportDistanceBuilder? distance) =>
      _$this._distance = distance;

  OperationsReportOverridesBuilder? _overrides;
  OperationsReportOverridesBuilder get overrides =>
      _$this._overrides ??= OperationsReportOverridesBuilder();
  set overrides(OperationsReportOverridesBuilder? overrides) =>
      _$this._overrides = overrides;

  OperationsReportSuggestionsBuilder? _suggestions;
  OperationsReportSuggestionsBuilder get suggestions =>
      _$this._suggestions ??= OperationsReportSuggestionsBuilder();
  set suggestions(OperationsReportSuggestionsBuilder? suggestions) =>
      _$this._suggestions = suggestions;

  MapBuilder<String, int>? _assignmentsByActor;
  MapBuilder<String, int> get assignmentsByActor =>
      _$this._assignmentsByActor ??= MapBuilder<String, int>();
  set assignmentsByActor(MapBuilder<String, int>? assignmentsByActor) =>
      _$this._assignmentsByActor = assignmentsByActor;

  OperationsReportOptimizerBuilder? _optimizer;
  OperationsReportOptimizerBuilder get optimizer =>
      _$this._optimizer ??= OperationsReportOptimizerBuilder();
  set optimizer(OperationsReportOptimizerBuilder? optimizer) =>
      _$this._optimizer = optimizer;

  OperationsReportBuilder() {
    OperationsReport._defaults(this);
  }

  OperationsReportBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _period = $v.period.toBuilder();
      _requests = $v.requests.toBuilder();
      _wait = $v.wait.toBuilder();
      _pooling = $v.pooling.toBuilder();
      _distance = $v.distance.toBuilder();
      _overrides = $v.overrides.toBuilder();
      _suggestions = $v.suggestions.toBuilder();
      _assignmentsByActor = $v.assignmentsByActor.toBuilder();
      _optimizer = $v.optimizer.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(OperationsReport other) {
    _$v = other as _$OperationsReport;
  }

  @override
  void update(void Function(OperationsReportBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  OperationsReport build() => _build();

  _$OperationsReport _build() {
    _$OperationsReport _$result;
    try {
      _$result = _$v ??
          _$OperationsReport._(
            period: period.build(),
            requests: requests.build(),
            wait: wait.build(),
            pooling: pooling.build(),
            distance: distance.build(),
            overrides: overrides.build(),
            suggestions: suggestions.build(),
            assignmentsByActor: assignmentsByActor.build(),
            optimizer: optimizer.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'period';
        period.build();
        _$failedField = 'requests';
        requests.build();
        _$failedField = 'wait';
        wait.build();
        _$failedField = 'pooling';
        pooling.build();
        _$failedField = 'distance';
        distance.build();
        _$failedField = 'overrides';
        overrides.build();
        _$failedField = 'suggestions';
        suggestions.build();
        _$failedField = 'assignmentsByActor';
        assignmentsByActor.build();
        _$failedField = 'optimizer';
        optimizer.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'OperationsReport', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
