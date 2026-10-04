//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'stop_status.g.dart';

class StopStatus extends EnumClass {

  @BuiltValueEnumConst(wireName: r'pending')
  static const StopStatus pending = _$pending;
  @BuiltValueEnumConst(wireName: r'en_route')
  static const StopStatus enRoute = _$enRoute;
  @BuiltValueEnumConst(wireName: r'arrived')
  static const StopStatus arrived = _$arrived;
  @BuiltValueEnumConst(wireName: r'done')
  static const StopStatus done = _$done;
  @BuiltValueEnumConst(wireName: r'skipped')
  static const StopStatus skipped = _$skipped;

  static Serializer<StopStatus> get serializer => _$stopStatusSerializer;

  const StopStatus._(String name): super(name);

  static BuiltSet<StopStatus> get values => _$values;
  static StopStatus valueOf(String name) => _$valueOf(name);
}

/// Optionally, enum_class can generate a mixin to go with your enum for use
/// with Angular. It exposes your enum constants as getters. So, if you mix it
/// in to your Dart component class, the values become available to the
/// corresponding Angular template.
///
/// Trigger mixin generation by writing a line like this one next to your enum.
abstract class StopStatusMixin = Object with _$StopStatusMixin;

