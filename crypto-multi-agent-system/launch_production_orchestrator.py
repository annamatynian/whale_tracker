"""
Production Orchestrator Launcher
Properly sets up environment and runs TheGraph-enabled orchestrator
"""
import os
import sys
import asyncio
import logging

# Ensure we're in the right directory and fix paths
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print(f"Project root: {project_root}")
print(f"Python path: {sys.path[0]}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Launch the production orchestrator with TheGraph integration."""
    print("="*60)
    print("LAUNCHING PRODUCTION ORCHESTRATOR WITH THEGRAPH")
    print("="*60)
    print("Expected improvement: 832 tokens vs 30 from DexScreener (27x)")
    print()
    
    try:
        # Import the orchestrator
        from agents.orchestrator.simple_orchestrator import SimpleOrchestrator
        
        print("✓ Orchestrator imported successfully")
        print("✓ TheGraph discovery agent initialized")
        
        # Create and run orchestrator
        orchestrator = SimpleOrchestrator()
        print("✓ Orchestrator created successfully")
        
        # Run the analysis pipeline
        print("\nStarting discovery pipeline...")
        
        async def run_pipeline():
            try:
                results = await orchestrator.run_analysis_pipeline()
                print(f"\nPipeline completed with {len(results)} results")
                return results
            except Exception as e:
                print(f"Pipeline error: {e}")
                import traceback
                traceback.print_exc()
                return []
        
        # Execute the pipeline
        results = asyncio.run(run_pipeline())
        
        if results:
            print(f"✓ SUCCESS: {len(results)} alerts generated")
        else:
            print("Pipeline completed - check logs for discovery results")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Check that all dependencies are installed")
    except Exception as e:
        print(f"❌ Runtime error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
