//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/date.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'billing_export_rows_inner.g.dart';

/// BillingExportRowsInner
///
/// Properties:
/// * [date] 
/// * [requestId] 
/// * [employee] 
/// * [direction] 
/// * [status] 
/// * [billable] 
/// * [billableReason] 
/// * [tripId] 
/// * [vehicle] 
/// * [ridersOnTrip] 
/// * [directKm] 
/// * [tripShareKm] 
/// * [billableKm] 
@BuiltValue()
abstract class BillingExportRowsInner implements Built<BillingExportRowsInner, BillingExportRowsInnerBuilder> {
  @BuiltValueField(wireName: r'date')
  Date? get date;

  @BuiltValueField(wireName: r'request_id')
  String? get requestId;

  @BuiltValueField(wireName: r'employee')
  String? get employee;

  @BuiltValueField(wireName: r'direction')
  String? get direction;

  @BuiltValueField(wireName: r'status')
  String? get status;

  @BuiltValueField(wireName: r'billable')
  bool? get billable;

  @BuiltValueField(wireName: r'billable_reason')
  String? get billableReason;

  @BuiltValueField(wireName: r'trip_id')
  String? get tripId;

  @BuiltValueField(wireName: r'vehicle')
  String? get vehicle;

  @BuiltValueField(wireName: r'riders_on_trip')
  int? get ridersOnTrip;

  @BuiltValueField(wireName: r'direct_km')
  num? get directKm;

  @BuiltValueField(wireName: r'trip_share_km')
  num? get tripShareKm;

  @BuiltValueField(wireName: r'billable_km')
  num? get billableKm;

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
    if (object.requestId != null) {
      yield r'request_id';
      yield serializers.serialize(
        object.requestId,
        specifiedType: const FullType(String),
      );
    }
    if (object.employee != null) {
      yield r'employee';
      yield serializers.serialize(
        object.employee,
        specifiedType: const FullType(String),
      );
    }
    if (object.direction != null) {
      yield r'direction';
      yield serializers.serialize(
        object.direction,
        specifiedType: const FullType(String),
      );
    }
    if (object.status != null) {
      yield r'status';
      yield serializers.serialize(
        object.status,
        specifiedType: const FullType(String),
      );
    }
    if (object.billable != null) {
      yield r'billable';
      yield serializers.serialize(
        object.billable,
        specifiedType: const FullType(bool),
      );
    }
    if (object.billableReason != null) {
      yield r'billable_reason';
      yield serializers.serialize(
        object.billableReason,
        specifiedType: const FullType(String),
      );
    }
    if (object.tripId != null) {
      yield r'trip_id';
      yield serializers.serialize(
        object.tripId,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.vehicle != null) {
      yield r'vehicle';
      yield serializers.serialize(
        object.vehicle,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.ridersOnTrip != null) {
      yield r'riders_on_trip';
      yield serializers.serialize(
        object.ridersOnTrip,
        specifiedType: const FullType(int),
      );
    }
    if (object.directKm != null) {
      yield r'direct_km';
      yield serializers.serialize(
        object.directKm,
        specifiedType: const FullType.nullable(num),
      );
    }
    if (object.tripShareKm != null) {
      yield r'trip_share_km';
      yield serializers.serialize(
        object.tripShareKm,
        specifiedType: const FullType.nullable(num),
      );
    }
    if (object.billableKm != null) {
      yield r'billable_km';
      yield serializers.serialize(
        object.billableKm,
        specifiedType: const FullType(num),
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
        case r'request_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.requestId = valueDes;
          break;
        case r'employee':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.employee = valueDes;
          break;
        case r'direction':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.direction = valueDes;
          break;
        case r'status':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.status = valueDes;
          break;
        case r'billable':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.billable = valueDes;
          break;
        case r'billable_reason':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.billableReason = valueDes;
          break;
        case r'trip_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.tripId = valueDes;
          break;
        case r'vehicle':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.vehicle = valueDes;
          break;
        case r'riders_on_trip':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.ridersOnTrip = valueDes;
          break;
        case r'direct_km':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.directKm = valueDes;
          break;
        case r'trip_share_km':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.tripShareKm = valueDes;
          break;
        case r'billable_km':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(num),
          ) as num;
          result.billableKm = valueDes;
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

