# Principle #42 - Data Governance and Privacy Controls

## Plain-Language Definition

Data governance and privacy controls ensure that sensitive information is protected, access is restricted based on need, and privacy regulations are followed throughout the data lifecycle. This means implementing policies, technical controls, and processes that protect personal information and comply with laws like GDPR, CCPA, and HIPAA.

## Why This Matters for AI-First Development

When AI agents build and maintain systems, they interact with vast amounts of data—some of which may be highly sensitive. Without proper governance and privacy controls, AI agents could inadvertently expose personal information, violate regulations, or create security vulnerabilities. An AI agent generating a dashboard might accidentally include PII in logs. An agent deploying a database migration might fail to encrypt sensitive fields. An agent creating an API endpoint might expose data to unauthorized users.

AI-first development amplifies privacy risks in three critical ways:

1. **Automated data access**: AI agents often need broad access to understand and modify systems. Without fine-grained controls, an agent debugging a payment issue might read sensitive health records. Data governance ensures agents can only access data relevant to their task.

2. **Code generation at scale**: When AI agents generate data processing code, privacy violations can be embedded and replicated across many components. A single mistake in a data access pattern can propagate through hundreds of generated files. Strong governance patterns make privacy violations obvious during code review.

3. **Compliance as code**: Privacy regulations require documented data handling practices, retention policies, and audit trails. AI agents can enforce these requirements programmatically, but only if governance rules are encoded in the system. Without machine-readable privacy policies, AI agents can't verify compliance.

When data governance fails in AI-driven systems, the consequences are severe: massive fines for regulatory violations, loss of customer trust, data breaches affecting millions of users, and potential criminal liability. Strong privacy controls transform data governance from a manual checkbox exercise into an automated, enforceable system property.

## Implementation Approaches

### 1. **Data Classification Framework**

Implement a formal data classification system that categorizes information by sensitivity level:
- **Public**: No restrictions (product catalogs, blog posts)
- **Internal**: Employee access only (company policies, org charts)
- **Confidential**: Role-based access (financial records, customer lists)
- **Restricted**: Strict access controls (PII, PHI, payment data)

Tag all data fields, database columns, and API responses with classification levels. Use these tags to automatically enforce access controls, encryption requirements, and retention policies.

**When to use**: Essential for any system handling multiple types of sensitive data. Particularly critical in healthcare, finance, and e-commerce.

**Success looks like**: Every data element has a classification tag. Access control decisions are based on classification. Audit logs track who accessed what classification level.

### 2. **PII Detection and Protection**

Build automated systems to detect and protect personally identifiable information:
- **Static analysis**: Scan code for hardcoded PII or insecure PII handling
- **Runtime detection**: Identify PII in API requests/responses and apply protections
- **Data masking**: Automatically redact PII in logs, error messages, and non-production environments
- **Tokenization**: Replace sensitive data with non-sensitive tokens for most operations

**When to use**: Required for any system processing user data. Especially important when AI agents generate code that handles user information.

**Success looks like**: PII never appears in logs or error messages. Non-production environments contain masked data. Audit trails show where PII was accessed.

### 3. **Consent and Purpose Limitation**

Implement technical controls that enforce user consent and data usage purposes:
- **Consent management**: Track what users have consented to and enforce at data access time
- **Purpose binding**: Tag data operations with purposes (analytics, marketing, service delivery)
- **Automated enforcement**: Block operations that violate consent or purpose boundaries
- **Audit trails**: Log all data access with associated purposes and consent

**When to use**: Required for GDPR compliance. Critical for any system with marketing, analytics, or third-party data sharing.

**Success looks like**: Data cannot be accessed without a valid purpose. User consent revocations immediately block access. All data usage is auditable by purpose.

### 4. **Encryption and Access Control Layers**

Build defense-in-depth through multiple layers of protection:
- **Encryption at rest**: All sensitive data encrypted in databases and file systems
- **Encryption in transit**: TLS/SSL for all network communication
- **Field-level encryption**: Encrypt individual sensitive fields with separate keys
- **Role-based access control (RBAC)**: Grant access based on job function
- **Attribute-based access control (ABAC)**: Grant access based on context (time, location, device)

**When to use**: Fundamental requirement for any system with sensitive data. Layer multiple controls for defense-in-depth.

**Success looks like**: Data is encrypted everywhere. Access requires valid credentials and appropriate role. Audit logs track all access attempts.

### 5. **Data Retention and Deletion Policies**

