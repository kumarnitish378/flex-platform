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
/// * [rides] 
/// * [billableRides] 
/// * [completed] 
/// * [noShows] 
/// * [cancellations] 
/// * [billableTrips] 
/// * [riders] 
/// * [billableKm] 
/// * [amount] - billable_km x rate_per_km; null when no rate is set. Never shown to riders.
@BuiltValue()
abstract class BillingExportSummary implements Built<BillingExportSummary, BillingExportSummaryBuilder> {
  @BuiltValueField(wireName: r'rides')
  int? get rides;

  @BuiltValueField(wireName: r'billable_rides')
  int? get billableRides;

  @BuiltValueField(wireName: r'completed')
  int? get completed;

  @BuiltValueField(wireName: r'no_shows')
  int? get noShows;

  @BuiltValueField(wireName: r'cancellations')
  int? get cancellations;

  @BuiltValueField(wireName: r'billable_trips')
  int? get billableTrips;

  @BuiltValueField(wireName: r'riders')
  int? get riders;

  @BuiltValueField(wireName: r'billable_km')
  num? get billableKm;

  /// billable_km x rate_per_km; null when no rate is set. Never shown to riders.
  @BuiltValueField(wireName: r'amount')
  num? get amount;

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
    if (object.rides != null) {
      yield r'rides';
      yield serializers.serialize(
        object.rides,
        specifiedType: const FullType(int),
      );
    }
    if (object.billableRides != null) {
      yield r'billable_rides';
      yield serializers.serialize(
        object.billableRides,
        specifiedType: const FullType(int),
      );
    }
    if (object.completed != null) {
      yield r'completed';
      yield serializers.serialize(
        object.completed,
        specifiedType: const FullType(int),
      );
    }
    if (object.noShows != null) {
      yield r'no_shows';
      yield serializers.serialize(
        object.noShows,
        specifiedType: const FullType(int),
      );
    }
    if (object.cancellations != null) {
      yield r'cancellations';
      yield serializers.serialize(
        object.cancellations,
        specifiedType: const FullType(int),
      );
    }
    if (object.billableTrips != null) {
      yield r'billable_trips';
      yield serializers.serialize(
        object.billableTrips,
        specifiedType: const FullType(int),
      );
    }
    if (object.riders != null) {
      yield r'riders';
      yield serializers.serialize(
        object.riders,
        specifiedType: const FullType(int),
      );
    }
    if (object.billableKm != null) {
      yield r'billable_km';
      yield serializers.serialize(
        object.billableKm,
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
        case r'rides':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.rides = valueDes;
          break;
        case r'billable_rides':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.billableRides = valueDes;
          break;
        case r'completed':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.completed = valueDes;
          break;
        case r'no_shows':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.noShows = valueDes;
          break;
        case r'cancellations':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.cancellations = valueDes;
          break;
        case r'billable_trips':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.billableTrips = valueDes;
          break;
        case r'riders':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.riders = valueDes;
          break;
        case r'billable_km':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.billableKm = valueDes;
          break;
        case r'amount':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.amount = valueDes;
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

