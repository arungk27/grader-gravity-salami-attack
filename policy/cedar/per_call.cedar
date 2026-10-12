// Grader 1: the check most teams ship first.
// Each call is judged on its own, with no memory of earlier calls.

@id("opsbot-may-issue-refunds")
permit (
  principal == Agent::"opsbot",
  action == Action::"issue_refund",
  resource
)
when { context.amount > 0 };

@id("opsbot-may-apply-goodwill-credit")
permit (
  principal == Agent::"opsbot",
  action == Action::"apply_goodwill_credit",
  resource
)
when { context.amount > 0 };

@id("refund-above-per-call-limit")
forbid (principal, action == Action::"issue_refund", resource)
when { context.amount > 5000 };

@id("credit-above-per-call-limit")
forbid (principal, action == Action::"apply_goodwill_credit", resource)
when { context.amount > 2000 };
