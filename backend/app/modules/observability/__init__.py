"""Scrape-time collection of the business gauges in `app/core/metrics.py`.

`core` defines the metrics and knows nothing about ride requests; this module asks the
database the questions and writes the answers into them. Keeping the queries out of
`core` is the same layering rule as everywhere else (coding-standards.md §2 layout).
"""

from app.modules.observability.service import BusinessGaugeCollector

__all__ = ["BusinessGaugeCollector"]
