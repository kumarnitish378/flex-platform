//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'request_status.g.dart';

class RequestStatus extends EnumClass {

  @BuiltValueEnumConst(wireName: r'requested')
  static const RequestStatus requested = _$requested;
  @BuiltValueEnumConst(wireName: r'queued')
  static const RequestStatus queued = _$queued;
  @BuiltValueEnumConst(wireName: r'suggested')
  static const RequestStatus suggested = _$suggested;
  @BuiltValueEnumConst(wireName: r'assigned')
  static const RequestStatus assigned = _$assigned;
  @BuiltValueEnumConst(wireName: r'picked_up')
  static const RequestStatus pickedUp = _$pickedUp;
  @BuiltValueEnumConst(wireName: r'dropped')
  static const RequestStatus dropped = _$dropped;
  @BuiltValueEnumConst(wireName: r'no_show')
  static const RequestStatus noShow = _$noShow;
  @BuiltValueEnumConst(wireName: r'cancelled')
  static const RequestStatus cancelled = _$cancelled;
  @BuiltValueEnumConst(wireName: r'expired')
  static const RequestStatus expired = _$expired;

  static Serializer<RequestStatus> get serializer => _$requestStatusSerializer;

  const RequestStatus._(String name): super(name);

  static BuiltSet<RequestStatus> get values => _$values;
  static RequestStatus valueOf(String name) => _$valueOf(name);
}

/// Optionally, enum_class can generate a mixin to go with your enum for use
/// with Angular. It exposes your enum constants as getters. So, if you mix it
/// in to your Dart component class, the values become available to the
/// corresponding Angular template.
///
/// Trigger mixin generation by writing a line like this one next to your enum.
abstract class RequestStatusMixin = Object with _$RequestStatusMixin;

