// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'request_status.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const RequestStatus _$requested = const RequestStatus._('requested');
const RequestStatus _$queued = const RequestStatus._('queued');
const RequestStatus _$suggested = const RequestStatus._('suggested');
const RequestStatus _$assigned = const RequestStatus._('assigned');
const RequestStatus _$pickedUp = const RequestStatus._('pickedUp');
const RequestStatus _$dropped = const RequestStatus._('dropped');
const RequestStatus _$noShow = const RequestStatus._('noShow');
const RequestStatus _$cancelled = const RequestStatus._('cancelled');
const RequestStatus _$expired = const RequestStatus._('expired');

RequestStatus _$valueOf(String name) {
  switch (name) {
    case 'requested':
      return _$requested;
    case 'queued':
      return _$queued;
    case 'suggested':
      return _$suggested;
    case 'assigned':
      return _$assigned;
    case 'pickedUp':
      return _$pickedUp;
    case 'dropped':
      return _$dropped;
    case 'noShow':
      return _$noShow;
    case 'cancelled':
      return _$cancelled;
    case 'expired':
      return _$expired;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<RequestStatus> _$values =
    BuiltSet<RequestStatus>(const <RequestStatus>[
  _$requested,
  _$queued,
  _$suggested,
  _$assigned,
  _$pickedUp,
  _$dropped,
  _$noShow,
  _$cancelled,
  _$expired,
]);

class _$RequestStatusMeta {
  const _$RequestStatusMeta();
  RequestStatus get requested => _$requested;
  RequestStatus get queued => _$queued;
  RequestStatus get suggested => _$suggested;
  RequestStatus get assigned => _$assigned;
  RequestStatus get pickedUp => _$pickedUp;
  RequestStatus get dropped => _$dropped;
  RequestStatus get noShow => _$noShow;
  RequestStatus get cancelled => _$cancelled;
  RequestStatus get expired => _$expired;
  RequestStatus valueOf(String name) => _$valueOf(name);
  BuiltSet<RequestStatus> get values => _$values;
}

abstract class _$RequestStatusMixin {
  // ignore: non_constant_identifier_names
  _$RequestStatusMeta get RequestStatus => const _$RequestStatusMeta();
}

Serializer<RequestStatus> _$requestStatusSerializer =
    _$RequestStatusSerializer();

class _$RequestStatusSerializer implements PrimitiveSerializer<RequestStatus> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'requested': 'requested',
    'queued': 'queued',
    'suggested': 'suggested',
    'assigned': 'assigned',
    'pickedUp': 'picked_up',
    'dropped': 'dropped',
    'noShow': 'no_show',
    'cancelled': 'cancelled',
    'expired': 'expired',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'requested': 'requested',
    'queued': 'queued',
    'suggested': 'suggested',
    'assigned': 'assigned',
    'picked_up': 'pickedUp',
    'dropped': 'dropped',
    'no_show': 'noShow',
    'cancelled': 'cancelled',
    'expired': 'expired',
  };

  @override
  final Iterable<Type> types = const <Type>[RequestStatus];
  @override
  final String wireName = 'RequestStatus';

  @override
  Object serialize(Serializers serializers, RequestStatus object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  RequestStatus deserialize(Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      RequestStatus.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