Implement automated lifecycle management for data:
- **Retention policies**: Define how long different data types are kept
- **Automated deletion**: Purge data when retention periods expire
- **Right to erasure**: Honor user deletion requests (GDPR Article 17)
- **Backup management**: Apply retention policies to backups and archives
- **Cascading deletes**: Ensure related data is deleted together

**When to use**: Required for GDPR, CCPA, and most privacy regulations. Essential for managing data growth.

**Success looks like**: Old data is automatically purged. User deletion requests complete within regulatory timeframes. Backups respect retention policies.

### 6. **Privacy-Preserving Analytics**

Enable data analysis while protecting individual privacy:
- **Differential privacy**: Add statistical noise to prevent individual re-identification
- **Aggregation boundaries**: Only expose aggregated data above minimum thresholds
- **K-anonymity**: Ensure each record is indistinguishable from k-1 others
- **Synthetic data generation**: Create realistic but fake data for testing and analysis

**When to use**: Essential for analytics, ML training, and any data sharing scenarios. Required when AI agents need to analyze sensitive data.

**Success looks like**: Analytics provide insights without exposing individuals. Test environments use synthetic data. ML models can't reverse-engineer training data.

## Good Examples vs Bad Examples

### Example 1: Database Column Classification

**Good:**
```python
from enum import Enum
from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.ext.declarative import declarative_base

class DataClassification(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class ClassifiedColumn:
    """Wrapper that adds classification metadata to columns"""
    def __init__(self, column, classification: DataClassification):
        self.column = column
        self.classification = classification

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    # Classification enforced at schema level
    email = ClassifiedColumn(
        Column(String, unique=True, nullable=False),
        DataClassification.RESTRICTED
    )
    name = ClassifiedColumn(
        Column(String, nullable=False),
        DataClassification.CONFIDENTIAL
    )
    bio = ClassifiedColumn(
        Column(Text),
        DataClassification.PUBLIC
    )

def can_access_classification(user_role: str, classification: DataClassification) -> bool:
    """Enforce classification-based access control"""
    access_matrix = {
        "admin": [DataClassification.RESTRICTED, DataClassification.CONFIDENTIAL,
                  DataClassification.INTERNAL, DataClassification.PUBLIC],
        "employee": [DataClassification.CONFIDENTIAL, DataClassification.INTERNAL,
                     DataClassification.PUBLIC],
        "customer": [DataClassification.PUBLIC]
    }
    return classification in access_matrix.get(user_role, [])
```

**Bad:**
```python
from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    # No classification metadata - all data treated equally
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    ssn = Column(String)  # Extremely sensitive, but no protection indicator
    bio = Column(Text)

    # No enforcement of different access levels
```

**Why It Matters:** Data classification enables automated access control, audit logging, and compliance verification. Without classification, AI agents can't distinguish between public bios and restricted SSNs, leading to data leaks and compliance violations.

### Example 2: PII Detection and Masking in Logs

**Good:**
```python
import re
import logging
from typing import Any

class PIIFilter(logging.Filter):
    """Automatically redact PII from log messages"""

    # Patterns for common PII
    PATTERNS = {
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        'credit_card': re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'),
        'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
    }

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact PII from log messages"""
        message = str(record.msg)

        for pii_type, pattern in self.PATTERNS.items():
            if pii_type == 'email':
                message = pattern.sub('***@***.***', message)
            elif pii_type == 'ssn':
                message = pattern.sub('***-**-****', message)
            elif pii_type == 'credit_card':
                message = pattern.sub('****-****-****-****', message)
            elif pii_type == 'phone':
                message = pattern.sub('***-***-****', message)

        record.msg = message
        return True

# Configure logger with PII filter
logger = logging.getLogger(__name__)
logger.addFilter(PIIFilter())

# Usage example
def process_payment(email: str, card_number: str):
    logger.info(f"Processing payment for {email} with card {card_number}")
    # Logs: "Processing payment for ***@***.*** with card ****-****-****-****"
```

**Bad:**
```python
import logging

logger = logging.getLogger(__name__)

def process_payment(email: str, card_number: str):
    # PII directly in logs - regulatory violation and security risk
    logger.info(f"Processing payment for {email} with card {card_number}")
    # Logs: "Processing payment for alice@example.com with card 4532-1234-5678-9010"

    try:
        charge_card(card_number)
    except Exception as e:
        # Exception message may contain PII
        logger.error(f"Payment failed for {email}: {e}")
```

