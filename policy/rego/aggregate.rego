package opsbot.aggregate

import rego.v1

# Grader 2: a grader that remembers.
# Refunds are checked against the running total for the ticket, not just
# the size of the current call. Goodwill credits are still checked per call,
# which leaves a side door open on purpose (see gateway.rego).

refund_limit_per_ticket := 5000

max_refunds_per_ticket := 3

credit_limit_per_call := 2000

known_actions := {"issue_refund", "apply_goodwill_credit"}

refunds_so_far := sum(input.history.ticket_refunds_today)

valid_amount if {
	is_number(input.amount)
	input.amount > 0
}

deny contains "amount must be a positive number" if not valid_amount

deny contains "unknown action" if not known_actions[input.action]

deny contains msg if {
	input.action == "issue_refund"
	valid_amount
	refunds_so_far + input.amount > refund_limit_per_ticket
	msg := sprintf(
		"refunds on this ticket would total ₹%v, above the ₹%v auto-approval limit",
		[refunds_so_far + input.amount, refund_limit_per_ticket],
	)
}

deny contains msg if {
	input.action == "issue_refund"
	count(input.history.ticket_refunds_today) >= max_refunds_per_ticket
	msg := sprintf("this ticket already has %v refunds today", [count(input.history.ticket_refunds_today)])
}

deny contains msg if {
	input.action == "apply_goodwill_credit"
	valid_amount
	input.amount > credit_limit_per_call
	msg := sprintf("₹%v is above the ₹%v per-credit limit", [input.amount, credit_limit_per_call])
}

decision := {"allow": true, "reason": "Approved."} if count(deny) == 0

decision := {"allow": false, "reason": msg} if {
	count(deny) > 0
	msg := sprintf("Denied: %v. Escalate to a human for approval.", [concat("; ", sort(deny))])
}
