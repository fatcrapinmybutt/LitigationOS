---
name: error-debugging-nexus
description: "ELITE error handling & debugging — fusion of 17 error/debug/incident skills. Covers error handling patterns, detective work, error analysis, error tracing, multi-agent review, smart debugging, diagnostics, debugging strategies, systematic debugging, Python errors, bug finding, and incident response."
metadata:
  model: opus
  forged_from: 17
  forge_date: 2026-03-12
---

# ERROR-DEBUGGING-NEXUS — Elite Composite Skill

> Forged from 17 individual skills into one supreme composite.
> Sources: error-handling-patterns, error-detective, error-debugging-error-analysis, error-debugging-error-trace, error-debugging-multi-agent-review, error-diagnostics-smart-debug, error-diagnostics-error-trace, error-diagnostics-error-analysis, debugging-strategies, debugging-toolkit-smart-debug, debugger, systematic-debugging, python-error-handling, find-bugs, incident-response-smart-fix, incident-response-incident-response, incident-responder

## When to Apply

Activate this skill for ANY work related to:
- **Error Handling Patterns**: exception hierarchies, retry logic, circuit breakers, fallbacks
- **Error Detective**: root cause analysis, reproduction, bisection, hypothesis testing
- **Error Analysis**: stack trace parsing, error classification, pattern recognition
- **Error Tracing**: distributed tracing, correlation IDs, causality chains
- **Smart Debugging**: AI-assisted debugging, automated diagnosis, fix suggestions
- **Systematic Debugging**: scientific method, binary search, rubber duck, wolf fence
- **Python Error Handling**: exception best practices, custom exceptions, context managers
- **Bug Finding**: static analysis, fuzzing, property-based testing, mutation testing
- **Incident Response**: triage, mitigation, post-mortem, runbooks, SLA management
- **Multi-Agent Debug**: debugging distributed agent systems, coordination failures

---

## §1. Error Handling Patterns

> exception hierarchies, retry logic, circuit breakers, fallbacks

## §2. Error Detective

> root cause analysis, reproduction, bisection, hypothesis testing

### Reproduction Checklist
*Source: debugging-strategies*

1. **Can you reproduce it?**
   - Always? Sometimes? Randomly?
   - Specific conditions needed?
   - Can others reproduce it?

2. **Create minimal reproduction**
   - Simplify to smallest example
   - Remove unrelated code
   - Isolate the problem

3. **Document steps**
   - Write down exact steps
   - Note environment details
   - Capture error messages
```

### Phase 2: Gather Information

```markdown

### Hypothesis Formation
*Source: debugging-strategies*

Based on gathered info, ask:

1. **What changed?**
   - Recent code changes
   - Dependency updates
   - Infrastructure changes

2. **What's different?**
   - Working vs broken environment
   - Working vs broken user
   - Before vs after

3. **Where could this fail?**
   - Input validation
   - Business logic
   - Data layer
   - External services
```

### Phase 4: Test & Verify

```markdown

### Testing Strategies
*Source: debugging-strategies*

1. **Binary Search**
   - Comment out half the code
   - Narrow down problematic section
   - Repeat until found

2. **Add Logging**
   - Strategic console.log/print
   - Track variable values
   - Trace execution flow

3. **Isolate Components**
   - Test each piece separately
   - Mock dependencies
   - Remove complexity

4. **Compare Working vs Broken**
   - Diff configurations
   - Diff environments
   - Diff data
```

## §3. Error Analysis

> stack trace parsing, error classification, pattern recognition

## §4. Error Tracing

> distributed tracing, correlation IDs, causality chains

## §5. Smart Debugging

> AI-assisted debugging, automated diagnosis, fix suggestions

## §6. Systematic Debugging

> scientific method, binary search, rubber duck, wolf fence

## §7. Python Error Handling

> exception best practices, custom exceptions, context managers

### Best Practices
*Source: error-handling-patterns*

1. **Fail Fast**: Validate input early, fail quickly
2. **Preserve Context**: Include stack traces, metadata, timestamps
3. **Meaningful Messages**: Explain what happened and how to fix it
4. **Log Appropriately**: Error = log, expected failure = don't spam logs
5. **Handle at Right Level**: Catch where you can meaningfully handle
6. **Clean Up Resources**: Use try-finally, context managers, defer
7. **Don't Swallow Errors**: Log or re-throw, don't silently ignore
8. **Type-Safe Errors**: Use typed errors when possible

```python
# Good error handling example
def process_order(order_id: str) -> Order:
    """Process order with comprehensive error handling."""
    try:
        # Validate input
        if not order_id:
            raise ValidationError("Order ID is required")

        # Fetch order
        order = db.get_order(order_id)
        if not order:
            raise NotFoundError("Order", order_id)

        # Process payment
        try:
            payment_result = payment_service.charge(order.total)
        except PaymentServiceError as e:
            # Log and wrap external service error
            logger.error(f"Payment failed for order {order_id}: {e}")
            raise ExternalServiceError(
                f"Payment processing failed",
                service="payment_service",
                details={"order_id": order_id, "amount": order.total}
            ) from e

        # Update order
        order.status = "completed"
        order.payment_id = payment_result.id
        db.save(order)

        return order

    except ApplicationError:
        # Re-raise known application errors
        raise
    except Exception as e:
        # Log unexpected errors
        logger.exception(f"Unexpected error processing order {order_id}")
        raise ApplicationError(
            "Order processing failed",
            code="INTERNAL_ERROR"
        ) from e
