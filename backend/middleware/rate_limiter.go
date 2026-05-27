package middleware

/*
RATE LIMITER MIDDLEWARE
=======================
Limits how many requests a user/IP can make per minute.

How it works:
  - Each IP gets a "bucket" with 100 tokens
  - Each request uses 1 token
  - Tokens refill at 10 per second
  - Bucket empty? → 429 Too Many Requests

Why two levels of rate limiting?
  - Ingress level (Phase 12.2): rough, per-IP, catches bots at the door
  - Code level (this file): precise, per-endpoint, business logic

Example:
  Normal user (2 req/sec): ✅ Always allowed
  Heavy user (50 req/sec): ✅ Allowed (within limit)
  Bot (200 req/sec): ❌ Blocked after 100 requests
*/

import (
	"net/http"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
)

// visitor tracks request count per IP
type visitor struct {
	tokens    int
	lastSeen  time.Time
}

// RateLimiter holds all visitors
type RateLimiter struct {
	visitors map[string]*visitor
	mu       sync.Mutex
	limit    int           // max tokens (requests) per window
	refill   int           // tokens added per second
	window   time.Duration // cleanup old visitors after this
}

// NewRateLimiter creates a rate limiter
// limit: max requests allowed in bucket
// refillPerSec: how many tokens refill per second
func NewRateLimiter(limit int, refillPerSec int) *RateLimiter {
	rl := &RateLimiter{
		visitors: make(map[string]*visitor),
		limit:    limit,
		refill:   refillPerSec,
		window:   5 * time.Minute,
	}

	// Cleanup old visitors every minute (prevent memory leak)
	go rl.cleanup()

	return rl
}

// cleanup removes visitors not seen in 5 minutes
func (rl *RateLimiter) cleanup() {
	for {
		time.Sleep(1 * time.Minute)
		rl.mu.Lock()
		for ip, v := range rl.visitors {
			if time.Since(v.lastSeen) > rl.window {
				delete(rl.visitors, ip)
			}
		}
		rl.mu.Unlock()
	}
}

// isAllowed checks if an IP can make a request
func (rl *RateLimiter) isAllowed(ip string) bool {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	v, exists := rl.visitors[ip]
	now := time.Now()

	if !exists {
		// First request from this IP — give full bucket
		rl.visitors[ip] = &visitor{tokens: rl.limit - 1, lastSeen: now}
		return true
	}

	// Refill tokens based on time passed
	elapsed := now.Sub(v.lastSeen).Seconds()
	v.tokens += int(elapsed) * rl.refill
	if v.tokens > rl.limit {
		v.tokens = rl.limit
	}
	v.lastSeen = now

	// Check if tokens available
	if v.tokens <= 0 {
		return false // RATE LIMITED!
	}

	v.tokens--
	return true
}

// Middleware returns a Gin middleware function
func (rl *RateLimiter) Middleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		ip := c.ClientIP()

		if !rl.isAllowed(ip) {
			c.JSON(http.StatusTooManyRequests, gin.H{
				"error":   "Too many requests",
				"message": "Rate limit exceeded. Please slow down.",
				"retry_after": "10 seconds",
			})
			c.Abort()
			return
		}

		// Add rate limit headers (tells client their status)
		c.Header("X-RateLimit-Limit", "100")
		c.Header("X-RateLimit-Remaining", "calculating")

		c.Next()
	}
}