**Why It Matters:** Logs are often stored insecurely, shared with third parties, or accessed by support staff. PII in logs creates compliance violations and makes data breaches more damaging. Automated PII filtering prevents accidental exposure.

### Example 3: Consent-Based Data Access

**Good:**
```python
from enum import Enum
from typing import Set
from datetime import datetime

class DataPurpose(Enum):
    SERVICE_DELIVERY = "service_delivery"
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    THIRD_PARTY_SHARING = "third_party_sharing"

class ConsentManager:
    """Enforce user consent for data access"""

    def __init__(self, db_session):
        self.db = db_session

    def check_consent(self, user_id: str, purpose: DataPurpose) -> bool:
        """Verify user has consented to this data usage purpose"""
        consent = self.db.query(UserConsent).filter_by(
            user_id=user_id,
            purpose=purpose.value,
            is_active=True
        ).first()

        if not consent:
            raise ConsentViolation(
                f"User {user_id} has not consented to {purpose.value}"
            )

        # Log the access with purpose
        self.db.add(DataAccessLog(
            user_id=user_id,
            purpose=purpose.value,
            accessed_at=datetime.utcnow()
        ))

        return True

class ConsentViolation(Exception):
    """Raised when attempting to access data without consent"""
    pass

# Usage in API
def get_user_for_marketing(user_id: str, consent_mgr: ConsentManager):
    # Consent check enforced before data access
    consent_mgr.check_consent(user_id, DataPurpose.MARKETING)

    user = db.query(User).get(user_id)
    return user
```

**Bad:**
```python
# No consent checking - violates GDPR and user privacy
def get_user_for_marketing(user_id: str):
    # Directly access user data without checking consent
    user = db.query(User).get(user_id)

    # Use data for marketing regardless of user preferences
    send_marketing_email(user.email)

    # No audit trail of data usage
    return user

def get_user_for_analytics(user_id: str):
    # Same data access for different purpose - no differentiation
    user = db.query(User).get(user_id)
    track_user_behavior(user)
    return user
```

**Why It Matters:** GDPR requires explicit consent for different data usage purposes and the ability to revoke consent. Without technical enforcement, consent becomes a legal fiction. Consent-based access control makes privacy compliance verifiable.

### Example 4: Field-Level Encryption with Key Management

**Good:**
```python
from cryptography.fernet import Fernet
from typing import Optional
import os

class FieldEncryption:
    """Handle field-level encryption for sensitive data"""

    def __init__(self):
        # Keys stored in secure key management system, not code
        self.key = os.environ.get('FIELD_ENCRYPTION_KEY')
        if not self.key:
            raise ValueError("FIELD_ENCRYPTION_KEY not configured")
        self.cipher = Fernet(self.key.encode())

    def encrypt(self, plaintext: str) -> str:
        """Encrypt sensitive field"""
        if not plaintext:
            return ""
        encrypted = self.cipher.encrypt(plaintext.encode())
        return encrypted.decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt sensitive field"""
        if not ciphertext:
            return ""
        decrypted = self.cipher.decrypt(ciphertext.encode())
        return decrypted.decode()

class EncryptedColumn:
    """SQLAlchemy column wrapper with automatic encryption"""

    def __init__(self, column_type):
        self.column_type = column_type
        self.encryptor = FieldEncryption()

    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """Encrypt on write"""
        if value is None:
            return None
        return self.encryptor.encrypt(value)

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Decrypt on read"""
        if value is None:
            return None
        return self.encryptor.decrypt(value)

# Usage in model
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String)  # Less sensitive, not encrypted
    ssn = Column(EncryptedColumn(String))  # Encrypted at field level
    credit_card = Column(EncryptedColumn(String))  # Encrypted separately

    # Even with database access, SSN and credit card are encrypted
```

**Bad:**
```python
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String)
    ssn = Column(String)  # Stored in plaintext - anyone with DB access can read
    credit_card = Column(String)  # Major security violation

    # If database is compromised, all sensitive data is exposed

# Manual encryption is error-prone
def create_user(email: str, ssn: str):
    # Developer must remember to encrypt - easy to forget
    user = User(email=email, ssn=ssn)  # Oops, forgot to encrypt!
    db.add(user)
```

**Why It Matters:** Database breaches are common. Unencrypted sensitive data in databases violates PCI DSS, HIPAA, and many other regulations. Field-level encryption with automatic handling prevents developers from accidentally storing sensitive data in plaintext.

### Example 5: Automated Data Retention and Deletion

