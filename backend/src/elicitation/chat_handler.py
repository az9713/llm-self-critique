from src.llm.base import LLMRequest, LLMProvider
from src.llm.router import LLMRouter
from src.elicitation.state_machine import ElicitationState, ElicitationPhase
from src.elicitation.completeness import CompletenessChecker


class ElicitationChatHandler:
    """Handle elicitation chat messages and guide the conversation."""

    SYSTEM_PROMPT = """You are a helpful AI assistant that guides users through defining a planning domain.
Your goal is to collect enough information to generate a PDDL (Planning Domain Definition Language) specification.

Current conversation phase: {phase}
Information collected so far:
- Domain name: {domain_name}
- Objects: {objects}
- Predicates: {predicates}
- Actions: {actions}
- Initial state: {initial_state}
- Goal state: {goal_state}

Based on the current phase, help the user provide the missing information.
Be conversational and helpful. Ask clarifying questions if needed.
When extracting information, output structured data in this format at the end of your response:

[EXTRACTED]
type: objects|predicates|actions|initial_state|goal_state|domain_name
data: <the extracted data as JSON>
[/EXTRACTED]

Phase-specific guidance:
- INTRO: Welcome the user, understand what they want to plan, and extract the domain name
- OBJECTS: Help identify all objects/entities in the domain
- PREDICATES: Help identify properties and relationships between objects
- ACTIONS: Help define what actions can be performed
- INITIAL: Help define the starting state
- GOAL: Help define the desired end goal
- REVIEW: Summarize everything and confirm correctness"""

    PHASE_PROMPTS = {
        ElicitationPhase.INTRO: "Welcome! I'll help you create a planning domain. What would you like to plan?",
        ElicitationPhase.OBJECTS: "Now let's identify the objects or entities in your domain. What things exist in your planning scenario?",
        ElicitationPhase.PREDICATES: "Great! Now let's define the properties and relationships. What states or conditions can these objects have?",
        ElicitationPhase.ACTIONS: "Excellent! What actions or operations can be performed in your domain?",
        ElicitationPhase.INITIAL: "Now let's define your starting situation. What is the current state of things?",
        ElicitationPhase.GOAL: "Almost done! What is your desired end goal?",
        ElicitationPhase.REVIEW: "Let me summarize what we've collected. Does this look correct?",
        ElicitationPhase.COMPLETE: "Your domain is complete! I can now generate the PDDL specification.",
    }

    def __init__(self, llm_router: LLMRouter, provider: LLMProvider):
        self.router = llm_router
        self.provider = provider

    async def handle_message(
        self,
        user_message: str,
        state: ElicitationState,
    ) -> tuple[str, ElicitationState]:
        """
        Handle a user message and return the assistant response with updated state.
        """
        # Add user message to state
        state.add_message("user", user_message)

        # Build the system prompt with current context
        system_prompt = self._build_system_prompt(state)

        # Build conversation history for LLM
        messages = self._build_messages(state, system_prompt)

        # Get LLM response
        response = await self.router.complete(LLMRequest(
            prompt=messages,
            provider=self.provider,
            temperature=0.7,
        ))

        assistant_message = response.content

        # Extract any structured data from response
        state = self._extract_data(assistant_message, state)

        # Add assistant message to state
        state.add_message("assistant", assistant_message)

        # Check if we should transition to next phase
        state = self._check_phase_transition(state)

        return assistant_message, state

    def get_initial_message(self, state: ElicitationState) -> str:
        """Get the initial greeting message for a new conversation."""
        return self.PHASE_PROMPTS.get(state.phase, "Hello! How can I help you?")

    def _build_system_prompt(self, state: ElicitationState) -> str:
        """Build system prompt with current state context."""
        return self.SYSTEM_PROMPT.format(
            phase=state.phase.value,
            domain_name=state.domain_name or "Not set",
            objects=", ".join(state.objects) if state.objects else "None",
            predicates=", ".join(state.predicates) if state.predicates else "None",
            actions=str(state.actions) if state.actions else "None",
            initial_state=", ".join(state.initial_state) if state.initial_state else "None",
            goal_state=", ".join(state.goal_state) if state.goal_state else "None",
        )

    def _build_messages(self, state: ElicitationState, system_prompt: str) -> str:
        """Build the full prompt including conversation history."""
        prompt = f"System: {system_prompt}\n\n"

        # Add conversation history
        for msg in state.messages[-10:]:  # Last 10 messages for context
            role = msg["role"].capitalize()
            prompt += f"{role}: {msg['content']}\n\n"

        prompt += "Assistant:"
        return prompt

    def _extract_data(self, response: str, state: ElicitationState) -> ElicitationState:
        """Extract structured data from LLM response if present."""
        import json
        import re

        pattern = r'\[EXTRACTED\]\s*type:\s*(\w+)\s*data:\s*(.+?)\s*\[/EXTRACTED\]'
        matches = re.findall(pattern, response, re.DOTALL)

        for data_type, data_str in matches:
            try:
                data = json.loads(data_str.strip())

                if data_type == "domain_name" and isinstance(data, str):
                    state.domain_name = data
                elif data_type == "objects" and isinstance(data, list):
                    state.objects.extend(data)
                elif data_type == "predicates" and isinstance(data, list):
                    state.predicates.extend(data)
                elif data_type == "actions" and isinstance(data, list):
                    state.actions.extend(data)
                elif data_type == "initial_state" and isinstance(data, list):
                    state.initial_state.extend(data)
                elif data_type == "goal_state" and isinstance(data, list):
                    state.goal_state.extend(data)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract as simple value
                data_str = data_str.strip().strip('"').strip("'")
                if data_type == "domain_name":
                    state.domain_name = data_str

        return state

    def _check_phase_transition(self, state: ElicitationState) -> ElicitationState:
        """Check if we should move to the next phase based on completeness."""
        next_phase = CompletenessChecker.get_next_phase(state)

        if next_phase != state.phase:
            from src.elicitation.state_machine import ElicitationStateMachine
            sm = ElicitationStateMachine()
            if sm.can_transition(state, next_phase):
                state = sm.transition(state, next_phase)

        return state
