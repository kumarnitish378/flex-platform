//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'operations_report_requests.g.dart';

/// counts of the requests asked for in the period, by where they ended up
///
/// Properties:
/// * [total] 
/// * [completed] 
/// * [noShows] 
/// * [cancelled] 
/// * [expired] 
/// * [stillOpen] 
@BuiltValue()
abstract class OperationsReportRequests implements Built<OperationsReportRequests, OperationsReportRequestsBuilder> {
  @BuiltValueField(wireName: r'total')
  int? get total;

  @BuiltValueField(wireName: r'completed')
  int? get completed;

  @BuiltValueField(wireName: r'no_shows')
  int? get noShows;

  @BuiltValueField(wireName: r'cancelled')
  int? get cancelled;

  @BuiltValueField(wireName: r'expired')
  int? get expired;

  @BuiltValueField(wireName: r'still_open')
  int? get stillOpen;

  OperationsReportRequests._();

  factory OperationsReportRequests([void updates(OperationsReportRequestsBuilder b)]) = _$OperationsReportRequests;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(OperationsReportRequestsBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<OperationsReportRequests> get serializer => _$OperationsReportRequestsSerializer();
}

class _$OperationsReportRequestsSerializer implements PrimitiveSerializer<OperationsReportRequests> {
  @override
  final Iterable<Type> types = const [OperationsReportRequests, _$OperationsReportRequests];

  @override
  final String wireName = r'OperationsReportRequests';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    OperationsReportRequests object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.total != null) {
      yield r'total';
      yield serializers.serialize(
        object.total,
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
    if (object.cancelled != null) {
      yield r'cancelled';
      yield serializers.serialize(
        object.cancelled,
        specifiedType: const FullType(int),
      );
    }
    if (object.expired != null) {
      yield r'expired';
      yield serializers.serialize(
        object.expired,
        specifiedType: const FullType(int),
      );
    }
    if (object.stillOpen != null) {
      yield r'still_open';
      yield serializers.serialize(
        object.stillOpen,
        specifiedType: const FullType(int),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    OperationsReportRequests object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required OperationsReportRequestsBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'total':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.total = valueDes;
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
        case r'cancelled':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.cancelled = valueDes;
          break;
        case r'expired':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.expired = valueDes;
          break;
        case r'still_open':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.stillOpen = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  OperationsReportRequests deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = OperationsReportRequestsBuilder();
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

