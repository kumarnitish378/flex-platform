// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'dispatch_automation_put_request.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$DispatchAutomationPutRequest extends DispatchAutomationPutRequest {
  @override
  final bool automationPaused;
  @override
  final ReasonCode reasonCode;
  @override
  final String? note;

  factory _$DispatchAutomationPutRequest(
          [void Function(DispatchAutomationPutRequestBuilder)? updates]) =>
      (DispatchAutomationPutRequestBuilder()..update(updates))._build();

  _$DispatchAutomationPutRequest._(
      {required this.automationPaused, required this.reasonCode, this.note})
      : super._();
  @override
  DispatchAutomationPutRequest rebuild(
          void Function(DispatchAutomationPutRequestBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  DispatchAutomationPutRequestBuilder toBuilder() =>
      DispatchAutomationPutRequestBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is DispatchAutomationPutRequest &&
        automationPaused == other.automationPaused &&
        reasonCode == other.reasonCode &&
        note == other.note;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, automationPaused.hashCode);
    _$hash = $jc(_$hash, reasonCode.hashCode);
    _$hash = $jc(_$hash, note.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'DispatchAutomationPutRequest')
          ..add('automationPaused', automationPaused)
          ..add('reasonCode', reasonCode)
          ..add('note', note))
        .toString();
  }
}

class DispatchAutomationPutRequestBuilder
    implements
        Builder<DispatchAutomationPutRequest,
            DispatchAutomationPutRequestBuilder> {
  _$DispatchAutomationPutRequest? _$v;

  bool? _automationPaused;
  bool? get automationPaused => _$this._automationPaused;
  set automationPaused(bool? automationPaused) =>
      _$this._automationPaused = automationPaused;

  ReasonCode? _reasonCode;
  ReasonCode? get reasonCode => _$this._reasonCode;
  set reasonCode(ReasonCode? reasonCode) => _$this._reasonCode = reasonCode;

  String? _note;
  String? get note => _$this._note;
  set note(String? note) => _$this._note = note;

  DispatchAutomationPutRequestBuilder() {
    DispatchAutomationPutRequest._defaults(this);
  }

  DispatchAutomationPutRequestBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _automationPaused = $v.automationPaused;
      _reasonCode = $v.reasonCode;
      _note = $v.note;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(DispatchAutomationPutRequest other) {
    _$v = other as _$DispatchAutomationPutRequest;
  }

  @override
  void update(void Function(DispatchAutomationPutRequestBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  DispatchAutomationPutRequest build() => _build();

  _$DispatchAutomationPutRequest _build() {
    final _$result = _$v ??
        _$DispatchAutomationPutRequest._(
          automationPaused: BuiltValueNullFieldError.checkNotNull(
              automationPaused,
              r'DispatchAutomationPutRequest',
              'automationPaused'),
          reasonCode: BuiltValueNullFieldError.checkNotNull(
              reasonCode, r'DispatchAutomationPutRequest', 'reasonCode'),
          note: note,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
