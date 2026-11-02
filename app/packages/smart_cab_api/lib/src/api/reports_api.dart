//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

import 'dart:async';

import 'package:built_value/json_object.dart';
import 'package:built_value/serializer.dart';
import 'package:dio/dio.dart';

import 'package:smart_cab_api/src/api_util.dart';
import 'package:smart_cab_api/src/model/admin_duty_sessions_session_id_billing_basis_put200_response.dart';
import 'package:smart_cab_api/src/model/admin_duty_sessions_session_id_billing_basis_put_request.dart';
import 'package:smart_cab_api/src/model/billing_export.dart';
import 'package:smart_cab_api/src/model/date.dart';
import 'package:smart_cab_api/src/model/error.dart';
import 'package:smart_cab_api/src/model/operations_report.dart';
import 'package:smart_cab_api/src/model/trip_report.dart';

class ReportsApi {

  final Dio _dio;

  final Serializers _serializers;

  const ReportsApi(this._dio, this._serializers);

  /// Choose whether a duty session is billed on GPS or on the odometer figure
  /// Requires &#x60;config.manage&#x60; (operator admin). The default is GPS. &#x60;odometer&#x60; needs both readings on the session (409 otherwise). Who chose and when is kept. The platform never decides which figure is right; this is the operator&#39;s call, usually after the report flagged &#x60;odometer_gap&#x60;. 
  ///
  /// Parameters:
  /// * [sessionId] 
  /// * [adminDutySessionsSessionIdBillingBasisPutRequest] 
  /// * [cancelToken] - A [CancelToken] that can be used to cancel the operation
  /// * [headers] - Can be used to add additional headers to the request
  /// * [extras] - Can be used to add flags to the request
  /// * [validateStatus] - A [ValidateStatus] callback that can be used to determine request success based on the HTTP status of the response
  /// * [onSendProgress] - A [ProgressCallback] that can be used to get the send progress
  /// * [onReceiveProgress] - A [ProgressCallback] that can be used to get the receive progress
  ///
  /// Returns a [Future] containing a [Response] with a [AdminDutySessionsSessionIdBillingBasisPut200Response] as data
  /// Throws [DioException] if API call or serialization fails
  Future<Response<AdminDutySessionsSessionIdBillingBasisPut200Response>> adminDutySessionsSessionIdBillingBasisPut({ 
    required String sessionId,
    required AdminDutySessionsSessionIdBillingBasisPutRequest adminDutySessionsSessionIdBillingBasisPutRequest,
    CancelToken? cancelToken,
    Map<String, dynamic>? headers,
    Map<String, dynamic>? extra,
    ValidateStatus? validateStatus,
    ProgressCallback? onSendProgress,
    ProgressCallback? onReceiveProgress,
  }) async {
    final _path = r'/admin/duty-sessions/{session_id}/billing-basis'.replaceAll('{' r'session_id' '}', encodeQueryParameter(_serializers, sessionId, const FullType(String)).toString());
    final _options = Options(
      method: r'PUT',
      headers: <String, dynamic>{
        ...?headers,
      },
      extra: <String, dynamic>{
        'secure': <Map<String, String>>[
          {
            'type': 'http',
            'scheme': 'bearer',
            'name': 'bearerAuth',
          },
        ],
        ...?extra,
      },
      contentType: 'application/json',
      validateStatus: validateStatus,
    );

    dynamic _bodyData;

    try {
      const _type = FullType(AdminDutySessionsSessionIdBillingBasisPutRequest);
      _bodyData = _serializers.serialize(adminDutySessionsSessionIdBillingBasisPutRequest, specifiedType: _type);

    } catch(error, stackTrace) {
      throw DioException(
         requestOptions: _options.compose(
          _dio.options,
          _path,
        ),
        type: DioExceptionType.unknown,
        error: error,
        stackTrace: stackTrace,
      );
    }

    final _response = await _dio.request<Object>(
      _path,
      data: _bodyData,
      options: _options,
      cancelToken: cancelToken,
      onSendProgress: onSendProgress,
      onReceiveProgress: onReceiveProgress,
    );

    AdminDutySessionsSessionIdBillingBasisPut200Response? _responseData;

    try {
      final rawResponse = _response.data;
      _responseData = rawResponse == null ? null : _serializers.deserialize(
        rawResponse,
        specifiedType: const FullType(AdminDutySessionsSessionIdBillingBasisPut200Response),
      ) as AdminDutySessionsSessionIdBillingBasisPut200Response;

    } catch (error, stackTrace) {
      throw DioException(
        requestOptions: _response.requestOptions,
        response: _response,
        type: DioExceptionType.unknown,
        error: error,
        stackTrace: stackTrace,
      );
    }

    return Response<AdminDutySessionsSessionIdBillingBasisPut200Response>(
      data: _responseData,
      headers: _response.headers,
      isRedirect: _response.isRedirect,
      requestOptions: _response.requestOptions,
      redirects: _response.redirects,
      statusCode: _response.statusCode,
      statusMessage: _response.statusMessage,
      extra: _response.extra,
    );
  }

