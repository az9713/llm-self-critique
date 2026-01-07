import json
import asyncio
from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from src.database import async_session_maker
from src.models import PlanningSession, PlanIteration
from src.models.planning import SessionStatus, Verdict
from src.critique.orchestrator import SelfCritiqueOrchestrator
from src.critique.parser import CritiqueParser
from src.critique.voting import VoteAggregator
from src.llm.base import LLMRequest, LLMResponse, LLMProvider
from src.llm.router import LLMRouter

router = APIRouter()


class StreamingOrchestrator:
    """Self-critique orchestrator that streams progress via WebSocket."""

    def __init__(
        self,
        websocket: WebSocket,
        llm_router: LLMRouter,
        provider: LLMProvider,
        max_iterations: int = 5,
        num_critique_samples: int = 5,
    ):
        self.ws = websocket
        self.router = llm_router
        self.provider = provider
        self.max_iterations = max_iterations
        self.num_critique_samples = num_critique_samples

    async def send_update(self, event_type: str, data: dict):
        """Send a progress update via WebSocket."""
        await self.ws.send_json({
            "type": event_type,
            "data": data,
        })

    async def run(self, domain_pddl: str, problem_pddl: str) -> dict:
        """Run the self-critique loop with streaming updates."""
        critique_history = ""

        await self.send_update("started", {
            "max_iterations": self.max_iterations,
            "num_critique_samples": self.num_critique_samples,
        })

        for iteration in range(1, self.max_iterations + 1):
            await self.send_update("iteration_started", {"iteration": iteration})

            # Generate plan
            await self.send_update("generating_plan", {"iteration": iteration})
            plan = await self._generate_plan(domain_pddl, problem_pddl, critique_history)
            await self.send_update("plan_generated", {
                "iteration": iteration,
                "plan": plan,
            })

            # Run critiques
            await self.send_update("critiquing", {
                "iteration": iteration,
                "num_samples": self.num_critique_samples,
            })
            vote_result = await self._run_critiques_streaming(domain_pddl, problem_pddl, plan, iteration)

            await self.send_update("critique_complete", {
                "iteration": iteration,
                "verdict": vote_result.majority_verdict.value,
                "confidence": vote_result.confidence,
                "breakdown": {k.value: v for k, v in vote_result.breakdown.items()},
            })

            if vote_result.majority_verdict == Verdict.CORRECT:
                await self.send_update("completed", {
                    "status": "valid",
                    "iterations": iteration,
                    "plan": plan,
                    "verdict": vote_result.majority_verdict.value,
                })
                return {
                    "status": "valid",
                    "plan": plan,
                    "iterations": iteration,
                    "verdict": vote_result.majority_verdict,
                }

            # Prepare for next iteration
            critique_history = f"\nPrevious attempt failed: {vote_result.best_critique.error_reason}\nPlease fix."
            await self.send_update("iteration_complete", {
                "iteration": iteration,
                "verdict": vote_result.majority_verdict.value,
                "error": vote_result.best_critique.error_reason,
            })

        await self.send_update("completed", {
            "status": "max_iterations",
            "iterations": self.max_iterations,
            "plan": plan,
            "verdict": vote_result.majority_verdict.value,
        })

        return {
            "status": "max_iterations",
            "plan": plan,
            "iterations": self.max_iterations,
            "verdict": vote_result.majority_verdict,
        }

    async def _generate_plan(self, domain: str, problem: str, history: str) -> str:
        prompt = f"""Given the domain definition:
{domain}

The problem to solve:
{problem}

{history}

Generate a plan to solve this problem. Output only the numbered list of actions."""

        response = await self.router.complete(LLMRequest(
            prompt=prompt,
            provider=self.provider,
        ))
        return response.content

    async def _run_critiques_streaming(self, domain: str, problem: str, plan: str, iteration: int):
        prompt = f"""Given the domain definition:
{domain}

The problem to solve:
{problem}

The suggested solution:
{plan}

Please carefully evaluate the plan. Conclude with 'the plan is correct', 'the plan is wrong', or 'goal not reached'."""

        tasks = [
            self._run_single_critique(prompt, iteration, i)
            for i in range(self.num_critique_samples)
        ]

        results = await asyncio.gather(*tasks)
        return VoteAggregator.aggregate(results)

    async def _run_single_critique(self, prompt: str, iteration: int, sample_idx: int):
        response = await self.router.complete(LLMRequest(
            prompt=prompt,
            provider=self.provider,
        ))

        result = CritiqueParser.parse(response.content)

        await self.send_update("critique_sample", {
            "iteration": iteration,
            "sample": sample_idx + 1,
            "verdict": result.verdict.value,
        })

        return result


@router.websocket("/ws/plan/{session_id}")
async def plan_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for streaming plan generation."""
    await websocket.accept()

    try:
        # Wait for the start message with PDDL definitions
        data = await websocket.receive_json()

        if data.get("action") != "start":
            await websocket.send_json({"type": "error", "message": "Expected 'start' action"})
            return

        domain_pddl = data.get("domain_pddl")
        problem_pddl = data.get("problem_pddl")

        if not domain_pddl or not problem_pddl:
            await websocket.send_json({"type": "error", "message": "Missing PDDL definitions"})
            return

        # Update session status
        async with async_session_maker() as db:
            result = await db.execute(
                select(PlanningSession).where(PlanningSession.id == UUID(session_id))
            )
            session = result.scalar_one_or_none()

            if not session:
                await websocket.send_json({"type": "error", "message": "Session not found"})
                return

            session.status = SessionStatus.PLANNING
            session.domain_pddl = domain_pddl
            session.problem_pddl = problem_pddl
            await db.commit()

        # Run streaming orchestrator
        # In production, get API keys from config
        try:
            llm_router = LLMRouter(api_keys={"claude": "mock-key"})
            orchestrator = StreamingOrchestrator(
                websocket=websocket,
                llm_router=llm_router,
                provider=LLMProvider.CLAUDE,
                max_iterations=data.get("max_iterations", 5),
                num_critique_samples=data.get("num_critique_samples", 5),
            )

            result = await orchestrator.run(domain_pddl, problem_pddl)

            # Save result to database
            async with async_session_maker() as db:
                result_db = await db.execute(
                    select(PlanningSession).where(PlanningSession.id == UUID(session_id))
                )
                session = result_db.scalar_one()
                session.status = SessionStatus.COMPLETE if result["status"] == "valid" else SessionStatus.FAILED
                session.current_plan = result["plan"]
                session.final_verdict = result["verdict"]
                session.iteration_count = result["iterations"]
                await db.commit()

        except ValueError as e:
            await websocket.send_json({"type": "error", "message": str(e)})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
