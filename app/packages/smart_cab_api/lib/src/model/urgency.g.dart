// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'urgency.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const Urgency _$high = const Urgency._('high');
const Urgency _$medium = const Urgency._('medium');
const Urgency _$low = const Urgency._('low');

Urgency _$valueOf(String name) {
  switch (name) {
    case 'high':
      return _$high;
    case 'medium':
      return _$medium;
    case 'low':
      return _$low;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<Urgency> _$values = BuiltSet<Urgency>(const <Urgency>[
  _$high,
  _$medium,
  _$low,
]);

class _$UrgencyMeta {
  const _$UrgencyMeta();
  Urgency get high => _$high;
  Urgency get medium => _$medium;
  Urgency get low => _$low;
  Urgency valueOf(String name) => _$valueOf(name);
  BuiltSet<Urgency> get values => _$values;
}

abstract class _$UrgencyMixin {
  // ignore: non_constant_identifier_names
  _$UrgencyMeta get Urgency => const _$UrgencyMeta();
}

Serializer<Urgency> _$urgencySerializer = _$UrgencySerializer();

class _$UrgencySerializer implements PrimitiveSerializer<Urgency> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'high': 'high',
    'medium': 'medium',
    'low': 'low',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'high': 'high',
    'medium': 'medium',
    'low': 'low',
  };

  @override
  final Iterable<Type> types = const <Type>[Urgency];
  @override
  final String wireName = 'Urgency';

  @override
  Object serialize(Serializers serializers, Urgency object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  Urgency deserialize(Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      Urgency.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
