//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'client_policy_all_of_effective.g.dart';

/// The numbers the platform will actually apply to this client's rides, after the stricter-value rule. Read-only. 
///
/// Properties:
/// * [maxDetourFactor] 
/// * [maxDetourMinutes] 
/// * [pickupWindowMinutes] 
/// * [noShowWaitMinutes] 
/// * [nightSafetyEnabled] 
/// * [nightStart] 
/// * [nightEnd] 
@BuiltValue()
abstract class ClientPolicyAllOfEffective implements Built<ClientPolicyAllOfEffective, ClientPolicyAllOfEffectiveBuilder> {
  @BuiltValueField(wireName: r'max_detour_factor')
  num? get maxDetourFactor;

  @BuiltValueField(wireName: r'max_detour_minutes')
  int? get maxDetourMinutes;

  @BuiltValueField(wireName: r'pickup_window_minutes')
  int? get pickupWindowMinutes;

  @BuiltValueField(wireName: r'no_show_wait_minutes')
  int? get noShowWaitMinutes;

  @BuiltValueField(wireName: r'night_safety_enabled')
  bool? get nightSafetyEnabled;

  @BuiltValueField(wireName: r'night_start')
  String? get nightStart;

  @BuiltValueField(wireName: r'night_end')
  String? get nightEnd;

  ClientPolicyAllOfEffective._();

  factory ClientPolicyAllOfEffective([void updates(ClientPolicyAllOfEffectiveBuilder b)]) = _$ClientPolicyAllOfEffective;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(ClientPolicyAllOfEffectiveBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<ClientPolicyAllOfEffective> get serializer => _$ClientPolicyAllOfEffectiveSerializer();
}

class _$ClientPolicyAllOfEffectiveSerializer implements PrimitiveSerializer<ClientPolicyAllOfEffective> {
  @override
  final Iterable<Type> types = const [ClientPolicyAllOfEffective, _$ClientPolicyAllOfEffective];

  @override
  final String wireName = r'ClientPolicyAllOfEffective';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    ClientPolicyAllOfEffective object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.maxDetourFactor != null) {
      yield r'max_detour_factor';
      yield serializers.serialize(
        object.maxDetourFactor,
        specifiedType: const FullType(num),
      );
    }
    if (object.maxDetourMinutes != null) {
      yield r'max_detour_minutes';
      yield serializers.serialize(
        object.maxDetourMinutes,
        specifiedType: const FullType(int),
      );
    }
    if (object.pickupWindowMinutes != null) {
      yield r'pickup_window_minutes';
      yield serializers.serialize(
        object.pickupWindowMinutes,
        specifiedType: const FullType(int),
      );
    }
    if (object.noShowWaitMinutes != null) {
      yield r'no_show_wait_minutes';
      yield serializers.serialize(
        object.noShowWaitMinutes,
        specifiedType: const FullType(int),
      );
    }
    if (object.nightSafetyEnabled != null) {
      yield r'night_safety_enabled';
      yield serializers.serialize(
        object.nightSafetyEnabled,
        specifiedType: const FullType(bool),
      );
    }
    if (object.nightStart != null) {
      yield r'night_start';
      yield serializers.serialize(
        object.nightStart,
        specifiedType: const FullType(String),
      );
    }
    if (object.nightEnd != null) {
      yield r'night_end';
      yield serializers.serialize(
        object.nightEnd,
        specifiedType: const FullType(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    ClientPolicyAllOfEffective object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required ClientPolicyAllOfEffectiveBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'max_detour_factor':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(num),
          ) as num;
          result.maxDetourFactor = valueDes;
          break;
        case r'max_detour_minutes':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.maxDetourMinutes = valueDes;
          break;
        case r'pickup_window_minutes':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.pickupWindowMinutes = valueDes;
          break;
        case r'no_show_wait_minutes':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.noShowWaitMinutes = valueDes;
          break;
        case r'night_safety_enabled':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.nightSafetyEnabled = valueDes;
          break;
        case r'night_start':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.nightStart = valueDes;
          break;
        case r'night_end':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.nightEnd = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  ClientPolicyAllOfEffective deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = ClientPolicyAllOfEffectiveBuilder();
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

