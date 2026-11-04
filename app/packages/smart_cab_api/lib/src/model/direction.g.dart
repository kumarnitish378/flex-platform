// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'direction.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const Direction _$toOffice = const Direction._('toOffice');
const Direction _$fromOffice = const Direction._('fromOffice');

Direction _$valueOf(String name) {
  switch (name) {
    case 'toOffice':
      return _$toOffice;
    case 'fromOffice':
      return _$fromOffice;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<Direction> _$values = BuiltSet<Direction>(const <Direction>[
  _$toOffice,
  _$fromOffice,
]);

class _$DirectionMeta {
  const _$DirectionMeta();
  Direction get toOffice => _$toOffice;
  Direction get fromOffice => _$fromOffice;
  Direction valueOf(String name) => _$valueOf(name);
  BuiltSet<Direction> get values => _$values;
}

abstract class _$DirectionMixin {
  // ignore: non_constant_identifier_names
  _$DirectionMeta get Direction => const _$DirectionMeta();
}

Serializer<Direction> _$directionSerializer = _$DirectionSerializer();

class _$DirectionSerializer implements PrimitiveSerializer<Direction> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'toOffice': 'to_office',
    'fromOffice': 'from_office',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'to_office': 'toOffice',
    'from_office': 'fromOffice',
  };

  @override
  final Iterable<Type> types = const <Type>[Direction];
  @override
  final String wireName = 'Direction';

  @override
  Object serialize(Serializers serializers, Direction object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  Direction deserialize(Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      Direction.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
