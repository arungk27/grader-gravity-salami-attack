package opsbot_test

import rego.v1

import data.opsbot.aggregate
import data.opsbot.gateway
import data.opsbot.per_call

empty_history := {"ticket_refunds_today": [], "ticket_credits_today": []}

first_slice := {
	"action": "issue_refund",
	"ticket_id": "T-4411",
	"amount": 4999,
	"history": empty_history,
}

second_slice := {
	"action": "issue_refund",
	"ticket_id": "T-4411",
	"amount": 4999,
	"history": {"ticket_refunds_today": [4999], "ticket_credits_today": []},
}

side_door := {
	"action": "apply_goodwill_credit",
	"ticket_id": "T-4411",
	"amount": 2000,
	"history": {"ticket_refunds_today": [4999], "ticket_credits_today": []},
}

string_amount := {
	"action": "issue_refund",
	"ticket_id": "T-4411",
	"amount": "4999",
	"history": empty_history,
}

test_per_call_waves_every_slice_through if {
	per_call.decision.allow with input as first_slice
	per_call.decision.allow with input as second_slice
}

test_per_call_blocks_one_big_refund if {
	not per_call.decision.allow with input as object.union(first_slice, {"amount": 12000})
}

test_aggregate_allows_the_first_slice if {
	aggregate.decision.allow with input as first_slice
}

test_aggregate_stops_the_second_slice if {
	not aggregate.decision.allow with input as second_slice
}

test_aggregate_leaves_the_credit_side_door_open if {
	aggregate.decision.allow with input as side_door
}

test_gateway_closes_the_side_door if {
	not gateway.decision.allow with input as side_door
}

test_gateway_allows_small_credit_on_a_fresh_ticket if {
	gateway.decision.allow with input as object.union(side_door, {"history": empty_history})
}

test_graders_fail_closed_on_a_string_amount if {
	not per_call.decision.allow with input as string_amount
	not aggregate.decision.allow with input as string_amount
	not gateway.decision.allow with input as string_amount
}

test_graders_fail_closed_on_unknown_action if {
	unknown := object.union(first_slice, {"action": "wire_transfer"})
	not per_call.decision.allow with input as unknown
	not aggregate.decision.allow with input as unknown
	not gateway.decision.allow with input as unknown
}
