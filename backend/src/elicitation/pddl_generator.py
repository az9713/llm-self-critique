from src.llm.base import LLMRequest, LLMProvider
from src.llm.router import LLMRouter
from src.elicitation.state_machine import ElicitationState


class PDDLGenerator:
    """Generate PDDL domain and problem definitions from elicitation state."""

    DOMAIN_PROMPT = """You are an expert in PDDL (Planning Domain Definition Language).
Generate a valid PDDL domain definition based on the following information:

Domain Name: {domain_name}
Description: {description}

Objects/Types: {objects}

Predicates (properties and relationships): {predicates}

Actions:
{actions}

Generate ONLY the PDDL domain definition. Use proper PDDL syntax with:
- (:requirements :strips :typing) if types are used
- (:types ...) section if needed
- (:predicates ...) section
- (:action ...) sections with :parameters, :precondition, and :effect

Output ONLY valid PDDL code, no explanations."""

    PROBLEM_PROMPT = """You are an expert in PDDL (Planning Domain Definition Language).
Generate a valid PDDL problem definition based on the following:

Domain Definition:
{domain_pddl}

Objects: {objects}

Initial State:
{initial_state}

Goal State:
{goal_state}

Generate ONLY the PDDL problem definition with:
- (:domain ...) referencing the domain
- (:objects ...) listing all objects with types
- (:init ...) with the initial state facts
- (:goal ...) with the goal conditions

Output ONLY valid PDDL code, no explanations."""

    def __init__(self, llm_router: LLMRouter, provider: LLMProvider):
        self.router = llm_router
        self.provider = provider

    def _build_domain_prompt(self, state: ElicitationState) -> str:
        """Build the prompt for domain generation."""
        actions_str = ""
        for action in state.actions:
            actions_str += f"\n- {action['name']}"
            if action.get('params'):
                actions_str += f"\n  Parameters: {', '.join(action['params'])}"
            if action.get('preconditions'):
                actions_str += f"\n  Preconditions: {', '.join(action['preconditions'])}"
            if action.get('effects'):
                actions_str += f"\n  Effects: {', '.join(action['effects'])}"

        return self.DOMAIN_PROMPT.format(
            domain_name=state.domain_name,
            description=state.domain_description or "No description provided",
            objects=", ".join(state.objects),
            predicates=", ".join(state.predicates),
            actions=actions_str,
        )

    def _build_problem_prompt(self, state: ElicitationState, domain_pddl: str) -> str:
        """Build the prompt for problem generation."""
        return self.PROBLEM_PROMPT.format(
            domain_pddl=domain_pddl,
            objects=", ".join(state.objects),
            initial_state="\n".join(f"- {s}" for s in state.initial_state),
            goal_state="\n".join(f"- {g}" for g in state.goal_state),
        )

    async def generate_domain(self, state: ElicitationState) -> str:
        """Generate PDDL domain definition from elicitation state."""
        prompt = self._build_domain_prompt(state)

        response = await self.router.complete(LLMRequest(
            prompt=prompt,
            provider=self.provider,
            temperature=0.3,  # Lower temperature for more deterministic output
        ))

        return self._extract_pddl(response.content)

    async def generate_problem(self, state: ElicitationState, domain_pddl: str) -> str:
        """Generate PDDL problem definition from elicitation state."""
        prompt = self._build_problem_prompt(state, domain_pddl)

        response = await self.router.complete(LLMRequest(
            prompt=prompt,
            provider=self.provider,
            temperature=0.3,
        ))

        return self._extract_pddl(response.content)

    async def generate_full(self, state: ElicitationState) -> tuple[str, str]:
        """Generate both domain and problem PDDL definitions."""
        domain_pddl = await self.generate_domain(state)
        problem_pddl = await self.generate_problem(state, domain_pddl)
        return domain_pddl, problem_pddl

    def _extract_pddl(self, content: str) -> str:
        """Extract PDDL code from LLM response, handling markdown code blocks."""
        content = content.strip()

        # Handle markdown code blocks
        if "```" in content:
            lines = content.split("\n")
            in_code_block = False
            pddl_lines = []

            for line in lines:
                if line.startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    pddl_lines.append(line)

            if pddl_lines:
                return "\n".join(pddl_lines).strip()

        return content
