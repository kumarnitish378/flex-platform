//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'billing_export_rows_inner_sessions_inner.g.dart';

/// BillingExportRowsInnerSessionsInner
///
/// Properties:
/// * [id] 
/// * [driver] 
/// * [dutyIn] 
/// * [dutyOut] 
/// * [gpsKm] 
/// * [odometerStartKm] 
/// * [odometerEndKm] 
/// * [odometerKm] 
/// * [basis] 
@BuiltValue()
abstract class BillingExportRowsInnerSessionsInner implements Built<BillingExportRowsInnerSessionsInner, BillingExportRowsInnerSessionsInnerBuilder> {
  @BuiltValueField(wireName: r'id')
  String? get id;

  @BuiltValueField(wireName: r'driver')
  String? get driver;

  @BuiltValueField(wireName: r'duty_in')
  DateTime? get dutyIn;

  @BuiltValueField(wireName: r'duty_out')
  DateTime? get dutyOut;

  @BuiltValueField(wireName: r'gps_km')
  num? get gpsKm;

  @BuiltValueField(wireName: r'odometer_start_km')
  num? get odometerStartKm;

  @BuiltValueField(wireName: r'odometer_end_km')
  num? get odometerEndKm;

  @BuiltValueField(wireName: r'odometer_km')
  num? get odometerKm;

  @BuiltValueField(wireName: r'basis')
  BillingExportRowsInnerSessionsInnerBasisEnum? get basis;
  // enum basisEnum {  gps,  odometer,  };

  BillingExportRowsInnerSessionsInner._();

  factory BillingExportRowsInnerSessionsInner([void updates(BillingExportRowsInnerSessionsInnerBuilder b)]) = _$BillingExportRowsInnerSessionsInner;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(BillingExportRowsInnerSessionsInnerBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<BillingExportRowsInnerSessionsInner> get serializer => _$BillingExportRowsInnerSessionsInnerSerializer();
}

class _$BillingExportRowsInnerSessionsInnerSerializer implements PrimitiveSerializer<BillingExportRowsInnerSessionsInner> {
  @override
  final Iterable<Type> types = const [BillingExportRowsInnerSessionsInner, _$BillingExportRowsInnerSessionsInner];

  @override
  final String wireName = r'BillingExportRowsInnerSessionsInner';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    BillingExportRowsInnerSessionsInner object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.id != null) {
      yield r'id';
      yield serializers.serialize(
        object.id,
        specifiedType: const FullType(String),
      );
    }
    if (object.driver != null) {
      yield r'driver';
      yield serializers.serialize(
        object.driver,
        specifiedType: const FullType(String),
      );
    }
    if (object.dutyIn != null) {
      yield r'duty_in';
      yield serializers.serialize(
        object.dutyIn,
        specifiedType: const FullType(DateTime),
      );
    }
    if (object.dutyOut != null) {
      yield r'duty_out';
      yield serializers.serialize(
        object.dutyOut,
        specifiedType: const FullType.nullable(DateTime),
      );
    }
    if (object.gpsKm != null) {
      yield r'gps_km';
      yield serializers.serialize(
        object.gpsKm,
        specifiedType: const FullType.nullable(num),
      );
    }
    if (object.odometerStartKm != null) {
      yield r'odometer_start_km';
      yield serializers.serialize(
        object.odometerStartKm,
        specifiedType: const FullType.nullable(num),
      );
    }
    if (object.odometerEndKm != null) {
      yield r'odometer_end_km';
      yield serializers.serialize(
        object.odometerEndKm,
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
    if (object.basis != null) {
      yield r'basis';
      yield serializers.serialize(
        object.basis,
        specifiedType: const FullType(BillingExportRowsInnerSessionsInnerBasisEnum),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    BillingExportRowsInnerSessionsInner object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required BillingExportRowsInnerSessionsInnerBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.id = valueDes;
          break;
        case r'driver':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.driver = valueDes;
          break;
        case r'duty_in':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(DateTime),
          ) as DateTime;
          result.dutyIn = valueDes;
          break;
        case r'duty_out':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(DateTime),
          ) as DateTime?;
          if (valueDes == null) continue;
          result.dutyOut = valueDes;
          break;
        case r'gps_km':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.gpsKm = valueDes;
          break;
        case r'odometer_start_km':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.odometerStartKm = valueDes;
          break;
        case r'odometer_end_km':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.odometerEndKm = valueDes;
          break;
        case r'odometer_km':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.odometerKm = valueDes;
          break;
        case r'basis':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BillingExportRowsInnerSessionsInnerBasisEnum),
          ) as BillingExportRowsInnerSessionsInnerBasisEnum;
          result.basis = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  BillingExportRowsInnerSessionsInner deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = BillingExportRowsInnerSessionsInnerBuilder();
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

class BillingExportRowsInnerSessionsInnerBasisEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'gps')
  static const BillingExportRowsInnerSessionsInnerBasisEnum gps = _$billingExportRowsInnerSessionsInnerBasisEnum_gps;
  @BuiltValueEnumConst(wireName: r'odometer')
  static const BillingExportRowsInnerSessionsInnerBasisEnum odometer = _$billingExportRowsInnerSessionsInnerBasisEnum_odometer;

  static Serializer<BillingExportRowsInnerSessionsInnerBasisEnum> get serializer => _$billingExportRowsInnerSessionsInnerBasisEnumSerializer;

  const BillingExportRowsInnerSessionsInnerBasisEnum._(String name): super(name);

  static BuiltSet<BillingExportRowsInnerSessionsInnerBasisEnum> get values => _$billingExportRowsInnerSessionsInnerBasisEnumValues;
  static BillingExportRowsInnerSessionsInnerBasisEnum valueOf(String name) => _$billingExportRowsInnerSessionsInnerBasisEnumValueOf(name);
}

