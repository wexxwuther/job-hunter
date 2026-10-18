# Mock interview mode

A practice run. The agent plays the interviewer for the chosen stage; the user
answers out loud or in text.

## Flow

1. Get the question order: `python scripts/build_prep_pack.py questions --stage <stage>
   --context <context.json> [--count 8]`. It opens with "tell me about yourself",
   adds questions built from the posting's requirements, then the stage bank, and
   closes with "what questions do you have for us?".
2. Ask ONE question. Wait for the full answer. Do not answer for the user.
3. Give feedback (below), then move on. Offer one retry of an answer if the user
   wants it.
4. At the end: the 2-3 strongest stories, the one answer to practice most, and any
   gap the user should think about before the real interview.

## Feedback rubric (per answer)

- **Answered the question asked?** Yes, partly, or drifted.
- **Structure:** for a "tell me about a time" question, are Situation, Task, Action,
  and Result all there? Which one is missing or thin?
- **Ownership:** "I" for what the user did; "we" only for the team's part.
- **Length:** roughly two minutes for a story, under one minute for a screen answer.
  Say what to cut.
- **Result:** is the outcome clear? A real outcome beats an impressive-sounding one.
- **Fit to this role:** which posting requirement did it show?

## Fabrication rules in mock mode

- Feedback may suggest structure, order, emphasis, and what to cut. It may NOT add a
  fact, number, tool, employer, or title.
- A "stronger version" of an answer is built only from the user's own words and
  confirmed facts. If it would need something the user has not said, ask them
  instead: "Do you know roughly how many patients a shift that was?"
- New facts the user states during the mock are theirs: add them to `facts.txt` and
  rerun the gate on any answer that will go into the saved pack.
- Interviewer questions may mention verified company research; they never assume
  anything about the user that the user did not say.
