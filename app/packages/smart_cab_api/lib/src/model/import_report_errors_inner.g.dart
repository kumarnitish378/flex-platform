// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'import_report_errors_inner.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$ImportReportErrorsInner extends ImportReportErrorsInner {
  @override
  final int? row;
  @override
  final String? field;
  @override
  final String? message;

  factory _$ImportReportErrorsInner(
          [void Function(ImportReportErrorsInnerBuilder)? updates]) =>
      (ImportReportErrorsInnerBuilder()..update(updates))._build();

  _$ImportReportErrorsInner._({this.row, this.field, this.message}) : super._();
  @override
  ImportReportErrorsInner rebuild(
          void Function(ImportReportErrorsInnerBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  ImportReportErrorsInnerBuilder toBuilder() =>
      ImportReportErrorsInnerBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is ImportReportErrorsInner &&
        row == other.row &&
        field == other.field &&
        message == other.message;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, row.hashCode);
    _$hash = $jc(_$hash, field.hashCode);
    _$hash = $jc(_$hash, message.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'ImportReportErrorsInner')
          ..add('row', row)
          ..add('field', field)
          ..add('message', message))
        .toString();
  }
}

class ImportReportErrorsInnerBuilder
    implements
        Builder<ImportReportErrorsInner, ImportReportErrorsInnerBuilder> {
  _$ImportReportErrorsInner? _$v;

  int? _row;
  int? get row => _$this._row;
  set row(int? row) => _$this._row = row;

  String? _field;
  String? get field => _$this._field;
  set field(String? field) => _$this._field = field;

  String? _message;
  String? get message => _$this._message;
  set message(String? message) => _$this._message = message;

  ImportReportErrorsInnerBuilder() {
    ImportReportErrorsInner._defaults(this);
  }

  ImportReportErrorsInnerBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _row = $v.row;
      _field = $v.field;
      _message = $v.message;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(ImportReportErrorsInner other) {
    _$v = other as _$ImportReportErrorsInner;
  }

  @override
  void update(void Function(ImportReportErrorsInnerBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  ImportReportErrorsInner build() => _build();

  _$ImportReportErrorsInner _build() {
    final _$result = _$v ??
        _$ImportReportErrorsInner._(
          row: row,
          field: field,
          message: message,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
