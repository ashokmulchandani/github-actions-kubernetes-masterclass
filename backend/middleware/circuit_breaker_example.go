package middleware

/*
CIRCUIT BREAKER USAGE EXAMPLE
==============================

How to wrap your database calls with circuit breaker:

```go
package main

import (
    "time"
    "github.com/trainwithshubham/skillpulse/middleware"
    "github.com/trainwithshubham/skillpulse/database"
)

// Create circuit breaker: opens after 3 failures, retries after 30 seconds
var dbCircuit = middleware.NewCircuitBreaker(3, 30*time.Second)

func GetSkillsWithCircuitBreaker() ([]Skill, error) {
    var skills []Skill

    err := dbCircuit.Execute(func() error {
        // This is the actual database call
        rows, err := database.DB.Query("SELECT * FROM skills")
        if err != nil {
            return err // This counts as a failure
        }
        defer rows.Close()
        // ... scan rows into skills ...
        return nil // This counts as a success
    })

    if err == middleware.ErrCircuitOpen {
        // Circuit is open! MySQL is down.
        // Option 1: Return cached data from Redis
        // Option 2: Return friendly error
        return nil, fmt.Errorf("Service temporarily unavailable. Try again in 30 seconds.")
    }

    return skills, err
}
```

WHAT HAPPENS:

  MySQL healthy:
    Request → Circuit CLOSED → MySQL query → ✅ success → return data

  MySQL goes down:
    Request 1 → Circuit CLOSED → MySQL query → ❌ timeout (failure 1)
    Request 2 → Circuit CLOSED → MySQL query → ❌ timeout (failure 2)
    Request 3 → Circuit CLOSED → MySQL query → ❌ timeout (failure 3)
    ⚡ Circuit OPENS!
    Request 4 → Circuit OPEN → instant error (1ms, no MySQL call!)
    Request 5 → Circuit OPEN → instant error (1ms!)
    ...users get fast error instead of 5-second timeout...
    
    30 seconds later:
    Request 50 → Circuit HALF-OPEN → try MySQL → ✅ works!
    ⚡ Circuit CLOSES!
    Request 51 → Circuit CLOSED → MySQL query → ✅ back to normal!

COMBINED WITH REDIS CACHE:

  Circuit OPEN (MySQL down)?
    → Check Redis cache → data available? → return cached data!
    → User doesn't even know MySQL is down! 🎉

  This is called "graceful degradation":
    Full service: MySQL + Redis (fresh data)
    Degraded:     Redis only (slightly stale data, but app still works!)
    Down:         Error message (only if Redis also empty)
*/
