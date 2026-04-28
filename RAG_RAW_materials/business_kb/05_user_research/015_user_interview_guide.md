# User Interview Methodology

**Category**: user_research
**Source**: Nielsen Norman Group, The Mom Test (Rob Fitzpatrick), Lenny's Newsletter
**Use Case**: Research Agent and Product Agent use this methodology when designing customer discovery activities.

---

## 1. Overview

User interviews are a primary tool for understanding what people do, why they do it, and where they struggle. Conducted well, they expose problems worth solving, falsify confident assumptions, and reveal language and context the product team would never invent on its own. Conducted poorly, they produce confirmation bias dressed as evidence: smiling participants telling the team that the idea sounds great, would definitely be useful, and is something they would absolutely buy. The difference between the two outcomes is almost entirely a matter of method.

Three sources anchor modern user-interview practice. **Nielsen Norman Group** provides the research foundation: how interviews fit into the broader UX research toolkit, when to use them versus alternatives, and how many participants are needed to spot patterns. **Rob Fitzpatrick's *The Mom Test*** provides the discipline that prevents interviews from collapsing into validation theater: ask about real past behavior, not hypothetical future opinions. **Lenny Rachitsky's writing on user interviews** offers practical guidance from product leaders who run discovery as part of their daily work.

This document synthesizes the three. It defines the three types of interviews, presents the Mom Test principles in detail, contrasts good and bad question forms, introduces the 5 Whys technique for reaching root causes, lists the anti-patterns that most commonly produce false positives, covers logistics (sample size, length, recording), and provides a sample interview script for parents evaluating an educational coding app for children aged 6–12.

---

## 2. Three Types of Interviews

User interviews are not a single activity. Three distinct types serve different purposes and require different question shapes.

**Discovery interviews**
Open-ended, exploratory conversations conducted before a product or feature has been designed. The goal is to understand the user's life, work, and pain points without preconception. The interviewer brings a topic area but no prepared solution. Discovery interviews surface the problems that are worth solving and the language the user uses to describe them. They are most valuable in the earliest phase of a project, when the team's hypotheses are still soft.

**Validation interviews**
Targeted conversations aimed at testing specific hypotheses about a problem, a workflow, or a proposed solution direction. Validation differs from discovery in that the interviewer arrives with a specific claim to falsify ("we believe parents are willing to pay $10/month for measurable learning outcomes") and the questions are designed to expose whether the claim survives contact with real user behavior. Validation interviews are most useful after discovery has produced candidate problems and the team needs to choose among them.

**Usability interviews**
Observational sessions in which users interact with a product (a working prototype, a wireframe, or a shipped feature) while the interviewer watches. The goal is to discover where the interface fails users—where they hesitate, misinterpret, or give up. Usability interviews are conducted on a designed artifact rather than on abstract problems and are typically conducted later in the development cycle than discovery or validation.

The three types are complementary. A typical product development cycle uses discovery to identify problems, validation to confirm priority, and usability to refine the solution.

---

## 3. The Mom Test — Three Core Principles

Rob Fitzpatrick's *The Mom Test* gets its name from the central insight: **even your mother can give you honest feedback if you ask the right questions**. The standard objection that family and friends will tell you what you want to hear is not really about family and friends; it is about the questions being asked. Anyone, including biased respondents, can provide reliable signal if the questions are anchored to real past behavior rather than to opinions about the future. The reverse is also true: anyone, including unbiased respondents, will produce noise if the questions invite politeness.

Three principles capture the discipline.

**Principle 1: Talk about their life, not your idea.**
The interviewer's job is to understand the user's existing situation, not to pitch a product. Once the conversation turns to the team's idea, participants shift into evaluator mode—they begin offering opinions, encouragement, or polite criticism rather than describing their actual lives. The data quality drops accordingly. A useful test: if the interviewer never explicitly described the product, the participant should still produce useful information about their problems and behaviors. If the only useful information depends on the participant having heard the pitch, the questions are wrong.

