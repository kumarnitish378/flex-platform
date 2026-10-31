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
/// * [optimizerRuns] - batch runs the jump caused
/// * [optimizerApplied] 
/// * [optimizerSuggested] 
/// * [optimizerHinted] 
/// * [optimizerFailed] 
@BuiltValue()
abstract class SimClock implements Built<SimClock, SimClockBuilder> {
  @BuiltValueField(wireName: r'now')
  DateTime? get now;

  /// PUT only
  @BuiltValueField(wireName: r'advance_seconds')
  int? get advanceSeconds;

  /// batch runs the jump caused
  @BuiltValueField(wireName: r'optimizer_runs')
  int? get optimizerRuns;

  @BuiltValueField(wireName: r'optimizer_applied')
  int? get optimizerApplied;

  @BuiltValueField(wireName: r'optimizer_suggested')
  int? get optimizerSuggested;

  @BuiltValueField(wireName: r'optimizer_hinted')
  int? get optimizerHinted;

  @BuiltValueField(wireName: r'optimizer_failed')
  int? get optimizerFailed;

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
    if (object.optimizerRuns != null) {
      yield r'optimizer_runs';
      yield serializers.serialize(
        object.optimizerRuns,
        specifiedType: const FullType(int),
      );
    }
    if (object.optimizerApplied != null) {
      yield r'optimizer_applied';
      yield serializers.serialize(
        object.optimizerApplied,
        specifiedType: const FullType(int),
      );
    }
    if (object.optimizerSuggested != null) {
      yield r'optimizer_suggested';
      yield serializers.serialize(
        object.optimizerSuggested,
        specifiedType: const FullType(int),
      );
    }
    if (object.optimizerHinted != null) {
      yield r'optimizer_hinted';
      yield serializers.serialize(
        object.optimizerHinted,
        specifiedType: const FullType(int),
      );
    }
    if (object.optimizerFailed != null) {
      yield r'optimizer_failed';
      yield serializers.serialize(
        object.optimizerFailed,
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
        case r'optimizer_runs':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.optimizerRuns = valueDes;
          break;
        case r'optimizer_applied':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.optimizerApplied = valueDes;
          break;
        case r'optimizer_suggested':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.optimizerSuggested = valueDes;
          break;
        case r'optimizer_hinted':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.optimizerHinted = valueDes;
          break;
        case r'optimizer_failed':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.optimizerFailed = valueDes;
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

