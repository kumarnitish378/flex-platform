//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'billing_export_summary.g.dart';

/// BillingExportSummary
///
/// Properties:
/// * [cabDays] 
/// * [cabs] 
/// * [gpsKm] 
/// * [odometerKm] 
/// * [billedKm] 
/// * [amount] - null when no rate is set. Never shown to riders.
/// * [flaggedDays] 
@BuiltValue()
abstract class BillingExportSummary implements Built<BillingExportSummary, BillingExportSummaryBuilder> {
  @BuiltValueField(wireName: r'cab_days')
  int? get cabDays;

  @BuiltValueField(wireName: r'cabs')
  int? get cabs;

  @BuiltValueField(wireName: r'gps_km')
  num? get gpsKm;

  @BuiltValueField(wireName: r'odometer_km')
  num? get odometerKm;

  @BuiltValueField(wireName: r'billed_km')
  num? get billedKm;

  /// null when no rate is set. Never shown to riders.
  @BuiltValueField(wireName: r'amount')
  num? get amount;

  @BuiltValueField(wireName: r'flagged_days')
  int? get flaggedDays;

  BillingExportSummary._();

  factory BillingExportSummary([void updates(BillingExportSummaryBuilder b)]) = _$BillingExportSummary;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(BillingExportSummaryBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<BillingExportSummary> get serializer => _$BillingExportSummarySerializer();
}

class _$BillingExportSummarySerializer implements PrimitiveSerializer<BillingExportSummary> {
  @override
  final Iterable<Type> types = const [BillingExportSummary, _$BillingExportSummary];

  @override
  final String wireName = r'BillingExportSummary';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    BillingExportSummary object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.cabDays != null) {
      yield r'cab_days';
      yield serializers.serialize(
        object.cabDays,
        specifiedType: const FullType(int),
      );
    }
    if (object.cabs != null) {
      yield r'cabs';
      yield serializers.serialize(
        object.cabs,
        specifiedType: const FullType(int),
      );
    }
    if (object.gpsKm != null) {
      yield r'gps_km';
      yield serializers.serialize(
        object.gpsKm,
        specifiedType: const FullType.nullable(num),
      );
    }
    if (object.odometerKm != null) {
      yield r'odometer_km';
      yield serializers.serialize(
        object.odometerKm,
        specifiedType: const FullType.nullable(num),
      );
    }
    if (object.billedKm != null) {
      yield r'billed_km';
      yield serializers.serialize(
        object.billedKm,
        specifiedType: const FullType(num),
      );
    }
    if (object.amount != null) {
      yield r'amount';
      yield serializers.serialize(
        object.amount,
        specifiedType: const FullType.nullable(num),
      );
    }
    if (object.flaggedDays != null) {
      yield r'flagged_days';
      yield serializers.serialize(
        object.flaggedDays,
        specifiedType: const FullType(int),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    BillingExportSummary object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required BillingExportSummaryBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'cab_days':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.cabDays = valueDes;
          break;
        case r'cabs':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.cabs = valueDes;
          break;
        case r'gps_km':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.gpsKm = valueDes;
          break;
        case r'odometer_km':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.odometerKm = valueDes;
          break;
        case r'billed_km':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(num),
          ) as num;
          result.billedKm = valueDes;
          break;
        case r'amount':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.amount = valueDes;
          break;
        case r'flagged_days':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.flaggedDays = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  BillingExportSummary deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = BillingExportSummaryBuilder();
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

