package opsbot.gateway

import rego.v1

# Grader 3: one grader at the gateway.
# Every action that moves money counts toward the same per-ticket totals,
# so it doesn't matter which tool the agent reaches for.

value_limit_per_ticket := 5000

max_money_moves_per_ticket := 3

money_actions := {"issue_refund", "apply_goodwill_credit"}

moved_so_far := sum(input.history.ticket_refunds_today) + sum(input.history.ticket_credits_today)

moves_so_far := count(input.history.ticket_refunds_today) + count(input.history.ticket_credits_today)

valid_amount if {
	is_number(input.amount)
	input.amount > 0
}

deny contains "amount must be a positive number" if not valid_amount

deny contains "unknown action" if not money_actions[input.action]

deny contains msg if {
	valid_amount
	moved_so_far + input.amount > value_limit_per_ticket
	msg := sprintf(
		"money returned on this ticket would total ₹%v across refunds and credits, above the ₹%v auto-approval limit",
		[moved_so_far + input.amount, value_limit_per_ticket],
	)
}

deny contains msg if {
	moves_so_far >= max_money_moves_per_ticket
	msg := sprintf("this ticket already has %v money movements today", [moves_so_far])
}

decision := {"allow": true, "reason": "Approved."} if count(deny) == 0

decision := {"allow": false, "reason": msg} if {
	count(deny) > 0
	msg := sprintf("Denied: %v. Escalate to a human for approval.", [concat("; ", sort(deny))])
}
