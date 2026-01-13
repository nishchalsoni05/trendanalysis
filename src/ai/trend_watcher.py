
from src.ai.data_gateway import DataGateway
from src.ai.insight_engine import InsightEngine

class TrendWatcher:
    """
    Continuous monitoring for trend shifts.
    """
    def __init__(self):
        self.gateway = DataGateway()
        self.ai = InsightEngine()
        
    def check_acceleration(self):
        """
        Check for acceleration in migration trends.
        """
        top_districts = self.gateway.get_top_moving_districts(50)
        # Logic to compare vs previous run would go here
        # For V1, we just identify current high accelerators
        return [d for d in top_districts if d.get('trend_type') == 'high_inflow']
