//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'trip_status.g.dart';

class TripStatus extends EnumClass {

  @BuiltValueEnumConst(wireName: r'planned')
  static const TripStatus planned = _$planned;
  @BuiltValueEnumConst(wireName: r'dispatched')
  static const TripStatus dispatched = _$dispatched;
  @BuiltValueEnumConst(wireName: r'in_progress')
  static const TripStatus inProgress = _$inProgress;
  @BuiltValueEnumConst(wireName: r'completed')
  static const TripStatus completed = _$completed;
  @BuiltValueEnumConst(wireName: r'cancelled')
  static const TripStatus cancelled = _$cancelled;
  @BuiltValueEnumConst(wireName: r'aborted')
  static const TripStatus aborted = _$aborted;

  static Serializer<TripStatus> get serializer => _$tripStatusSerializer;

  const TripStatus._(String name): super(name);

  static BuiltSet<TripStatus> get values => _$values;
  static TripStatus valueOf(String name) => _$valueOf(name);
}

/// Optionally, enum_class can generate a mixin to go with your enum for use
/// with Angular. It exposes your enum constants as getters. So, if you mix it
/// in to your Dart component class, the values become available to the
/// corresponding Angular template.
///
/// Trigger mixin generation by writing a line like this one next to your enum.
abstract class TripStatusMixin = Object with _$TripStatusMixin;

