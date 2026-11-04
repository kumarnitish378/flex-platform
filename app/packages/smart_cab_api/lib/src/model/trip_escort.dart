//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'trip_escort.g.dart';

/// TripEscort
///
/// Properties:
/// * [required_] 
/// * [confirmed] 
/// * [basis] 
/// * [confirmedBy] 
/// * [confirmedAt] 
/// * [note] 
@BuiltValue()
abstract class TripEscort implements Built<TripEscort, TripEscortBuilder> {
  @BuiltValueField(wireName: r'required')
  bool get required_;

  @BuiltValueField(wireName: r'confirmed')
  bool get confirmed;

  @BuiltValueField(wireName: r'basis')
  TripEscortBasisEnum? get basis;
  // enum basisEnum {  escort_arranged,  male_co_rider_present,  ,  };

  @BuiltValueField(wireName: r'confirmed_by')
  String? get confirmedBy;

  @BuiltValueField(wireName: r'confirmed_at')
  DateTime? get confirmedAt;

  @BuiltValueField(wireName: r'note')
  String? get note;

  TripEscort._();

  factory TripEscort([void updates(TripEscortBuilder b)]) = _$TripEscort;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(TripEscortBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<TripEscort> get serializer => _$TripEscortSerializer();
}

class _$TripEscortSerializer implements PrimitiveSerializer<TripEscort> {
  @override
  final Iterable<Type> types = const [TripEscort, _$TripEscort];

  @override
  final String wireName = r'TripEscort';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    TripEscort object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'required';
    yield serializers.serialize(
      object.required_,
      specifiedType: const FullType(bool),
    );
    yield r'confirmed';
    yield serializers.serialize(
      object.confirmed,
      specifiedType: const FullType(bool),
    );
    if (object.basis != null) {
      yield r'basis';
      yield serializers.serialize(
        object.basis,
        specifiedType: const FullType.nullable(TripEscortBasisEnum),
      );
    }
    if (object.confirmedBy != null) {
      yield r'confirmed_by';
      yield serializers.serialize(
        object.confirmedBy,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.confirmedAt != null) {
      yield r'confirmed_at';
      yield serializers.serialize(
        object.confirmedAt,
        specifiedType: const FullType.nullable(DateTime),
      );
    }
    if (object.note != null) {
      yield r'note';
      yield serializers.serialize(
        object.note,
        specifiedType: const FullType.nullable(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    TripEscort object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required TripEscortBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'required':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.required_ = valueDes;
          break;
        case r'confirmed':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.confirmed = valueDes;
          break;
        case r'basis':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(TripEscortBasisEnum),
          ) as TripEscortBasisEnum?;
          if (valueDes == null) continue;
          result.basis = valueDes;
          break;
        case r'confirmed_by':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.confirmedBy = valueDes;
          break;
        case r'confirmed_at':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(DateTime),
          ) as DateTime?;
          if (valueDes == null) continue;
          result.confirmedAt = valueDes;
          break;
        case r'note':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.note = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  TripEscort deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = TripEscortBuilder();
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

class TripEscortBasisEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'escort_arranged')
  static const TripEscortBasisEnum escortArranged = _$tripEscortBasisEnum_escortArranged;
  @BuiltValueEnumConst(wireName: r'male_co_rider_present')
  static const TripEscortBasisEnum maleCoRiderPresent = _$tripEscortBasisEnum_maleCoRiderPresent;

  static Serializer<TripEscortBasisEnum> get serializer => _$tripEscortBasisEnumSerializer;

  const TripEscortBasisEnum._(String name): super(name);

  static BuiltSet<TripEscortBasisEnum> get values => _$tripEscortBasisEnumValues;
  static TripEscortBasisEnum valueOf(String name) => _$tripEscortBasisEnumValueOf(name);
}

