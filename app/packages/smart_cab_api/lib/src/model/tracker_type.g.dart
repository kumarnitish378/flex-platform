// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'tracker_type.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const TrackerType _$app = const TrackerType._('app');
const TrackerType _$esp32 = const TrackerType._('esp32');

TrackerType _$valueOf(String name) {
  switch (name) {
    case 'app':
      return _$app;
    case 'esp32':
      return _$esp32;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<TrackerType> _$values =
    BuiltSet<TrackerType>(const <TrackerType>[
  _$app,
  _$esp32,
]);

class _$TrackerTypeMeta {
  const _$TrackerTypeMeta();
  TrackerType get app => _$app;
  TrackerType get esp32 => _$esp32;
  TrackerType valueOf(String name) => _$valueOf(name);
  BuiltSet<TrackerType> get values => _$values;
}

abstract class _$TrackerTypeMixin {
  // ignore: non_constant_identifier_names
  _$TrackerTypeMeta get TrackerType => const _$TrackerTypeMeta();
}

Serializer<TrackerType> _$trackerTypeSerializer = _$TrackerTypeSerializer();

class _$TrackerTypeSerializer implements PrimitiveSerializer<TrackerType> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'app': 'app',
    'esp32': 'esp32',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'app': 'app',
    'esp32': 'esp32',
  };

  @override
  final Iterable<Type> types = const <Type>[TrackerType];
  @override
  final String wireName = 'TrackerType';

  @override
  Object serialize(Serializers serializers, TrackerType object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  TrackerType deserialize(Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      TrackerType.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
