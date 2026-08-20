from src.resources.models import ResourceAuditLog


def test_resource_audit_log_uses_user_naming():
    assert "user_id" in ResourceAuditLog.__table__.columns
    assert "actor_id" not in ResourceAuditLog.__table__.columns
    assert "user" in ResourceAuditLog.__mapper__.relationships
    assert "actor" not in ResourceAuditLog.__mapper__.relationships
