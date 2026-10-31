//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'client_policy_input.g.dart';

/// Every field optional. `null` clears an override and the operator's value applies. The numeric four are **stricter only** - a client may tighten a limit, never loosen it - and a laxer value is kept as written and simply not applied, which the `effective` block makes visible. 
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
@BuiltValue(instantiable: false)
abstract class ClientPolicyInput  {
  /// False means this client's riders never share a cab. Equivalent to every one of their requests arriving with `no_sharing`. 
  @BuiltValueField(wireName: r'pooling_allowed')
  bool? get poolingAllowed;

  /// Whether an employee of this client may ask not to share. False makes `no_sharing: true` on their request a 422 rather than a silently ignored field - the rider is told, instead of being quietly pooled. 
  @BuiltValueField(wireName: r'employee_opt_out_allowed')
  bool? get employeeOptOutAllowed;

  @BuiltValueField(wireName: r'night_safety_enabled')
  bool? get nightSafetyEnabled;

  /// local time, HH:MM:SS
  @BuiltValueField(wireName: r'night_start')
  String? get nightStart;

  @BuiltValueField(wireName: r'night_end')
  String? get nightEnd;

  @BuiltValueField(wireName: r'max_detour_factor')
  num? get maxDetourFactor;

  @BuiltValueField(wireName: r'max_detour_minutes')
  int? get maxDetourMinutes;

  @BuiltValueField(wireName: r'pickup_window_minutes')
  int? get pickupWindowMinutes;

  @BuiltValueField(wireName: r'no_show_wait_minutes')
  int? get noShowWaitMinutes;

  @BuiltValueSerializer(custom: true)
  static Serializer<ClientPolicyInput> get serializer => _$ClientPolicyInputSerializer();
}

class _$ClientPolicyInputSerializer implements PrimitiveSerializer<ClientPolicyInput> {
  @override
  final Iterable<Type> types = const [ClientPolicyInput];

  @override
  final String wireName = r'ClientPolicyInput';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    ClientPolicyInput object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.poolingAllowed != null) {
      yield r'pooling_allowed';
      yield serializers.serialize(
        object.poolingAllowed,
        specifiedType: const FullType(bool),
      );
    }
    if (object.employeeOptOutAllowed != null) {
      yield r'employee_opt_out_allowed';
      yield serializers.serialize(
        object.employeeOptOutAllowed,
        specifiedType: const FullType(bool),
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
    if (object.maxDetourFactor != null) {
      yield r'max_detour_factor';
      yield serializers.serialize(
        object.maxDetourFactor,
        specifiedType: const FullType.nullable(num),
      );
    }
    if (object.maxDetourMinutes != null) {
      yield r'max_detour_minutes';
      yield serializers.serialize(
        object.maxDetourMinutes,
        specifiedType: const FullType.nullable(int),
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
  }

  @override
  Object serialize(
    Serializers serializers,
    ClientPolicyInput object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  @override
  ClientPolicyInput deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return serializers.deserialize(serialized, specifiedType: FullType($ClientPolicyInput)) as $ClientPolicyInput;
  }
}

/// a concrete implementation of [ClientPolicyInput], since [ClientPolicyInput] is not instantiable
@BuiltValue(instantiable: true)
abstract class $ClientPolicyInput implements ClientPolicyInput, Built<$ClientPolicyInput, $ClientPolicyInputBuilder> {
  $ClientPolicyInput._();

  factory $ClientPolicyInput([void Function($ClientPolicyInputBuilder)? updates]) = _$$ClientPolicyInput;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults($ClientPolicyInputBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<$ClientPolicyInput> get serializer => _$$ClientPolicyInputSerializer();
}

class _$$ClientPolicyInputSerializer implements PrimitiveSerializer<$ClientPolicyInput> {
  @override
  final Iterable<Type> types = const [$ClientPolicyInput, _$$ClientPolicyInput];

  @override
  final String wireName = r'$ClientPolicyInput';

  @override
  Object serialize(
    Serializers serializers,
    $ClientPolicyInput object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return serializers.serialize(object, specifiedType: FullType(ClientPolicyInput))!;
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required ClientPolicyInputBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'pooling_allowed':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.poolingAllowed = valueDes;
          break;
        case r'employee_opt_out_allowed':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.employeeOptOutAllowed = valueDes;
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
        case r'max_detour_factor':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.maxDetourFactor = valueDes;
          break;
        case r'max_detour_minutes':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(int),
          ) as int?;
          if (valueDes == null) continue;
          result.maxDetourMinutes = valueDes;
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
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  $ClientPolicyInput deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = $ClientPolicyInputBuilder();
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

