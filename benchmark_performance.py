#!/usr/bin/env python3
"""
Direct performance benchmark showing real-world improvements.
Tests actual extraction scenarios with and without caching.
"""

import shutil
import time
from pathlib import Path

from amplifier.utils.cache import ArtifactCache

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def simulate_knowledge_extraction(content: str) -> dict:
    """Simulate a realistic knowledge extraction that would call an LLM."""
    # Simulate API call latency (conservative estimate)
    time.sleep(2.0)

    # Return realistic extraction results
    return {
        "concepts": ["software architecture", "microservices", "APIs", "cloud native", "scalability"],
        "relationships": [
            ["microservices", "enables", "scalability"],
            ["APIs", "connect", "microservices"],
            ["cloud native", "uses", "microservices"],
        ],
        "insights": [
            "Microservices architecture improves scalability",
            "API design is critical for microservice success",
            "Cloud native applications benefit from containerization",
        ],
        "metadata": {"extraction_time": time.time(), "word_count": len(content.split()), "concept_count": 5},
    }


def benchmark_without_cache(documents: list) -> dict:
    """Benchmark extraction without caching (old method)."""
    print(f"\n{BOLD}Testing WITHOUT Cache (Old Method){RESET}")
    print("-" * 40)

    results = []
    start_time = time.time()

    for i, doc in enumerate(documents, 1):
        doc_start = time.time()
        # Every extraction requires full processing
        result = simulate_knowledge_extraction(doc["content"])
        doc_time = time.time() - doc_start
        results.append(result)
        print(f"  Document {i}: {doc_time:.2f}s")

    total_time = time.time() - start_time

    return {"total_time": total_time, "results": results, "avg_per_doc": total_time / len(documents)}


def benchmark_with_cache(documents: list, cache_dir: Path) -> dict:
    """Benchmark extraction with caching (new method)."""
    print(f"\n{BOLD}Testing WITH Cache (New Method){RESET}")
    print("-" * 40)

    cache = ArtifactCache(cache_dir=cache_dir)

    # First run - populate cache
    print(f"\n{YELLOW}First Run (Populating Cache):{RESET}")
    first_run_start = time.time()
    first_results = []

    for i, doc in enumerate(documents, 1):
        doc_start = time.time()
        result, was_cached = cache.check_or_process(
            content=doc["content"],
            stage="extraction",
            processor_func=simulate_knowledge_extraction,
            model="claude-3",
            params={"doc_id": doc["id"]},
        )
        doc_time = time.time() - doc_start
        first_results.append(result)
        status = "[CACHED]" if was_cached else "[PROCESSED]"
        print(f"  Document {i}: {doc_time:.2f}s {status}")

    first_run_time = time.time() - first_run_start

    # Second run - use cache
    print(f"\n{YELLOW}Second Run (Using Cache):{RESET}")
    second_run_start = time.time()
    second_results = []

    for i, doc in enumerate(documents, 1):
        doc_start = time.time()
        result, was_cached = cache.check_or_process(
            content=doc["content"],
            stage="extraction",
            processor_func=simulate_knowledge_extraction,
            model="claude-3",
            params={"doc_id": doc["id"]},
        )
        doc_time = time.time() - doc_start
        second_results.append(result)
        status = "[CACHED]" if was_cached else "[PROCESSED]"
        print(f"  Document {i}: {doc_time:.3f}s {status}")

    second_run_time = time.time() - second_run_start

    return {
        "first_run_time": first_run_time,
        "second_run_time": second_run_time,
        "speedup": first_run_time / second_run_time if second_run_time > 0 else 0,
        "cache_stats": cache.get_stats(),
    }