**Good:**
```python
from datetime import datetime, timedelta
from enum import Enum

class RetentionPolicy(Enum):
    """Standard retention periods by data type"""
    USER_ACTIVITY = timedelta(days=365)  # 1 year
    ANALYTICS_DATA = timedelta(days=90)  # 3 months
    AUDIT_LOGS = timedelta(days=2555)  # 7 years (compliance requirement)
    TEMPORARY_DATA = timedelta(days=7)  # 1 week

class DataRetentionManager:
    """Enforce automated data retention and deletion"""

    def __init__(self, db_session):
        self.db = db_session

    def apply_retention_policy(self, table_name: str, policy: RetentionPolicy):
        """Delete data older than retention period"""
        cutoff_date = datetime.utcnow() - policy.value

        # Log retention action for audit
        self.db.add(RetentionLog(
            table_name=table_name,
            policy=policy.name,
            cutoff_date=cutoff_date,
            executed_at=datetime.utcnow()
        ))

        # Execute deletion
        deleted_count = self.db.query(table_name).filter(
            table_name.created_at < cutoff_date
        ).delete()

        self.db.commit()
        return deleted_count

    def process_user_deletion_request(self, user_id: str):
        """Handle GDPR right to erasure"""
        # Log the deletion request
        self.db.add(DeletionRequest(
            user_id=user_id,
            requested_at=datetime.utcnow(),
            status="processing"
        ))

        # Delete user and all related data
        self.db.query(UserActivity).filter_by(user_id=user_id).delete()
        self.db.query(UserPreferences).filter_by(user_id=user_id).delete()
        self.db.query(User).filter_by(id=user_id).delete()

        # Mark deletion complete
        self.db.query(DeletionRequest).filter_by(user_id=user_id).update({
            "status": "completed",
            "completed_at": datetime.utcnow()
        })

        self.db.commit()

# Scheduled task runs daily
def daily_retention_cleanup():
    manager = DataRetentionManager(db.session)
    manager.apply_retention_policy(UserActivity, RetentionPolicy.USER_ACTIVITY)
    manager.apply_retention_policy(AnalyticsEvent, RetentionPolicy.ANALYTICS_DATA)
```

**Bad:**
```python
# No retention policy - data accumulates forever
class UserActivity(Base):
    __tablename__ = 'user_activity'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    activity_type = Column(String)
    created_at = Column(DateTime)
    # No deletion logic - grows indefinitely

# Manual deletion requests - error-prone and slow
def delete_user(user_id: str):
    # Only deletes user table, orphans related data
    db.query(User).filter_by(id=user_id).delete()
    # Forgot to delete UserActivity, UserPreferences, etc.

    # No audit trail of deletion
    # No verification that deletion completed
    db.commit()
```

**Why It Matters:** GDPR requires data minimization and timely deletion. Unlimited data retention increases storage costs, security risks, and compliance violations. Automated retention policies with audit trails ensure compliance and reduce risk.

## Related Principles

