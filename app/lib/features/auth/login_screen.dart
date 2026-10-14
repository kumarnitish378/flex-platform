import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/session_controller.dart';
import '../../l10n/app_localizations.dart';

/// Phone + OTP sign-in (C-02).
///
/// Handles phone number entry (+91 default) and 6-digit OTP verification.
/// Respects backend security rules: single error message for refused OTP (OQ-24)
/// and no "user not found" messages on phone submit.
class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  late final TextEditingController _phoneController;
  late final TextEditingController _codeController;

  Timer? _resendTimer;
  int _resendCountdown = 30;

  @override
  void initState() {
    super.initState();
    _phoneController = TextEditingController(text: '+91');
    _codeController = TextEditingController();
  }

  @override
  void dispose() {
    _resendTimer?.cancel();
    _phoneController.dispose();
    _codeController.dispose();
    super.dispose();
  }

  void _startResendTimer() {
    _resendTimer?.cancel();
    setState(() {
      _resendCountdown = 30;
    });
    _resendTimer = Timer.periodic(const Duration(seconds: 1), (Timer timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      if (_resendCountdown > 1) {
        setState(() {
          _resendCountdown--;
        });
      } else {
        timer.cancel();
        setState(() {
          _resendCountdown = 0;
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final AppText text = AppText.of(context);
    final SignInState signInState = ref.watch(sessionControllerProvider);

    // Start countdown timer when entering code stage if not already running.
    if (signInState.stage == SignInStage.code &&
        _resendTimer == null &&
        _resendCountdown == 30) {
      _startResendTimer();
    } else if (signInState.stage == SignInStage.phone && _resendTimer != null) {
      _resendTimer?.cancel();
      _resendTimer = null;
      _resendCountdown = 30;
    }

    return Scaffold(
      key: const Key('C-02'),
      appBar: AppBar(title: Text(text.signIn)),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Center(
          child: SingleChildScrollView(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                if (signInState.stage == SignInStage.phone)
                  _buildPhoneStage(context, text, signInState)
                else
                  _buildCodeStage(context, text, signInState),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildPhoneStage(
    BuildContext context,
    AppText text,
    SignInState state,
  ) {
    final String? errorMessage = _getErrorMessage(text, state);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        Text(
          text.enterPhoneNumber,
          style: Theme.of(context).textTheme.titleLarge,
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 24),
        TextField(
          key: const Key('phone-input'),
          controller: _phoneController,
          keyboardType: TextInputType.phone,
          onChanged: (_) => setState(() {}),
          decoration: InputDecoration(
            labelText: text.phoneNumber,
            border: const OutlineInputBorder(),
            prefixIcon: const Icon(Icons.phone),
          ),
          enabled: !state.busy,
        ),
        if (errorMessage != null) ...<Widget>[
          const SizedBox(height: 16),
          Text(
            errorMessage,
            style: TextStyle(color: Theme.of(context).colorScheme.error),
            textAlign: TextAlign.center,
          ),
        ],
        const SizedBox(height: 24),
        ElevatedButton(
          key: const Key('send-code'),
          onPressed: state.busy || _phoneController.text.trim().isEmpty
              ? null
              : () async {
                  await ref
                      .read(sessionControllerProvider.notifier)
                      .requestCode(_phoneController.text.trim());
                  if (ref.read(sessionControllerProvider).stage ==
                      SignInStage.code) {
                    _startResendTimer();
                  }
                },
          child: state.busy
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : Text(text.sendCode),
        ),
      ],
    );
  }

  Widget _buildCodeStage(
    BuildContext context,
    AppText text,
    SignInState state,
  ) {
    final String? errorMessage = _getErrorMessage(text, state);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        Text(
          text.enterCode,
          style: Theme.of(context).textTheme.titleLarge,
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 8),
        Text(
          text.codeSentTo(state.phone.isNotEmpty ? state.phone : _phoneController.text),
          style: Theme.of(context).textTheme.bodyMedium,
          textAlign: TextAlign.center,
        ),
        TextButton(
          key: const Key('change-phone'),
          onPressed: state.busy
              ? null
              : () {
                  _codeController.clear();
                  ref.read(sessionControllerProvider.notifier).backToPhone();
                },
          child: Text(text.changePhone),
        ),
        const SizedBox(height: 16),
        TextField(
          key: const Key('code-input'),
          controller: _codeController,
          keyboardType: TextInputType.number,
          maxLength: 6,
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 24, letterSpacing: 8),
          onChanged: (_) => setState(() {}),
          decoration: InputDecoration(
            hintText: '000000',
            border: const OutlineInputBorder(),
            counterText: '',
            errorText: state.rejected ? text.otpRejected : null,
          ),
          enabled: !state.busy,
        ),
        if (errorMessage != null && !state.rejected) ...<Widget>[
          const SizedBox(height: 16),
          Text(
            errorMessage,
            style: TextStyle(color: Theme.of(context).colorScheme.error),
            textAlign: TextAlign.center,
          ),
        ],
        const SizedBox(height: 24),
        ElevatedButton(
          key: const Key('verify-code'),
          onPressed: state.busy || _codeController.text.trim().length < 6
              ? null
              : () async {
                  await ref
                      .read(sessionControllerProvider.notifier)
                      .submitCode(_codeController.text.trim());
                },
          child: state.busy
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : Text(text.verifyCode),
        ),
        const SizedBox(height: 12),
        TextButton(
          key: const Key('resend-code'),
          onPressed: state.busy || _resendCountdown > 0
              ? null
              : () async {
                  _startResendTimer();
                  await ref
                      .read(sessionControllerProvider.notifier)
                      .requestCode(state.phone);
                },
          child: Text(
            _resendCountdown > 0
                ? text.resendCodeIn(_resendCountdown)
                : text.resendCode,
          ),
        ),
      ],
    );
  }

  String? _getErrorMessage(AppText text, SignInState state) {
    if (state.unavailable == 'too_many_requests') {
      return text.tooManyRequests;
    }
    if (state.unavailable == 'no_roles') {
      return text.noRolesAssigned;
    }
    if (state.unavailable != null) {
      return text.authUnavailable;
    }
    return null;
  }
}
