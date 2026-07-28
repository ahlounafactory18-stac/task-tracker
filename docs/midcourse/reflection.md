# Reflection

For this mid-course project I used an AI assistant in two distinct modes. First as
a planner: before writing any code, I had it reconstruct the expected Modules 1–3
baseline from the prompt libraries and propose which two features would be smallest
to implement end-to-end. That planning step is where the AI was most useful — it
noticed that "Due dates + overdue filter" and "Search + combined filters" both live
in the same `GET /tasks` query path, which meant I could add two graded features
while touching only one endpoint and one data field. That framing kept the whole
change small and the tests cohesive. Second, I used it as a code generator for each
layer (model field, storage, business rule, endpoint, frontend, tests), always
treating its output as a draft to inspect and run rather than accept.

The clearest moment the AI helped was scaffolding the `is_overdue` helper and the
matching pytest cases quickly, including building due dates relative to "today" so
the suite stays correct whenever it runs. That saved real time compared with
writing the fixtures by hand.

The clearest moment it slowed me down was subtle and would have shipped a bug if I
had trusted it. The first `is_overdue` draft flagged *any* past-due task as overdue,
including tasks already marked Done. A finished task is not late, so this was wrong.
I caught it while reading the draft, not from a failing test — the test passed
because the AI had also written the test to match its own flawed assumption. I fixed
the rule to exempt Done tasks and wrote `test_completed_task_is_not_overdue` to lock
the correct behavior in, then proved it with a Break Test: removing the exemption
made that test fail, exactly as it should.

The place where my review changed the result was the search feature. The assistant
proposed filtering the already-loaded task list in the browser and, separately,
adding a new `/search` endpoint. Both were wrong for this project. Client-side
filtering would have left the backend search untested, and a new endpoint was out
of scope. I directed it to extend the existing `GET /tasks` with a `q` parameter and
have the filter bar call that endpoint, so the feature is enforced and tested on the
backend.

The habit I will carry forward is the Break Test. A green suite told me the code
worked; deliberately breaking the source and watching the *right* tests fail told me
the tests were actually protecting the behavior I cared about. Combined with reading
each diff before running it, that is what kept ownership of the work with me rather
than the AI.
