// Grader 2 adds memory for refunds: the running total on the ticket.
// Goodwill credits are still only checked per call, which leaves a side door
// open on purpose. Grader 3 (money_totals.cedar) closes it.

@id("ticket-refund-total-above-limit")
forbid (principal, action == Action::"issue_refund", resource)
when { context.ticket_refunds_total + context.amount > 5000 };

@id("too-many-refunds-on-ticket")
forbid (principal, action == Action::"issue_refund", resource)
when { context.ticket_refund_count >= 3 };
