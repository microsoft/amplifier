"""
Contract Validation Module

This module provides validation utilities to ensure implementations comply
with the defined API contracts. It enables contract-based testing and
runtime validation of module boundaries.
"""

import inspect
import json
from dataclasses import fields
from dataclasses import is_dataclass
from typing import Any
from typing import Optional


class ContractValidator:
    """
    Validates that implementations comply with defined contracts.
    Used for both testing and runtime validation.
    """

    @staticmethod
    def validate_protocol_implementation(implementation: Any, protocol: type) -> list[str]:
        """
        Validate that a class implements all methods required by a protocol.

        Returns list of validation errors (empty if valid).
        """
        errors = []

        # Get all abstract methods from protocol
        protocol_methods = {
            name: method
            for name, method in inspect.getmembers(protocol)
            if not name.startswith("_") and callable(method)
        }

        # Check each required method
        for method_name, protocol_method in protocol_methods.items():
            if not hasattr(implementation, method_name):
                errors.append(f"Missing required method: {method_name}")
                continue

            impl_method = getattr(implementation, method_name)
            if not callable(impl_method):
                errors.append(f"Attribute {method_name} is not callable")
                continue

            # Check method signature compatibility
            protocol_sig = inspect.signature(protocol_method)
            impl_sig = inspect.signature(impl_method)

            # Check parameters (excluding self)
            protocol_params = list(protocol_sig.parameters.values())[1:]
            impl_params = list(impl_sig.parameters.values())[1:]

            if len(protocol_params) != len(impl_params):
                errors.append(
                    f"Method {method_name} has wrong number of parameters: "
                    f"expected {len(protocol_params)}, got {len(impl_params)}"
                )

        return errors

    @staticmethod
    def validate_data_model(instance: Any, model_class: type) -> list[str]:
        """
        Validate that an instance conforms to a data model.
        """
        errors = []

        if not isinstance(instance, model_class):
            errors.append(f"Instance is not of type {model_class.__name__}")
            return errors

        # Validate required fields for dataclasses
        if is_dataclass(model_class):
            for field in fields(model_class):
                if not hasattr(instance, field.name):
                    errors.append(f"Missing required field: {field.name}")
                    continue

                value = getattr(instance, field.name)

                # Check None for non-optional fields
                if value is None and not _is_optional(field.type):
                    errors.append(f"Non-optional field {field.name} is None")

        return errors

    @staticmethod
    def validate_json_serialization(instance: Any, model_class: type) -> list[str]:
        """
        Validate that an instance can be serialized and deserialized.
        """
        errors = []

        # Check for to_json method
        if not hasattr(instance, "to_json"):
            errors.append(f"{model_class.__name__} missing to_json method")
            return errors

        # Try serialization
        try:
            json_str = instance.to_json()
            json_data = json.loads(json_str)

            # Check for sorted keys (git-friendly requirement)
            if json_str != json.dumps(json_data, sort_keys=True, indent=2):
                errors.append("JSON not serialized with sorted keys")
        except Exception as e:
            errors.append(f"Serialization failed: {e}")
            return errors

        # Check for from_json method
        if not hasattr(model_class, "from_json"):
            errors.append(f"{model_class.__name__} missing from_json method")
            return errors

        # Try round-trip
        try:
            restored = model_class.from_json(json_str)
            if not isinstance(restored, model_class):
                errors.append("Deserialization returned wrong type")
        except Exception as e:
            errors.append(f"Deserialization failed: {e}")

        return errors

    @staticmethod
    def validate_api_response(response: dict[str, Any], schema: dict[str, Any]) -> list[str]:
        """
        Validate API response against OpenAPI schema.
        """
        errors = []

        # Check required fields
        for field in schema.get("required", []):
            if field not in response:
                errors.append(f"Missing required field: {field}")

        # Check field types
        for field, value in response.items():
            if field in schema.get("properties", {}):
                field_schema = schema["properties"][field]
                errors.extend(_validate_field(field, value, field_schema))

        return errors

    @staticmethod
    def validate_event_schema(event: dict[str, Any], event_type: str) -> list[str]:
        """
        Validate event conforms to expected schema.
        """
        errors = []

        # Check standard event fields
        required_fields = ["event_type", "timestamp"]
        for field in required_fields:
            if field not in event:
                errors.append(f"Missing required event field: {field}")

        # Check event type
        if event.get("event_type") != event_type:
            errors.append(f"Event type mismatch: expected {event_type}, got {event.get('event_type')}")

        # Check timestamp format
        if "timestamp" in event:
            try:
                from datetime import datetime

                datetime.fromisoformat(event["timestamp"])
            except (ValueError, TypeError):
                errors.append("Invalid timestamp format")

        return errors


