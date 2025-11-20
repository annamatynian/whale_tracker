"""
Base abstractions for pipeline stages in the analysis system.
Defines contracts for loosely coupled architecture.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Dict, TypeVar, Generic
from dataclasses import dataclass

# Generic type for data flowing through pipeline
T = TypeVar('T')

@dataclass
class StageResult(Generic[T]):
    """Container for stage execution results with metadata."""
    data: T
    errors: List[str]
    metadata: Dict[str, Any]
    stage_name: str

class AnalysisStage(ABC, Generic[T]):
    """Abstract base class for all analysis pipeline stages."""
    
    def __init__(self, stage_name: str):
        self.stage_name = stage_name
        self.errors = []
        
    @abstractmethod
    async def execute(self, input_data: Any) -> StageResult[T]:
        """Execute the stage logic and return results."""
        pass
    
    def _create_result(self, data: T, metadata: Dict[str, Any] = None) -> StageResult[T]:
        """Helper to create standardized stage results."""
        return StageResult(
            data=data,
            errors=self.errors.copy(),
            metadata=metadata or {},
            stage_name=self.stage_name
        )
    
    def _add_error(self, error: str):
        """Add error to current stage execution."""
        self.errors.append(f"{self.stage_name}: {error}")

class Pipeline:
    """Orchestrates execution of analysis stages in sequence."""
    
    def __init__(self, stages: List[AnalysisStage]):
        self.stages = stages
        self.execution_log = []
        
    async def execute(self, initial_data: Any) -> List[StageResult]:
        """Execute all stages in sequence, passing data between them."""
        current_data = initial_data
        results = []
        
        for stage in self.stages:
            try:
                result = await stage.execute(current_data)
                results.append(result)
                current_data = result.data
                
                # Log execution for debugging
                self.execution_log.append({
                    'stage': stage.stage_name,
                    'input_size': len(current_data) if hasattr(current_data, '__len__') else 1,
                    'output_size': len(result.data) if hasattr(result.data, '__len__') else 1,
                    'errors': len(result.errors)
                })
                
            except Exception as e:
                # Stage failed completely - decide whether to continue or abort
                error_result = StageResult(
                    data=current_data,  # Pass through previous data
                    errors=[f"{stage.stage_name}: Critical failure - {str(e)}"],
                    metadata={'critical_failure': True},
                    stage_name=stage.stage_name
                )
                results.append(error_result)
                # Continue with previous data
                
        return results
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of pipeline execution for monitoring."""
        return {
            'total_stages': len(self.stages),
            'executed_stages': len(self.execution_log),
            'stage_details': self.execution_log
        }
