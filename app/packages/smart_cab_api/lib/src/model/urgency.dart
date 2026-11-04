//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'urgency.g.dart';

class Urgency extends EnumClass {

  @BuiltValueEnumConst(wireName: r'high')
  static const Urgency high = _$high;
  @BuiltValueEnumConst(wireName: r'medium')
  static const Urgency medium = _$medium;
  @BuiltValueEnumConst(wireName: r'low')
  static const Urgency low = _$low;

  static Serializer<Urgency> get serializer => _$urgencySerializer;

  const Urgency._(String name): super(name);

  static BuiltSet<Urgency> get values => _$values;
  static Urgency valueOf(String name) => _$valueOf(name);
}

/// Optionally, enum_class can generate a mixin to go with your enum for use
/// with Angular. It exposes your enum constants as getters. So, if you mix it
/// in to your Dart component class, the values become available to the
/// corresponding Angular template.
///
/// Trigger mixin generation by writing a line like this one next to your enum.
abstract class UrgencyMixin = Object with _$UrgencyMixin;

