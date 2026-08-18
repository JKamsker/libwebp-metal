---
name: worker-session-lifecycle
description: Manage delegated Codex worker tasks from handoff through cleanup. Use whenever Codex creates, resumes, or sends work to a separate task, thread, chat, or worker session, especially for background experiments, benchmarks, reviews, or long-running implementation work. Enforce an explicit callback to the originating task, end the originating turn immediately after dispatch, gather the callback result when it wakes the task, and archive the worker after acceptance.
---

# Worker Session Lifecycle

Use a strict dispatch-and-callback lifecycle. Do not poll a worker after
delegation.

## Dispatch

1. Define one bounded task with its exact repository, branch or immutable
   commit, allowed files, expected artifact, validation, and completion
   criteria.
2. Create or resume the worker task with the user-requested model and reasoning
   effort. Record its task/thread ID and host ID when available.
3. Include the originating task ID in the worker prompt.
4. End the prompt with an explicit callback requirement:

   > Before finishing, use the task messaging tool to send the originating
   > task `<origin-task-id>` the final status, commit or artifact identifiers,
   > validation results, blockers, and push/PR status. This callback is
   > required to wake the originating task; a final answer in this worker task
   > alone is insufficient.

5. After successful dispatch, immediately end the originating turn. Tell the
   user only that the worker was dispatched and will wake this task by message.

Do not call wait, read, list, or polling tools after dispatch. Do not continue
unrelated local work in that turn. The callback starts the next turn.

## Receive and Gather

When the worker's message wakes the originating task:

1. Treat the callback as a result notification, not automatically as proof of
   completion.
2. Read the worker task once if the callback omits required details. This is
   result gathering, not polling.
3. Inspect the named commit, files, logs, tests, or remote state in proportion
   to risk. Preserve raw measurement artifacts and distinguish measured facts
   from the worker's interpretation.
4. Integrate or summarize the result in the originating task.
5. If work is incomplete, send one precise follow-up task containing the
   missing acceptance criteria and the same callback requirement, then end the
   turn again without polling.

If the worker failed to send a callback and the user manually wakes the task,
perform one result-gathering read, recover any completed output, and continue
this receive flow. Do not start a polling loop.

## Close the Worker

After gathering and accepting the result, archive the worker task with the
thread/task archival tool. Report that it was archived. Do not archive it
before collecting required artifacts or while a follow-up is still running.

The lifecycle is complete only when all four conditions hold:

- the worker output was gathered;
- the result was checked or integrated;
- the originating task received the outcome;
- the worker task was archived.

## Shared-Repository Guardrails

- Assign branch and worktree ownership explicitly. Never let two active tasks
  assume exclusive ownership of the same mutable checkout.
- Prefer an immutable starting commit for measurements and reviews.
- Tell the worker whether it may edit, commit, push, or update a PR.
- Require a narrow commit scope when the worker produces raw evidence.
- Require raw rows, commands, environment details, and checksums for delegated
  benchmarks; evaluate conclusions in the originating task unless explicitly
  delegated too.
