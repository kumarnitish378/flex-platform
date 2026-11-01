//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'duty_state_gps.g.dart';

/// DutyStateGps
///
/// Properties:
/// * [distanceFilterM] 
/// * [heartbeatSeconds] 
@BuiltValue()
abstract class DutyStateGps implements Built<DutyStateGps, DutyStateGpsBuilder> {
  @BuiltValueField(wireName: r'distance_filter_m')
  int get distanceFilterM;

  @BuiltValueField(wireName: r'heartbeat_seconds')
  int get heartbeatSeconds;

  DutyStateGps._();

  factory DutyStateGps([void updates(DutyStateGpsBuilder b)]) = _$DutyStateGps;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(DutyStateGpsBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<DutyStateGps> get serializer => _$DutyStateGpsSerializer();
}

class _$DutyStateGpsSerializer implements PrimitiveSerializer<DutyStateGps> {
  @override
  final Iterable<Type> types = const [DutyStateGps, _$DutyStateGps];

  @override
  final String wireName = r'DutyStateGps';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    DutyStateGps object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'distance_filter_m';
    yield serializers.serialize(
      object.distanceFilterM,
      specifiedType: const FullType(int),
    );
    yield r'heartbeat_seconds';
    yield serializers.serialize(
      object.heartbeatSeconds,
      specifiedType: const FullType(int),
    );
  }

  @override
  Object serialize(
    Serializers serializers,
    DutyStateGps object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required DutyStateGpsBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'distance_filter_m':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.distanceFilterM = valueDes;
          break;
        case r'heartbeat_seconds':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.heartbeatSeconds = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  DutyStateGps deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = DutyStateGpsBuilder();
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

