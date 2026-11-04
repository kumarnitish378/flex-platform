//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/client_policy_input.dart';
import 'package:smart_cab_api/src/model/client_policy_all_of_effective.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'client_policy.g.dart';

/// ClientPolicy
///
/// Properties:
/// * [poolingAllowed] - False means this client's riders never share a cab. Equivalent to every one of their requests arriving with `no_sharing`. 
/// * [employeeOptOutAllowed] - Whether an employee of this client may ask not to share. False makes `no_sharing: true` on their request a 422 rather than a silently ignored field - the rider is told, instead of being quietly pooled. 
/// * [nightSafetyEnabled] 
/// * [nightStart] - local time, HH:MM:SS
/// * [nightEnd] 
/// * [maxDetourFactor] 
/// * [maxDetourMinutes] 
/// * [pickupWindowMinutes] 
/// * [noShowWaitMinutes] 
/// * [clientId] 
/// * [effective] 
@BuiltValue()
abstract class ClientPolicy implements ClientPolicyInput, Built<ClientPolicy, ClientPolicyBuilder> {
  @BuiltValueField(wireName: r'effective')
  ClientPolicyAllOfEffective? get effective;

  @BuiltValueField(wireName: r'client_id')
  String? get clientId;

  ClientPolicy._();

  factory ClientPolicy([void updates(ClientPolicyBuilder b)]) = _$ClientPolicy;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(ClientPolicyBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<ClientPolicy> get serializer => _$ClientPolicySerializer();
}

class _$ClientPolicySerializer implements PrimitiveSerializer<ClientPolicy> {
  @override
  final Iterable<Type> types = const [ClientPolicy, _$ClientPolicy];

  @override
  final String wireName = r'ClientPolicy';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    ClientPolicy object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.effective != null) {
      yield r'effective';
      yield serializers.serialize(
        object.effective,
        specifiedType: const FullType(ClientPolicyAllOfEffective),
      );
    }
    if (object.nightStart != null) {
      yield r'night_start';
      yield serializers.serialize(
        object.nightStart,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.nightEnd != null) {
      yield r'night_end';
      yield serializers.serialize(
        object.nightEnd,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.poolingAllowed != null) {
      yield r'pooling_allowed';
      yield serializers.serialize(
        object.poolingAllowed,
        specifiedType: const FullType(bool),
      );
    }
    if (object.maxDetourMinutes != null) {
      yield r'max_detour_minutes';
      yield serializers.serialize(
        object.maxDetourMinutes,
        specifiedType: const FullType.nullable(int),
      );
    }
    if (object.clientId != null) {
      yield r'client_id';
      yield serializers.serialize(
        object.clientId,
        specifiedType: const FullType(String),
      );
    }
    if (object.employeeOptOutAllowed != null) {
      yield r'employee_opt_out_allowed';
      yield serializers.serialize(
        object.employeeOptOutAllowed,
        specifiedType: const FullType(bool),
      );
    }
    if (object.pickupWindowMinutes != null) {
      yield r'pickup_window_minutes';
      yield serializers.serialize(
        object.pickupWindowMinutes,
        specifiedType: const FullType.nullable(int),
      );
    }
    if (object.noShowWaitMinutes != null) {
      yield r'no_show_wait_minutes';
      yield serializers.serialize(
        object.noShowWaitMinutes,
        specifiedType: const FullType.nullable(int),
      );
    }
    if (object.maxDetourFactor != null) {
      yield r'max_detour_factor';
      yield serializers.serialize(
        object.maxDetourFactor,
        specifiedType: const FullType.nullable(num),
      );
    }
    if (object.nightSafetyEnabled != null) {
      yield r'night_safety_enabled';
      yield serializers.serialize(
        object.nightSafetyEnabled,
        specifiedType: const FullType(bool),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    ClientPolicy object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required ClientPolicyBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'effective':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(ClientPolicyAllOfEffective),
          ) as ClientPolicyAllOfEffective;
          result.effective.replace(valueDes);
          break;
        case r'night_start':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.nightStart = valueDes;
          break;
        case r'night_end':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.nightEnd = valueDes;
          break;
        case r'pooling_allowed':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.poolingAllowed = valueDes;
          break;
        case r'max_detour_minutes':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(int),
          ) as int?;
          if (valueDes == null) continue;
          result.maxDetourMinutes = valueDes;
          break;
        case r'client_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.clientId = valueDes;
          break;
        case r'employee_opt_out_allowed':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.employeeOptOutAllowed = valueDes;
          break;
        case r'pickup_window_minutes':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(int),
          ) as int?;
          if (valueDes == null) continue;
          result.pickupWindowMinutes = valueDes;
          break;
        case r'no_show_wait_minutes':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(int),
          ) as int?;
          if (valueDes == null) continue;
          result.noShowWaitMinutes = valueDes;
          break;
        case r'max_detour_factor':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.maxDetourFactor = valueDes;
          break;
        case r'night_safety_enabled':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.nightSafetyEnabled = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  ClientPolicy deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = ClientPolicyBuilder();
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

