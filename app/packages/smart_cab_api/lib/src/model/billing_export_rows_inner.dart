//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/date.dart';
import 'package:smart_cab_api/src/model/billing_export_rows_inner_sessions_inner.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'billing_export_rows_inner.g.dart';

/// BillingExportRowsInner
///
/// Properties:
/// * [date] 
/// * [cab] - registration number
/// * [drivers] 
/// * [dutyIn] 
/// * [dutyOut] 
/// * [gpsKm] 
/// * [odometerKm] 
/// * [gapPercent] 
/// * [billedKm] 
/// * [ratePerKm] 
/// * [amount] 
/// * [flags] 
/// * [sessions] - The duty sessions behind the row, so an operator can mark one as billed on its odometer.
@BuiltValue()
abstract class BillingExportRowsInner implements Built<BillingExportRowsInner, BillingExportRowsInnerBuilder> {
  @BuiltValueField(wireName: r'date')
  Date? get date;

  /// registration number
  @BuiltValueField(wireName: r'cab')
  String? get cab;

  @BuiltValueField(wireName: r'drivers')
  BuiltList<String>? get drivers;

  @BuiltValueField(wireName: r'duty_in')
  DateTime? get dutyIn;

  @BuiltValueField(wireName: r'duty_out')
  DateTime? get dutyOut;

  @BuiltValueField(wireName: r'gps_km')
  num? get gpsKm;

  @BuiltValueField(wireName: r'odometer_km')
  num? get odometerKm;

  @BuiltValueField(wireName: r'gap_percent')
  num? get gapPercent;

  @BuiltValueField(wireName: r'billed_km')
  num? get billedKm;

  @BuiltValueField(wireName: r'rate_per_km')
  num? get ratePerKm;

  @BuiltValueField(wireName: r'amount')
  num? get amount;

  @BuiltValueField(wireName: r'flags')
  BuiltList<BillingExportRowsInnerFlagsEnum>? get flags;
  // enum flagsEnum {  odometer_gap,  multiple_clients,  no_client_trips,  default_client_unset,  still_on_duty,  no_gps,  odometer_billed,  };

  /// The duty sessions behind the row, so an operator can mark one as billed on its odometer.
  @BuiltValueField(wireName: r'sessions')
  BuiltList<BillingExportRowsInnerSessionsInner>? get sessions;

  BillingExportRowsInner._();

  factory BillingExportRowsInner([void updates(BillingExportRowsInnerBuilder b)]) = _$BillingExportRowsInner;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(BillingExportRowsInnerBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<BillingExportRowsInner> get serializer => _$BillingExportRowsInnerSerializer();
}

class _$BillingExportRowsInnerSerializer implements PrimitiveSerializer<BillingExportRowsInner> {
  @override
  final Iterable<Type> types = const [BillingExportRowsInner, _$BillingExportRowsInner];

  @override
  final String wireName = r'BillingExportRowsInner';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    BillingExportRowsInner object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.date != null) {
      yield r'date';
      yield serializers.serialize(
        object.date,
        specifiedType: const FullType(Date),
      );
    }
    if (object.cab != null) {
      yield r'cab';
      yield serializers.serialize(
        object.cab,
        specifiedType: const FullType(String),
      );
    }
    if (object.drivers != null) {
      yield r'drivers';
      yield serializers.serialize(
        object.drivers,
        specifiedType: const FullType(BuiltList, [FullType(String)]),
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
    if (object.odometerKm != null) {
      yield r'odometer_km';
      yield serializers.serialize(
        object.odometerKm,
        specifiedType: const FullType.nullable(num),
      );
    }
    if (object.gapPercent != null) {
      yield r'gap_percent';
      yield serializers.serialize(
        object.gapPercent,
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
    if (object.ratePerKm != null) {
      yield r'rate_per_km';
      yield serializers.serialize(
        object.ratePerKm,
        specifiedType: const FullType.nullable(num),
      );
    }
    if (object.amount != null) {
      yield r'amount';
      yield serializers.serialize(
        object.amount,
        specifiedType: const FullType.nullable(num),
      );
    }
    if (object.flags != null) {
      yield r'flags';
      yield serializers.serialize(
        object.flags,
        specifiedType: const FullType(BuiltList, [FullType(BillingExportRowsInnerFlagsEnum)]),
      );
    }
    if (object.sessions != null) {
      yield r'sessions';
      yield serializers.serialize(
        object.sessions,
        specifiedType: const FullType(BuiltList, [FullType(BillingExportRowsInnerSessionsInner)]),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    BillingExportRowsInner object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required BillingExportRowsInnerBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'date':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(Date),
          ) as Date;
          result.date = valueDes;
          break;
        case r'cab':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.cab = valueDes;
          break;
        case r'drivers':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(String)]),
          ) as BuiltList<String>;
          result.drivers.replace(valueDes);
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
        case r'odometer_km':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.odometerKm = valueDes;
          break;
        case r'gap_percent':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.gapPercent = valueDes;
          break;
        case r'billed_km':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(num),
          ) as num;
          result.billedKm = valueDes;
          break;
        case r'rate_per_km':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.ratePerKm = valueDes;
          break;
        case r'amount':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.amount = valueDes;
          break;
        case r'flags':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(BillingExportRowsInnerFlagsEnum)]),
          ) as BuiltList<BillingExportRowsInnerFlagsEnum>;
          result.flags.replace(valueDes);
          break;
        case r'sessions':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(BillingExportRowsInnerSessionsInner)]),
          ) as BuiltList<BillingExportRowsInnerSessionsInner>;
          result.sessions.replace(valueDes);
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  BillingExportRowsInner deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = BillingExportRowsInnerBuilder();
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

class BillingExportRowsInnerFlagsEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'odometer_gap')
  static const BillingExportRowsInnerFlagsEnum odometerGap = _$billingExportRowsInnerFlagsEnum_odometerGap;
  @BuiltValueEnumConst(wireName: r'multiple_clients')
  static const BillingExportRowsInnerFlagsEnum multipleClients = _$billingExportRowsInnerFlagsEnum_multipleClients;
  @BuiltValueEnumConst(wireName: r'no_client_trips')
  static const BillingExportRowsInnerFlagsEnum noClientTrips = _$billingExportRowsInnerFlagsEnum_noClientTrips;
  @BuiltValueEnumConst(wireName: r'default_client_unset')
  static const BillingExportRowsInnerFlagsEnum defaultClientUnset = _$billingExportRowsInnerFlagsEnum_defaultClientUnset;
  @BuiltValueEnumConst(wireName: r'still_on_duty')
  static const BillingExportRowsInnerFlagsEnum stillOnDuty = _$billingExportRowsInnerFlagsEnum_stillOnDuty;
  @BuiltValueEnumConst(wireName: r'no_gps')
  static const BillingExportRowsInnerFlagsEnum noGps = _$billingExportRowsInnerFlagsEnum_noGps;
  @BuiltValueEnumConst(wireName: r'odometer_billed')
  static const BillingExportRowsInnerFlagsEnum odometerBilled = _$billingExportRowsInnerFlagsEnum_odometerBilled;

  static Serializer<BillingExportRowsInnerFlagsEnum> get serializer => _$billingExportRowsInnerFlagsEnumSerializer;

  const BillingExportRowsInnerFlagsEnum._(String name): super(name);

  static BuiltSet<BillingExportRowsInnerFlagsEnum> get values => _$billingExportRowsInnerFlagsEnumValues;
  static BillingExportRowsInnerFlagsEnum valueOf(String name) => _$billingExportRowsInnerFlagsEnumValueOf(name);
}