**Principle 2: Ask about specifics in the past, not generics or opinions about the future.**
"What do you usually do when…" invites generalization, which invites confabulation. "Would you use a tool that…" invites speculation, which is unreliable. "Tell me about the last time you…" invites a specific story, which is grounded in actual behavior. Past behavior is the most reliable predictor of future behavior, and specific past episodes contain the texture, friction, and emotional tone that abstract answers miss.

**Principle 3: Talk less and listen more.**
A good interviewer's voice should occupy a small fraction of total airtime. Most novice interviewers fill silences with their own commentary, narrate the product, or rush to the next question. The discipline is to ask a question, listen fully, allow silence, and follow up on the most interesting thread the participant raised. The participant's words are the data; the interviewer's words are overhead.

The combined effect of the three principles is that interviews produce evidence about real user lives rather than reactions to the team's pitch. This is the only kind of interview data worth acting on.

---

## 4. Question Templates

Good interview questions share a structure: they ask about specific past episodes, they invite the participant to do most of the talking, and they avoid framing that suggests the desired answer. The table below contrasts good and bad forms of common questions.

| Bad question | Why it fails | Good replacement |
|---|---|---|
| "Would you use a feature that…?" | Future hypothetical; people answer politely. | "Tell me about the last time you faced [problem the feature would address]. What did you do?" |
| "Wouldn't it be great if our app could…?" | Leading; participant agrees to be agreeable. | "Walk me through your current workflow for [task]. What's the hardest part?" |
| "How much would you pay for this?" | Pricing speculation is unreliable; people don't know. | "What have you spent on solving this in the past? What did you choose, and why that option?" |
| "Do you think [feature] is important?" | Solicits opinion, not evidence. | "Tell me about the last time you needed [feature's underlying job]. What did you do without it?" |
| "Would you recommend this to a friend?" | Future hypothetical; produces inflated NPS-like answers. | "Have you ever recommended a [tool in this category] to anyone? Tell me about that." |
| "Are you happy with [current solution]?" | Yes/no question about feelings. | "Tell me about the last time [current solution] frustrated you. What happened?" |

A useful core set of question stems, all rooted in past behavior, applies to almost any discovery context:

- "Tell me about the last time you [did X]."
- "What was the hardest part about that?"
- "Have you tried solving this? What did you try? Why didn't it work?"
- "How do you do [task] today?"
- "Walk me through how you decided to [buy / use] X."

These stems work because they invite the participant to recount a specific episode, surface friction, and reveal both the workflow and the criteria they actually used—as opposed to the criteria they would describe in the abstract.

---

## 5. The 5 Whys Technique

The 5 Whys is a follow-up technique borrowed from root-cause analysis. When a participant describes a behavior or pain point, the interviewer asks "why" repeatedly—typically up to about five times—to peel back the surface explanation and reach the underlying motivation.

A worked example from a parent interview about a child's coding app:

1. "We stopped using the app." — *Why?*
2. "My daughter lost interest after about two weeks." — *Why?*
3. "She kept getting stuck on the same kind of problem." — *Why was that frustrating?*
4. "Because she felt stupid, and there was no one to help her." — *Why no help?*
5. "The hint button just told her the answer, and that didn't teach her anything—she wanted to figure it out herself with a smaller nudge."

The surface answer ("she lost interest") is true but unactionable. The root cause—a hint system that gave away too much and undermined the child's sense of competence—is specific and points directly to a product change. The 5 Whys is best used sparingly; asking "why" five times mechanically can feel interrogative. Skilled interviewers vary the phrasing ("what was going on there?", "tell me more about that," "what made that the moment you decided?") while pursuing the same depth.

---

## 6. Anti-Patterns to Avoid

Several patterns reliably produce misleading data and should be recognized and avoided.

