import asyncio
from dataclasses import dataclass, field

from src.llm.base import LLMRequest, LLMProvider
from src.llm.router import LLMRouter
from src.critique.parser import CritiqueParser
from src.critique.voting import VoteAggregator, VoteResult
from src.models.planning import Verdict


@dataclass
class PlanResult:
    plan: str
    status: str  # "valid", "max_iterations", "failed"
    iterations: int
    final_verdict: Verdict
    iteration_history: list[dict] = field(default_factory=list)


class SelfCritiqueOrchestrator:
    PLAN_PROMPT = """Given the domain definition:
{domain_pddl}

The problem to solve:
{problem_pddl}

{critique_history}

Generate a plan to solve this problem. Output only the numbered list of actions."""

    CRITIQUE_PROMPT = """Given the domain definition:
{domain_pddl}

So, for each action:
1. Take the action and its preconditions from the domain definition for the specific action.
2. Verify whether the preconditions are met for the action.
3. Apply the action and provide the resulting state.

The problem to solve:
{problem_pddl}

The suggested solution:
{plan}

Please carefully evaluate the plan. Verify each step as described above. Do not stop until each action is verified; please *do not* omit steps. Conclude with the assessment literally either with 'the plan is correct', 'the plan is wrong', or 'goal not reached'."""

    def __init__(
        self,
        llm_router: LLMRouter,
        provider: LLMProvider,
        max_iterations: int = 5,
        num_critique_samples: int = 5,
    ):
        self.router = llm_router
        self.provider = provider
        self.max_iterations = max_iterations
        self.num_critique_samples = num_critique_samples

    async def run(self, domain_pddl: str, problem_pddl: str) -> PlanResult:
        critique_history = ""
        iteration_history = []

        for iteration in range(1, self.max_iterations + 1):
            # Generate plan
            plan = await self._generate_plan(domain_pddl, problem_pddl, critique_history)

            # Run parallel critiques
            vote_result = await self._run_critiques(domain_pddl, problem_pddl, plan)

            iteration_history.append({
                "iteration": iteration,
                "plan": plan,
                "vote_result": vote_result,
            })

            if vote_result.majority_verdict == Verdict.CORRECT:
                return PlanResult(
                    plan=plan,
                    status="valid",
                    iterations=iteration,
                    final_verdict=Verdict.CORRECT,
                    iteration_history=iteration_history,
                )

            # Append critique for next iteration
            critique_history = f"\nPrevious attempt failed with: {vote_result.best_critique.error_reason}\nPlease fix this issue."

        return PlanResult(
            plan=plan,
            status="max_iterations",
            iterations=self.max_iterations,
            final_verdict=vote_result.majority_verdict,
            iteration_history=iteration_history,
        )

    async def _generate_plan(self, domain: str, problem: str, history: str) -> str:
        prompt = self.PLAN_PROMPT.format(
            domain_pddl=domain,
            problem_pddl=problem,
            critique_history=history,
        )

        response = await self.router.complete(LLMRequest(
            prompt=prompt,
            provider=self.provider,
        ))

        return response.content

    async def _run_critiques(self, domain: str, problem: str, plan: str) -> VoteResult:
        prompt = self.CRITIQUE_PROMPT.format(
            domain_pddl=domain,
            problem_pddl=problem,
            plan=plan,
        )

        tasks = [
            self.router.complete(LLMRequest(prompt=prompt, provider=self.provider))
            for _ in range(self.num_critique_samples)
        ]

        responses = await asyncio.gather(*tasks)
        results = [CritiqueParser.parse(r.content) for r in responses]

        return VoteAggregator.aggregate(results)
