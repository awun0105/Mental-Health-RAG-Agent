from enum import Enum


class AuthProvider(str, Enum):
    """Authentication providers supported by the application."""

    LOCAL = "local"
    GOOGLE = "google"


class UserRole(str, Enum):
    """Application user roles."""

    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"


class SessionStatus(str, Enum):
    """Patient chat session lifecycle statuses."""

    ACTIVE = "active"
    CLOSED = "closed"
    TIMEOUT = "timeout"


class MessageRole(str, Enum):
    """Roles for messages stored in chat_messages."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SafetySeverity(str, Enum):
    """Safety severity levels for patient-facing chat messages."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskSeverity(str, Enum):
    """Stress/risk severity categories."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditAction(str, Enum):
    """Audit log actions for sensitive user, admin, and AI workflow events."""

    USER_REGISTERED = "user_registered"
    USER_LOGIN = "user_login"

    CONSENT_ACCEPTED = "consent_accepted"

    SESSION_STARTED = "session_started"
    SESSION_CLOSED = "session_closed"

    CRISIS_WORKFLOW_ACTIVATED = "crisis_workflow_activated"

    CLINICAL_PROFILE_GENERATED = "clinical_profile_generated"
    DOCTOR_VIEWED_PROFILE = "doctor_viewed_profile"

    DIFFERENTIAL_DIAGNOSIS_GENERATED = "differential_diagnosis_generated"
    DOCTOR_COPILOT_QUERY = "doctor_copilot_query"

    DOCTOR_ASSIGNMENT_CREATED = "doctor_assignment_created"
    ASSIGNMENT_DEACTIVATED = "assignment_deactivated"

    ADMIN_CONFIG_CHANGE = "admin_config_change"