```

### Best Practices Summary
*Source: python-error-handling*

1. **Validate early** - Check inputs before expensive operations
2. **Use specific exceptions** - `ValueError`, `TypeError`, not generic `Exception`
3. **Include context** - Messages should explain what, why, and how to fix
4. **Convert types at boundaries** - Parse strings to enums/domain types early
5. **Chain exceptions** - Use `raise ... from e` to preserve debug info
6. **Handle partial failures** - Don't abort batches on single item errors
7. **Use Pydantic** - For complex input validation with structured errors
8. **Document failure modes** - Docstrings should list possible exceptions
9. **Log with context** - Include IDs, counts, and other debugging info
10. **Test error paths** - Verify exceptions are raised correctly

## §8. Bug Finding

> static analysis, fuzzing, property-based testing, mutation testing

## §9. Incident Response

> triage, mitigation, post-mortem, runbooks, SLA management

### Phase 1: Detection & Triage
*Source: incident-response-incident-response*

### 1. Incident Detection and Classification
- Use Task tool with subagent_type="incident-responder"
- Prompt: "URGENT: Detect and classify incident: $ARGUMENTS. Analyze alerts from PagerDuty/Opsgenie/monitoring. Determine: 1) Incident severity (P0-P3), 2) Affected services and dependencies, 3) User impact and business risk, 4) Initial incident command structure needed. Check error budgets and SLO violations."
- Output: Severity classification, impact assessment, incident command assignments, SLO status
- Context: Initial alerts, monitoring dashboards, recent changes

### 2. Observability Analysis
- Use Task tool with subagent_type="observability-monitoring::observability-engineer"
- Prompt: "Perform rapid observability sweep for incident: $ARGUMENTS. Query: 1) Distributed tracing (OpenTelemetry/Jaeger), 2) Metrics correlation (Prometheus/Grafana/DataDog), 3) Log aggregation (ELK/Splunk), 4) APM data, 5) Real User Monitoring. Identify anomalies, error patterns, and service degradation points."
- Output: Observability findings, anomaly detection, service health matrix, trace analysis
- Context: Severity level from step 1, affected services

### 3. Initial Mitigation
- Use Task tool with subagent_type="incident-responder"
- Prompt: "Implement immediate mitigation for P$SEVERITY incident: $ARGUMENTS. Actions: 1) Traffic throttling/rerouting if needed, 2) Feature flag disabling for affected features, 3) Circuit breaker activation, 4) Rollback assessment for recent deployments, 5) Scale resources if capacity-related. Prioritize user experience restoration."
- Output: Mitigation actions taken, temporary fixes applied, rollback decisions
- Context: Observability findings, severity classification

## §10. Multi-Agent Debug

> debugging distributed agent systems, coordination failures

### Phase 4: Communication & Coordination
*Source: incident-response-incident-response*

### 9. Stakeholder Communication
- Use Task tool with subagent_type="content-marketing::content-marketer"
- Prompt: "Manage incident communication for: $ARGUMENTS. Create: 1) Status page updates (public-facing), 2) Internal engineering updates (technical details), 3) Executive summary (business impact/ETA), 4) Customer support briefing (talking points), 5) Timeline documentation with key decisions. Update every 15-30 minutes based on severity."
- Output: Communication artifacts, status updates, stakeholder briefings, timeline log
- Context: All previous phases, current resolution status

### 10. Customer Impact Assessment
- Use Task tool with subagent_type="incident-responder"
- Prompt: "Assess and document customer impact for incident: $ARGUMENTS. Analyze: 1) Affected user segments and geography, 2) Failed transactions or data loss, 3) SLA violations and contractual implications, 4) Customer support ticket volume, 5) Revenue impact estimation. Prepare proactive customer outreach list."
- Output: Customer impact report, SLA analysis, outreach recommendations
- Context: Resolution progress, communication status

### Coordination Protocols
*Source: incident-response-incident-response*

### Incident Command Structure
- **Incident Commander**: Decision authority, coordination
- **Technical Lead**: Technical investigation and resolution
- **Communications Lead**: Stakeholder updates
- **Subject Matter Experts**: Specific system expertise

### Communication Channels
- War room (Slack/Teams channel or Zoom)
- Status page updates (StatusPage, Statusly)
- PagerDuty/Opsgenie for alerting
- Confluence/Notion for documentation

### Handoff Requirements
- Each phase provides clear context to the next
- All findings documented in shared incident doc
- Decision rationale recorded for postmortem
- Timestamp all significant events

Production incident requiring immediate response: $ARGUMENTS
