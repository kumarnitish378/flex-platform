//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'admin_duty_sessions_session_id_billing_basis_put_request.g.dart';

/// AdminDutySessionsSessionIdBillingBasisPutRequest
///
/// Properties:
/// * [basis] 
/// * [note] 
@BuiltValue()
abstract class AdminDutySessionsSessionIdBillingBasisPutRequest implements Built<AdminDutySessionsSessionIdBillingBasisPutRequest, AdminDutySessionsSessionIdBillingBasisPutRequestBuilder> {
  @BuiltValueField(wireName: r'basis')
  AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum get basis;
  // enum basisEnum {  gps,  odometer,  };

  @BuiltValueField(wireName: r'note')
  String? get note;

  AdminDutySessionsSessionIdBillingBasisPutRequest._();

  factory AdminDutySessionsSessionIdBillingBasisPutRequest([void updates(AdminDutySessionsSessionIdBillingBasisPutRequestBuilder b)]) = _$AdminDutySessionsSessionIdBillingBasisPutRequest;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(AdminDutySessionsSessionIdBillingBasisPutRequestBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<AdminDutySessionsSessionIdBillingBasisPutRequest> get serializer => _$AdminDutySessionsSessionIdBillingBasisPutRequestSerializer();
}

class _$AdminDutySessionsSessionIdBillingBasisPutRequestSerializer implements PrimitiveSerializer<AdminDutySessionsSessionIdBillingBasisPutRequest> {
  @override
  final Iterable<Type> types = const [AdminDutySessionsSessionIdBillingBasisPutRequest, _$AdminDutySessionsSessionIdBillingBasisPutRequest];

  @override
  final String wireName = r'AdminDutySessionsSessionIdBillingBasisPutRequest';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    AdminDutySessionsSessionIdBillingBasisPutRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'basis';
    yield serializers.serialize(
      object.basis,
      specifiedType: const FullType(AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum),
    );
    if (object.note != null) {
      yield r'note';
      yield serializers.serialize(
        object.note,
        specifiedType: const FullType(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    AdminDutySessionsSessionIdBillingBasisPutRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required AdminDutySessionsSessionIdBillingBasisPutRequestBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'basis':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum),
          ) as AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum;
          result.basis = valueDes;
          break;
        case r'note':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
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
  AdminDutySessionsSessionIdBillingBasisPutRequest deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = AdminDutySessionsSessionIdBillingBasisPutRequestBuilder();
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

class AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'gps')
  static const AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum gps = _$adminDutySessionsSessionIdBillingBasisPutRequestBasisEnum_gps;
  @BuiltValueEnumConst(wireName: r'odometer')
  static const AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum odometer = _$adminDutySessionsSessionIdBillingBasisPutRequestBasisEnum_odometer;

  static Serializer<AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum> get serializer => _$adminDutySessionsSessionIdBillingBasisPutRequestBasisEnumSerializer;

  const AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum._(String name): super(name);

  static BuiltSet<AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum> get values => _$adminDutySessionsSessionIdBillingBasisPutRequestBasisEnumValues;
  static AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum valueOf(String name) => _$adminDutySessionsSessionIdBillingBasisPutRequestBasisEnumValueOf(name);
}

