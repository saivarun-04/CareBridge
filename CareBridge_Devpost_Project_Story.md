## Inspiration

Many older adults live independently while their family members cannot always be available to check on them. A missed response does not necessarily mean something is wrong, but repeated changes in routines or unanswered check-ins can sometimes deserve attention.

We wanted to build something that could help families stay connected without turning elderly care into constant monitoring.

This led us to **CareBridge** — an adaptive AI care and check-in agent that understands individual communication preferences, manages personalized check-ins, recognizes meaningful patterns, and involves caregivers when appropriate.

## What it does

CareBridge provides three core capabilities:

- **Adaptive Communication:** CareBridge remembers user preferences and interaction patterns and adapts communication accordingly, including preferred name, check-in timing, prompt length, repetition, and interaction style.

- **Intelligent Check-Ins:** The system manages scheduled check-ins for user-defined routines such as meals and other everyday wellbeing activities. Responses are recorded to build useful context over time.

- **Tiered Escalation:** A single missed check-in does not immediately trigger an alert. CareBridge can re-prompt the user, evaluate surrounding context and previous patterns, and notify a caregiver when repeated or meaningful deviations warrant attention.

The system is designed as a **wellbeing-awareness and caregiver coordination tool**, not a medical diagnostic or emergency-response system.

## How we built it

CareBridge uses an agentic architecture built around the Amazon ecosystem.

- **Alexa+** — conversational agent experience
- **MCP with Streamable HTTP** — controlled agent-to-tool communication
- **Amazon Bedrock + Strands SDK** — agent reasoning and communication adaptation
- **AWS Lambda** — backend execution
- **Amazon DynamoDB** — user profiles, routines, preferences, and check-in history
- **Amazon EventBridge Scheduler** — scheduled check-ins
- **Amazon SNS/SES** — caregiver notifications
- **Python** — backend and agent implementation

The MCP server exposes focused tools including:

```text
get_routine
log_checkin
adapt_style
get_pattern_summary
notify_caregiver
snooze_or_ack
```

We also designed two interfaces: a simplified elder-facing experience and a caregiver dashboard for viewing check-in history, patterns, and notifications.

## Challenges we ran into

One of our biggest challenges was designing proactive check-ins around an agent architecture. MCP tools are invoked by the agent rather than independently initiating conversations, so proactive scheduling needs to be handled by the application's scheduling layer.

Another challenge was making **"adaptive"** concrete. We did not want adaptation to be just a claim in the description. We therefore based it on stored preferences and interaction history so that changes in communication can be demonstrated.

We also had to consider false alarms. A person missing one check-in should not automatically trigger a caregiver alert. This led us to implement a tiered escalation approach that considers repeated or meaningful patterns.

Finally, we had to carefully define the product's scope. CareBridge focuses on wellbeing awareness and caregiver coordination rather than making medical diagnoses or emergency decisions.

## Accomplishments that we're proud of

We are proud of turning a simple reminder concept into an **agentic workflow that can understand context and determine the appropriate next action**.

We built the system around focused MCP tools rather than giving the AI unrestricted control over the application.

We are also proud of making personalization measurable. CareBridge can demonstrate how communication changes based on a user's preferences and previous interactions.

Most importantly, we designed the product around a human-centered principle:

> **The AI should support caregivers, not replace them.**

## What we learned

We learned that building a useful AI agent involves much more than connecting an LLM to an application.

The difficult questions are often about **when the agent should act, when it should wait, what context it should consider, and when a human should take over**.

We also learned the importance of designing for real-world users rather than assuming everyone interacts with technology in the same way. For older adults in particular, communication needs to be simple, personalized, and flexible.

Working with MCP and the AWS ecosystem also helped us understand how specialized tools, scheduling systems, persistent data, and AI reasoning can work together as a complete product rather than as isolated technologies.

## What's next for CareBridge - Adaptive Care & Check-In Agent

Our next steps are focused on making CareBridge more useful while keeping the system simple and trustworthy.

We plan to improve personalization, expand caregiver insights, strengthen accessibility, and support additional interaction methods.

We also want to explore deeper integrations across the Amazon ecosystem, allowing CareBridge to coordinate information from multiple sources while maintaining clear boundaries around privacy and user control.

The long-term vision is simple:

> **Help older adults maintain independence while giving their families better awareness, without requiring constant monitoring.**