def main():
    """Run the performance benchmark."""
    print(f"{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}{BLUE}AMPLIFIER PERFORMANCE BENCHMARK{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")

    # Create test documents (simulate real articles)
    documents = [
        {
            "id": "doc-001",
            "title": "Introduction to Microservices",
            "content": """
            Microservices architecture is an approach to developing a single application
            as a suite of small services, each running in its own process and communicating
            with lightweight mechanisms. This architectural style has gained popularity due
            to its scalability and flexibility benefits.
            """,
        },
        {
            "id": "doc-002",
            "title": "API Design Best Practices",
            "content": """
            Well-designed APIs are crucial for successful software systems. They should be
            intuitive, consistent, and well-documented. RESTful principles provide a good
            foundation, but GraphQL and gRPC offer alternatives for specific use cases.
            """,
        },
        {
            "id": "doc-003",
            "title": "Cloud Native Applications",
            "content": """
            Cloud native applications are designed to take full advantage of cloud computing
            frameworks. They use containerization, microservices, and declarative APIs to
            enable loosely coupled systems that are resilient, manageable, and observable.
            """,
        },
        {
            "id": "doc-004",
            "title": "DevOps and CI/CD",
            "content": """
            DevOps practices combined with continuous integration and continuous deployment
            enable teams to deliver software faster and more reliably. Automation is key
            to achieving the goals of DevOps.
            """,
        },
        {
            "id": "doc-005",
            "title": "Container Orchestration",
            "content": """
            Container orchestration platforms like Kubernetes have become essential for
            managing containerized applications at scale. They provide automated deployment,
            scaling, and management of containerized applications.
            """,
        },
    ]

    print(f"\nBenchmarking with {len(documents)} documents...")
    print("Each extraction simulates a 2-second LLM API call")

    # Test without cache
    no_cache_results = benchmark_without_cache(documents)

    # Test with cache
    cache_dir = Path(".benchmark_cache")
    cache_results = benchmark_with_cache(documents, cache_dir)

    # Display comparison
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}{CYAN}PERFORMANCE COMPARISON{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")

    print(f"\n{BOLD}Without Cache (Old Method):{RESET}")
    print(f"  Total time: {no_cache_results['total_time']:.2f}s")
    print(f"  Average per document: {no_cache_results['avg_per_doc']:.2f}s")

    print(f"\n{BOLD}With Cache (New Method):{RESET}")
    print(f"  First run: {cache_results['first_run_time']:.2f}s")
    print(f"  Cached run: {cache_results['second_run_time']:.3f}s")
    print(f"  {GREEN}Speedup: {cache_results['speedup']:.0f}x faster{RESET}")

    # Show cache statistics
    print(f"\n{BOLD}Cache Statistics:{RESET}")
    for stage, stats in cache_results["cache_stats"].items():
        print(f"  {stage}: {stats['count']} items, {stats['size_mb']:.3f} MB")

    # Real-world impact
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}{GREEN}REAL-WORLD IMPACT{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")

    # Calculate for 100 documents
    time_100_no_cache = no_cache_results["avg_per_doc"] * 100
    time_100_cached = cache_results["second_run_time"] / len(documents) * 100

    print("\nFor 100 documents:")
    print(f"  Without cache: {time_100_no_cache:.1f}s ({time_100_no_cache / 60:.1f} minutes)")
    print(f"  With cache (90% hit rate): ~{time_100_cached + (time_100_no_cache * 0.1):.1f}s")
    print(f"  {GREEN}Time saved: {time_100_no_cache - (time_100_cached + time_100_no_cache * 0.1):.1f}s{RESET}")

    print("\nIterative Development Benefits:")
    print(f"  • Re-run extraction after code changes: {GREEN}Near instant{RESET}")
    print(f"  • Test on subset of documents: {GREEN}No re-processing{RESET}")
    print(f"  • Resume after interruption: {GREEN}Automatic{RESET}")

    # Clean up
    shutil.rmtree(cache_dir, ignore_errors=True)

    print(f"\n{BOLD}Conclusion:{RESET}")
    print(
        f"The new caching system provides a {GREEN}{cache_results['speedup']:.0f}x speedup{RESET} for cached operations,"
    )
    print("dramatically improving development iteration speed and user experience.")


if __name__ == "__main__":
    main()
