//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'candidate_added_minutes_existing_inner.g.dart';

/// CandidateAddedMinutesExistingInner
///
/// Properties:
/// * [requestId] 
/// * [minutes] 
@BuiltValue()
abstract class CandidateAddedMinutesExistingInner implements Built<CandidateAddedMinutesExistingInner, CandidateAddedMinutesExistingInnerBuilder> {
  @BuiltValueField(wireName: r'request_id')
  String? get requestId;

  @BuiltValueField(wireName: r'minutes')
  num? get minutes;

  CandidateAddedMinutesExistingInner._();

  factory CandidateAddedMinutesExistingInner([void updates(CandidateAddedMinutesExistingInnerBuilder b)]) = _$CandidateAddedMinutesExistingInner;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(CandidateAddedMinutesExistingInnerBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<CandidateAddedMinutesExistingInner> get serializer => _$CandidateAddedMinutesExistingInnerSerializer();
}

class _$CandidateAddedMinutesExistingInnerSerializer implements PrimitiveSerializer<CandidateAddedMinutesExistingInner> {
  @override
  final Iterable<Type> types = const [CandidateAddedMinutesExistingInner, _$CandidateAddedMinutesExistingInner];

  @override
  final String wireName = r'CandidateAddedMinutesExistingInner';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    CandidateAddedMinutesExistingInner object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.requestId != null) {
      yield r'request_id';
      yield serializers.serialize(
        object.requestId,
        specifiedType: const FullType(String),
      );
    }
    if (object.minutes != null) {
      yield r'minutes';
      yield serializers.serialize(
        object.minutes,
        specifiedType: const FullType(num),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    CandidateAddedMinutesExistingInner object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required CandidateAddedMinutesExistingInnerBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'request_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.requestId = valueDes;
          break;
        case r'minutes':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(num),
          ) as num;
          result.minutes = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  CandidateAddedMinutesExistingInner deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = CandidateAddedMinutesExistingInnerBuilder();
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

