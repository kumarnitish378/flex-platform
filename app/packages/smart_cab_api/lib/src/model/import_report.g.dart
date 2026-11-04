// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'import_report.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$ImportReport extends ImportReport {
  @override
  final int? totalRows;
  @override
  final int? validRows;
  @override
  final int? created;
  @override
  final int? updated;
  @override
  final BuiltList<ImportReportErrorsInner>? errors;

  factory _$ImportReport([void Function(ImportReportBuilder)? updates]) =>
      (ImportReportBuilder()..update(updates))._build();

  _$ImportReport._(
      {this.totalRows, this.validRows, this.created, this.updated, this.errors})
      : super._();
  @override
  ImportReport rebuild(void Function(ImportReportBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  ImportReportBuilder toBuilder() => ImportReportBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is ImportReport &&
        totalRows == other.totalRows &&
        validRows == other.validRows &&
        created == other.created &&
        updated == other.updated &&
        errors == other.errors;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, totalRows.hashCode);
    _$hash = $jc(_$hash, validRows.hashCode);
    _$hash = $jc(_$hash, created.hashCode);
    _$hash = $jc(_$hash, updated.hashCode);
    _$hash = $jc(_$hash, errors.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'ImportReport')
          ..add('totalRows', totalRows)
          ..add('validRows', validRows)
          ..add('created', created)
          ..add('updated', updated)
          ..add('errors', errors))
        .toString();
  }
}

class ImportReportBuilder
    implements Builder<ImportReport, ImportReportBuilder> {
  _$ImportReport? _$v;

  int? _totalRows;
  int? get totalRows => _$this._totalRows;
  set totalRows(int? totalRows) => _$this._totalRows = totalRows;

  int? _validRows;
  int? get validRows => _$this._validRows;
  set validRows(int? validRows) => _$this._validRows = validRows;

  int? _created;
  int? get created => _$this._created;
  set created(int? created) => _$this._created = created;

  int? _updated;
  int? get updated => _$this._updated;
  set updated(int? updated) => _$this._updated = updated;

  ListBuilder<ImportReportErrorsInner>? _errors;
  ListBuilder<ImportReportErrorsInner> get errors =>
      _$this._errors ??= ListBuilder<ImportReportErrorsInner>();
  set errors(ListBuilder<ImportReportErrorsInner>? errors) =>
      _$this._errors = errors;

  ImportReportBuilder() {
    ImportReport._defaults(this);
  }

  ImportReportBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _totalRows = $v.totalRows;
      _validRows = $v.validRows;
      _created = $v.created;
      _updated = $v.updated;
      _errors = $v.errors?.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(ImportReport other) {
    _$v = other as _$ImportReport;
  }

  @override
  void update(void Function(ImportReportBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  ImportReport build() => _build();

  _$ImportReport _build() {
    _$ImportReport _$result;
    try {
      _$result = _$v ??
          _$ImportReport._(
            totalRows: totalRows,
            validRows: validRows,
            created: created,
            updated: updated,
            errors: _errors?.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'errors';
        _errors?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'ImportReport', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
