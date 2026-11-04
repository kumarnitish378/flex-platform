// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'stop_status.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const StopStatus _$pending = const StopStatus._('pending');
const StopStatus _$enRoute = const StopStatus._('enRoute');
const StopStatus _$arrived = const StopStatus._('arrived');
const StopStatus _$done = const StopStatus._('done');
const StopStatus _$skipped = const StopStatus._('skipped');

StopStatus _$valueOf(String name) {
  switch (name) {
    case 'pending':
      return _$pending;
    case 'enRoute':
      return _$enRoute;
    case 'arrived':
      return _$arrived;
    case 'done':
      return _$done;
    case 'skipped':
      return _$skipped;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<StopStatus> _$values = BuiltSet<StopStatus>(const <StopStatus>[
  _$pending,
  _$enRoute,
  _$arrived,
  _$done,
  _$skipped,
]);

class _$StopStatusMeta {
  const _$StopStatusMeta();
  StopStatus get pending => _$pending;
  StopStatus get enRoute => _$enRoute;
  StopStatus get arrived => _$arrived;
  StopStatus get done => _$done;
  StopStatus get skipped => _$skipped;
  StopStatus valueOf(String name) => _$valueOf(name);
  BuiltSet<StopStatus> get values => _$values;
}

abstract class _$StopStatusMixin {
  // ignore: non_constant_identifier_names
  _$StopStatusMeta get StopStatus => const _$StopStatusMeta();
}

Serializer<StopStatus> _$stopStatusSerializer = _$StopStatusSerializer();

class _$StopStatusSerializer implements PrimitiveSerializer<StopStatus> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'pending': 'pending',
    'enRoute': 'en_route',
    'arrived': 'arrived',
    'done': 'done',
    'skipped': 'skipped',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'pending': 'pending',
    'en_route': 'enRoute',
    'arrived': 'arrived',
    'done': 'done',
    'skipped': 'skipped',
  };

  @override
  final Iterable<Type> types = const <Type>[StopStatus];
  @override
  final String wireName = 'StopStatus';

  @override
  Object serialize(Serializers serializers, StopStatus object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  StopStatus deserialize(Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      StopStatus.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
