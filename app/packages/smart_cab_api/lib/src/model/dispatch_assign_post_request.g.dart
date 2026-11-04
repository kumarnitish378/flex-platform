// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'dispatch_assign_post_request.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$DispatchAssignPostRequest extends DispatchAssignPostRequest {
  @override
  final String requestId;
  @override
  final String vehicleId;
  @override
  final String? tripId;
  @override
  final ReasonCode? reasonCode;
  @override
  final String? note;

  factory _$DispatchAssignPostRequest(
          [void Function(DispatchAssignPostRequestBuilder)? updates]) =>
      (DispatchAssignPostRequestBuilder()..update(updates))._build();

  _$DispatchAssignPostRequest._(
      {required this.requestId,
      required this.vehicleId,
      this.tripId,
      this.reasonCode,
      this.note})
      : super._();
  @override
  DispatchAssignPostRequest rebuild(
          void Function(DispatchAssignPostRequestBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  DispatchAssignPostRequestBuilder toBuilder() =>
      DispatchAssignPostRequestBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is DispatchAssignPostRequest &&
        requestId == other.requestId &&
        vehicleId == other.vehicleId &&
        tripId == other.tripId &&
        reasonCode == other.reasonCode &&
        note == other.note;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, requestId.hashCode);
    _$hash = $jc(_$hash, vehicleId.hashCode);
    _$hash = $jc(_$hash, tripId.hashCode);
    _$hash = $jc(_$hash, reasonCode.hashCode);
    _$hash = $jc(_$hash, note.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'DispatchAssignPostRequest')
          ..add('requestId', requestId)
          ..add('vehicleId', vehicleId)
          ..add('tripId', tripId)
          ..add('reasonCode', reasonCode)
          ..add('note', note))
        .toString();
  }
}

class DispatchAssignPostRequestBuilder
    implements
        Builder<DispatchAssignPostRequest, DispatchAssignPostRequestBuilder> {
  _$DispatchAssignPostRequest? _$v;

  String? _requestId;
  String? get requestId => _$this._requestId;
  set requestId(String? requestId) => _$this._requestId = requestId;

  String? _vehicleId;
  String? get vehicleId => _$this._vehicleId;
  set vehicleId(String? vehicleId) => _$this._vehicleId = vehicleId;

  String? _tripId;
  String? get tripId => _$this._tripId;
  set tripId(String? tripId) => _$this._tripId = tripId;

  ReasonCode? _reasonCode;
  ReasonCode? get reasonCode => _$this._reasonCode;
  set reasonCode(ReasonCode? reasonCode) => _$this._reasonCode = reasonCode;

  String? _note;
  String? get note => _$this._note;
  set note(String? note) => _$this._note = note;

  DispatchAssignPostRequestBuilder() {
    DispatchAssignPostRequest._defaults(this);
  }

  DispatchAssignPostRequestBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _requestId = $v.requestId;
      _vehicleId = $v.vehicleId;
      _tripId = $v.tripId;
      _reasonCode = $v.reasonCode;
      _note = $v.note;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(DispatchAssignPostRequest other) {
    _$v = other as _$DispatchAssignPostRequest;
  }

  @override
  void update(void Function(DispatchAssignPostRequestBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  DispatchAssignPostRequest build() => _build();

  _$DispatchAssignPostRequest _build() {
    final _$result = _$v ??
        _$DispatchAssignPostRequest._(
          requestId: BuiltValueNullFieldError.checkNotNull(
              requestId, r'DispatchAssignPostRequest', 'requestId'),
          vehicleId: BuiltValueNullFieldError.checkNotNull(
              vehicleId, r'DispatchAssignPostRequest', 'vehicleId'),
          tripId: tripId,
          reasonCode: reasonCode,
          note: note,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
