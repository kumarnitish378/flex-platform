// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'billing_export.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$BillingExport extends BillingExport {
  @override
  final String clientId;
  @override
  final String clientName;
  @override
  final String month;
  @override
  final BillingExportTreatment treatment;
  @override
  final BillingExportSummary summary;
  @override
  final BuiltList<BillingExportRowsInner> rows;

  factory _$BillingExport([void Function(BillingExportBuilder)? updates]) =>
      (BillingExportBuilder()..update(updates))._build();

  _$BillingExport._(
      {required this.clientId,
      required this.clientName,
      required this.month,
      required this.treatment,
      required this.summary,
      required this.rows})
      : super._();
  @override
  BillingExport rebuild(void Function(BillingExportBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  BillingExportBuilder toBuilder() => BillingExportBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is BillingExport &&
        clientId == other.clientId &&
        clientName == other.clientName &&
        month == other.month &&
        treatment == other.treatment &&
        summary == other.summary &&
        rows == other.rows;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, clientId.hashCode);
    _$hash = $jc(_$hash, clientName.hashCode);
    _$hash = $jc(_$hash, month.hashCode);
    _$hash = $jc(_$hash, treatment.hashCode);
    _$hash = $jc(_$hash, summary.hashCode);
    _$hash = $jc(_$hash, rows.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'BillingExport')
          ..add('clientId', clientId)
          ..add('clientName', clientName)
          ..add('month', month)
          ..add('treatment', treatment)
          ..add('summary', summary)
          ..add('rows', rows))
        .toString();
  }
}

class BillingExportBuilder
    implements Builder<BillingExport, BillingExportBuilder> {
  _$BillingExport? _$v;

  String? _clientId;
  String? get clientId => _$this._clientId;
  set clientId(String? clientId) => _$this._clientId = clientId;

  String? _clientName;
  String? get clientName => _$this._clientName;
  set clientName(String? clientName) => _$this._clientName = clientName;

  String? _month;
  String? get month => _$this._month;
  set month(String? month) => _$this._month = month;

  BillingExportTreatmentBuilder? _treatment;
  BillingExportTreatmentBuilder get treatment =>
      _$this._treatment ??= BillingExportTreatmentBuilder();
  set treatment(BillingExportTreatmentBuilder? treatment) =>
      _$this._treatment = treatment;

  BillingExportSummaryBuilder? _summary;
  BillingExportSummaryBuilder get summary =>
      _$this._summary ??= BillingExportSummaryBuilder();
  set summary(BillingExportSummaryBuilder? summary) =>
      _$this._summary = summary;

  ListBuilder<BillingExportRowsInner>? _rows;
  ListBuilder<BillingExportRowsInner> get rows =>
      _$this._rows ??= ListBuilder<BillingExportRowsInner>();
  set rows(ListBuilder<BillingExportRowsInner>? rows) => _$this._rows = rows;

  BillingExportBuilder() {
    BillingExport._defaults(this);
  }

  BillingExportBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _clientId = $v.clientId;
      _clientName = $v.clientName;
      _month = $v.month;
      _treatment = $v.treatment.toBuilder();
      _summary = $v.summary.toBuilder();
      _rows = $v.rows.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(BillingExport other) {
    _$v = other as _$BillingExport;
  }

  @override
  void update(void Function(BillingExportBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  BillingExport build() => _build();

  _$BillingExport _build() {
    _$BillingExport _$result;
    try {
      _$result = _$v ??
          _$BillingExport._(
            clientId: BuiltValueNullFieldError.checkNotNull(
                clientId, r'BillingExport', 'clientId'),
            clientName: BuiltValueNullFieldError.checkNotNull(
                clientName, r'BillingExport', 'clientName'),
            month: BuiltValueNullFieldError.checkNotNull(
                month, r'BillingExport', 'month'),
            treatment: treatment.build(),
            summary: summary.build(),
            rows: rows.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'treatment';
        treatment.build();
        _$failedField = 'summary';
        summary.build();
        _$failedField = 'rows';
        rows.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'BillingExport', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
