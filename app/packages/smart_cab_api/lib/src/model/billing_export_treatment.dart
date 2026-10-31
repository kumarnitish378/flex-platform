//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'billing_export_treatment.g.dart';

/// BillingExportTreatment
///
/// Properties:
/// * [noShowBillable] 
/// * [lateCancelBillable] 
/// * [distanceBasis] 
@BuiltValue()
abstract class BillingExportTreatment implements Built<BillingExportTreatment, BillingExportTreatmentBuilder> {
  @BuiltValueField(wireName: r'no_show_billable')
  bool? get noShowBillable;

  @BuiltValueField(wireName: r'late_cancel_billable')
  bool? get lateCancelBillable;

  @BuiltValueField(wireName: r'distance_basis')
  BillingExportTreatmentDistanceBasisEnum? get distanceBasis;
  // enum distanceBasisEnum {  trip_share,  direct,  };

  BillingExportTreatment._();

  factory BillingExportTreatment([void updates(BillingExportTreatmentBuilder b)]) = _$BillingExportTreatment;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(BillingExportTreatmentBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<BillingExportTreatment> get serializer => _$BillingExportTreatmentSerializer();
}

class _$BillingExportTreatmentSerializer implements PrimitiveSerializer<BillingExportTreatment> {
  @override
  final Iterable<Type> types = const [BillingExportTreatment, _$BillingExportTreatment];

  @override
  final String wireName = r'BillingExportTreatment';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    BillingExportTreatment object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.noShowBillable != null) {
      yield r'no_show_billable';
      yield serializers.serialize(
        object.noShowBillable,
        specifiedType: const FullType(bool),
      );
    }
    if (object.lateCancelBillable != null) {
      yield r'late_cancel_billable';
      yield serializers.serialize(
        object.lateCancelBillable,
        specifiedType: const FullType(bool),
      );
    }
    if (object.distanceBasis != null) {
      yield r'distance_basis';
      yield serializers.serialize(
        object.distanceBasis,
        specifiedType: const FullType(BillingExportTreatmentDistanceBasisEnum),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    BillingExportTreatment object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required BillingExportTreatmentBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'no_show_billable':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.noShowBillable = valueDes;
          break;
        case r'late_cancel_billable':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.lateCancelBillable = valueDes;
          break;
        case r'distance_basis':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BillingExportTreatmentDistanceBasisEnum),
          ) as BillingExportTreatmentDistanceBasisEnum;
          result.distanceBasis = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  BillingExportTreatment deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = BillingExportTreatmentBuilder();
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

class BillingExportTreatmentDistanceBasisEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'trip_share')
  static const BillingExportTreatmentDistanceBasisEnum tripShare = _$billingExportTreatmentDistanceBasisEnum_tripShare;
  @BuiltValueEnumConst(wireName: r'direct')
  static const BillingExportTreatmentDistanceBasisEnum direct = _$billingExportTreatmentDistanceBasisEnum_direct;

  static Serializer<BillingExportTreatmentDistanceBasisEnum> get serializer => _$billingExportTreatmentDistanceBasisEnumSerializer;

  const BillingExportTreatmentDistanceBasisEnum._(String name): super(name);

  static BuiltSet<BillingExportTreatmentDistanceBasisEnum> get values => _$billingExportTreatmentDistanceBasisEnumValues;
  static BillingExportTreatmentDistanceBasisEnum valueOf(String name) => _$billingExportTreatmentDistanceBasisEnumValueOf(name);
}

