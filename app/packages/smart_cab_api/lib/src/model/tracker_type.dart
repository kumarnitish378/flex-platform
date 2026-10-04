//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'tracker_type.g.dart';

class TrackerType extends EnumClass {

  @BuiltValueEnumConst(wireName: r'app')
  static const TrackerType app = _$app;
  @BuiltValueEnumConst(wireName: r'esp32')
  static const TrackerType esp32 = _$esp32;

  static Serializer<TrackerType> get serializer => _$trackerTypeSerializer;

  const TrackerType._(String name): super(name);

  static BuiltSet<TrackerType> get values => _$values;
  static TrackerType valueOf(String name) => _$valueOf(name);
}

/// Optionally, enum_class can generate a mixin to go with your enum for use
/// with Angular. It exposes your enum constants as getters. So, if you mix it
/// in to your Dart component class, the values become available to the
/// corresponding Angular template.
///
/// Trigger mixin generation by writing a line like this one next to your enum.
abstract class TrackerTypeMixin = Object with _$TrackerTypeMixin;