  /// One client&#39;s month, one row per cab per day - running km, odometer check, amount (B38, OPA-06)
  /// Requires &#x60;billing.view&#x60; (operator admin, client admin). A client admin is invoiced for their own company whatever &#x60;client_id&#x60; they send; an operator admin must name one.  **Basis (owner decision, OQ-03): the employer company pays the operator per cab per day on the total running km between duty start (cab in) and duty end (cab out), dead km between trips included, at &#x60;billing_rate_per_km&#x60;** (Rs 8 to begin with). Riders never pay and see no charge anywhere. A row is one cab on one local day (operator timezone, by the day its duty began). &#x60;gps_km&#x60; is measured from the cab&#39;s pings between going on and off duty, ignoring jitter and GPS jumps; &#x60;odometer_km&#x60; is the closing minus the opening reading the driver entered, when both exist. &#x60;billed_km&#x60; is the GPS figure unless an operator admin marked the odometer figure for that duty session (&#x60;PUT /admin/duty-sessions/{id}/billing-basis&#x60;). &#x60;gap_percent&#x60; is the difference as a share of the odometer figure, and &#x60;odometer_gap&#x60; is in &#x60;flags&#x60; when it exceeds &#x60;billing_odometer_gap_percent&#x60; (default 10). &#x60;amount&#x60; is &#x60;null&#x60; until a rate is set. Flags: &#x60;odometer_gap&#x60;, &#x60;multiple_clients&#x60; / &#x60;no_client_trips&#x60; (the cab carried several clients&#39; riders that day, or none, so it was billed to the operator&#39;s default client - OQ-41), &#x60;default_client_unset&#x60;, &#x60;still_on_duty&#x60;, &#x60;no_gps&#x60;, &#x60;odometer_billed&#x60;. The CSV is the invoice: one line per cab-day and a TOTAL line. 
  ///
  /// Parameters:
  /// * [month] - YYYY-MM
  /// * [clientId] 
  /// * [format] 
  /// * [cancelToken] - A [CancelToken] that can be used to cancel the operation
  /// * [headers] - Can be used to add additional headers to the request
  /// * [extras] - Can be used to add flags to the request
  /// * [validateStatus] - A [ValidateStatus] callback that can be used to determine request success based on the HTTP status of the response
  /// * [onSendProgress] - A [ProgressCallback] that can be used to get the send progress
  /// * [onReceiveProgress] - A [ProgressCallback] that can be used to get the receive progress
  ///
  /// Returns a [Future] containing a [Response] with a [BillingExport] as data
  /// Throws [DioException] if API call or serialization fails
  Future<Response<BillingExport>> reportsBillingGet({ 
    required String month,
    String? clientId,
    String? format = 'json',
    CancelToken? cancelToken,
    Map<String, dynamic>? headers,
    Map<String, dynamic>? extra,
    ValidateStatus? validateStatus,
    ProgressCallback? onSendProgress,
    ProgressCallback? onReceiveProgress,
  }) async {
    final _path = r'/reports/billing';
    final _options = Options(
      method: r'GET',
      headers: <String, dynamic>{
        ...?headers,
      },
      extra: <String, dynamic>{
        'secure': <Map<String, String>>[
          {
            'type': 'http',
            'scheme': 'bearer',
            'name': 'bearerAuth',
          },
        ],
        ...?extra,
      },
      validateStatus: validateStatus,
    );

    final _queryParameters = <String, dynamic>{
      r'month': encodeQueryParameter(_serializers, month, const FullType(String)),
      if (clientId != null) r'client_id': encodeQueryParameter(_serializers, clientId, const FullType(String)),
      if (format != null) r'format': encodeQueryParameter(_serializers, format, const FullType(String)),
    };

    final _response = await _dio.request<Object>(
      _path,
      options: _options,
      queryParameters: _queryParameters,
      cancelToken: cancelToken,
      onSendProgress: onSendProgress,
      onReceiveProgress: onReceiveProgress,
    );

    BillingExport? _responseData;

    try {
      final rawResponse = _response.data;
      _responseData = rawResponse == null ? null : _serializers.deserialize(
        rawResponse,
        specifiedType: const FullType(BillingExport),
      ) as BillingExport;

    } catch (error, stackTrace) {
      throw DioException(
        requestOptions: _response.requestOptions,
        response: _response,
        type: DioExceptionType.unknown,
        error: error,
        stackTrace: stackTrace,
      );
    }

    return Response<BillingExport>(
      data: _responseData,
      headers: _response.headers,
      isRedirect: _response.isRedirect,
      requestOptions: _response.requestOptions,
      redirects: _response.redirects,
      statusCode: _response.statusCode,
      statusMessage: _response.statusMessage,
      extra: _response.extra,
    );
  }

