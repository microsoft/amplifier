#!/usr/bin/env python3
"""
Direct performance test of the ArtifactCache system.
Shows the dramatic speedup from caching.
"""

import time

from amplifier.utils.cache import ArtifactCache


def simulate_expensive_extraction(content: str) -> dict:
    """Simulate an expensive extraction operation."""
    # Simulate API call delay
    time.sleep(2.0)
    return {
        "concepts": ["architecture", "patterns", "microservices"],
        "relationships": [["architecture", "uses", "patterns"]],
        "insights": ["Patterns improve architecture"],
    }


def main():
    print("=" * 60)
    print("ARTIFACT CACHE PERFORMANCE TEST")
    print("=" * 60)

    # Initialize cache
    cache = ArtifactCache()

    # Test documents
    documents = [
        "Document about software architecture and design patterns.",
        "Article discussing microservices and cloud native apps.",
        "Tutorial on implementing REST APIs with best practices.",
    ]

    print("\n1. FIRST RUN (No Cache)")
    print("-" * 40)
    first_run_start = time.time()
    first_run_times = []

    for i, doc in enumerate(documents, 1):
        doc_start = time.time()
        result, was_cached = cache.check_or_process(
            content=doc,
            stage="extraction",
            processor_func=simulate_expensive_extraction,
            model="claude-3",
            params={"doc_id": f"doc-{i}"},
        )
        doc_time = time.time() - doc_start
        first_run_times.append(doc_time)
        print(f"  Document {i}: {doc_time:.2f}s {'[CACHED]' if was_cached else '[PROCESSED]'}")

    first_total = time.time() - first_run_start
    print(f"\nTotal time: {first_total:.2f} seconds")

    print("\n2. SECOND RUN (With Cache)")
    print("-" * 40)
    second_run_start = time.time()
    second_run_times = []

    for i, doc in enumerate(documents, 1):
        doc_start = time.time()
        result, was_cached = cache.check_or_process(
            content=doc,
            stage="extraction",
            processor_func=simulate_expensive_extraction,
            model="claude-3",
            params={"doc_id": f"doc-{i}"},
        )
        doc_time = time.time() - doc_start
        second_run_times.append(doc_time)
        print(f"  Document {i}: {doc_time:.3f}s {'[CACHED]' if was_cached else '[PROCESSED]'}")

    second_total = time.time() - second_run_start
    print(f"\nTotal time: {second_total:.3f} seconds")

    # Calculate metrics
    print("\n" + "=" * 60)
    print("PERFORMANCE METRICS")
    print("=" * 60)

    speedup = first_total / second_total if second_total > 0 else float("inf")
    time_saved = first_total - second_total
    efficiency = (1 - second_total / first_total) * 100 if first_total > 0 else 100

    print(f"\n🚀 Speedup: {speedup:.0f}x faster with cache")
    print(f"⏱️  Time saved: {time_saved:.2f} seconds")
    print(f"📊 Cache efficiency: {efficiency:.1f}%")

    # Show cache stats
    stats = cache.get_stats()
    print("\n📁 Cache storage:")
    for stage, info in stats.items():
        print(f"   {stage}: {info['count']} items, {info['size_mb']:.3f} MB")

    print("\n" + "=" * 60)
    print("CONCLUSION")
    print("=" * 60)
    print(f"""
The ArtifactCache provides a {speedup:.0f}x speedup for repeated operations.
This translates to:
- {time_saved:.1f} seconds saved on just 3 documents
- {efficiency:.0f}% reduction in processing time
- Near-instant results for previously processed content

For a typical workflow with 100 documents:
- Without cache: ~200 seconds (3.3 minutes)
- With cache (90% hit rate): ~20 seconds
- Time saved: ~3 minutes per run
""")


if __name__ == "__main__":
    main()
