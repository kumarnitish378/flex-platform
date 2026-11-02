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
/// * [basis] 
/// * [ratePerKm] - Operator config billing_rate_per_km; null when no rate is set.
/// * [odometerGapThresholdPercent] 
/// * [defaultClientId] - Where a shared or empty cab-day is billed.
@BuiltValue()
abstract class BillingExportTreatment implements Built<BillingExportTreatment, BillingExportTreatmentBuilder> {
  @BuiltValueField(wireName: r'basis')
  BillingExportTreatmentBasisEnum? get basis;
  // enum basisEnum {  per_cab_per_day_km,  };

  /// Operator config billing_rate_per_km; null when no rate is set.
  @BuiltValueField(wireName: r'rate_per_km')
  num? get ratePerKm;

  @BuiltValueField(wireName: r'odometer_gap_threshold_percent')
  num? get odometerGapThresholdPercent;

  /// Where a shared or empty cab-day is billed.
  @BuiltValueField(wireName: r'default_client_id')
  String? get defaultClientId;

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
    if (object.basis != null) {
      yield r'basis';
      yield serializers.serialize(
        object.basis,
        specifiedType: const FullType(BillingExportTreatmentBasisEnum),
      );
    }
    if (object.ratePerKm != null) {
      yield r'rate_per_km';
      yield serializers.serialize(
        object.ratePerKm,
        specifiedType: const FullType.nullable(num),
      );
    }
    if (object.odometerGapThresholdPercent != null) {
      yield r'odometer_gap_threshold_percent';
      yield serializers.serialize(
        object.odometerGapThresholdPercent,
        specifiedType: const FullType(num),
      );
    }
    if (object.defaultClientId != null) {
      yield r'default_client_id';
      yield serializers.serialize(
        object.defaultClientId,
        specifiedType: const FullType(String),
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
        case r'basis':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BillingExportTreatmentBasisEnum),
          ) as BillingExportTreatmentBasisEnum;
          result.basis = valueDes;
          break;
        case r'rate_per_km':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.ratePerKm = valueDes;
          break;
        case r'odometer_gap_threshold_percent':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(num),
          ) as num;
          result.odometerGapThresholdPercent = valueDes;
          break;
        case r'default_client_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.defaultClientId = valueDes;
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

class BillingExportTreatmentBasisEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'per_cab_per_day_km')
  static const BillingExportTreatmentBasisEnum perCabPerDayKm = _$billingExportTreatmentBasisEnum_perCabPerDayKm;

  static Serializer<BillingExportTreatmentBasisEnum> get serializer => _$billingExportTreatmentBasisEnumSerializer;

  const BillingExportTreatmentBasisEnum._(String name): super(name);

  static BuiltSet<BillingExportTreatmentBasisEnum> get values => _$billingExportTreatmentBasisEnumValues;
  static BillingExportTreatmentBasisEnum valueOf(String name) => _$billingExportTreatmentBasisEnumValueOf(name);
}

