package spooky.quality

debate_required {
  input.task.risk >= 3
}

second_opinion {
  input.validator_error_rate > 0.25
}
