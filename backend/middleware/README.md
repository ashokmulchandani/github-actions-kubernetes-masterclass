# Rate Limiter Middleware

## How to enable in main.go

```go
package main

import (
    "github.com/trainwithshubham/skillpulse/middleware"
)

func main() {
    router := gin.Default()

    // Create rate limiter: 100 requests max, refill 10/second
    limiter := middleware.NewRateLimiter(100, 10)

    // Apply to ALL routes
    router.Use(limiter.Middleware())

    // OR apply to specific routes only
    api := router.Group("/api")
    api.Use(limiter.Middleware())
    {
        api.GET("/skills", handlers.GetSkills)
        api.POST("/skills", handlers.CreateSkill)
    }
}
```

## What happens

```
Normal user (2 req/sec):
  Request 1: ✅ 200 OK (X-RateLimit-Remaining: 99)
  Request 2: ✅ 200 OK (X-RateLimit-Remaining: 98)

Bot (1000 req/sec):
  Request 1-100: ✅ 200 OK
  Request 101:   ❌ 429 Too Many Requests
                 {"error": "Too many requests", "retry_after": "10 seconds"}
```

## Token Bucket Algorithm (what we use)

```
Bucket starts with 100 tokens
Each request uses 1 token
10 tokens refill every second

Timeline:
  0s:  100 tokens (full)
  1s:  User made 20 requests → 80 tokens + 10 refilled = 90 tokens
  2s:  User made 50 requests → 40 tokens + 10 refilled = 50 tokens
  3s:  User made 60 requests → BLOCKED at request #51 (0 tokens)
  4s:  10 tokens refilled → can make 10 more requests
```
