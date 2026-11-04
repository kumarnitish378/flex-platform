//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/candidate_added_minutes_existing_inner.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'candidate.g.dart';

/// Candidate
///
/// Properties:
/// * [vehicleId] 
/// * [registrationNo] 
/// * [tripId] - existing trip if en-route reuse
/// * [etaToPickupSeconds] 
/// * [etaApproximate] - true when this ETA is a straight-line estimate, not road routing (ADR-0010)
/// * [seatsFreeAfter] 
/// * [gpsAgeSeconds] - How old this vehicle's position is, by the server's clock. `null` when it has never reported one. A supervisor choosing between cabs is choosing between claims about where they are, and a claim four minutes old is a different thing from one four seconds old - `gps_stale` in `violations` only says it crossed `stale_gps_seconds`, not by how much. 
/// * [addedMinutesExisting] 
/// * [emptyKmAdded] 
/// * [newTrip] 
/// * [cost] - Phase 2+
/// * [reasons] - Phase 2+ human-readable
/// * [violations] - hard rules violated (shown for manual only
@BuiltValue()
abstract class Candidate implements Built<Candidate, CandidateBuilder> {
  @BuiltValueField(wireName: r'vehicle_id')
  String? get vehicleId;

  @BuiltValueField(wireName: r'registration_no')
  String? get registrationNo;

  /// existing trip if en-route reuse
  @BuiltValueField(wireName: r'trip_id')
  String? get tripId;

  @BuiltValueField(wireName: r'eta_to_pickup_seconds')
  int? get etaToPickupSeconds;

  /// true when this ETA is a straight-line estimate, not road routing (ADR-0010)
  @BuiltValueField(wireName: r'eta_approximate')
  bool? get etaApproximate;

  @BuiltValueField(wireName: r'seats_free_after')
  int? get seatsFreeAfter;

  /// How old this vehicle's position is, by the server's clock. `null` when it has never reported one. A supervisor choosing between cabs is choosing between claims about where they are, and a claim four minutes old is a different thing from one four seconds old - `gps_stale` in `violations` only says it crossed `stale_gps_seconds`, not by how much. 
  @BuiltValueField(wireName: r'gps_age_seconds')
  num? get gpsAgeSeconds;

  @BuiltValueField(wireName: r'added_minutes_existing')
  BuiltList<CandidateAddedMinutesExistingInner>? get addedMinutesExisting;

  @BuiltValueField(wireName: r'empty_km_added')
  num? get emptyKmAdded;

  @BuiltValueField(wireName: r'new_trip')
  bool? get newTrip;

  /// Phase 2+
  @BuiltValueField(wireName: r'cost')
  num? get cost;

  /// Phase 2+ human-readable
  @BuiltValueField(wireName: r'reasons')
  BuiltList<String>? get reasons;

  /// hard rules violated (shown for manual only
  @BuiltValueField(wireName: r'violations')
  BuiltList<String>? get violations;

  Candidate._();

  factory Candidate([void updates(CandidateBuilder b)]) = _$Candidate;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(CandidateBuilder b) => b
      ..etaApproximate = false;

  @BuiltValueSerializer(custom: true)
  static Serializer<Candidate> get serializer => _$CandidateSerializer();
}

class _$CandidateSerializer implements PrimitiveSerializer<Candidate> {
  @override
  final Iterable<Type> types = const [Candidate, _$Candidate];

  @override
  final String wireName = r'Candidate';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    Candidate object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.vehicleId != null) {
      yield r'vehicle_id';
      yield serializers.serialize(
        object.vehicleId,
        specifiedType: const FullType(String),
      );
    }
    if (object.registrationNo != null) {
      yield r'registration_no';
      yield serializers.serialize(
        object.registrationNo,
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
    if (object.etaToPickupSeconds != null) {
      yield r'eta_to_pickup_seconds';
      yield serializers.serialize(
        object.etaToPickupSeconds,
        specifiedType: const FullType(int),
      );
    }
    if (object.etaApproximate != null) {
      yield r'eta_approximate';
      yield serializers.serialize(
        object.etaApproximate,
        specifiedType: const FullType(bool),
      );
    }
    if (object.seatsFreeAfter != null) {
      yield r'seats_free_after';
      yield serializers.serialize(
        object.seatsFreeAfter,
        specifiedType: const FullType(int),
      );
    }
    if (object.gpsAgeSeconds != null) {
      yield r'gps_age_seconds';
      yield serializers.serialize(
        object.gpsAgeSeconds,
        specifiedType: const FullType.nullable(num),
      );
    }
    if (object.addedMinutesExisting != null) {
      yield r'added_minutes_existing';
      yield serializers.serialize(
        object.addedMinutesExisting,
        specifiedType: const FullType(BuiltList, [FullType(CandidateAddedMinutesExistingInner)]),
      );
    }
    if (object.emptyKmAdded != null) {
      yield r'empty_km_added';
      yield serializers.serialize(
        object.emptyKmAdded,
        specifiedType: const FullType(num),
      );
    }
    if (object.newTrip != null) {
      yield r'new_trip';
      yield serializers.serialize(
        object.newTrip,
        specifiedType: const FullType(bool),
      );
    }
    if (object.cost != null) {
      yield r'cost';
      yield serializers.serialize(
        object.cost,
        specifiedType: const FullType.nullable(num),
      );
    }
    if (object.reasons != null) {
      yield r'reasons';
      yield serializers.serialize(
        object.reasons,
        specifiedType: const FullType(BuiltList, [FullType(String)]),
      );
    }
    if (object.violations != null) {
      yield r'violations';
      yield serializers.serialize(
        object.violations,
        specifiedType: const FullType(BuiltList, [FullType(String)]),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    Candidate object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required CandidateBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'vehicle_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.vehicleId = valueDes;
          break;
        case r'registration_no':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.registrationNo = valueDes;
          break;
        case r'trip_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.tripId = valueDes;
          break;
        case r'eta_to_pickup_seconds':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.etaToPickupSeconds = valueDes;
          break;
        case r'eta_approximate':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.etaApproximate = valueDes;
          break;
        case r'seats_free_after':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.seatsFreeAfter = valueDes;
          break;
        case r'gps_age_seconds':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.gpsAgeSeconds = valueDes;
          break;
        case r'added_minutes_existing':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(CandidateAddedMinutesExistingInner)]),
          ) as BuiltList<CandidateAddedMinutesExistingInner>;
          result.addedMinutesExisting.replace(valueDes);
          break;
        case r'empty_km_added':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(num),
          ) as num;
          result.emptyKmAdded = valueDes;
          break;
        case r'new_trip':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.newTrip = valueDes;
          break;
        case r'cost':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.cost = valueDes;
          break;
        case r'reasons':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(String)]),
          ) as BuiltList<String>;
          result.reasons.replace(valueDes);
          break;
        case r'violations':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(String)]),
          ) as BuiltList<String>;
          result.violations.replace(valueDes);
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  Candidate deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = CandidateBuilder();
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