  /// The full operator report (B39, OPA-05)
  /// Waits, pooling, cab-km, overrides and suggestion acceptance for a period, computed from the records the platform keeps. Requires &#x60;report.operational.view&#x60; (operator admin, supervisor); a client admin has no operational report.  **Days are the operator&#39;s calendar days** in their own timezone, both ends inclusive.  **Cab-km and vehicles used come from what the cabs drove**: &#x60;trip.actual_distance_m&#x60;, measured from the cab&#39;s pings when the driver completes the trip - never from what dispatch planned. A trip with no pings has no distance, and is left out of the average rather than counted as zero kilometres.  **&#x60;suggestions.acceptance_rate&#x60; is OQ-39 stated, not decided.** It counts only the system&#39;s first choice that a person or the failsafe settled in the period; a &#x60;failsafe_assigned&#x60; offer is never an acceptance (nobody agreed to it) and a &#x60;superseded&#x60; one is never a verdict. Two readings are returned because the open question names two: &#x60;acceptance_rate&#x60; (approved) and &#x60;acceptance_rate_with_alternatives&#x60; (approved, or rejected in favour of a cab the system had also offered). Say which one when quoting either. 
  ///
  /// Parameters:
  /// * [from] 
  /// * [to] 
  /// * [clientId] 
  /// * [format] 
  /// * [cancelToken] - A [CancelToken] that can be used to cancel the operation
  /// * [headers] - Can be used to add additional headers to the request
  /// * [extras] - Can be used to add flags to the request
  /// * [validateStatus] - A [ValidateStatus] callback that can be used to determine request success based on the HTTP status of the response
  /// * [onSendProgress] - A [ProgressCallback] that can be used to get the send progress
  /// * [onReceiveProgress] - A [ProgressCallback] that can be used to get the receive progress
  ///
  /// Returns a [Future] containing a [Response] with a [OperationsReport] as data
  /// Throws [DioException] if API call or serialization fails
  Future<Response<OperationsReport>> reportsOperationsGet({ 
    required Date from,
    required Date to,
    String? clientId,
    String? format = 'json',
    CancelToken? cancelToken,
    Map<String, dynamic>? headers,
    Map<String, dynamic>? extra,
    ValidateStatus? validateStatus,
    ProgressCallback? onSendProgress,
    ProgressCallback? onReceiveProgress,
  }) async {
    final _path = r'/reports/operations';
    final _options = Options(
      method: r'GET',
      headers: <String, dynamic>{
        ...?headers,
      },
      extra: <String, dynamic>{
        'secure': <Map<String, String>>[
          {
            'type': 'http',
            'scheme': 'bearer',
            'name': 'bearerAuth',
          },
        ],
        ...?extra,
      },
      validateStatus: validateStatus,
    );

    final _queryParameters = <String, dynamic>{
      r'from': encodeQueryParameter(_serializers, from, const FullType(Date)),
      r'to': encodeQueryParameter(_serializers, to, const FullType(Date)),
      if (clientId != null) r'client_id': encodeQueryParameter(_serializers, clientId, const FullType(String)),
      if (format != null) r'format': encodeQueryParameter(_serializers, format, const FullType(String)),
    };

    final _response = await _dio.request<Object>(
      _path,
      options: _options,
      queryParameters: _queryParameters,
      cancelToken: cancelToken,
      onSendProgress: onSendProgress,
      onReceiveProgress: onReceiveProgress,
    );

    OperationsReport? _responseData;

    try {
      final rawResponse = _response.data;
      _responseData = rawResponse == null ? null : _serializers.deserialize(
        rawResponse,
        specifiedType: const FullType(OperationsReport),
      ) as OperationsReport;

    } catch (error, stackTrace) {
      throw DioException(
        requestOptions: _response.requestOptions,
        response: _response,
        type: DioExceptionType.unknown,
        error: error,
        stackTrace: stackTrace,
      );
    }

    return Response<OperationsReport>(
      data: _responseData,
      headers: _response.headers,
      isRedirect: _response.isRedirect,
      requestOptions: _response.requestOptions,
      redirects: _response.redirects,
      statusCode: _response.statusCode,
      statusMessage: _response.statusMessage,
      extra: _response.extra,
    );
  }

