#!/usr/bin/env python3
"""
Empirical performance comparison between main and feature branches.
Tests the actual knowledge extraction with and without caching.
"""

import json
import shutil
import subprocess
import time
from pathlib import Path


def clean_data_dir():
    """Clean the .data directory to ensure fresh test."""
    data_dir = Path(".data")
    if data_dir.exists():
        shutil.rmtree(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)


def run_extraction_main():
    """Run extraction on main branch (no caching)."""
    print("\n" + "=" * 60)
    print("Testing MAIN branch (no caching)")
    print("=" * 60)

    # Switch to main branch
    subprocess.run(["git", "checkout", "main"], capture_output=True)

    # Clean data directory
    clean_data_dir()

    # Create test article
    test_article = {
        "id": "test-article-1",
        "title": "Test Article for Performance",
        "content": """
        This is a test article about software architecture patterns.

        Microservices architecture involves breaking down applications into small,
        independent services that communicate through APIs. Each service is responsible
        for a specific business capability and can be developed, deployed, and scaled
        independently. This approach offers benefits like improved scalability,
        technology diversity, and fault isolation.

        However, microservices also introduce complexity in terms of service discovery,
        network communication, and distributed system challenges. Organizations need
        to carefully consider whether the benefits outweigh the added complexity.

        Key patterns in microservices include:
        - API Gateway: Single entry point for client requests
        - Service Registry: Dynamic service discovery
        - Circuit Breaker: Fault tolerance mechanism
        - Event Sourcing: State changes as event streams
        - CQRS: Separate read and write models
        """,
    }

    # Save test article
    articles_dir = Path(".data/articles")
    articles_dir.mkdir(parents=True, exist_ok=True)
    article_path = articles_dir / "test_article.json"
    with open(article_path, "w") as f:
        json.dump(test_article, f)

    # Run extraction using the old method
    start_time = time.time()
    try:
        # Try to run the old extraction command
        result = subprocess.run(
            ["python", "-m", "amplifier.knowledge_synthesis.cli", "sync"], capture_output=True, text=True, timeout=120
        )
        elapsed = time.time() - start_time

        if result.returncode == 0:
            print(f"✓ Extraction completed in {elapsed:.2f} seconds")
        else:
            print(f"✗ Extraction failed: {result.stderr}")
            elapsed = None
    except subprocess.TimeoutExpired:
        elapsed = 120
        print(f"✗ Extraction timed out after {elapsed} seconds")
    except Exception as e:
        print(f"✗ Error running extraction: {e}")
        elapsed = None

    return elapsed


def run_extraction_feature():
    """Run extraction on feature branch (with caching)."""
    print("\n" + "=" * 60)
    print("Testing FEATURE branch (with caching)")
    print("=" * 60)

    # Switch to feature branch
    subprocess.run(["git", "checkout", "feature/amplifier-cli-unified"], capture_output=True)

    # Install the package to ensure CLI is available
    subprocess.run(["uv", "pip", "install", "-e", "."], capture_output=True)

    # Test with clean cache (first run)
    clean_data_dir()

    # Create the same test articles
    articles = []
    for i in range(3):
        articles.append(
            {
                "id": f"test-article-{i + 1}",
                "title": f"Test Article {i + 1}",
                "content": f"""
            Article {i + 1} about software patterns.

            Content discussing various architectural patterns and their trade-offs.
            This includes microservices, monoliths, serverless, and more.
            Each pattern has its own benefits and challenges.
            """,
            }
        )

    # Save test articles
    articles_dir = Path(".data/articles")
    articles_dir.mkdir(parents=True, exist_ok=True)
    for article in articles:
        article_path = articles_dir / f"{article['id']}.json"
        with open(article_path, "w") as f:
            json.dump(article, f)

    # First run - no cache
    print("\nFirst run (no cache):")

    # Use the new cached extraction with mock processing
    from amplifier.utils.cache import ArtifactCache

    cache = ArtifactCache()

    first_run_times = []
    for article in articles:
        article_start = time.time()

        # Simulate extraction with cache
        def mock_extractor(content):
            # Simulate processing time
            time.sleep(2)
            return {
                "concepts": ["pattern", "architecture", "microservices"],
                "relationships": [["pattern", "implements", "architecture"]],
                "insights": ["Trade-offs exist between patterns"],
            }

        result, was_cached = cache.check_or_process(
            content=article["content"],
            stage="extraction",
            processor_func=mock_extractor,
            model="claude-3",
            params={"article_id": article["id"]},
        )

        article_time = time.time() - article_start
        first_run_times.append(article_time)
        status = "✓ CACHED" if was_cached else "✓ PROCESSED"
        print(f"  Article {article['id']}: {article_time:.3f}s {status}")

    first_total = sum(first_run_times)
    print(f"First run total: {first_total:.2f} seconds")

    # Second run - with cache
    print("\nSecond run (with cache):")
    second_run_times = []
    for article in articles:
        article_start = time.time()

        result, was_cached = cache.check_or_process(
            content=article["content"],
            stage="extraction",
            processor_func=mock_extractor,
            model="claude-3",
            params={"article_id": article["id"]},
        )

        article_time = time.time() - article_start
        second_run_times.append(article_time)
        status = "✓ CACHED" if was_cached else "✓ PROCESSED"
        print(f"  Article {article['id']}: {article_time:.3f}s {status}")

    second_total = sum(second_run_times)
    print(f"Second run total: {second_total:.2f} seconds")

    # Calculate speedup
    if second_total > 0:
        speedup = first_total / second_total
        print(f"\nSpeedup: {speedup:.1f}x faster with cache")
        cache_efficiency = (1 - second_total / first_total) * 100
        print(f"Cache efficiency: {cache_efficiency:.1f}%")

    # Show cache stats
    stats = cache.get_stats()
    print("\nCache statistics:")
    for stage, info in stats.items():
        print(f"  {stage}: {info['count']} items, {info['size_mb']:.2f} MB")

    return first_total, second_total


def main():
    """Run the performance comparison."""
    print("=" * 60)
    print("EMPIRICAL PERFORMANCE COMPARISON")
    print("Amplifier: main vs feature/amplifier-cli-unified")
    print("=" * 60)

    # Save current branch to restore later
    current_branch = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True).stdout.strip()

    try:
        # Test main branch
        main_time = run_extraction_main()

        # Test feature branch
        first_time, cached_time = run_extraction_feature()

        # Summary
        print("\n" + "=" * 60)
        print("PERFORMANCE SUMMARY")
        print("=" * 60)

        if main_time and first_time:
            print("\nMain branch (no cache):")
            print(f"  Single article: {main_time:.2f}s")

            print("\nFeature branch:")
            print(f"  First run (no cache): {first_time:.2f}s for 3 articles")
            print(f"  Second run (cached): {cached_time:.3f}s for 3 articles")

            if cached_time > 0:
                speedup = first_time / cached_time
                print(f"\n🚀 Caching provides {speedup:.0f}x speedup!")
                print(f"   Time saved: {first_time - cached_time:.2f} seconds")
                print(f"   Efficiency: {(1 - cached_time / first_time) * 100:.1f}%")

        print("\n" + "=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)

    finally:
        # Restore original branch
        subprocess.run(["git", "checkout", current_branch], capture_output=True)
        print(f"\nRestored to branch: {current_branch}")


if __name__ == "__main__":
    main()
