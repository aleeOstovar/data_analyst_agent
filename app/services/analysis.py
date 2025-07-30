import os
import base64
from typing import Dict, Any, Optional
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import aiofiles

from ..core.agent import DataAnalysisAgent
from ..config.settings import UPLOAD_DIR

class AnalysisService:
    def __init__(self):
        self.agent = DataAnalysisAgent()
        
    async def process_analysis_request(self, 
                                     query: str, 
                                     file_path: Optional[str] = None,
                                     code: Optional[str] = None,
                                     thread_id: str = "default") -> Dict[str, Any]:
        """Process an analysis request asynchronously"""
        
        # Prepare the query with file path information if provided
        full_query = query
        if file_path:
            abs_file_path = os.path.join(UPLOAD_DIR, os.path.basename(file_path))
            # Use aiofiles for async file checking
            if await self._file_exists(abs_file_path):
                full_query = f"Analyze the data from this file: {abs_file_path}\n\n{query}"
        
        # Add custom code if provided
        if code:
            full_query = f"{full_query}\n\nUse this code as a starting point:\n```python\n{code}\n```"
        
        # Run the agent analysis
        response = await self.agent.analyze(full_query, thread_id)
        
        # Extract the result
        messages = response.get("messages", [])
        last_message = messages[-1] if messages else None
        content = last_message.content if last_message else ""
        
        return {
            "result": content,
            "messages": [{
                "role": msg.type,
                "content": msg.content
            } for msg in messages]
        }
    
    async def _file_exists(self, file_path: str) -> bool:
        """Check if file exists asynchronously"""
        try:
            async with aiofiles.open(file_path, 'r'):
                return True
        except FileNotFoundError:
            return False
        except:
            return os.path.exists(file_path)  # Fallback
    
    def generate_plot_base64(self, plt_figure):
        """Convert a matplotlib figure to base64 encoded string"""
        buf = BytesIO()
        plt_figure.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        return img_str