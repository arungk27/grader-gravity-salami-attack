// Grader 3: one grader at the gateway.
// Every action that moves money counts toward the same per-ticket totals,
// so it doesn't matter which tool the agent reaches for.

@id("ticket-money-total-above-limit")
forbid (
  principal,
  action in [Action::"issue_refund", Action::"apply_goodwill_credit"],
  resource
)
when { context.ticket_money_total + context.amount > 5000 };

@id("too-many-money-moves-on-ticket")
forbid (
  principal,
  action in [Action::"issue_refund", Action::"apply_goodwill_credit"],
  resource
)
when { context.ticket_money_moves >= 3 };
