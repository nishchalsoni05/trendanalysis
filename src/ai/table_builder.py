
import pandas as pd

class TableBuilder:
    """
    AI-generated table formatter.
    """
    @staticmethod
    def to_markdown(data_list):
        if not data_list:
            return ""
        df = pd.DataFrame(data_list)
        return df.to_markdown(index=False)
