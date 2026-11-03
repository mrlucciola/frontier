# Quiz workflow

1. Run `doctor`. A missing database is normal before the first quiz; it is created on the first `start`.
2. `start` in the requested domain, concepts, and scope. If the request names a topic the bank lacks, say so and list the available concept keys; do not relabel an item as a new subject.
3. Present one question with all four options, exact wording and labels. Do not reveal `selection_reason` as a judgment of the learner.
4. Wait for a definite answer. If the user asks for a hint, give one and record the eventual answer with `--assisted`. If the user skips, leave it unanswered.
5. Record the answer once. Report `correct`, the correct label, and the explanation. A disputed question stays disputed: stop using it and do not rewrite stored results during the conversation.
6. Continue only through the session's selected questions. At the end, report correct/answered and assisted counts separately. Omit a mastery percentage.

Selection: unseen, unseen, weak, review in rotation, one concept per question where possible. "Weak" means the latest unaided answer to that specific item was wrong, not a judgment about the domain. Options are shuffled per session. Repeating an item never increases the distinct-item count; the latest unaided answer wins.

Scope: `global` by default. `--scope here` derives a stable `repo:<hash>` identity from
the Git common directory, so repository-specific quiz history stays separate per repo.
The quiz never reads repository code.

Evidence: a correct multiple-choice answer is recognition-level evidence. It is weaker than a teach-back and must not be reported as transfer or mastery.