- **[Principle #38 - Access Control and Compliance as First-Class](38-compliance-as-code.md)** - Data governance policies should be encoded and automatically validated, enabling AI agents to verify compliance

- **[Principle #35 - Least-Privilege Automation with Scoped Permissions](../technology/35-security-first-api-design.md)** - Privacy controls must be enforced at the API layer, ensuring all data access goes through proper authorization

- **[Principle #36 - Dependency Pinning and Security Scanning](36-audit-trails-everything.md)** - Comprehensive audit logging is essential for demonstrating privacy compliance and investigating breaches

- **[Principle #14 - Context Management as Discipline](../process/14-version-control-everything.md)** - Privacy policies and data governance rules should be versioned to track changes and maintain compliance history

- **[Principle #19 - Cost and Token Budgeting](../process/19-documentation-lives-with-code.md)** - Data handling practices should be documented alongside code to ensure developers understand privacy requirements

- **[Principle #43 - Model Lifecycle Management](43-explainability-requirements.md)** - AI systems processing personal data must be explainable to comply with GDPR's right to explanation

## Common Pitfalls

1. **Treating All Data Equally**: Applying the same security controls to public and restricted data wastes resources and creates a false sense of security.
   - Example: Encrypting public product descriptions while leaving SSNs in plaintext logs.
   - Impact: Misallocated security effort, compliance violations where it matters most, inefficient resource usage.

2. **PII in Error Messages and Stack Traces**: Debugging information often leaks sensitive data into logs, monitoring systems, and error reporting tools.
   - Example: `ValueError: Invalid email format for alice@example.com` in production logs.
   - Impact: PII exposed to developers, support staff, and third-party monitoring services. GDPR violation.

3. **Consent Collected But Not Enforced**: Many systems ask for consent but don't actually check it before using data.
   - Example: Marketing opt-out checkbox that doesn't prevent marketing emails from being sent.
   - Impact: Privacy violations, user distrust, regulatory fines, reputational damage.

4. **Backup and Archive Blindness**: Data is deleted from production databases but remains in backups, snapshots, and archives indefinitely.
   - Example: User exercises right to erasure, but their data persists in daily backups for years.
   - Impact: Incomplete compliance with deletion requests, increased breach exposure, storage costs.

5. **Third-Party Data Sharing Without Safeguards**: Sending data to analytics, monitoring, or integration partners without data protection agreements or technical controls.
   - Example: Sending full user records to analytics service that doesn't need PII.
   - Impact: Data processor violations under GDPR, expanded breach surface, liability for partner failures.

6. **Development and Testing with Production Data**: Using real user data in non-production environments exposes it to developers and lower security controls.
   - Example: Copying production database to staging environment for debugging.
   - Impact: PII exposed to unauthorized users, compliance violations, increased breach risk.

7. **Missing Data Breach Response Plan**: Not having automated detection and response procedures for data breaches.
   - Example: Discovering a breach weeks later through customer complaints rather than monitoring.
   - Impact: Delayed breach notification (GDPR requires 72 hours), larger breach impact, regulatory penalties.

## Tools & Frameworks

### Data Classification and Discovery
- **AWS Macie**: Automated PII discovery and classification in S3 buckets using ML
- **Microsoft Purview**: Enterprise data governance with automated classification and sensitivity labeling
- **Google Cloud DLP API**: Detect and redact PII in text, images, and structured data

### Encryption and Key Management
- **HashiCorp Vault**: Centralized secrets management with dynamic encryption keys and audit logs
- **AWS KMS**: Managed encryption key service with automatic rotation and CloudTrail integration
- **Azure Key Vault**: Secure storage for encryption keys, certificates, and secrets with RBAC
- **Google Cloud KMS**: Multi-region encryption key management with automatic rotation

### Access Control and Identity
- **Auth0**: User authentication with consent management and privacy-aware session handling
- **Okta**: Identity and access management with fine-grained RBAC and ABAC
- **Keycloak**: Open-source identity management with consent screens and GDPR features
- **Casbin**: Access control library supporting RBAC, ABAC, and custom policies in code

### Consent Management Platforms
- **OneTrust**: Comprehensive privacy management with consent tracking and preference centers
- **TrustArc**: Privacy compliance automation with consent management and data mapping
- **Osano**: Privacy compliance software with consent management and data subject requests

### Privacy-Preserving Analytics
- **Differential Privacy Library (Google)**: Add statistical noise to datasets for privacy protection
- **PySyft**: Privacy-preserving ML with federated learning and encrypted computation
- **OpenMined**: Privacy-focused ML tools including encrypted ML and secure multi-party computation

### Data Retention and Deletion
- **Apache Airflow**: Workflow orchestration for automated data retention policies and cleanup jobs
- **Temporal**: Durable workflow engine for managing complex data lifecycle processes
- **Kubernetes CronJobs**: Scheduled jobs for automated data deletion and archival

## Implementation Checklist

When implementing this principle, ensure:

- [ ] All data fields are classified by sensitivity level (public, internal, confidential, restricted)
- [ ] PII detection is automated in logs, error messages, and monitoring systems
- [ ] Field-level encryption is applied to all restricted data with proper key management
- [ ] Access control is based on data classification and user roles/attributes
- [ ] User consent is tracked and enforced at data access time
- [ ] Data retention policies are defined and automatically enforced for all data types
- [ ] User deletion requests (right to erasure) are processed within regulatory timeframes
- [ ] All data access is logged with purpose, user, and timestamp for audit trails
- [ ] Non-production environments use masked, synthetic, or anonymized data
- [ ] Third-party data sharing includes data protection agreements and technical controls
- [ ] Backup and archive systems respect retention and deletion policies
- [ ] Data breach detection and response procedures are automated and tested

## Metadata

**Category**: Governance
**Principle Number**: 42
**Related Patterns**: Data Classification, Field-Level Encryption, Purpose-Based Access Control, Data Minimization, Privacy by Design
**Prerequisites**: Understanding of privacy regulations (GDPR, CCPA, HIPAA), encryption fundamentals, access control models
**Difficulty**: High
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0