  /// reportsTripsGet
  /// 
  ///
  /// Parameters:
  /// * [from] 
  /// * [to] 
  /// * [clientId] 
  /// * [format] 
  /// * [cancelToken] - A [CancelToken] that can be used to cancel the operation
  /// * [headers] - Can be used to add additional headers to the request
  /// * [extras] - Can be used to add flags to the request
  /// * [validateStatus] - A [ValidateStatus] callback that can be used to determine request success based on the HTTP status of the response
  /// * [onSendProgress] - A [ProgressCallback] that can be used to get the send progress
  /// * [onReceiveProgress] - A [ProgressCallback] that can be used to get the receive progress
  ///
  /// Returns a [Future] containing a [Response] with a [TripReport] as data
  /// Throws [DioException] if API call or serialization fails
  Future<Response<TripReport>> reportsTripsGet({ 
    required Date from,
    required Date to,
    String? clientId,
    String? format = 'json',
    CancelToken? cancelToken,
    Map<String, dynamic>? headers,
    Map<String, dynamic>? extra,
    ValidateStatus? validateStatus,
    ProgressCallback? onSendProgress,
    ProgressCallback? onReceiveProgress,
  }) async {
    final _path = r'/reports/trips';
    final _options = Options(
      method: r'GET',
      headers: <String, dynamic>{
        ...?headers,
      },
      extra: <String, dynamic>{
        'secure': <Map<String, String>>[
          {
            'type': 'http',
            'scheme': 'bearer',
            'name': 'bearerAuth',
          },
        ],
        ...?extra,
      },
      validateStatus: validateStatus,
    );

    final _queryParameters = <String, dynamic>{
      r'from': encodeQueryParameter(_serializers, from, const FullType(Date)),
      r'to': encodeQueryParameter(_serializers, to, const FullType(Date)),
      if (clientId != null) r'client_id': encodeQueryParameter(_serializers, clientId, const FullType(String)),
      if (format != null) r'format': encodeQueryParameter(_serializers, format, const FullType(String)),
    };

    final _response = await _dio.request<Object>(
      _path,
      options: _options,
      queryParameters: _queryParameters,
      cancelToken: cancelToken,
      onSendProgress: onSendProgress,
      onReceiveProgress: onReceiveProgress,
    );

    TripReport? _responseData;

    try {
      final rawResponse = _response.data;
      _responseData = rawResponse == null ? null : _serializers.deserialize(
        rawResponse,
        specifiedType: const FullType(TripReport),
      ) as TripReport;

    } catch (error, stackTrace) {
      throw DioException(
        requestOptions: _response.requestOptions,
        response: _response,
        type: DioExceptionType.unknown,
        error: error,
        stackTrace: stackTrace,
      );
    }

    return Response<TripReport>(
      data: _responseData,
      headers: _response.headers,
      isRedirect: _response.isRedirect,
      requestOptions: _response.requestOptions,
      redirects: _response.redirects,
      statusCode: _response.statusCode,
      statusMessage: _response.statusMessage,
      extra: _response.extra,
    );
  }

}
