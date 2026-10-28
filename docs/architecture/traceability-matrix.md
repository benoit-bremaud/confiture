# Traceability matrix

| ID | Name | Source | Realisation | Components | Tests | Status |
|---|---|---|---|---|---|---|
| UC1 | Ask a question | REQ-2 → UC1, REQ-9 → UC1 | [02-sequence](diagrams/voice-assistant/02-sequence-ask-a-question.md) | — | — | planned |
| UC2 | Control a home device | REQ-3 → UC2, REQ-8 → UC2 | — | — | — | planned |
| UC3 | Check a room's conditions | REQ-8 → UC3 | — | — | — | planned |
| UC4 | Set a timer or reminder | REQ-2 → UC4, REQ-3 → UC4 | — | — | — | planned |
| UC5 | Wake the assistant | REQ-5 → UC5, REQ-6 → UC5, REQ-11 → UC5, REQ-14 → UC5, REQ-15 → UC5, REQ-18 → UC5 | — | — | — | planned |
| UC6 | Mute the microphones | REQ-5 → UC6, REQ-19 → UC6 | — | — | — | planned |
| UC7 | Train a custom wake word | — | — | — | — | planned |
| UC8 | Enrol a node | REQ-1 → UC8 | — | — | — | planned |
| UC9 | Check node health | — | — | — | — | planned |
| UC10 | Check the weather | — | — | — | — | planned |
| UC11 | Play music | REQ-3 → UC11, REQ-7 → UC11 | — | — | — | planned |
| NFR-1 | Voice stays local | ADR-0001, ADR-0005 | — | — | — | planned |
| NFR-2 | Responsiveness | — | — | — | — | planned |
| NFR-3 | Wake reliability | — | — | — | — | planned |
| NFR-4 | Recycled hardware | — | — | — | — | planned |
| NFR-5 | LLM path latency | ADR-0003, ADR-0004 | — | — | — | planned |
| REQ-4 | Speaker recognition | — | — | — | — | iteration 2 |
| REQ-10 | Voices | — | — | — | — | planned |
| REQ-12 | Announcement speakers | — | ADR-0006, 02-sequence | Piper (Pi 5), `yuki_say` | — | planned |
| REQ-13 | Remote visual check | Q8 | — | — | — | planned |
| REQ-16 | Answer output (Nest Mini) | REQ-12 | ADR-0006, 02-sequence, 03-deployment | Piper (Pi 5), `yuki_say`, Nest Mini | — | planned |
| REQ-17 | Barge-in | UC1 *a | — | — | — | iteration 2 |
| REQ-20 | Question log | — | — | — | — | planned |

REQ-1 to REQ-3, REQ-5 to REQ-9, REQ-11, REQ-14, REQ-15, REQ-18 and REQ-19 are traced
through the use case rows above.
