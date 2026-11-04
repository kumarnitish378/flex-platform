import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

/// Trip completed & rating screen (E-05).
///
/// Features 1-5 star rating bar, comment box, and single-submit rating action.
class TripCompletedScreen extends ConsumerStatefulWidget {
  const TripCompletedScreen({required this.tripId, super.key});

  final String tripId;

  @override
  ConsumerState<TripCompletedScreen> createState() => _TripCompletedScreenState();
}

class _TripCompletedScreenState extends ConsumerState<TripCompletedScreen> {
  int _rating = 5;
  final TextEditingController _commentController = TextEditingController();
  bool _submitted = false;

  @override
  void dispose() {
    _commentController.dispose();
    super.dispose();
  }

  void _submitRating() {
    setState(() {
      _submitted = true;
    });
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Thank you for rating your trip!')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);

    return Scaffold(
      key: const Key('E-05'),
      appBar: AppBar(title: const Text('Trip Completed')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Icon(
              Icons.check_circle_outline,
              size: 72,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(height: 16),
            Text(
              'You have arrived!',
              textAlign: TextAlign.center,
              style: theme.textTheme.headlineMedium,
            ),
            const SizedBox(height: 32),

            Text(
              'How was your trip?',
              textAlign: TextAlign.center,
              style: theme.textTheme.titleMedium,
            ),
            const SizedBox(height: 16),

            // Rating Bar (1-5 stars)
            Row(
              key: const Key('rating-bar'),
              mainAxisAlignment: MainAxisAlignment.center,
              children: <Widget>[
                for (int star = 1; star <= 5; star++)
                  IconButton(
                    key: Key('star-$star'),
                    icon: Icon(
                      star <= _rating ? Icons.star : Icons.star_border,
                      size: 36,
                      color: Colors.amber,
                    ),
                    onPressed: _submitted
                        ? null
                        : () {
                            setState(() {
                              _rating = star;
                            });
                          },
                  ),
              ],
            ),
            const SizedBox(height: 24),

            TextField(
              key: const Key('rating-comment'),
              controller: _commentController,
              enabled: !_submitted,
              maxLines: 3,
              decoration: const InputDecoration(
                labelText: 'Feedback / Comment (optional)',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 32),

            ElevatedButton(
              key: const Key('submit-rating'),
              onPressed: _submitted ? null : _submitRating,
              child: Text(_submitted ? 'Rating Submitted' : 'Submit Rating'),
            ),
            const SizedBox(height: 12),

            TextButton(
              onPressed: () => context.go('/employee'),
              child: const Text('Back to Home'),
            ),
          ],
        ),
      ),
    );
  }
}
