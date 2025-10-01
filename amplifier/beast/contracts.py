"""Behavioral contracts for verifying actual behavior"""

from abc import ABC
from abc import abstractmethod
from typing import Any

from .tracer import ExecutionTrace
from .tracer import ExecutionTracer


class BehavioralContract(ABC):
    """Base class for behavioral contracts"""

    def __init__(self, name: str):
        self.name = name
        self.tracer = ExecutionTracer()

    @abstractmethod
    def setup(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def execute(self, context: dict[str, Any]) -> ExecutionTrace:
        pass

    @abstractmethod
    def verify(self, trace: ExecutionTrace, context: dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def cleanup(self, context: dict[str, Any]):
        pass


class ContractVerifier:
    """Verifies behavioral contracts"""

    def __init__(self):
        self.contracts = []

    def add_contract(self, contract: BehavioralContract):
        self.contracts.append(contract)

    def verify_all(self, verbose: bool = False) -> dict[str, Any]:
        results = []
        failures = []
        passed_count = 0
        failed_count = 0

        print("\nBEAST - ACTUAL BEHAVIOR VERIFICATION")
        print("=" * 70)
        print("Verifying actual system behavior through execution tracing\n")

        for i, contract in enumerate(self.contracts, 1):
            print("-" * 70)
            # Show what we're testing with clear explanation
            print(f"\nTEST #{i}: {contract.name}")
            if hasattr(contract, "description"):
                print(f"Purpose: {contract.description}")

            print("\nExecution steps:")

            context = contract.setup()
            try:
                # Explain setup in plain language
                print("  1. Setting up test environment")
                if verbose and context:
                    # Make context human-readable
                    if "broken_file" in context:
                        print("     - Creating broken Python file with actual syntax/logic errors")
                    if "test_data" in context:
                        print("     - Preparing test data for persistence verification")
                    if "test_dir" in context:
                        print(f"     - Test directory: {context['test_dir']}")
                    if "commands_to_test" in context:
                        cmds = context["commands_to_test"]
                        print(f"     - Commands to test: {', '.join(cmds[:2])}")

                # Explain execution in plain language
                print("\n  2. Executing feature")
                trace = contract.execute(context)
                if verbose:
                    # Explain what happened in plain English
                    if "heal" in str(trace.command).lower():
                        print("     - Running healing system on broken code")
                        print("     - Checking for error identification")
                    elif "memory" in str(trace.command).lower():
                        print("     - Saving data to memory system")
                        print("     - Testing persistence across file operations")
                    elif "synthesis" in str(trace.command).lower():
                        print("     - Running synthesis on test documents")
                        print("     - Checking for pattern detection")
                    elif "cli" in str(trace.command).lower():
                        print("     - Executing CLI commands")
                    else:
                        cmd_str = str(trace.command)[:50]
                        print(f"     - Command: {cmd_str}")

                    # Show system response
                    if hasattr(trace, "exit_code"):
                        if trace.exit_code == 0:
                            print("     - Exit code: 0 (success)")
                        else:
                            print(f"     - Exit code: {trace.exit_code} (error)")

                # Explain verification in plain language
                print("\n  3. Verifying results")
                passed, reasons = contract.verify(trace, context)

                result = {"contract": contract.name, "passed": passed, "reasons": reasons}
                results.append(result)

                if passed:
                    passed_count += 1
                    print("\n  Result: PASSED")

                    # Explain what we proved
                    if "heal" in contract.name.lower():
                        print("     - Healing system successfully identified errors")
                    elif "memory" in contract.name.lower():
                        print("     - Data persisted correctly across operations")
                    elif "synthesis" in contract.name.lower():
                        print("     - Synthesis generated insights from documents")
                    elif "cli" in contract.name.lower():
                        print("     - CLI commands executed successfully")

                    if verbose and hasattr(trace, "stdout") and trace.stdout:
                        # Show proof it worked
                        output_preview = trace.stdout[:80].replace("\n", " ")
                        if len(trace.stdout) > 80:
                            output_preview += "..."
                        print(f"     - Output: {output_preview}")
                else:
                    failed_count += 1
                    print("\n  Result: FAILED")
                    print("  Issues found:")
                    if reasons:
                        for reason in reasons:
                            print(f"     - {reason}")
                    else:
                        print("     - Feature did not work as expected")
                    failures.append(result)

                # Cleanup
                print("\n  4. Cleaning up")
                print("     - Removing temporary files")
                contract.cleanup(context)

            except Exception as e:
                failed_count += 1
                error_msg = f"{str(e)}"
                print("\n  Result: ERROR")
                print(f"  Test crashed: {error_msg}")
                result = {"contract": contract.name, "passed": False, "reasons": [error_msg]}
                results.append(result)
                failures.append(result)
            finally:
                from contextlib import suppress

                with suppress(Exception):
                    contract.cleanup(context)

        total = len(self.contracts)
        success_rate = (passed_count / total * 100) if total > 0 else 0

        # Final summary with clear explanation
        print("\n" + "=" * 70)
        print("VERIFICATION COMPLETE")
        print("=" * 70)

        print(f"\nTests passed: {passed_count} out of {total}")
        print(f"Success rate: {success_rate:.1f}%")

        if failed_count > 0:
            print(f"\nFailed tests: {failed_count}")
            print("Failed contracts:")
            for failure in failures[:5]:  # Show first 5
                print(f"  - {failure['contract']}")

        # Give clear verdict
        print("\nSummary:")
        if success_rate == 100:
            print("All features working correctly.")
        elif success_rate >= 80:
            print("Most features working, some issues found.")
        elif success_rate >= 50:
            print("Significant issues detected - multiple features failing.")
        else:
            print("Critical failures - most features not working.")

        return {
            "summary": {
                "total_contracts": total,
                "passed": passed_count,
                "failed": failed_count,
                "success_rate": success_rate,
            },
            "results": results,
            "failures": failures,
        }
