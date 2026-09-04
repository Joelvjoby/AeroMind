"""Alert retrieval and acknowledgement."""

from app.models.alert import Alert


def get_alerts(db, is_read=None):
    """Return alerts newest first, optionally filtered by read state."""
    query = db.query(Alert)
    if is_read is not None:
        query = query.filter(Alert.is_read == is_read)
    return query.order_by(Alert.created_at.desc()).all()


def mark_read(db, alert_id):
    """Acknowledge an alert. Returns None if it does not exist.

    Marking an already-read alert is a no-op rather than an error, so the
    endpoint stays safe to retry.
    """
    alert = db.get(Alert, alert_id)
    if alert is None:
        return None

    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return alert