class ContractTest:
    """
    Base class for contract-based testing.
    Provides utilities for testing module contracts.
    """

    def assert_implements_protocol(self, implementation: Any, protocol: type):
        """Assert that implementation satisfies protocol contract."""
        errors = ContractValidator.validate_protocol_implementation(implementation, protocol)
        if errors:
            raise AssertionError(
                f"Contract violation for {protocol.__name__}:\n" + "\n".join(f"  - {e}" for e in errors)
            )

    def assert_valid_data_model(self, instance: Any, model_class: type):
        """Assert that instance is valid according to data model."""
        errors = ContractValidator.validate_data_model(instance, model_class)
        if errors:
            raise AssertionError(f"Invalid {model_class.__name__}:\n" + "\n".join(f"  - {e}" for e in errors))

    def assert_serializable(self, instance: Any, model_class: type):
        """Assert that instance can be serialized and restored."""
        errors = ContractValidator.validate_json_serialization(instance, model_class)
        if errors:
            raise AssertionError("Serialization contract violation:\n" + "\n".join(f"  - {e}" for e in errors))

    def assert_valid_api_response(self, response: dict[str, Any], schema: dict[str, Any]):
        """Assert API response matches schema."""
        errors = ContractValidator.validate_api_response(response, schema)
        if errors:
            raise AssertionError("API response contract violation:\n" + "\n".join(f"  - {e}" for e in errors))


class ContractMonitor:
    """
    Runtime contract monitoring for production systems.
    Logs contract violations without failing.
    """

    def __init__(self, logger=None):
        self.logger = logger or self._get_default_logger()
        self.violations = []

    def check_protocol(self, implementation: Any, protocol: type) -> bool:
        """Check protocol implementation, log violations."""
        errors = ContractValidator.validate_protocol_implementation(implementation, protocol)

        if errors:
            self.log_violation(f"Protocol {protocol.__name__}", implementation.__class__.__name__, errors)
            return False
        return True

    def check_data_model(self, instance: Any, model_class: type) -> bool:
        """Check data model validity, log violations."""
        errors = ContractValidator.validate_data_model(instance, model_class)

        if errors:
            self.log_violation(f"Data model {model_class.__name__}", str(instance)[:100], errors)
            return False
        return True

    def log_violation(self, contract: str, context: str, errors: list[str]):
        """Log contract violation."""
        violation = {"contract": contract, "context": context, "errors": errors}
        self.violations.append(violation)

        if self.logger:
            self.logger.warning(
                f"Contract violation in {contract} for {context}:\n" + "\n".join(f"  - {e}" for e in errors)
            )

    def get_report(self) -> dict[str, Any]:
        """Get contract violation report."""
        return {
            "total_violations": len(self.violations),
            "violations_by_contract": self._group_by_contract(),
            "recent_violations": self.violations[-10:],
        }

    def _group_by_contract(self) -> dict[str, int]:
        """Group violations by contract type."""
        grouped = {}
        for violation in self.violations:
            contract = violation["contract"]
            grouped[contract] = grouped.get(contract, 0) + 1
        return grouped

    def _get_default_logger(self):
        """Get default logger."""
        import logging

        return logging.getLogger(__name__)


# Helper functions


def _is_optional(type_hint) -> bool:
    """Check if type hint is Optional."""
    return hasattr(type_hint, "__origin__") and type_hint.__origin__ is Optional


def _validate_field(field_name: str, value: Any, schema: dict[str, Any]) -> list[str]:
    """Validate a single field against schema."""
    errors = []

    # Check type
    if "type" in schema:
        expected_type = schema["type"]
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        if expected_type in type_map:
            expected_python_type = type_map[expected_type]
            if not isinstance(value, expected_python_type):
                errors.append(
                    f"Field {field_name} has wrong type: expected {expected_type}, got {type(value).__name__}"
                )

    # Check enum values
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"Field {field_name} has invalid value: {value} not in {schema['enum']}")

    # Check string constraints
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"Field {field_name} too short: minimum {schema['minLength']}, got {len(value)}")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"Field {field_name} too long: maximum {schema['maxLength']}, got {len(value)}")

    # Check array constraints
    if isinstance(value, list) and "items" in schema:
        item_schema = schema["items"]
        for i, item in enumerate(value):
            errors.extend(_validate_field(f"{field_name}[{i}]", item, item_schema))

    return errors


# Export contract validation utilities
__all__ = ["ContractValidator", "ContractTest", "ContractMonitor"]
