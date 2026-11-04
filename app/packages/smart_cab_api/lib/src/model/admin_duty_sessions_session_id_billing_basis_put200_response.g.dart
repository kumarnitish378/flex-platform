// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'admin_duty_sessions_session_id_billing_basis_put200_response.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum
    _$adminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum_gps =
    const AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum._(
        'gps');
const AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum
    _$adminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum_odometer =
    const AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum._(
        'odometer');

AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum
    _$adminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnumValueOf(
        String name) {
  switch (name) {
    case 'gps':
      return _$adminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum_gps;
    case 'odometer':
      return _$adminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum_odometer;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum>
    _$adminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnumValues =
    BuiltSet<
        AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum>(const <AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum>[
  _$adminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum_gps,
  _$adminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum_odometer,
]);

Serializer<AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum>
    _$adminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnumSerializer =
    _$AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnumSerializer();

class _$AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnumSerializer
    implements
        PrimitiveSerializer<
            AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'gps': 'gps',
    'odometer': 'odometer',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'gps': 'gps',
    'odometer': 'odometer',
  };

  @override
  final Iterable<Type> types = const <Type>[
    AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum
  ];
  @override
  final String wireName =
      'AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum';

  @override
  Object serialize(Serializers serializers,
          AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum deserialize(
          Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$AdminDutySessionsSessionIdBillingBasisPut200Response
    extends AdminDutySessionsSessionIdBillingBasisPut200Response {
  @override
  final String? sessionId;
  @override
  final AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum? basis;
  @override
  final String? setBy;
  @override
  final DateTime? setAt;
  @override
  final String? note;

  factory _$AdminDutySessionsSessionIdBillingBasisPut200Response(
          [void Function(
                  AdminDutySessionsSessionIdBillingBasisPut200ResponseBuilder)?
              updates]) =>
      (AdminDutySessionsSessionIdBillingBasisPut200ResponseBuilder()
            ..update(updates))
          ._build();

  _$AdminDutySessionsSessionIdBillingBasisPut200Response._(
      {this.sessionId, this.basis, this.setBy, this.setAt, this.note})
      : super._();
  @override
  AdminDutySessionsSessionIdBillingBasisPut200Response rebuild(
          void Function(
                  AdminDutySessionsSessionIdBillingBasisPut200ResponseBuilder)
              updates) =>
      (toBuilder()..update(updates)).build();

  @override
  AdminDutySessionsSessionIdBillingBasisPut200ResponseBuilder toBuilder() =>
      AdminDutySessionsSessionIdBillingBasisPut200ResponseBuilder()
        ..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is AdminDutySessionsSessionIdBillingBasisPut200Response &&
        sessionId == other.sessionId &&
        basis == other.basis &&
        setBy == other.setBy &&
        setAt == other.setAt &&
        note == other.note;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, sessionId.hashCode);
    _$hash = $jc(_$hash, basis.hashCode);
    _$hash = $jc(_$hash, setBy.hashCode);
    _$hash = $jc(_$hash, setAt.hashCode);
    _$hash = $jc(_$hash, note.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(
            r'AdminDutySessionsSessionIdBillingBasisPut200Response')
          ..add('sessionId', sessionId)
          ..add('basis', basis)
          ..add('setBy', setBy)
          ..add('setAt', setAt)
          ..add('note', note))
        .toString();
  }
}

class AdminDutySessionsSessionIdBillingBasisPut200ResponseBuilder
    implements
        Builder<AdminDutySessionsSessionIdBillingBasisPut200Response,
            AdminDutySessionsSessionIdBillingBasisPut200ResponseBuilder> {
  _$AdminDutySessionsSessionIdBillingBasisPut200Response? _$v;

  String? _sessionId;
  String? get sessionId => _$this._sessionId;
  set sessionId(String? sessionId) => _$this._sessionId = sessionId;

  AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum? _basis;
  AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum? get basis =>
      _$this._basis;
  set basis(
          AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum?
              basis) =>
      _$this._basis = basis;

  String? _setBy;
  String? get setBy => _$this._setBy;
  set setBy(String? setBy) => _$this._setBy = setBy;

  DateTime? _setAt;
  DateTime? get setAt => _$this._setAt;
  set setAt(DateTime? setAt) => _$this._setAt = setAt;

  String? _note;
  String? get note => _$this._note;
  set note(String? note) => _$this._note = note;

  AdminDutySessionsSessionIdBillingBasisPut200ResponseBuilder() {
    AdminDutySessionsSessionIdBillingBasisPut200Response._defaults(this);
  }

  AdminDutySessionsSessionIdBillingBasisPut200ResponseBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _sessionId = $v.sessionId;
      _basis = $v.basis;
      _setBy = $v.setBy;
      _setAt = $v.setAt;
      _note = $v.note;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(AdminDutySessionsSessionIdBillingBasisPut200Response other) {
    _$v = other as _$AdminDutySessionsSessionIdBillingBasisPut200Response;
  }

  @override
  void update(
      void Function(
              AdminDutySessionsSessionIdBillingBasisPut200ResponseBuilder)?
          updates) {
    if (updates != null) updates(this);
  }

  @override
  AdminDutySessionsSessionIdBillingBasisPut200Response build() => _build();

  _$AdminDutySessionsSessionIdBillingBasisPut200Response _build() {
    final _$result = _$v ??
        _$AdminDutySessionsSessionIdBillingBasisPut200Response._(
          sessionId: sessionId,
          basis: basis,
          setBy: setBy,
          setAt: setAt,
          note: note,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
