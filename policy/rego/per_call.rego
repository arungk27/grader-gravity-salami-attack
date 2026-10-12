package opsbot.per_call

import rego.v1

# Grader 1: the check most teams ship first.
# Every call is judged on its own, with no memory of earlier calls.

per_call_limits := {
	"issue_refund": 5000,
	"apply_goodwill_credit": 2000,
}

default decision := {
	"allow": false,
	"reason": "Denied: unknown action or invalid amount. Escalate to a human for approval.",
}

decision := {"allow": true, "reason": "Approved."} if {
	limit := per_call_limits[input.action]
	is_number(input.amount)
	input.amount > 0
	input.amount <= limit
}

decision := {"allow": false, "reason": msg} if {
	limit := per_call_limits[input.action]
	is_number(input.amount)
	input.amount > limit
	msg := sprintf(
		"Denied: ₹%v is above the ₹%v per-call limit for %v. Escalate to a human for approval.",
		[input.amount, limit, input.action],
	)
}
