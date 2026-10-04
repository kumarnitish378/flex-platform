//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'sim_clock.g.dart';

/// SimClock
///
/// Properties:
/// * [now] 
/// * [advanceSeconds] - PUT only
@BuiltValue()
abstract class SimClock implements Built<SimClock, SimClockBuilder> {
  @BuiltValueField(wireName: r'now')
  DateTime? get now;

  /// PUT only
  @BuiltValueField(wireName: r'advance_seconds')
  int? get advanceSeconds;

  SimClock._();

  factory SimClock([void updates(SimClockBuilder b)]) = _$SimClock;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(SimClockBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<SimClock> get serializer => _$SimClockSerializer();
}

class _$SimClockSerializer implements PrimitiveSerializer<SimClock> {
  @override
  final Iterable<Type> types = const [SimClock, _$SimClock];

  @override
  final String wireName = r'SimClock';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    SimClock object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.now != null) {
      yield r'now';
      yield serializers.serialize(
        object.now,
        specifiedType: const FullType(DateTime),
      );
    }
    if (object.advanceSeconds != null) {
      yield r'advance_seconds';
      yield serializers.serialize(
        object.advanceSeconds,
        specifiedType: const FullType(int),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    SimClock object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required SimClockBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'now':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(DateTime),
          ) as DateTime;
          result.now = valueDes;
          break;
        case r'advance_seconds':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.advanceSeconds = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  SimClock deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = SimClockBuilder();
    final serializedList = (serialized as Iterable<Object?>).toList();
    final unhandled = <Object?>[];
    _deserializeProperties(
      serializers,
      serialized,
      specifiedType: specifiedType,
      serializedList: serializedList,
      unhandled: unhandled,
      result: result,
    );
    return result.build();
  }
}

