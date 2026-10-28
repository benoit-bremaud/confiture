# Glossary

| Term | Definition | Source |
|---|---|---|
| Adult | Household member with full rights, including home control. Actor (specialises Household member). | UC2, REQ-3 |
| Brain | The hosts that turn a request into an answer: the Pi 5 runs the voice pipeline (speech-to-text, intents, text-to-speech), a laptop runs the local LLM. | ADR-0004, ADR-0005 |
| Child | Household member with restricted rights (child profile). Actor (specialises Household member). | REQ-3 |
| Ducking | Temporarily lowering other devices' volume while the assistant listens or speaks. | REQ-6 |
| Home device | External connected equipment (light, plug…) the assistant can actuate. Actor. | UC2 |
| Household member | Anyone living at home who talks to the assistant (assistant vocal : membre du foyer). Actor. | UC1–UC6 |
| Intent | A known command the brain recognises without an LLM (e.g. "set a timer"). | REQ-2 |
| LLM | Large language model answering requests no intent matches. | REQ-2 |
| Maintainer | Role that sets up and keeps the system running. Actor. | UC7–UC9 |
| Music source | External or local system that provides music (streaming service or local library). Actor. | UC11 |
| Node | Any recycled Raspberry Pi that is part of confiture: a satellite or a sensor node. | UC8, UC9 |
| Satellite | Listening point with a microphone that detects the wake word and streams the request to the brain; answers may play elsewhere (Nest Mini). In iteration 1 the Pi 5 itself listens. | REQ-12, REQ-15, REQ-16 |
| Sensor node | Node that measures a room's conditions (temperature, humidity). | UC3 |
| Wake word | The assistant's spoken name that starts every voice interaction (mot d'activation). | UC5, UC7 |
| Weather service | External online service that returns forecasts for a place and date. Actor. | UC10 |
| Yuki | The assistant's name and wake word (« neige » in Japanese). | Q4 |
