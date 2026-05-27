package middleware

/*
CIRCUIT BREAKER PATTERN
========================
Protects your app when a dependency (MySQL, Redis, external API) goes down.

States:
  🟢 CLOSED  → normal, requests flow through
  🔴 OPEN    → dependency is down, fail fast (don't wait)
  🟡 HALF-OPEN → testing if dependency recovered

Config:
  MaxFailures: 3 (open circuit after 3 consecutive failures)
  Timeout: 30 seconds (try again after 30 seconds)

Without circuit breaker:
  MySQL down → every request waits 5s for timeout → app freezes
  
With circuit breaker:
  MySQL down → 3 failures → circuit opens → instant error (1ms)
  → 30 seconds later → test one request → MySQL back? → circuit closes
*/

import (
	"errors"
	"sync"
	"time"
)

// State of the circuit breaker
type State int

const (
	StateClosed   State = iota // 🟢 Normal - requests flow
	StateOpen                  // 🔴 Broken - fail fast
	StateHalfOpen              // 🟡 Testing - one request allowed
)

// CircuitBreaker protects calls to external services
type CircuitBreaker struct {
	mu            sync.Mutex
	state         State
	failures      int
	maxFailures   int
	timeout       time.Duration
	lastFailure   time.Time
	successCount  int
	totalRequests int
	totalFailures int
}

// Errors
var (
	ErrCircuitOpen = errors.New("circuit breaker is OPEN - service unavailable, try again later")
)

// NewCircuitBreaker creates a circuit breaker
// maxFailures: how many failures before opening (e.g., 3)
// timeout: how long to wait before testing again (e.g., 30 seconds)
func NewCircuitBreaker(maxFailures int, timeout time.Duration) *CircuitBreaker {
	return &CircuitBreaker{
		state:       StateClosed,
		maxFailures: maxFailures,
		timeout:     timeout,
	}
}

// Execute runs a function through the circuit breaker
// If circuit is open, returns error immediately (fast fail)
// If circuit is closed, runs the function normally
func (cb *CircuitBreaker) Execute(fn func() error) error {
	cb.mu.Lock()
	cb.totalRequests++

	switch cb.state {
	case StateOpen:
		// Check if timeout has passed (should we try again?)
		if time.Since(cb.lastFailure) > cb.timeout {
			// Move to half-open: allow ONE test request
			cb.state = StateHalfOpen
			cb.mu.Unlock()
			return cb.doRequest(fn)
		}
		cb.mu.Unlock()
		// Circuit is OPEN — fail immediately (don't even try)
		return ErrCircuitOpen

	case StateHalfOpen:
		cb.mu.Unlock()
		return cb.doRequest(fn)

	default: // StateClosed
		cb.mu.Unlock()
		return cb.doRequest(fn)
	}
}

// doRequest executes the actual request and updates state
func (cb *CircuitBreaker) doRequest(fn func() error) error {
	err := fn()

	cb.mu.Lock()
	defer cb.mu.Unlock()

	if err != nil {
		// Request FAILED
		cb.failures++
		cb.totalFailures++
		cb.lastFailure = time.Now()

		if cb.failures >= cb.maxFailures {
			// Too many failures → OPEN the circuit
			cb.state = StateOpen
		}
		return err
	}

	// Request SUCCEEDED
	cb.failures = 0
	cb.successCount++

	if cb.state == StateHalfOpen {
		// Was testing → test passed → CLOSE the circuit
		cb.state = StateClosed
	}

	return nil
}

// GetState returns current state as string (for logging/monitoring)
func (cb *CircuitBreaker) GetState() string {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	switch cb.state {
	case StateClosed:
		return "🟢 CLOSED"
	case StateOpen:
		return "🔴 OPEN"
	case StateHalfOpen:
		return "🟡 HALF-OPEN"
	default:
		return "UNKNOWN"
	}
}

// GetStats returns circuit breaker statistics
func (cb *CircuitBreaker) GetStats() map[string]interface{} {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	return map[string]interface{}{
		"state":          cb.GetState(),
		"failures":       cb.failures,
		"max_failures":   cb.maxFailures,
		"total_requests": cb.totalRequests,
		"total_failures": cb.totalFailures,
		"success_count":  cb.successCount,
	}
}