- **Pitching the idea instead of asking about the user's life.** The moment the participant understands what the team is building, their answers shift from descriptive to evaluative. Avoid revealing the idea until after the discovery questions are exhausted.
- **Hypothetical questions about the future.** "Would you," "could you imagine," "if we built" all invite speculation. Replace with past-behavior framings.
- **Compliments and validation-seeking.** "We're really excited about this idea, what do you think?" produces polite agreement. Stay neutral.
- **Leading questions.** "Wouldn't it be great if…" telegraphs the desired answer.
- **Closed yes/no questions.** Single-word answers carry little signal. Use open questions that invite stories.
- **Asking about pricing in the abstract.** "How much would you pay?" produces unreliable numbers. Ask what they have actually paid for related products.
- **Filling silence.** When the participant pauses, the interviewer's instinct is to talk. Resist; pauses often produce the most valuable follow-on disclosures.
- **Treating one strong opinion as evidence.** A single emphatic participant is not a pattern. Patterns appear across multiple interviews; isolated strong reactions are noise until corroborated.
- **Confirmation bias in note-taking.** Writing down only the answers that support the team's hypothesis filters the data. Record everything; tag and analyze afterward.

---

## 7. Logistics — Sample Size, Length, Recording

**Sample size.** Nielsen Norman Group's research and broader practice converge on **5–10 deep interviews per persona** as sufficient to spot patterns. Diminishing returns set in quickly past that range; the sixth interview rarely produces an insight that the first five did not foreshadow. If interviews continue to produce surprising new findings past the tenth, the persona is probably not yet well-defined and should be split.

**Length.** **30 to 60 minutes** is the standard interview length. Shorter sessions struggle to reach the depth where useful insights appear; longer sessions exhaust both participant and interviewer and produce diminishing returns on attention.

**Recording.** Always record with explicit consent, and obtain consent in writing where required by jurisdiction. Recording allows the interviewer to focus on the conversation rather than note-taking and supports later analysis. Transcribe afterward and tag transcripts by theme; tagged transcripts make patterns across interviews visible in a way that raw notes do not.

**Other logistics.** Schedule with buffer time before and after for setup and notes. Offer modest incentives where appropriate; this improves no-show rates and signals respect for the participant's time. Conduct interviews in environments where the participant is comfortable; remote video is now standard and works well. Brief any second observers (designers, engineers) on the protocol—their well-meant interjections can derail the conversation.

---

## 8. Example: Interview Plan for Educational Coding App for Kids

The following is a sample 8–10 question discovery script for parents of children aged 6–12. The script applies the Mom Test principles: every question asks about real past behavior, not opinions about the team's idea or future hypotheticals.

**Opening (rapport, context)**

1. "To start, can you tell me a bit about your child—age, what they like to do for fun, and what their typical week looks like?"
2. "Tell me about your child's screen time on a typical school day. What apps or activities are they using, and roughly how long?"

**Current behavior (existing solutions)**

3. "Tell me about the last time your child used an educational app or game—not entertainment, but something you considered learning. What was it, and how did they end up on it?"
4. "Walk me through how you decided to let them use that app. What made you pick it, and what alternatives did you consider?"
5. "What's the longest your child has stuck with any educational app? Tell me about that one—what kept them coming back?"

**Pain points and friction**

6. "Tell me about the last time you felt frustrated with an educational app your child was using. What happened?"
7. "Have you ever tried something specifically to teach your child to code or to introduce them to programming? What did you try, and how did it go?"

**Decision-making and willingness to act**

8. "When you've paid for a kids' educational app or product in the past, walk me through how you decided it was worth paying for. What did you pay, and how did you decide?"
9. "How do you currently know whether your child is actually learning something from an app, versus just being entertained by it?"

**Closing**

10. "Is there anything I haven't asked about your child's learning or screen time that you think would be useful for me to understand?"

Notes on what the script avoids. There is no question of the form "Would you use an app that teaches your child Python?"—a future hypothetical that would produce polite agreement. There is no pricing speculation; instead, question 8 asks what the parent has actually paid in the past. The team's product is not described at any point. The script invites stories from real recent episodes, and the follow-up technique (5 Whys, "tell me more about that") is applied during the conversation as the participant's answers reveal threads worth pursuing.

---

## 9. References

- Nielsen Norman Group — User Interviews: https://www.nngroup.com/articles/user-interviews/
- Rob Fitzpatrick — The Mom Test: https://www.momtestbook.com/
- Lenny's Newsletter — How to Do User Interviews: https://www.lennysnewsletter.com/p/how-to-do-user-interviews