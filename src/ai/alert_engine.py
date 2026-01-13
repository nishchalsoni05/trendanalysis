
class AlertEngine:
    """
    Human-readable alert generation.
    """
    @staticmethod
    def format_alert(anomaly_record):
        """
        Convert anomaly record to readable string.
        """
        return f"⚠️ ALERT: {anomaly_record.get('district', 'Unknown')} showing unexpected deviation."
