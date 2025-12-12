"""
Agent Scheduler - Runs agents on schedule
Can be deployed as Supabase Edge Function, AWS Lambda, or cron job
"""

import asyncio
import logging
from typing import List
from datetime import datetime

from agents.monitoring_agent import MonitoringAgent
from agents.forecast_agent import ForecastAgent
from agents.report_agent import ReportAgent
from agents.memory_agent import MemoryAgent
from utils.supabase_admin import get_supabase_admin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

supabase = get_supabase_admin()


async def run_agent_for_all_workspaces(agent_class, agent_name: str):
    """Run an agent for all active workspaces"""
    logger.info(f"Running {agent_name} for all workspaces")
    
    try:
        # Get all workspaces (you may want to add pagination)
        # Assuming you have a workspaces table
        response = supabase.table('workspaces').select('id').execute()
        
        if not response.data:
            logger.warning("No workspaces found")
            return
        
        workspace_ids = [w['id'] for w in response.data]
        logger.info(f"Found {len(workspace_ids)} workspaces")
        
        # Run agent for each workspace
        agent = agent_class()
        
        for workspace_id in workspace_ids:
            try:
                await agent.run(workspace_id)
                logger.info(f"Completed {agent_name} for workspace {workspace_id}")
            except Exception as e:
                logger.error(f"Failed to run {agent_name} for workspace {workspace_id}: {e}")
        
    except Exception as e:
        logger.error(f"Failed to run {agent_name}: {e}")


async def run_monitoring():
    """Run MonitoringAgent - every 1-6 hours"""
    await run_agent_for_all_workspaces(MonitoringAgent, "MonitoringAgent")


async def run_forecast():
    """Run ForecastAgent - daily"""
    await run_agent_for_all_workspaces(ForecastAgent, "ForecastAgent")


async def run_reports():
    """Run ReportAgent - weekly"""
    # Only send reports if user has weekly_reports enabled
    await run_agent_for_all_workspaces(ReportAgent, "ReportAgent")


async def run_memory():
    """Run MemoryAgent - nightly"""
    await run_agent_for_all_workspaces(MemoryAgent, "MemoryAgent")


# Main scheduler function for deployment
async def scheduled_handler(event, context):
    """
    Main handler for scheduled function
    Event will contain which agent to run
    
    Example event:
    {
        "agent": "monitoring|forecast|report|memory"
    }
    """
    agent_type = event.get('agent', 'monitoring')
    
    logger.info(f"Scheduled execution started: {agent_type} at {datetime.now()}")
    
    if agent_type == 'monitoring':
        await run_monitoring()
    elif agent_type == 'forecast':
        await run_forecast()
    elif agent_type == 'report':
        await run_reports()
    elif agent_type == 'memory':
        await run_memory()
    else:
        logger.error(f"Unknown agent type: {agent_type}")
        return {
            'statusCode': 400,
            'body': f'Unknown agent type: {agent_type}'
        }
    
    logger.info(f"Scheduled execution completed: {agent_type}")
    
    return {
        'statusCode': 200,
        'body': f'Successfully ran {agent_type} agent'
    }


# For local testing/debugging
if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) > 1:
            agent = sys.argv[1]
            await scheduled_handler({'agent': agent}, {})
        else:
            print("Usage: python scheduler.py [monitoring|forecast|report|memory]")
            print("\nRunning all agents as test...")
            await run_monitoring()
            await run_forecast()
            await run_reports()
            await run_memory()
    
    asyncio.run(main())
