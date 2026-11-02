//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'admin_duty_sessions_session_id_billing_basis_put200_response.g.dart';

/// AdminDutySessionsSessionIdBillingBasisPut200Response
///
/// Properties:
/// * [sessionId] 
/// * [basis] 
/// * [setBy] 
/// * [setAt] 
/// * [note] 
@BuiltValue()
abstract class AdminDutySessionsSessionIdBillingBasisPut200Response implements Built<AdminDutySessionsSessionIdBillingBasisPut200Response, AdminDutySessionsSessionIdBillingBasisPut200ResponseBuilder> {
  @BuiltValueField(wireName: r'session_id')
  String? get sessionId;

  @BuiltValueField(wireName: r'basis')
  AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum? get basis;
  // enum basisEnum {  gps,  odometer,  };

  @BuiltValueField(wireName: r'set_by')
  String? get setBy;

  @BuiltValueField(wireName: r'set_at')
  DateTime? get setAt;

  @BuiltValueField(wireName: r'note')
  String? get note;

  AdminDutySessionsSessionIdBillingBasisPut200Response._();

  factory AdminDutySessionsSessionIdBillingBasisPut200Response([void updates(AdminDutySessionsSessionIdBillingBasisPut200ResponseBuilder b)]) = _$AdminDutySessionsSessionIdBillingBasisPut200Response;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(AdminDutySessionsSessionIdBillingBasisPut200ResponseBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<AdminDutySessionsSessionIdBillingBasisPut200Response> get serializer => _$AdminDutySessionsSessionIdBillingBasisPut200ResponseSerializer();
}

class _$AdminDutySessionsSessionIdBillingBasisPut200ResponseSerializer implements PrimitiveSerializer<AdminDutySessionsSessionIdBillingBasisPut200Response> {
  @override
  final Iterable<Type> types = const [AdminDutySessionsSessionIdBillingBasisPut200Response, _$AdminDutySessionsSessionIdBillingBasisPut200Response];

  @override
  final String wireName = r'AdminDutySessionsSessionIdBillingBasisPut200Response';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    AdminDutySessionsSessionIdBillingBasisPut200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.sessionId != null) {
      yield r'session_id';
      yield serializers.serialize(
        object.sessionId,
        specifiedType: const FullType(String),
      );
    }
    if (object.basis != null) {
      yield r'basis';
      yield serializers.serialize(
        object.basis,
        specifiedType: const FullType(AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum),
      );
    }
    if (object.setBy != null) {
      yield r'set_by';
      yield serializers.serialize(
        object.setBy,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.setAt != null) {
      yield r'set_at';
      yield serializers.serialize(
        object.setAt,
        specifiedType: const FullType.nullable(DateTime),
      );
    }
    if (object.note != null) {
      yield r'note';
      yield serializers.serialize(
        object.note,
        specifiedType: const FullType.nullable(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    AdminDutySessionsSessionIdBillingBasisPut200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required AdminDutySessionsSessionIdBillingBasisPut200ResponseBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'session_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.sessionId = valueDes;
          break;
        case r'basis':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum),
          ) as AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum;
          result.basis = valueDes;
          break;
        case r'set_by':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.setBy = valueDes;
          break;
        case r'set_at':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(DateTime),
          ) as DateTime?;
          if (valueDes == null) continue;
          result.setAt = valueDes;
          break;
        case r'note':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.note = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  AdminDutySessionsSessionIdBillingBasisPut200Response deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = AdminDutySessionsSessionIdBillingBasisPut200ResponseBuilder();
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

class AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'gps')
  static const AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum gps = _$adminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum_gps;
  @BuiltValueEnumConst(wireName: r'odometer')
  static const AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum odometer = _$adminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum_odometer;

  static Serializer<AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum> get serializer => _$adminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnumSerializer;

  const AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum._(String name): super(name);

  static BuiltSet<AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum> get values => _$adminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnumValues;
  static AdminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnum valueOf(String name) => _$adminDutySessionsSessionIdBillingBasisPut200ResponseBasisEnumValueOf(name);
}

