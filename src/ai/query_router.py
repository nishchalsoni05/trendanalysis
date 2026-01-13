
from src.ai.insight_engine import InsightEngine
from src.ai.data_gateway import DataGateway

class QueryRouter:
    """
    Maps user question -> data operation.
    """
    def __init__(self):
        self.ai = InsightEngine()
        self.gateway = DataGateway()
        
    def route(self, user_query):
        # In a complex system, this would parse intent
        # For now, it passes through to InsightEngine's internal gather logic
        return self.ai.ask(user_query)
