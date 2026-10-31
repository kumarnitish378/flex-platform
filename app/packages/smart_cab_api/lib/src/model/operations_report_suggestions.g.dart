// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'operations_report_suggestions.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$OperationsReportSuggestions extends OperationsReportSuggestions {
  @override
  final int? answeredByAPerson;
  @override
  final int? accepted;
  @override
  final int? rejected;
  @override
  final int? failsafeAssigned;
  @override
  final int? rejectedForAnOfferedAlternative;
  @override
  final num? acceptanceRate;
  @override
  final num? acceptanceRateWithAlternatives;

  factory _$OperationsReportSuggestions(
          [void Function(OperationsReportSuggestionsBuilder)? updates]) =>
      (OperationsReportSuggestionsBuilder()..update(updates))._build();

  _$OperationsReportSuggestions._(
      {this.answeredByAPerson,
      this.accepted,
      this.rejected,
      this.failsafeAssigned,
      this.rejectedForAnOfferedAlternative,
      this.acceptanceRate,
      this.acceptanceRateWithAlternatives})
      : super._();
  @override
  OperationsReportSuggestions rebuild(
          void Function(OperationsReportSuggestionsBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  OperationsReportSuggestionsBuilder toBuilder() =>
      OperationsReportSuggestionsBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is OperationsReportSuggestions &&
        answeredByAPerson == other.answeredByAPerson &&
        accepted == other.accepted &&
        rejected == other.rejected &&
        failsafeAssigned == other.failsafeAssigned &&
        rejectedForAnOfferedAlternative ==
            other.rejectedForAnOfferedAlternative &&
        acceptanceRate == other.acceptanceRate &&
        acceptanceRateWithAlternatives == other.acceptanceRateWithAlternatives;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, answeredByAPerson.hashCode);
    _$hash = $jc(_$hash, accepted.hashCode);
    _$hash = $jc(_$hash, rejected.hashCode);
    _$hash = $jc(_$hash, failsafeAssigned.hashCode);
    _$hash = $jc(_$hash, rejectedForAnOfferedAlternative.hashCode);
    _$hash = $jc(_$hash, acceptanceRate.hashCode);
    _$hash = $jc(_$hash, acceptanceRateWithAlternatives.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'OperationsReportSuggestions')
          ..add('answeredByAPerson', answeredByAPerson)
          ..add('accepted', accepted)
          ..add('rejected', rejected)
          ..add('failsafeAssigned', failsafeAssigned)
          ..add('rejectedForAnOfferedAlternative',
              rejectedForAnOfferedAlternative)
          ..add('acceptanceRate', acceptanceRate)
          ..add(
              'acceptanceRateWithAlternatives', acceptanceRateWithAlternatives))
        .toString();
  }
}

class OperationsReportSuggestionsBuilder
    implements
        Builder<OperationsReportSuggestions,
            OperationsReportSuggestionsBuilder> {
  _$OperationsReportSuggestions? _$v;

  int? _answeredByAPerson;
  int? get answeredByAPerson => _$this._answeredByAPerson;
  set answeredByAPerson(int? answeredByAPerson) =>
      _$this._answeredByAPerson = answeredByAPerson;

  int? _accepted;
  int? get accepted => _$this._accepted;
  set accepted(int? accepted) => _$this._accepted = accepted;

  int? _rejected;
  int? get rejected => _$this._rejected;
  set rejected(int? rejected) => _$this._rejected = rejected;

  int? _failsafeAssigned;
  int? get failsafeAssigned => _$this._failsafeAssigned;
  set failsafeAssigned(int? failsafeAssigned) =>
      _$this._failsafeAssigned = failsafeAssigned;

  int? _rejectedForAnOfferedAlternative;
  int? get rejectedForAnOfferedAlternative =>
      _$this._rejectedForAnOfferedAlternative;
  set rejectedForAnOfferedAlternative(int? rejectedForAnOfferedAlternative) =>
      _$this._rejectedForAnOfferedAlternative = rejectedForAnOfferedAlternative;

  num? _acceptanceRate;
  num? get acceptanceRate => _$this._acceptanceRate;
  set acceptanceRate(num? acceptanceRate) =>
      _$this._acceptanceRate = acceptanceRate;

  num? _acceptanceRateWithAlternatives;
  num? get acceptanceRateWithAlternatives =>
      _$this._acceptanceRateWithAlternatives;
  set acceptanceRateWithAlternatives(num? acceptanceRateWithAlternatives) =>
      _$this._acceptanceRateWithAlternatives = acceptanceRateWithAlternatives;

  OperationsReportSuggestionsBuilder() {
    OperationsReportSuggestions._defaults(this);
  }

  OperationsReportSuggestionsBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _answeredByAPerson = $v.answeredByAPerson;
      _accepted = $v.accepted;
      _rejected = $v.rejected;
      _failsafeAssigned = $v.failsafeAssigned;
      _rejectedForAnOfferedAlternative = $v.rejectedForAnOfferedAlternative;
      _acceptanceRate = $v.acceptanceRate;
      _acceptanceRateWithAlternatives = $v.acceptanceRateWithAlternatives;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(OperationsReportSuggestions other) {
    _$v = other as _$OperationsReportSuggestions;
  }

  @override
  void update(void Function(OperationsReportSuggestionsBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  OperationsReportSuggestions build() => _build();

  _$OperationsReportSuggestions _build() {
    final _$result = _$v ??
        _$OperationsReportSuggestions._(
          answeredByAPerson: answeredByAPerson,
          accepted: accepted,
          rejected: rejected,
          failsafeAssigned: failsafeAssigned,
          rejectedForAnOfferedAlternative: rejectedForAnOfferedAlternative,
          acceptanceRate: acceptanceRate,
          acceptanceRateWithAlternatives: acceptanceRateWithAlternatives,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
