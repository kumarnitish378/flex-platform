// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'trip_status.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const TripStatus _$planned = const TripStatus._('planned');
const TripStatus _$dispatched = const TripStatus._('dispatched');
const TripStatus _$inProgress = const TripStatus._('inProgress');
const TripStatus _$completed = const TripStatus._('completed');
const TripStatus _$cancelled = const TripStatus._('cancelled');
const TripStatus _$aborted = const TripStatus._('aborted');

TripStatus _$valueOf(String name) {
  switch (name) {
    case 'planned':
      return _$planned;
    case 'dispatched':
      return _$dispatched;
    case 'inProgress':
      return _$inProgress;
    case 'completed':
      return _$completed;
    case 'cancelled':
      return _$cancelled;
    case 'aborted':
      return _$aborted;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<TripStatus> _$values = BuiltSet<TripStatus>(const <TripStatus>[
  _$planned,
  _$dispatched,
  _$inProgress,
  _$completed,
  _$cancelled,
  _$aborted,
]);

class _$TripStatusMeta {
  const _$TripStatusMeta();
  TripStatus get planned => _$planned;
  TripStatus get dispatched => _$dispatched;
  TripStatus get inProgress => _$inProgress;
  TripStatus get completed => _$completed;
  TripStatus get cancelled => _$cancelled;
  TripStatus get aborted => _$aborted;
  TripStatus valueOf(String name) => _$valueOf(name);
  BuiltSet<TripStatus> get values => _$values;
}

abstract class _$TripStatusMixin {
  // ignore: non_constant_identifier_names
  _$TripStatusMeta get TripStatus => const _$TripStatusMeta();
}

Serializer<TripStatus> _$tripStatusSerializer = _$TripStatusSerializer();

class _$TripStatusSerializer implements PrimitiveSerializer<TripStatus> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'planned': 'planned',
    'dispatched': 'dispatched',
    'inProgress': 'in_progress',
    'completed': 'completed',
    'cancelled': 'cancelled',
    'aborted': 'aborted',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'planned': 'planned',
    'dispatched': 'dispatched',
    'in_progress': 'inProgress',
    'completed': 'completed',
    'cancelled': 'cancelled',
    'aborted': 'aborted',
  };

  @override
  final Iterable<Type> types = const <Type>[TripStatus];
  @override
  final String wireName = 'TripStatus';

  @override
  Object serialize(Serializers serializers, TripStatus object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  TripStatus deserialize(Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      TripStatus.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
